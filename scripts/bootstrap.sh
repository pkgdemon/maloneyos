#!/bin/bash

source ../config/build.conf

if [ ! -d "${WORKDIR}" ] ; then mkdir ${WORKDIR} ; fi
cp -r /usr/share/archiso/configs/releng/ ${RELENG}