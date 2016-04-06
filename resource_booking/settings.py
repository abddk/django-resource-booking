""" Django settings for resource_booking project.

Generated by 'django-admin startproject' using Django 1.8.5.

For more information on this file, see
https://docs.djangoproject.com/en/1.8/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.8/ref/settings/
"""
# Build paths inside the project like this: os.path.join(BASE_DIR, ...)

import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CONFIG_DIR = os.path.dirname(os.path.abspath(__file__))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.8/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'lfr72r#z^)_z=$-@b&0!eeu(rs5vd#ozlx__&u$wptk^cb3=6r'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
DEFAULT_FROM_EMAIL = 'noreply@adm.ku.dk'
EMAIL_HOST = 'localhost'

# Application definition

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'booking',
    'profile',
    'recurrence',
    'timedelta',
    'tinymce',
    'djangosaml2',
    'django_cron',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.security.SecurityMiddleware',
)

ROOT_URLCONF = 'resource_booking.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'override_templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

STATICFILES_FINDERS = [
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'npm.finders.NpmFinder'
]

# Django-npm config

# Local thirdparty cache; holds all downloaded
# dependencies in this folder under the root
NPM_PREFIX_PATH = 'thirdparty'

# collectstatic will put dependencies in static/thirdparty/
NPM_DESTINATION_PREFIX = 'thirdparty'

# Mapping for dependencies: Only the listed files from
# each dependency will make it into static/
NPM_FILE_PATTERNS = {
    'jquery': ['dist/jquery.min.js'],
    'bootstrap': ['dist/css/bootstrap.min.css',
                  'dist/fonts/*', 'dist/js/bootstrap.min.js'],
    'bootstrap-datepicker': ['dist/js/bootstrap-datepicker.min.js',
                                  'dist/locales/bootstrap-datepicker.da.min.js',
                                  'dist/css/bootstrap-datepicker.min.css'],
    'bootstrap-datetime-picker': ['js/bootstrap-datetimepicker.min.js',
                                  'js/locales/bootstrap-datetimepicker.da.js',
                                  'css/bootstrap-datetimepicker.min.css'],
    'bootstrap-3-typeahead': ['bootstrap3-typeahead.min.js'],
    'jquery-table-sort': ['jquery.table_sort.min.js'],
    'pickadate': ['lib/compressed/picker.js',
                  'lib/compressed/picker.date.js',
                  'lib/compressed/picker.time.js',
                  'lib/compressed/themes/default.css',
                  'lib/compressed/themes/default.time.css'
                  ],
    'rrule': ['lib/rrule.js']
}

# Django-tinymce config

TINYMCE_DEFAULT_CONFIG = {
    'plugins': "table,paste,searchreplace",
    'theme': "advanced",
    'cleanup_on_startup': True,
    'custom_undo_redo_levels': 100,
    'theme_advanced_buttons1':
        'bold,italic,underline,|,justifyleft,justifycenter,justifyright,'
        'justifyfull,|,formatselect,|,bullist,numlist,outdent,indent,|,undo,'
        'redo,|,link,unlink,anchor,image,cleanup,help,code,|,hr,removeformat,'
        'visualaid,charmap'

}
TINYMCE_COMPRESSOR = True
TINYMCE_JS_ROOT = '/static/thirdparty/tinymce'


WSGI_APPLICATION = 'resource_booking.wsgi.application'

# Database
# https://docs.djangoproject.com/en/1.8/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'resource_booking',
        'USER': 'resource_booking',
        'PASSWORD': 'resource_booking',
        'HOST': '127.0.0.1',
    }
}

# Internationalization
# https://docs.djangoproject.com/en/1.8/topics/i18n/

LANGUAGE_CODE = 'da-dk'

TIME_ZONE = 'Europe/Copenhagen'

USE_I18N = True

USE_L10N = True

USE_TZ = True

LOCALE_PATHS = (
    os.path.join(BASE_DIR, "locale"),
)

# On login, redirect to /profile/
LOGIN_REDIRECT_URL = '/profile/'
# Default URL for login
LOGIN_URL = '/profile/login'
# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.8/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static')

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Whether to enable SAML
USE_SAML = False
MAKE_SAML_LOGIN_DEFAULT = False
# Setup the default login backend so we can override it after loading local
# saml settings
AUTHENTICATION_BACKENDS = [
    'profile.auth.backends.EmailLoginBackend',
    'django.contrib.auth.backends.ModelBackend'
]

PUBLIC_URL_PROTOCOL = 'http'
PUBLIC_URL_HOSTNAME = 'fokusku.dk'
PUBLIC_URL_PORT = None

local_settings_file = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    'local_settings.py'
)
if os.path.exists(local_settings_file):
    from local_settings import *  # noqa

PUBLIC_URL = "".join([
    PUBLIC_URL_PROTOCOL, "://",
    ":".join([str(x) for x in (PUBLIC_URL_HOSTNAME, PUBLIC_URL_PORT) if x])
])

# Include SAML setup if the local settings specify it:
if USE_SAML:
    from saml_settings import *  # noqa
    if MAKE_SAML_LOGIN_DEFAULT:
        AUTHENTICATION_BACKENDS.insert(1, 'djangosaml2.backends.Saml2Backend')
    else:
        AUTHENTICATION_BACKENDS.append('djangosaml2.backends.Saml2Backend')

CRON_CLASSES = [
    "booking.cron.ReminderJob",
    "booking.cron.IdleHostroleJob"
]
