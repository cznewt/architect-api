#!/bin/bash -e

# Usage:
#
# ./gen-image.sh node.domain.com-20180405 node.domain.com bbbc
#
# bbbb  - BeagleBone Black Rev B
# bbbc  - BeagleBone Black Rev C (BeagleBone Blue)
# bbv14 - BeagleBoard-X15

IMAGENAME="${1:-rpi.domain-config-datetime}"
HOSTNAME="${2:-rpi.domain-config}"
PLATFORM="${3:-bbb}"

base_rootfs="$IMAGENAME" 
wfile="$IMAGENAME"

DIR="$PWD"

archive_base_rootfs () {
        if [ -d ./${base_rootfs} ] ; then
                rm -rf ${base_rootfs} || true
        fi
        if [ -f ${base_rootfs}.tar ] ; then
                xz -z -8 -v ${base_rootfs}.tar && sha256sum ${base_rootfs}.tar.xz > ${base_rootfs}.tar.xz.sha256sum &
        fi
}

extract_base_rootfs () {
        if [ -d ./${base_rootfs} ] ; then
                rm -rf ${base_rootfs} || true
        fi

        if [ -f ${base_rootfs}.tar.xz ] ; then
                tar xf ${base_rootfs}.tar.xz
        else
                tar xf ${base_rootfs}.tar
        fi
}

archive_img () {
        #prevent xz warning for 'Cannot set the file group: Operation not permitted'
        sudo chown ${UID}:${GROUPS} ${wfile}.img
        if [ -f ${wfile}.img ] ; then
                if [ ! -f ${wfile}.bmap ] ; then
                        if [ -f /usr/bin/bmaptool ] ; then
                                bmaptool create -o ${wfile}.bmap ${wfile}.img
                        fi
                fi
                xz -z -8 -v ${wfile}.img && sha256sum ${wfile}.img.xz > ${wfile}.img.xz.sha256sum &
        fi
}

generate_img () {
        cd ${base_rootfs}/
        sudo ./setup_sdcard.sh ${options}
        mv *.img ../
        mv *.job.txt ../
        cd ..
}

#./RootStock-NG.sh -c $IMAGENAME

if [ "$PLATFORM" = "bbb" ] ; then
        platform_options="--dtb beaglebone --bbb-old-bootloader-in-emmc --emmc-flasher"
fi

if [ "$PLATFORM" = "bbx15" ] ; then
        platform_options="--dtb am57xx-beagle-x15"
fi

options="--img ${IMAGENAME} ${platform_options} --hostname ${HOSTNAME}"

cd ./deploy

extract_base_rootfs
generate_img
archive_base_rootfs
archive_img

cd ..
