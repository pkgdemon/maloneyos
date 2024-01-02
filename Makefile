#
# Makefile for building releases
#

check-root:
	@if [ $$(id -u) -ne 0 ]; then \
	    echo "Error: This target requires root privileges. Use 'sudo make target'."; \
	    exit 1; \
	fi

release: check-root
	cd scripts && ./cleanup.sh
	cd scripts && ./bootstrap.sh
	cd scripts && ./customize.sh
	cd scripts && ./buildimage.sh

clean: check-root
	cd scripts && ./cleanup.sh