CWD=$(shell pwd)

help:
	@echo "Available actions:"
	@echo "  build_container_api         Build and publish architect-api docker container"
	@echo "  build_container_worker      Build and publish architect-worker docker container"
	@echo "  documentation               Build project documentation"

all: build_container_api

build_container_api:
	docker build -t cznewt/architect-api:latest -f ./api.Dockerfile .

build_container_worker:
	docker build -t cznewt/architect-api:latest -f ./worker.Dockerfile .

documentation:
	cd doc && make html && cd ..; done
