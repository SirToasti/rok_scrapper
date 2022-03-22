import os
import glob
import boto3
import multiprocessing
import mimetypes

BUCKET_NAME = 'rok-2402-screenshots'
s3_client = boto3.resource('s3')
bucket = s3_client.Bucket(BUCKET_NAME)

def upload_file(prefix, filename):
    key = os.path.join(prefix, os.path.basename(filename)).replace('\\', '/')
    guessed_type = mimetypes.guess_type(filename)[0] or 'binary/octet-stream'
    with open(filename, 'rb') as f:
        bucket.put_object(Body=f, ContentType=guessed_type, Key=key)

class FileStorage:
    def __init__(self, prefix=''):
        self.base_path = r'output\files'
        self.prefix = prefix

    def save_image(self, image, filename):
        dir_path = os.path.join(self.base_path, self.prefix, os.path.dirname(filename))
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
        path = r'{}\{}'.format(dir_path, os.path.basename(filename))
        image.save(path)

    def save_text(self, text, filename):
        dir_path = os.path.join(self.base_path, self.prefix, os.path.dirname(filename))
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
        path = r'{}\{}'.format(dir_path, filename)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(text)

    def upload_to_s3(self):
        dir_path = os.path.join(self.base_path, self.prefix)
        for filename in glob.glob(dir_path + r'\*.*'):
            upload_file(self.prefix, filename)
        with multiprocessing.pool.ThreadPool(16) as pool:
            for _ in pool.starmap(upload_file, [(self.prefix, filename) for filename in glob.glob(dir_path+r'\*.*')]):
                pass

