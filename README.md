# ekspiper
Data pipeline asyncio library for I/O bounded workflows.

# Execute
If you are not looking to use this as a library, this is to execute a running daemon server to kick off the set up flow. 
```bash
python server_container.py
```

## Standalone
For downloading/exporting all the ledger objects in a given ledger index:
```bash
python get_ledger_objects.py

-- examples
--
time python get_ledger_objects.py -ft prod -x https://73322D636C696F.ripple.com:51233
time python get_ledger_objects.py -ft devnet -x https://s.devnet.rippletest.net:51234

```

# General Structure and Components
Behavior is constructed using composite components designed to run under a template. Each component has a responsibility and individually testable. See the `template.TemplateFlow` class for the details. The general flow of the template is the following.

```python
for message in iterator:

  for pc in processor_collectors_maps:

    outputs = pc.processor.process(message)

    for o in outputs:

      for c in pc.collectors:

        c.collect_output(output)
```

The key components that make up the flow are:
- an implementation of `connect.DataSource`: the `iterator`
- implementation of `processor.EntryProcessor`: the `processor` in the map
- an implementation of `collector.OutputCollector`: a list of `collectors` in the map

## Note: Special Type `QueueSourceSink`
This type acts as a glue between the templatized flows. It may act as input to one flow while acting as a collector to another flow.


# Flows
Check out the "build_template_flows" method in `server_container.py`.

## Flow: Ledger Details
- Data Source
  - New Ledger Events
- Processors
  - Ledger Details
    - Queue Collector (book_offers_fetch_flow_q)
    - Queue Collector (ledger_record_flow_q)

## Flow: Book Offers Fetch Flow
- Data Source
  - Queue Source (book_offers_fetch_flow_q)
- Processors
  - Book Offer Builder Processor
    - Queue Collector (book_offers_req_flow_q)

## Flow: Book Offers Record Flow
- Data Source
  - Queue Source (book_offers_req_flow_q)
- Processors
  - Book Offer Request Processor
    - Fluent Output Collector
    - Metric Output Collector

## Flow: Ledger to Transactions Break Flow
- Data Source
  - Queue Source (ledger_record_flow_q)
- Processors
  - Extract-Transaction-From-Ledger Processor
    - Queue Collector (txn_records_flow_q)

## Flow: Transaction Record Flow
- Data Source
  - Queue Source (txn_records_flow_q)
- Processors
  - ETLProcessor
    - Fluent Output Collector
