.PHONY: reproduce test

reproduce:
	python3 phase2/analysis/analyze_p2.py
	python3 pilot/run/analyze.py -q
	python3 phase3/analysis/analyze_p3.py
	python3 phase3/analysis/analyze_addendum.py
	python3 phase3/analysis/survival_p3.py
	git diff --exit-code -- phase2/analysis/phase2_metrics.json pilot/run/pilot_metrics.json phase3/analysis/phase3_metrics.json phase3/analysis/phase3_addendum_metrics.json phase3/analysis/survival_p3.json

test:
	pytest
	ruff check whostop tests site/build_pages_artifact.py
