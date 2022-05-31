import os

import dj_database_url
from eshop.settings.dev import SECRET_KEY

from .common import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False
# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ['SECRET_KEY']

ALLOWED_HOSTS = ['django-myeshop.de.r.appspot.com', 'django-myeshop.herokuapp.com']

DATABASES = {
  'default': dj_database_url.config()
}
