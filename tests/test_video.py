from module.AWS import Aws

def test_aws():
    aws = Aws()
    assert isinstance(aws.get_access_key(), str) is True
    assert isinstance(aws.get_bucket_name(), str) is True
    assert isinstance(aws.get_access_key(), str) is True
    assert isinstance(aws.get_bucket_region(), str) is True
    assert isinstance(aws.get_origin_url(), str) is True