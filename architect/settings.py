"""
Django settings for Architect service.
"""
import os
from .utils import load_yaml_json_file

DEBUG = True

SECRET_KEY = '^0r*t3%t@h-auaqh+gq(bxueqc-7)8jryh#)_l4yd315))$*@z'

ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.admindocs',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_extensions',
    'rest_framework',
    'django_select2',
    'crispy_forms',
    'compressor',
    'architect',
    'architect.inventory',
    'architect.manager',
    'architect.monitor',
    'architect.document',
    'architect.manager.engine.saltstack',
    'graphene_django',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'architect.urls'

GRAPHENE = {
    'SCHEMA': 'architect.schema.schema'
}

CONFIG_FILE = os.environ.get('ARCHITECT_CONFIG_FILE',
                             '/etc/architect/api.yml')

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CONFIG = load_yaml_json_file(CONFIG_FILE)

WEBROOT = '/'
LOGIN_URL = None
LOGOUT_URL = None
LOGIN_REDIRECT_URL = None
STATIC_ROOT = None
STATIC_URL = None

BASE_TEMPLATES = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                              'templates')

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_TEMPLATES],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'architect.context_processors.base'
            ],
        },
    },
]

WSGI_APPLICATION = 'architect.wsgi.application'

if 'TRAVIS' in os.environ:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql_psycopg2',
            'NAME': 'travisci',
            'USER': 'postgres',
            'PASSWORD': '',
            'HOST': 'localhost',
            'PORT': '',
        }
    }
elif 'databases' in CONFIG:
    DATABASES = CONFIG['databases']
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
        }
    }

if 'caches' in CONFIG:
    CACHES = CONFIG['caches']
else:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True

if LOGIN_URL is None:
    LOGIN_URL = WEBROOT + 'accounts/login/'
if LOGOUT_URL is None:
    LOGOUT_URL = WEBROOT + 'accounts/logout/'
if LOGIN_REDIRECT_URL is None:
    LOGIN_REDIRECT_URL = WEBROOT

MEDIA_ROOT = os.path.abspath(os.path.join(BASE_DIR, 'media'))
MEDIA_URL = WEBROOT + 'media/'

if STATIC_ROOT is None:
    STATIC_ROOT = os.path.abspath(os.path.join(BASE_DIR, 'static'))

if STATIC_URL is None:
    STATIC_URL = WEBROOT + 'static/'

RESOURCE_CACHE_DURATION = 10

INVENTORY_ENGINES = CONFIG.get('inventory', {})
MANAGER_ENGINES = CONFIG.get('manager', {})
MONITOR_ENGINES = CONFIG.get('monitor', {})
DOCUMENT_ENGINES = CONFIG.get('document', {})

INVENTORY_BASE_DIR = '/srv/architect'
INVENTORY_RECLASS_CLASSES_DIRS = CONFIG.get('inventory_reclass_classes_dirs', [])
INVENTORY_SALT_FORMULAS_DIRS = CONFIG.get('inventory_salt_formulas_dirs', [])

if 'inventory_classes' in CONFIG:
    INVENTORY_CLASS_MAPPINGS = CONFIG['inventory_classes']
else:
    INVENTORY_CLASS_MAPPINGS = {
        "architect": "architect.inventory.engine.architect.client.ArchitectClient",
        "salt-formulas": "architect.inventory.engine.salt_formulas.client.SaltFormulasClient",
        "reclass": "architect.inventory.engine.reclass.client.ReclassClient",
    }

if 'manager_classes' in CONFIG:
    MANAGER_CLASS_MAPPINGS = CONFIG['manager_classes']
else:
    MANAGER_CLASS_MAPPINGS = {
        "amazon": "architect.manager.engine.amazon.client.AmazonWebServicesClient",
        "ansible": "architect.manager.engine.ansible.client.AnsibleClient",
        "heat": "architect.manager.engine.heat.client.HeatClient",
        "jenkins": "architect.manager.engine.jenkins.client.JenkinsClient",
        "kubernetes": "architect.manager.engine.kubernetes.client.KubernetesClient",
        "openstack": "architect.manager.engine.openstack.client.OpenStackClient",
        "saltstack": "architect.manager.engine.saltstack.client.SaltStackClient",
        "spinnaker": "architect.manager.engine.spinnaker.client.SpinnakerClient",
        "terraform": "architect.manager.engine.terraform.client.TerraformClient",
    }

if 'monitor_classes' in CONFIG:
    MONITOR_CLASS_MAPPINGS = CONFIG['monitor_classes']
else:
    MONITOR_CLASS_MAPPINGS = {
        "elasticsearch": "architect.monitor.engine.elasticsearch.client.ElasticSearchClient",
        "graphite": "architect.monitor.engine.graphite.client.GraphiteClient",
        "influxdb": "architect.monitor.engine.influxdb.client.InfluxdbClient",
        "prometheus": "architect.monitor.engine.prometheus.client.PrometheusClient",
    }

RECLASS_SERVICE_BLACKLIST = [
    '_param',
    'private_keys',
    'public_keys',
    'known_hosts'
]

RECLASS_ROLE_BLACKLIST = [
    '_support',
    '_orchestrate',
    'common'
]

BROKER_URL = 'redis://localhost:6379'
CELERY_RESULT_BACKEND = 'redis://localhost:6379'
CELERY_ACCEPT_CONTENT = ['application/json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'Europe/Prague'

# Compressor settings
COMPRESS_ENABLED = True
COMPRESS_OFFLINE = True
COMPRESS_ROOT = STATIC_ROOT
COMPRESS_PRECOMPILERS = (
    ('text/scss', 'sass {infile} {outfile}'),
)
COMPRESS_CSS_FILTERS = (
    'compressor.filters.css_default.CssAbsoluteFilter',
)
COMPRESS_CSS_HASHING_METHOD = 'hash'
COMPRESS_PARSER = 'compressor.parser.HtmlParser'

# STATICFILES_DIRS = [
#     os.path.join(BASE_DIR, 'architect', 'static'),
# ]

STATICFILES_FINDERS = (
    'npm.finders.NpmFinder',
    'compressor.finders.CompressorFinder',
    # 'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
)

CRISPY_TEMPLATE_PACK = 'bootstrap4'


REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.DjangoModelPermissionsOrAnonReadOnly'
    ]
}
