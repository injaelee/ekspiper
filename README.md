# ekspiper
Data pipeline library

# Tasks

## Task: Ledger Details
- Input Source
  - New Ledger Events
- Processors
  - Ledger Details
    - Queue Collector (book_offers_fetch_flow_q)
    - Queue Collector (txn_record_flow_q)

## Task: Book Offers Fetch Flow
- Input Source
  - Queue Source (book_offers_fetch_flow_q)
- Processors
  - Book Offer Builder Processor
    - Queue Collector (book_offers_req_flow_q)

## Task: Book Offers Record Flow
- Input Source
  - Queue Source (book_offers_req_flow_q)
- Processors
  - Book Offer Request Processor
    - Fluent Collector
    - Metric Collector

## Task: Transaction Record Flow
- Input Source
  - Queue Source (txn_record_flow_q)
- Processors
  - ETLProcessor
    - Fluent Collector