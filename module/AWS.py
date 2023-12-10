import os
from dotenv import load_dotenv

class Aws():
    def __init__(self):
        self._aws_secret_key = os.getenv("SECRET_ACCESS_KEY") 
        self._aws_access_key = os.getenv("ACCESS_KEY")
        self._bucket_name = os.getenv("BUCKET_NAME")
        self._bucket_region = os.getenv("BUCKET_REGION")
        self._url = os.getenv("CLOUD_FRONT_URL")

    def get_secret_key(self):
        return self._aws_secret_key

    def get_access_key(self):
        return self._aws_access_key
    
    def get_bucket_name(self):
        return self._bucket_name

    def get_bucket_region(self):
        return self._bucket_region
    
    def get_origin_url(self):
        return self._url

if __name__ != "__main__":
    load_dotenv()