from storages.backends.s3 import S3Storage


class MediaStorage(S3Storage):
    location = 'media'
