#!/bin/bash

source ../config/build.conf

mkarchiso -v -w ${ISO} -o ${WORKDIR} ${RELENG}