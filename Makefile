#
# Makefile for building releases
#

check-root:
	@if [ $$(id -u) -ne 0 ]; then \
	    echo "Error: This target requires root privileges. Use 'sudo make target'."; \
	    exit 1; \
	fi


release: check-root
	cd scripts && python3 cleanup.py
	cd scripts && python3 bootstrap.py
	cd scripts && python3 buildimage.py

clean: check-root
	cd scripts && python3 cleanup.py