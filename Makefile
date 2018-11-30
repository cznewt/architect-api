CWD=$(shell pwd)

VERSION = "0.5.5"
ORGANIZATION ?= "cznewt"

help:
	@echo "Available actions:"
	@echo "  build         Build architect-api docker container"
	@echo "  publish       Publish architect-api docker container"
	@echo "  doc           Build project documentation"

all: build publish

build:
	docker build --no-cache -t $(ORGANIZATION)/architect-api:$(VERSION) -f ./Dockerfile .
	docker tag $(ORGANIZATION)/architect-api:$(VERSION) $(ORGANIZATION)/architect-api:latest

publish:
	docker push cznewt/architect-api:latest
	docker push $(ORGANIZATION)/architect-api:$(VERSION)
	docker push $(ORGANIZATION)/architect-api:latest

doc:
	cd doc && make html && cd ..; done
