.PHONY: reproduce test

reproduce:
	python3 phase2/analysis/analyze_p2.py
	python3 pilot/run/analyze.py -q
	git diff --exit-code -- phase2/analysis/phase2_metrics.json pilot/run/pilot_metrics.json

test:
	pytest
	ruff check whostop tests site/build_pages_artifact.py
