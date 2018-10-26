CWD=$(shell pwd)

help:
	@echo "Available actions:"
	@echo "  build         Build architect-api docker container"
	@echo "  publish       Publish architect-api docker container"
	@echo "  doc           Build project documentation"

all: build

build:
	docker build -t cznewt/architect-api:latest -f ./Dockerfile .

publish:
	docker push cznewt/architect-api:latest

doc:
	cd doc && make html && cd ..; done
