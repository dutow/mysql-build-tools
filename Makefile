
test:
	pipenv run py.test tests

install_dev:
	pipenv install --python 3.6 --dev

.PHONY: test install_pipenv
