# colors, 'cause bitches loves colors
RED=\033[01;31m
GREEN=\033[01;32m
NC=\033[01;00m

# env
SRCDIR = $(shell pwd)

# local
os=$(shell uname)

.PHONY: default
default: main

.PHONY: main
main:
	@echo "=> Downloading binary files"
	@echo "${GREEN}MongoDB${NC}"
	@if [ ! -e "$(SRCDIR)/mongodb-osx-x86_64-2.0.6.tgz" ] ; then wget http://fastdl.mongodb.org/osx/mongodb-osx-x86_64-2.0.6.tgz;fi
	@if [ ! -e "$(SRCDIR)/mongodb-osx-x86_64-2.0.6" ] ; then tar -vxf $(SRCDIR)/mongodb-osx-x86_64-2.0.6.tgz;fi
	@echo "OK"
	@echo "=> Install dependencies Python"
	@echo "${GREEN}London Framework${NC}"
	@python $(SRCDIR)/src/london/setup.py install
	@echo "OK"
	@echo "=> Run"
	@echo "${GREEN}MongoDB${NC}"
	@$(SRCDIR)/mongodb-osx-x86_64-2.0.6/bin/mongod &
	@echo "OK"
	@echo "${GREEN}London Framework${NC}"
	@cd $(SRCDIR)/src/ && $(SRCDIR)/src/london/london/bin/london-admin.py run public
	@echo "OK"
	@echo "=> Open Browser"
	@open http://127.0.0.1:8000/
