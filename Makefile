# -*- MakeFile -*-

VERSION = $(shell grep "__version__" cmphy/__init__.py | cut -d " " -f 3)

clean:
	find . -type f -name '*.py[co]' -exec rm -f {} +
	find . -type d -name '__pycache__' -exec rm -rf {} +
	rm -rf cmphy.egg-info

link: clean
	python setup.py develop

unlink:
	python setup.py develop --uninstall

build: clean
	python setup.py sdist

install:
	pip install dist/cmphy-$(VERSION).tar.gz

uninstall:
	pip uninstall cmphy

gh-pages:
	git checkout gh-pages
	# Clean-up current directory, otherwise `mv docs/_build/html/* ./` 
	# will fail.
	git rm -rf ./*
	# Pull the needed source files from the master branch and remove 
	# them from the index (won't go into commit).
	git checkout master docs cmphy
	git reset HEAD
	# Generate documentation with Sphinx.
	make html --directory=docs
	# GitHub Pages needs the index.html file in the root directory.
	mv docs/_build/html/* ./
	rm -rf docs cmphy
	# Bypass Jekyll processing on GitHub Pages which ignores files or
	# directories that start with an underscore (e.g. _build, _static).
	touch .nojekyll
	git add -A
	git commit -m "Generate documentation for commit `git log master -1 --pretty=\"%h\"`"
	git push origin gh-pages
	git checkout master

pep8:
	pep8 --ignore=W503,E721 cmphy tests

pyflakes:
	pyflakes cmphy tests
