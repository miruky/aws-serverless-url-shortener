.PHONY: install test lint format check serve docs package
install:
	./dev setup
test:
	./dev test
lint:
	.venv/bin/ruff check src tests tools
	.venv/bin/mypy src
format:
	.venv/bin/ruff format src tests tools
check:
	./dev check
serve:
	./dev serve
docs:
	./dev docs
package:
	./dev package
