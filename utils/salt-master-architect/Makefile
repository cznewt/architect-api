VERSION = "0.3"
ORGANIZATION ?= "cznewt"
SUDO ?= "sudo"

build:
	docker build --no-cache -t $(ORGANIZATION)/salt-master-architect:$(VERSION) -f Dockerfile .
	docker tag $(ORGANIZATION)/salt-master-architect:$(VERSION) $(ORGANIZATION)/salt-master-architect:latest

push:
	docker push $(ORGANIZATION)/salt-master-architect:$(VERSION)
	docker push $(ORGANIZATION)/salt-master-architect:latest
