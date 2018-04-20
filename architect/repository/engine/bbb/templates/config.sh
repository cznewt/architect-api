{%- set user = {
    'fullname': 'First user',
    'username': 'user',
    'password': 'pass'
} %}
{%- set image_types = {
    'bbb-armhf-debian-stretch-4.9': {
        'arch': 'armhf',
        'distribution': 'debian',
        'release': '9',
        'codename': 'stretch',
        'kernel': '4.9.83-ti-r104',
    },
    'bbb-armhf-debian-stretch-4.14': {
        'arch': 'armhf',
        'distribution': 'debian',
        'release': '9',
        'codename': 'stretch',
        'kernel': '4.14.25-ti-r38',
    },
    'bbb-armhf-debian-buster-4.14': {
        'arch': 'armhf',
        'distribution': 'debian',
        'release': '10',
        'codename': 'buster',
        'kernel': '4.14.25-ti-r38',
    },
} %}
{%- set noop = image_types.update({
	'bbx15-armhf-debian-stretch-4.9': image_types['bbb-armhf-debian-stretch-4.9'],
	'bbx15-armhf-debian-stretch-4.14': image_types['bbb-armhf-debian-stretch-4.14'],
    'bbx15-armhf-debian-buster-4.14': image_types['bbb-armhf-debian-buster-4.14']
}) %}
{%- set os = image_types[type] %}
release="salt"
image_type="{{ type }}"
export_filename="{{ image_name }}"
deb_distribution="{{ os.distribution }}"
deb_codename="{{ os.codename }}"
deb_arch="{{ os.arch }}"
deb_include="	\
	alsa-utils	\
	at	\
	automake	\
	avahi-utils	\
	bash-completion	\
	bc	\
	bluetooth	\
	build-essential	\
	ca-certificates	\
	can-utils	\
	connman	\
	cpufrequtils	\
	curl	\
	device-tree-compiler	\
	dosfstools	\
	dnsmasq	\
	firmware-atheros	\
	firmware-brcm80211	\
	firmware-iwlwifi	\
	firmware-libertas	\
	firmware-misc-nonfree	\
	firmware-realtek	\
	firmware-ti-connectivity	\
	firmware-zd1211	\
	git-core	\
	haveged	\
	hdparm	\
	hexedit	\
	htop	\
	i2c-tools	\
	initramfs-tools	\
	iperf	\
	iw	\
	less	\
	libiio-utils	\
	libncurses5-dev	\
	libnss-mdns	\
	libtool	\
	libdbus-1-dev	\
	libusb-1.0-0-dev	\
	linux-base	\
	linux-cpupower	\
	locales	\
	lshw	\
	lsof	\
	lzma	\
	lzop	\
	memtester	\
	nethogs	\
	net-tools	\
	openssh-server	\
	pastebinit	\
	pkg-config	\
	ppp	\
	python-dev	\
	python3	\
	python3-dev	\
	python3-setuptools	\
	rfkill	\
	rsync	\
	screen	\
	ssl-cert	\
	sudo	\
	systemd	\
	tio	\
	tmux	\
	u-boot-tools	\
	udhcpd	\
	unzip	\
	usb-modeswitch	\
	usbutils	\
	v4l-utils	\
	vim	\
	wget	\
	wireless-tools	\
	wpasupplicant	\
	xz-utils	\
"
deb_exclude=""
deb_components="main contrib non-free"
deb_mirror=""
deb_additional_pkgs="	\
{%- if os.codename == 'jessie' %}
	libpam-systemd	\
	libpython2.7-dev	\
	lsb-release	\
	pylint	\
	python-dbus	\
	python-dev	\
	python-flask	\
	python-minimal	\
	python-pip	\
{%- elif os.codename == 'stretch' %}
	btrfs-progs	\
	libpam-systemd	\
{%- elif os.codename == 'buster' %}
	btrfs-progs	\
	grub-efi-arm	\
	libnss-systemd	\
	libpam-systemd	\
	ostree	\
{%- endif %}
	salt-minion	\
"

rfs_username="{{ user.username }}"
rfs_fullname="{{ user.fullname }}"
rfs_password="{{ user.password }}"
rfs_hostname="{{ hostname }}"
rfs_startup_scripts="enable"
rfs_opt_scripts="https://github.com/RobertCNelson/boot-scripts"
rfs_default_desktop=""
rfs_desktop_background=""
rfs_default_locale="en_US.UTF-8"
rfs_etc_dogtag=""
rfs_console_banner=""
rfs_console_user_pass="enable"
rfs_ssh_banner=""
rfs_ssh_user_pass="enable"

repo_rcnee="enable"
repo_rcnee_pkg_list="	\
	bb-cape-overlays	\
	bb-customizations	\
	bb-wl18xx-firmware	\
	linux-image-{{ os.kernel }}	\
	pru-software-support-package	\
	rcn-ee-archive-keyring	\
	tiomapconf	\
{%- if os.codename == 'jessie' %}
	am335x-pru-package	\
	device-tree-compiler	\
	haveged	\
	libiio-utils	\
	libsoc-dev	\
	libsoc2	\
	ti-wlconf	\
	upm	\
{%- endif %}
{%- if os.codename in ['stretch', 'buster'] %}
	can-utils	\
	ipumm-dra7xx-installer	\
	gpiod	\
	tiomapconf	\
	vpdma-dra7xx-installer	\
	wireguard-tools	\
{%- endif %}
{%- if os.codename == 'stretch' %}
	firmware-am57xx-opencl-monitor	\
{%- endif %}
"
#	ti-pru-cgt-installer	\

repo_rcnee_pkg_version="{{ os.kernel }}"

include_firmware="enable"

chroot_COPY_SETUP_SDCARD="enable"
chroot_before_hook=""
chroot_after_hook=""
chroot_script="salt-{{ os.codename }}.sh"
chroot_post_uenv_txt=""
chroot_tarball="enable"

ENABLE_SALT=true
SALT_VERSION="2017.7"
SALT_RELEASE_NUM="{{ os.release }}"
SALT_RELEASE_CODE="{{ os.codename }}"
CONFIGURE_SALT=true
SALT_MINION="{{ hostname }}"
SALT_MASTER="{{ config.master }}"
PRESEED_SALT=true
SALT_PUB_KEY="{{ config.pub_key }}"
SALT_PRIV_KEY="{{ config.priv_key }}"
APPLY_SALT=true
SALT_STATES=""
