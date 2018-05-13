#!/bin/bash -ex

export DEBIAN_FRONTEND=noninteractive
export LC_ALL=en_US.utf8

printf "Update Ubuntu ..."
sudo apt-get update -y

printf "Install raspberry pi dependencies ..."
apt-get install -y debootstrap debian-archive-keyring qemu-user-static binfmt-support dosfstools bmap-tools whois bc crossbuild-essential-armhf

printf "Install beaglebone dependencies ..."
apt-get install -y m4 bmap-tools
