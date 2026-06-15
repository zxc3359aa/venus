.PHONY: setup test demo eval lint compliance-gate contract-conformance feishu-live
PYTHON ?= $(shell if [ -x .venv/bin/python ]; then printf ".venv/bin/python"; elif command -v python3 >/dev/null 2>&1; then command -v python3; else command -v python; fi)

setup:
	python3 -m venv .venv
	.venv/bin/python -m pip install -U pip pytest

test:
	$(PYTHON) -m pytest -q

demo:
	PYTHONPATH=src $(PYTHON) -m venus.demo_e2e

eval:
	$(PYTHON) eval/scorer.py

compliance-gate:
	PYTHONPATH=src $(PYTHON) scripts/compliance_gate.py

contract-conformance:
	PYTHONPATH=src $(PYTHON) scripts/contract_conformance.py

lint:
	@echo "安装 ruff/black/mypy 后启用：ruff check . && black --check . && mypy src"

feishu-live:
	@echo "启动飞书实时接入看门人（仅检查；未通过门禁将退出）"
	PYTHONPATH=src $(PYTHON) scripts/feishu_live_bootstrap.py
