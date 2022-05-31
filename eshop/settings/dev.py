from .common import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True
# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-*u*+w)x4p#apt706n6@wf@v#47z$_9sj9gho*rpgpn2m1a-qhx'

ALLOWED_HOSTS = ['0.0.0.0']

MIDDLEWARE.insert(0, 'debug_toolbar.middleware.DebugToolbarMiddleware')

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'my_eshop',
        'HOST': 'mysql',
        'USER': 'root',
        'PASSWORD': '04160220',
    }
}

DEBUG_TOOLBAR_CONFIG = {
    'SHOW_TOOLBAR_CALLBACK': lambda request: True
}
