APP_NAME=cursor_dreams_bot
IMAGE_NAME=$(APP_NAME):latest
IMAGE_NAME_DEV=$(APP_NAME)-dev:latest
CONTAINER_NAME=$(APP_NAME)_container

.PHONY: help build run stop logs sh local

help:
	@echo "Targets: build run stop logs sh local"

build:
	docker build -t $(IMAGE_NAME) .

build-dev:
	docker build -t $(IMAGE_NAME_DEV) --build-arg INSTALL_DEV=true .

run:
	docker run --rm -it \
		--name $(CONTAINER_NAME) \
		--env-file .env \
		-v $(PWD)/data:/app/data \
		$(IMAGE_NAME)

test:
	docker run --rm -it \
		--name $(CONTAINER_NAME)_test \
		--env-file .env \
		$(IMAGE_NAME_DEV) uv run pytest -q

stop:
	-@docker stop $(CONTAINER_NAME)

logs:
	docker logs -f $(CONTAINER_NAME)

sh:
	docker exec -it $(CONTAINER_NAME) /bin/sh

local:
	uv run python main.py
