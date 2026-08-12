.PHONY: install test lint typecheck format-check sample capture verify clean

install:
	python3 -m pip install -e ".[dev]"

test:
	PYTHONPATH=src python3 -m pytest -q

lint:
	ruff check src tests examples scripts

benchmark:
	PYTHONPATH=src python3 scripts/benchmark_hashing.py

typecheck:
	mypy src

format-check:
	ruff format --check src tests examples scripts
	python3 -m compileall -q src tests examples scripts

sample:
	python3 examples/train_sample.py

capture:
	proofledger capture \
	  --root . \
	  --manifest examples/proofledger.json \
	  --command python examples/train_sample.py \
	  --input dataset=examples/dataset.csv \
	  --output model=examples/model.json \
	  --output predictions=examples/predictions.csv \
	  --parameter algorithm=nearest_centroid \
	  --parameter seed=7 \
	  --metric accuracy=1.0 \
	  --split '{"name":"fixture","strategy":"explicit","seed":7,"counts":{"train":4,"test":2}}' \
	  --package pytest \
	  --package setuptools \
	  --allow-dirty \
	  --no-git-revision

verify:
	proofledger verify --root . --manifest examples/proofledger.json

clean:
	rm -f examples/model.json examples/predictions.csv examples/proofledger.json
