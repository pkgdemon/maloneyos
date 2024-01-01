#
# Makefile for building releases
#

release:
	cd scripts && ./bootstrap.sh
	cd scripts && ./customize.sh
	cd scripts && ./buildimage.sh

clean:
	cd scripts && ./cleanup.sh