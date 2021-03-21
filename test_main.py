import unittest
import boto3

from botocore.stub import Stubber
from botocore.exceptions import ClientError

s3_client = boto3.client('s3')
stubber = Stubber(s3_client)

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


class TestingMain(unittest.TestCase):
    def test_format_two_decimal_points(self):
        self.assertEqual('123.00', format_two_decimal_points(123))
        self.assertEqual('12345.68', format_two_decimal_points(12345.6789))

    def test_get_public_access_information(self):
        stubber.add_response('get_public_access_block', {
            'PublicAccessBlockConfiguration': {
                'RestrictPublicBuckets': True
            }
        })

        with stubber:
            self.assertTrue(get_public_access_information('my_bucket'))

    def test_get_public_access_information_with_error(self):
        stubber.add_client_error('get_public_access_block')

        with stubber:
            self.assertFalse(get_public_access_information('my_bucket'))

    def test_get_website_information(self):
        stubber.add_response('get_bucket_website', {
            'RedirectAllRequestsTo': {
                'HostName': 'custom.host'
            }
        })

        with stubber:
            self.assertEqual((True, 'custom.host'), get_website_information('my_bucket'))

    def test_get_website_information_with_error(self):
        stubber.add_client_error('get_bucket_website')

        with stubber:
            self.assertEqual((False, None), get_website_information('my_bucket'))

    def test_get_encryption_information(self):
        stubber.add_response('get_bucket_encryption', {
            'ServerSideEncryptionConfiguration': {
                'Rules': [
                    {
                        'ApplyServerSideEncryptionByDefault': {
                            'SSEAlgorithm': 'aws:kms',
                            'KMSMasterKeyID': '123'
                        }
                    }
                ]
            }
        })

        with stubber:
            self.assertTrue(get_encryption_information('my_bucket'))

    def test_get_encryption_information_with_error(self):
        stubber.add_client_error('get_bucket_encryption')

        with stubber:
            self.assertFalse(get_encryption_information('my_bucket'))



if __name__ == '__main__':
    unittest.main()
