VERSION = "0.1"
ORGANIZATION ?= "cznewt"
SUDO ?= "sudo"

build:
	docker build --no-cache -t $(ORGANIZATION)/xonsh:$(VERSION) -f Dockerfile .
	docker tag $(ORGANIZATION)/xonsh:$(VERSION) $(ORGANIZATION)/xonsh:latest

push:
	docker push $(ORGANIZATION)/xonsh:$(VERSION)
	docker push $(ORGANIZATION)/xonsh:latest
