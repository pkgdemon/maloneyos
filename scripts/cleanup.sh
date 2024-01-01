#!/bin/bash

source ../config/build.conf

if [ -d "${WORKDIR}" ] ; then rm -rf ${WORKDIR} ; fi