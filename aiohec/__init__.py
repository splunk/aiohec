#!/usr/bin/env python3

__version__ = "0.2.1"
__author__ = "Marcus LaFerrera (@mlaferrera)"

import asyncio
import json
import logging
import sys
from typing import Any, Dict, Union

import aiohttp


logger = logging.getLogger(__name__)


class SplunkHEC:

    RETRY_STATUS_CODES = [500, 503]

    def __init__(
        self,
        splunk_host: str,
        token: str,
        splunk_port: str = "8088",
        max_consumers: int = 20,
        max_qsize: int = 50_000,
        max_content_length: int = 100_000,
        max_retries: int = 2,
        verify_ssl: bool = False,
        timeout: int = 600,
        host: str = None,
        source: str = None,
        index: str = None,
        sourcetype: str = None,
    ) -> None:
        self.splunk_host = f"https://{splunk_host}:{splunk_port}/services/collector"
        self.headers: Dict[str, str] = {"Authorization": f"Splunk {token}"}
        self.max_consumers = max_consumers
        self.max_qsize = max_qsize
        self.max_content_length = max_content_length
        self.max_retries = max_retries
        self.verify_ssl = verify_ssl
        self.timeout = timeout
        event_meta_matrix = dict(
            host=host, source=source, index=index, sourcetype=sourcetype
        )
        self.event_meta = {k: v for k, v in event_meta_matrix.items() if v}
        self.count = 0
        self.queue = asyncio.Queue(maxsize=self.max_qsize)
        self.consumers = [
            asyncio.create_task(self._batch_post(self.queue))
            for _ in range(self.max_consumers)
        ]

    async def __aenter__(self):
        logger.debug("__aenter__")
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
        host: str = None,
        source: str = None,
        index: str = None,
        sourcetype: str = None,
    ) -> None:
        logger.debug(f"add_event: {entry}")
        event: Dict[str, Union[Dict[str, Any], str]] = {"event": entry}
        event.update(
            self.set_event_meta(
                host=host, source=source, index=index, sourcetype=sourcetype
            )
        )
        await self.queue.put(event)

    def set_event_meta(
        self,
        host: str = None,
        source: str = None,
        index: str = None,
        sourcetype: str = None,
    ) -> Dict[str, str]:
        new_event_meta = dict(
            host=host, source=source, index=index, sourcetype=sourcetype
        )
        event_meta = self.event_meta.copy()
        event_meta.update({k: v for k, v in new_event_meta.items() if v})
        return event_meta

    async def _post_events(self, session, events) -> aiohttp.ClientResponse:
        return await session.post(
            self.splunk_host,
            headers=self.headers,
            data="".join(events),
            ssl=self.verify_ssl,
        )

    async def _batch_post(self, queue: asyncio.Queue):
        logger.debug("_batch_post")
        timeout = aiohttp.ClientTimeout(total=self.timeout)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            while True:
                retry_count = 0
                logger.debug(f"Queue Size: {queue.qsize()}")
                events = [json.dumps(await queue.get())]
                while (
                    not queue.empty()
                    and sys.getsizeof(events) < self.max_content_length
                ):
                    events.append(json.dumps(await queue.get()))

                while retry_count <= self.max_retries:
                    retry: Union[str, bool] = False
                    try:
                        response = await self._post_events(session, events)
                        if response.status in self.RETRY_STATUS_CODES:
                            retry = f"Failed to post {len(events)} to {self.splunk_host}, status: {response.status}, response: {response.content}"
                        else:
                            break
                    except asyncio.exceptions.TimeoutError:
                        retry = f"Timeout when posting {len(events)} events to {self.splunk_host}"
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
