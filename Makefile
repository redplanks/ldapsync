.PHONY: venv
venv: vendor/venv-update Makefile
	vendor/venv-update \
		venv= $@ -ppython3 \
		install= -r requirements.txt

.PHONY: test
test: venv install-hooks
	venv/bin/pre-commit run --all-files

.PHONY: install-hooks
install-hooks: venv
	venv/bin/pre-commit install -f --install-hooks
