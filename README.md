# aiohec

An async Splunk module for Getting Data In (GDI).


## Setup

The Splunk instance being used must already have a HEC endpoint setup and configuredi to use `SplunkHEC`.
More information is available [here](https://docs.splunk.com/Documentation/Splunk/latest/Data/UsetheHTTPEventCollector)

You can find more information on KV store [here](https://docs.splunk.com/Documentation/Splunk/8.2.1/Admin/AboutKVstore).

## Installation

    pip3 install git+git://github.com/splunk/aiohec.git

## Quick Start

### HTTP Event Collector (HEC)

    from aiohec import SplunkHEC

    splunk_host = "localhost"
    token = "XXXX"

    async with SplunkHEC(splunk_host=splunk_host, token=token) as hec:
        for r in my_data:
            await hec.add_event(r)

#### Additional options (HEC)

`max_consumers`: Maximum number of async consumers for sending data to the HEC endpoint

`max_qsize`: Maximum number of events in the queue before it is automatically flushed

`max_content_length`: Maximum content length, in bytes, that the HEC endpoint will accept. See [limits.conf](https://docs.splunk.com/Documentation/Splunk/latest/Admin/Limitsconf#.5Bhttp_input.5D) for configuration options.

`host`: Hostname of the originating events

`source`: Source name of the originating events

`index`: Index to send events into

`sourcetype`: Sourcetype of the originating events


### KVStore

    from aiohec import SplunkKVStore

    splunk_host = "localhost"
    username = "admin"
    password = "changeme"
    app = "search"
    collection = "my_kvstore_collection"

    async with SplunkKVStore(
        splunk_host=splunk_host, 
        username=username, 
        password=password, 
        app=app, 
        collection=collection
    ) as kvstore:
        for r in my_data:
            await kvstore.add_event(r)


## Todo

[ ] Add support for raw events for `SplunkHEC`

[ ] Create tests

[ ] Create more robust documentation
