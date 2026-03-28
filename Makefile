.PHONY: install test lint format clean

# 依存関係のインストール
install:
	python -m pip install -e ".[dev]"

# テスト実行
test:
	pytest tests/ -v --tb=short --cov=src --cov-report=term-missing

# リンター実行
lint:
	ruff check src/ tests/
	mypy src/

# コードフォーマット
format:
	ruff check --fix src/ tests/
	ruff format src/ tests/

# キャッシュ・ビルド成果物の削除
clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -rf .pytest_cache .mypy_cache .ruff_cache htmlcov .coverage dist build *.egg-info
