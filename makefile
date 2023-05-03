test:
	./scripts/test.sh

lint:
	./scripts/lint.sh

.PHONY: build
build:
	hatchling build

install:
	pip install dist/*.whl
