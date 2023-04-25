# Set up

## Environment Variable

```bash
export GOOGLE_APPLICATION_CREDENTIALS="KEY_PATH"
```

# Usage

```bash
-- print the BigQuery schema transation given 
-- the 'ledger_object' schema
-- 
python tool.py --schame ledger_object --print
```

```bash
python tool.py --schema ledger_object \
--project ripplex-347905 \
--dataset rx \
--table xrpl_ledger_objects

python tool.py --schema ledger_object \
--project ripplex-ilee-pipeline \
--dataset raw_xrpl_data \
--table xrpl_ledger_objects

```