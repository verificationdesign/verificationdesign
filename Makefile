.PHONY: help check test verify verify-local skills patterns site site-build site-check site-lint-cards site-a11y site-dev site-preview site-smoke

SITE_DIR := verificationdesign

help:
	@printf '%s\n' \
		'Targets:' \
		'  make check            Run repo verification and full website verification' \
		'  make verify           Run repo and skills checks, including link liveness' \
		'  make verify-local     Run repo and skills checks without network link checks' \
		'  make test             Run offline research-tools tests' \
		'  make skills           Check skills, corpus pins, fixtures and loopback tests' \
		'  make patterns         Lint AI design pattern cards' \
		'  make site             Run full website verification' \
		'  make site-build       Build the Astro website' \
		'  make site-check       Run Astro type checks' \
		'  make site-lint-cards  Lint cards through the website npm script' \
		'  make site-a11y        Run pa11y-ci against built website HTML' \
		'  make site-dev         Start the website dev server' \
		'  make site-preview     Preview the built website' \
		'  make site-smoke       Smoke-test the deployed agent-facing artifacts'

check: site verify

verify: test
	python3 -m research_tools verify
	python3 scripts/check_skills.py --links

verify-local: test
	python3 -m research_tools verify --skip-links
	python3 scripts/check_skills.py

test:
	python3 -m unittest discover -s tests -t .

skills:
	python3 scripts/check_skills.py

patterns:
	python3 ai-design-patterns/scripts/lint_patterns.py

site:
	cd $(SITE_DIR) && npm run verify

site-build:
	cd $(SITE_DIR) && npm run build

site-check:
	cd $(SITE_DIR) && npm run check

site-lint-cards:
	cd $(SITE_DIR) && npm run lint:cards

site-a11y:
	cd $(SITE_DIR) && npm run a11y

site-dev:
	cd $(SITE_DIR) && npm run dev

site-preview:
	cd $(SITE_DIR) && npm run preview

site-smoke:
	cd $(SITE_DIR) && npm run smoke:live
