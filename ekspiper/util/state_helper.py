import boto3
import yaml
import logging
import json

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def load_from_s3(bucket: str = 'caspian-ripplex-dev', path: str = '/app_data/state'):
    logger.info("[StateHelper] Loading from s3 bucket [%s] and path [%s]", bucket, path)
    try:
        s3 = boto3.client('s3')
        obj = s3.get_object(Bucket=bucket, Key=path)
        state = json.loads(obj['Body'].read().decode('utf-8'))
        logger.info("[StateHelper] Loaded state: %s", str(state))
        return state
    except Exception as e:
        logger.error("[StateHelper] Failed to load from S3: %s", str(e))
    return None


def save_ledger_to_s3(ledger: int, bucket: str = 'caspian-ripplex-dev', path: str = '/app_data/state'):
    save_data = {}

    if ledger is not None:
        save_data["ledger_index"] = ledger
        logger.info("[StateHelper] Saving state to S3: %s", str(save_data))
        save_data_bytes = json.dumps(save_data).encode('utf-8')
        return save_to_s3(save_data_bytes, bucket=bucket, path=path)
    else:
        logger.info("[StateHelper] No ledger to save")

    return False


def save_to_s3(data, bucket: str = 'caspian-ripplex-dev', path: str = '/app_data/state'):
    try:
        if data is not None:
            s3 = boto3.client('s3')
            logger.info("[StateHelper] Saving data to path %s", path)
            s3.put_object(Body=data, Key=path, Bucket=bucket)
    except Exception as e:
        logger.error("[StateHelper] Failed to save to s3: %s", str(e))
        return False

    return True


def load_from_file(yml_path: str):
    logger.info("[StateHelper] loading config from path: " + yml_path)
    try:
        with open(yml_path, mode="rt", encoding="utf-8") as file:
            yml_config = yaml.safe_load(file)
            logger.info("[StateHelper] config file: " + str(yml_config))
    except Exception as e:
        logger.info("[StateHelper] Wasn't able to load config file: " + str(e))

    return yml_config


def write_to_file(ledger: str, ledger_path: str):
    try:
        if ledger is not None:
            with open(ledger_path, "w") as f:
                f.write(ledger + "\n")
                logger.info("[StateHelper] Writing ledger [%s] to path [%s]", ledger, ledger_path)
    except Exception as e:
        logger.error("[StateHelper] Failed to write to file: " + str(e))


def read_from_file(ledger_path: str):
    try:
        with open(ledger_path, "r") as f:
            logger.info("[StateHelper] Reading ledger index from file")
            for line in f:
                starting_index = int(line)
    except FileNotFoundError:
        logger.info("[StateHelper] No ledger index file present")

    return starting_index
