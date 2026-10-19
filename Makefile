.PHONY: reproduce test

reproduce:
	python3 scripts/analyze_p2.py
	python3 scripts/analyze_pilot.py -q
	python3 scripts/analyze_p3.py
	python3 scripts/analyze_addendum.py
	python3 scripts/survival_p3.py
	git diff --exit-code -- results/phase2/phase2_metrics.json results/pilot/pilot_metrics.json results/phase3/phase3_metrics.json results/phase3/phase3_addendum_metrics.json results/phase3/survival_p3.json

test:
	pytest
	ruff check whostop tests scripts/build_pages_artifact.py
