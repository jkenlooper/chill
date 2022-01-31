# Reformats any code that is newer than files in
# ./code-formatter/.last-modified/*
#
# Run this makefile from the top level of the project:
# make format -f ./code-formatter/code-formatter.mk

# This file was generated from the code-formatter directory in https://github.com/jkenlooper/cookiecutters . Any modifications needed to this file should be done on that originating file.

SHELL := bash
.SHELLFLAGS := -eu -o pipefail -c
.DEFAULT_GOAL := all
.DELETE_ON_ERROR:
.SUFFIXES:

mkfile_path := $(abspath $(lastword $(MAKEFILE_LIST)))
project_dir := $(dir $(mkfile_path))

DOCKER := docker

# For debugging what is set in variables
inspect.%:
	@echo $($*)

# Always run.  Useful when target is like targetname.% .
# Use $* to get the stem
FORCE:

objects := $(project_dir)package-lock.json format

.PHONY: all
all: $(objects)

$(project_dir)package-lock.json: $(project_dir)package.json code-formatter.dockerfile
	$(DOCKER) build -f code-formatter.dockerfile \
		-t chill-code-formatter \
		./
	$(DOCKER) run \
		--name chill-code-formatter \
		chill-code-formatter \
		npm install --ignore-scripts
	$(DOCKER) cp \
		chill-code-formatter:/code/package-lock.json \
		$@
	$(DOCKER) rm \
		chill-code-formatter

.PHONY: format
format: $(project_dir)package-lock.json
	$(DOCKER) build -f code-formatter.dockerfile \
		-t chill-code-formatter \
		./
	$(DOCKER) run -it --rm \
		--mount type=bind,src=$(PWD)/code-formatter/.last-modified,dst=/code/.last-modified \
		--mount type=bind,src=$(PWD)/docs,dst=/code/docs \
		--mount type=bind,src=$(PWD)/src,dst=/code/src \
		chill-code-formatter \
		npm run format




