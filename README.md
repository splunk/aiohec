# aiohec

An async module for sending data to Splunk HEC endpoints


## Setup

The Splunk instance being used must already have a HEC endpoint setup and configured.
More information is available [here](https://docs.splunk.com/Documentation/Splunk/latest/Data/UsetheHTTPEventCollector)

## Installation

    pip3 install git+git://github.com/splunk/aiohttp.git

## Quick Start

    from aiohec import SplunkHEC

    splunk_host = "localhost"
    token = "XXXX"

    async with SplunkHEC(splunk_host=splunk_host, token=token) as hec:
        for r in my_data:
            hec.add_event(r)


### Additional options

`max_consumers`: Maximum number of async consumers for sending data to the HEC endpoint

`max_qsize`: Maximum number of events in the queue before it is automatically flushed

`max_content_length`: Maximum content length, in bytes, that the HEC endpoint will accept. See [limits.conf](https://docs.splunk.com/Documentation/Splunk/latest/Admin/Limitsconf#.5Bhttp_input.5D) for configuration options.

`host`: Hostname of the originating events

`source`: Source name of the originating events

`index`: Index to send events into

`sourcetype`: Sourcetype of the originating events

## Todo

[ ] Add support for raw events

[ ] Create tests

[ ] Create more robust documentation
