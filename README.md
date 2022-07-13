# ekspiper
Data pipeline asyncio library for I/O bounded workflows.

# General Structure and Components
## Templatized Processor Flow
```
# the major components are:
#   - datasource_iterator
#   - process_collectors
#     - processor
#     - list of collectors
#
for data in datasource_iterator:
    for pc in process_collectors_list:
        outputs = pc.processor.process(data)
        for o in outputs:
            for c in pc.collectors:
                c.collect_output(o) 
```
## Message Iterator
- TODO

## Processor
- TODO

## Output Collector
- TODO

# Tasks

## Task: Ledger Details
- Data Source
  - New Ledger Events
- Processors
  - Ledger Details
    - Queue Collector (book_offers_fetch_flow_q)
    - Queue Collector (txn_record_flow_q)

## Task: Book Offers Fetch Flow
- Data Source
  - Queue Source (book_offers_fetch_flow_q)
- Processors
  - Book Offer Builder Processor
    - Queue Collector (book_offers_req_flow_q)

## Task: Book Offers Record Flow
- Data Source
  - Queue Source (book_offers_req_flow_q)
- Processors
  - Book Offer Request Processor
    - Fluent Output Collector
    - Metric Output Collector

## Task: Transaction Record Flow
- Data Source
  - Queue Source (txn_record_flow_q)
- Processors
  - ETLProcessor
    - Fluent Output Collector