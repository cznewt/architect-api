{%- set user = {
    'fullname': 'First user',
    'username': 'user',
    'password': 'pass'
} %}
{%- set image_types = {
    'rpi2-armhf-debian-stretch-4.9': {
        'arch': 'armhf',
        'model': '2',
        'distribution': 'debian',
        'release': '9',
        'codename': 'stretch',
        'kernel': '4.9',
    },
    'rpi3-armhf-debian-stretch-4.9': {
        'arch': 'armhf',
        'model': '3',
        'distribution': 'debian',
        'release': '9',
        'codename': 'stretch',
        'kernel': '4.9',
    },
    'rpi3-arm64-debian-stretch-4.9': {
        'arch': 'arm64',
        'model': '3',
        'distribution': 'debian',
        'release': '9',
        'codename': 'stretch',
        'kernel': '4.9',
    },
} %}
{%- set os = image_types[type] %}
IMAGE_NAME="{{ repository.image_dir }}/{{ image_name }}"
HOSTNAME="{{ hostname }}"
RPI_MODEL={{ os.model }}
RELEASE="{{ os.codename }}"

USER_NAME="{{ user.username }}"
PASSWORD="{{ user.password }}"
USER_PASSWORD="{{ user.password }}"

ENABLE_I2C=true
ENABLE_SPI=true
ENABLE_SSHD=true
ENABLE_IFNAMES=false

ENABLE_REDUCE=true
REDUCE_APT=true
REDUCE_DOC=false
REDUCE_MAN=false
REDUCE_HWDB=false
REDUCE_SSHD=false
REDUCE_LOCALE=false

ENABLE_SALT=true
SALT_VERSION=2017.7
CONFIGURE_SALT=true
SALT_MINION="{{ hostname }}"
SALT_MASTER="{{ config.master }}"
PRESEED_SALT=true
SALT_PUB_KEY="{{ config.pub_key }}"
SALT_PRIV_KEY="{{ config.priv_key }}"
APPLY_SALT=true

{%- if os.model == '3' %}
ENABLE_WIRELESS=true
BUILD_KERNEL=true
{%- if os.arch == 'arm64' %}
KERNEL_ARCH=arm64
RELEASE_ARCH=arm64
CROSS_COMPILE=aarch64-linux-gnu-
QEMU_BINARY=/usr/bin/qemu-aarch64-static
KERNEL_DEFCONFIG=bcmrpi3_defconfig
KERNEL_BIN_IMAGE=Image
KERNEL_IMAGE=kernel8.img
KERNEL_BRANCH=rpi-4.11.y
{%- endif %}
{%- endif %}
