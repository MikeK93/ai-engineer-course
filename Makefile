PYTHON ?= python

.PHONY: install run

install:
	$(PYTHON) -m pip install -r requirements.txt

# Latest prompt + latest golden set, api_t0 config
run:
	$(PYTHON) main.py run --config configs/api_t0.yaml --golden --prompt latest --golden-version latest
