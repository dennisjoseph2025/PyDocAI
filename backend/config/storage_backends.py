from storages.backends.s3 import S3Storage, S3StaticStorage


class MediaStorage(S3Storage):
    location = 'media'
