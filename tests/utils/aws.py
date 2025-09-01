from contextlib import contextmanager
from botocore.stub import Stubber
import boto3


@contextmanager
def stubbed_client(service, **kwargs):
    client = boto3.client(service, **kwargs)
    with Stubber(client) as stub:
        yield client, stub

# Example:
# with stubbed_client("s3") as (s3, stub):
#     stub.add_response("list_buckets", {"Buckets": []})
#     assert s3.list_buckets()["Buckets"] == []
