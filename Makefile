SPHINX_BUILDARGS=

.PHONY: requirements test

dev-start:
	docker-compose up -d

dev-stop:
	docker-compose down

test:
	pytest

requirements/dev.txt: setup.cfg
	@# allows you to do this...
	@# make requirements | tee > requirements/some_file.txt
	@pip-compile setup.cfg --rebuild --extra dev --output-file=- > $@

binder/requirements.txt: setup.cfg
	@pip-compile setup.cfg --rebuild --extra binder --output-file=- > $@

docs-build:
	cd docs && sphinx-build . ./_build/html $(SPHINX_BUILDARGS)

docs-watch:
	cd docs && sphinx-autobuild . ./_build/html $(SPHINX_BUILDARGS)

README.md: README.Rmd
	jupytext --from Rmd --to ipynb --output - $^ \
		| jupyter nbconvert \
			--stdin --to markdown \
			--execute \
			--ExecutePreprocessor.kernel_name='venv-dbcooper-py' \
			--TagRemovePreprocessor.remove_all_outputs_tags='hide-cell' \
			--TagRemovePreprocessor.remove_input_tags='hide-cell' \
			--output $@
