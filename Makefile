.PHONY: help check verify verify-local patterns site site-build site-check site-lint-cards site-a11y site-dev site-preview

SITE_DIR := verificationdesign

help:
	@printf '%s\n' \
		'Targets:' \
		'  make check            Run repo verification and full website verification' \
		'  make verify           Run full repo verifier, including link liveness' \
		'  make verify-local     Run repo verifier without network link checks' \
		'  make patterns         Lint AI design pattern cards' \
		'  make site             Run full website verification' \
		'  make site-build       Build the Astro website' \
		'  make site-check       Run Astro type checks' \
		'  make site-lint-cards  Lint cards through the website npm script' \
		'  make site-a11y        Run pa11y-ci against built website HTML' \
		'  make site-dev         Start the website dev server' \
		'  make site-preview     Preview the built website'

check: site verify

verify:
	python3 scripts/verify.py

verify-local:
	python3 scripts/verify.py --skip-links

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
