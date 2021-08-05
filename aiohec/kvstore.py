#!/usr/bin/env python3

#  Copyright 2021 Splunk Inc.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

import asyncio
import json
import logging
import sys
from typing import Dict, Union

import aiohttp


logger = logging.getLogger(__name__)


class SplunkKVStore:

    RETRY_STATUS_CODES = [500, 503]

    def __init__(
        self,
        host: str,
        username: str,
        password: str,
        app: str,
        collection: str,
        port: str = "8089",
        max_consumers: int = 20,
        max_qsize: int = 50_000,
        max_content_length: int = 1000,
        max_retries: int = 2,
        verify_ssl: bool = False,
        timeout: int = 600,
    ) -> None:
        self.app = app
        self.collection = collection
        self.url = (
            f"https://{host}:{port}/servicesNS/nobody/{self.app}/storage/collections"
        )
        self.headers: Dict[str, str] = {
            "Content-Type": "application/json",
            "Accept": "text/plain",
        }
        self.auth = aiohttp.BasicAuth(username, password)
        self.max_consumers = max_consumers
        self.max_qsize = max_qsize
        self.max_content_length = max_content_length
        self.max_retries = max_retries
        self.verify_ssl = verify_ssl
        self.timeout = timeout
        self.count = 0
        self.queue = asyncio.Queue(maxsize=self.max_qsize)
        self.consumers = [
            asyncio.create_task(self._batch_post(self.queue))
            for _ in range(self.max_consumers)
        ]

    async def __aenter__(self):
        logger.debug("__aenter__")
        timeout = aiohttp.ClientTimeout(total=self.timeout)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            await self.wipe_collection(session)
        return self

    async def __aexit__(self, *args):
        logger.debug(f"__aexit__({args})")
        await self.queue.join()
        for consumer in self.consumers:
            consumer.cancel()
        logger.debug(f"Processed {self.count} events")

    async def add_event(
        self,
        entry: Dict,
    ) -> None:
        logger.debug(f"add_event: {entry}")
        await self.queue.put(entry)

    async def create_collection(self, session) -> aiohttp.ClientResponse:
        return await session.post(
            f"{self.url}/config/{self.collection}",
            auth=self.auth,
            data=f"name={self.collection}",
            ssl=self.verify_ssl,
        )

    async def wipe_collection(self, session) -> aiohttp.ClientResponse:
        return await session.delete(
            f"{self.url}/data/{self.collection}",
            auth=self.auth,
            ssl=self.verify_ssl,
        )

    async def _post_events(self, session, events) -> aiohttp.ClientResponse:
        return await session.post(
            f"{self.url}/data/{self.collection}/batch_save",
            auth=self.auth,
            headers=self.headers,
            data=json.dumps(events),
            ssl=self.verify_ssl,
        )

    async def _batch_post(self, queue: asyncio.Queue):
        logger.debug("_batch_post")
        timeout = aiohttp.ClientTimeout(total=self.timeout)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            while True:
                retry_count = 0
                logger.debug(f"Queue Size: {queue.qsize()}")
                events = [await queue.get()]
                while (
                    not queue.empty()
                    and sys.getsizeof(events) < self.max_content_length
                ):
                    events.append(await queue.get())

                while retry_count <= self.max_retries:
                    retry: Union[str, bool] = False
                    try:
                        response = await self._post_events(session, events)
                        if response.status in self.RETRY_STATUS_CODES:
                            retry = f"Failed to post {len(events)} to {self.url}, status: {response.status}, response: {response.content}"
                        else:
                            break
                    except asyncio.exceptions.TimeoutError:
                        retry = (
                            f"Timeout when posting {len(events)} events to {self.url}"
                        )
                    except:  # type: ignore
                        logger.warn(
                            f"Failed to post {len(events)} events", exc_info=True
                        )
                        break
                    finally:
                        if retry:
                            retry_count += 1
                            if retry_count <= self.max_retries:
                                logger.warn(f"retry_count: {retry_count}, msg: {retry}")
                                await asyncio.sleep(retry_count * 2)
                self.count += len(events)
                for _ in events:
                    queue.task_done()
