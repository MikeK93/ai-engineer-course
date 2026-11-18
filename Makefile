PYTHON ?= python

.PHONY: install run extract

install:
	$(PYTHON) -m pip install -r requirements.txt

# RAG one-command run. The block-1 extraction recipe is `make extract`.
run:
	$(PYTHON) main.py rag-all

extract:
	$(PYTHON) main.py run --config configs/api_t0.yaml --golden --prompt latest --golden-version latest
