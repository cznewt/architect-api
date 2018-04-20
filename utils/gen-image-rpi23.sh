#!/bin/sh

# Usage:
#
# ./gen-image.sh node.domain.com-20180405

set -e
set -x

IMAGENAME="${1:-rpi.domain.com-timestamp}"

rm -rf "./images/jessie/"
rm -rf "./images/stretch/"
rm -rf "./images/buster/"

CONFIG_TEMPLATE="${IMAGENAME}" ./rpi23-gen-image.sh

rm -rf "./images/jessie/"
rm -rf "./images/stretch/"
rm -rf "./images/buster/"
