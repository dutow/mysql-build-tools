
test: pycodestlye flake8
	pipenv run py.test tests

pycodestlye:
	pipenv run pycodestyle mbt

flake8:
	pipenv run flake8 mbt

install_dev:
	pipenv install --python 3.6 --dev

.PHONY: test install_pipenv pycodestlyle flake8
