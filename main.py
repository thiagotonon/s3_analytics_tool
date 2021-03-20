import sys
import datetime

import boto3
from botocore.exceptions import ClientError

S3_STORAGE_PRICE_PER_GB = 0.0023
S3_STORAGE_AVAILABLE_TYPES = [
    'StandardStorage', 'IntelligentTieringFAStorage', 'IntelligentTieringIAStorage',
    'IntelligentTieringAAStorage', 'IntelligentTieringDAAStorage', 'StandardIAStorage',
    'StandardIASizeOverhead', 'StandardIAObjectOverhead', 'OneZoneIAStorage',
    'OneZoneIASizeOverhead', 'ReducedRedundancyStorage', 'GlacierStorage', 'GlacierStagingStorage',
    'GlacierObjectOverhead', 'GlacierS3ObjectOverhead', 'DeepArchiveStorage',
    'DeepArchiveObjectOverhead', 'DeepArchiveS3ObjectOverhead', 'DeepArchiveStagingStorage'
]

def get_s3_metric_data(metric_name, storage_types, bucket_name):
    metric_data_queries = []

    for idx, storage_type in enumerate(storage_types):
        metric_item = {
            'Id': f'metric_alias{idx}',
            'MetricStat': {
                'Metric': {
                    'Namespace': 'AWS/S3',
                    'MetricName': metric_name,
                    'Dimensions': [
                        {'Name': 'StorageType', 'Value': storage_type},
                        {'Name': 'BucketName', 'Value': bucket_name}
                    ]
                },
                'Period': 3600,
                'Stat': 'Sum'
            },
            'ReturnData': True
        }

        metric_data_queries.append(metric_item)

    response = cloudwatch_client.get_metric_data(
        MetricDataQueries=metric_data_queries,
        StartTime=(now-datetime.timedelta(days=2)).isoformat(),
        EndTime=now.isoformat()
    )

    value = 0
    for item in response['MetricDataResults']:
        if item['Values'] and float(item['Values'][0]) > 0:
            value += float(item['Values'][0])

    return value

def get_last_modified_date(s3_result):
    get_last_modified = lambda obj: int(obj['LastModified'].strftime('%s'))
    last_added = [
        obj['LastModified'] for obj in sorted(s3_result['Contents'],
                                              key=get_last_modified,
                                              reverse=True)
    ][0]

    return last_added

def fetch_size_with_prefix(s3_result, item, prefix):
    size = 0

    while s3_result['IsTruncated']:
        continuation_token = s3_result['NextContinuationToken']
        s3_result = s3_client.list_objects_v2(
            Bucket=item['Name'], ContinuationToken=continuation_token, Prefix=prefix
        )
        size += sum(obj['Size'] for obj in s3_result['Contents'])

    size_in_kb = size / 1000

    return size_in_kb

def fetch_size_without_prefix(item):
    bucket_size_bytes = get_s3_metric_data(
        "BucketSizeBytes", S3_STORAGE_AVAILABLE_TYPES, item['Name']
    )

    size_in_kb = int(bucket_size_bytes) / 1000

    return size_in_kb

def format_two_decimal_points(value):
    return "{:.2f}".format(value)

def get_public_access_information(bucket_name):
    try:
        s3_client.get_public_access_block(Bucket=bucket_name)
        return True
    except ClientError:
        return False

def get_website_information(bucket_name):
    try:
        response = s3_client.get_bucket_website(Bucket=bucket_name)

        return True, response['RedirectAllRequestsTo']['HostName']
    except ClientError:
        return False, None

def get_encryption_information(bucket_name):
    try:
        s3_client.get_bucket_encryption(Bucket=bucket_name)
        return True
    except ClientError:
        return False

def print_additional_metric_data(item):
    public_access_block_enabled = get_public_access_information(item['Name'])
    website_enabled, host = get_website_information(item['Name'])
    encryption_enabled = get_encryption_information(item['Name'])

    print(f'Public Access Block enabled: {public_access_block_enabled}')
    print(f'Encryption enabled: {encryption_enabled}')

    if website_enabled:
        print(f'Website enabled: {website_enabled}, Host: {host}')
    else:
        print(f'Website enabled: {website_enabled}')

def get_bucket_info_and_print(item):
    number_of_objects = get_s3_metric_data("NumberOfObjects", ["AllStorageTypes"], item['Name'])

    print(f'------ {item["Name"]} ------')
    print(f'CreationDate: {item["CreationDate"]}')

    if ENABLE_ADDITIONAL_METRICS:
        print_additional_metric_data(item)

    if number_of_objects > 0:
        s3_result = s3_client.list_objects_v2(Bucket=item['Name'])

        last_added = get_last_modified_date(s3_result)

        if USE_PREFIX:
            size_in_kb = fetch_size_with_prefix(s3_result, item, PREFIX)
        else:
            size_in_kb = fetch_size_without_prefix(item)

        cost = (size_in_kb / 1000000) * S3_STORAGE_PRICE_PER_GB

        print(f'Number of objects: {int(number_of_objects)}')
        print(f'Total size: {format_two_decimal_points(size_in_kb)} KB')
        print(f'Last modified: {last_added}')
        print(f'Total storage cost: {format_two_decimal_points(cost)} USD')
    else:
        print('The bucket is empty, skipping cost and usage details...')

    print('\n')


def single_bucket_handler(item):
    get_bucket_info_and_print(item)

def all_buckets_handler(items):
    total_buckets = len(items['Buckets'])
    print(f'Total number of Buckets: {total_buckets} \n')

    for item in buckets['Buckets']:
        get_bucket_info_and_print(item)

print("\nWelcome to the AWS S3 Analytics Tool! This tool will help you map your S3 costs for each"\
      " bucket in your account.\n")

USE_PREFIX = None
while USE_PREFIX not in ('Y', 'n'):
    USE_PREFIX = input(
        "By default, we will entirely scan each bucket in your account using the"\
        " default prefix ('/'). Do you want to scan a specific bucket prefix? (Y/n): "
    )

if USE_PREFIX == "Y":
    BUCKET_NAME = ""
    while BUCKET_NAME == "":
        BUCKET_NAME = input("Type the bucket name that you want to analyse a specific prefix: ")

    PREFIX = ""
    while PREFIX == "":
        PREFIX = input(f"Type the prefix that you want to analyse for the bucket {BUCKET_NAME}: ")

    USE_PREFIX = True
else:
    USE_PREFIX = False

ENABLE_ADDITIONAL_METRICS = None
while ENABLE_ADDITIONAL_METRICS not in ('Y', 'n'):
    ENABLE_ADDITIONAL_METRICS = input("Do you want to enable additional metrics? (Y/n): ")

ENABLE_ADDITIONAL_METRICS = ENABLE_ADDITIONAL_METRICS == "Y"

s3_client = boto3.client('s3')
cloudwatch_client = boto3.client('cloudwatch')

now = datetime.datetime.now()

buckets = s3_client.list_buckets()

if USE_PREFIX:
    BUCKET_EXSISTS = False

    for bucket in buckets['Buckets']:
        if bucket['Name'] == BUCKET_NAME:
            BUCKET_EXSISTS = True
            single_bucket_handler(bucket)

    if not BUCKET_EXSISTS:
        sys.exit(f"Bucket {BUCKET_NAME} not found. Terminating...")
else:
    all_buckets_handler(buckets)
