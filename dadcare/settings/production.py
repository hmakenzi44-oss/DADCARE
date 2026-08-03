from .base import *
import os

DEBUG = os.environ.get("DEBUG", "False").lower() == "true"

# Use DATABASE_URL from environment (Neon.tech format)
DATABASE_URL = os.environ.get('DATABASE_URL')
if DATABASE_URL:
    import urllib.parse
    url = urllib.parse.urlparse(DATABASE_URL)
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': url.path[1:],
            'USER': url.username,
            'PASSWORD': url.password,
            'HOST': url.hostname,
            'PORT': url.port or 5432,
            'OPTIONS': {
                'sslmode': 'require',
                'options': '-c search_path=public',
            },
        }
    }
