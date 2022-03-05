SPHINX_BUILDARGS=

.PHONY: requirements test

dev-start:
	docker-compose up -d

dev-stop:
	docker-compose down

test:
	pytest

requirements:
	@# allows you to do this...
	@# make requirements | tee > requirements/some_file.txt
	@pip-compile setup.cfg --rebuild --extra dev --output-file=-

docs-build:
	cd docs && sphinx-build . ./_build/html $(SPHINX_BUILDARGS)

docs-watch:
	cd docs && sphinx-autobuild . ./_build/html $(SPHINX_BUILDARGS)
