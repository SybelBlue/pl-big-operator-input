SHELL := /bin/bash
.SHELLFLAGS := -euo pipefail -c

.DEFAULT_GOAL := test

UV_CACHE_DIR ?= /private/tmp/learnvia_uv_cache

LIB_TEST_PATHS := e2e-tests/tests elements/**/tests scripts/tests
CONTENT_TEST_PATHS := e2e-tests/test_questions.py
QUESTION_PATHS ?= questions
E2E_SEED_COUNT ?= 3
E2E_FUZZ_SEED_COUNT ?= 10
E2E_FUZZ_SEED ?=
E2E_DIFF_BASE ?= main
E2E_DIFF_HEAD ?= HEAD
E2E_TEST_ARGS := \
	--question-path "$(QUESTION_PATHS)" \
	--seed-count "$(E2E_SEED_COUNT)" \
	--prairielearn-path "$(PRAIRIELEARN_PATH)"
E2E_FUZZ_SEED_ARG = $(if $(strip $(E2E_FUZZ_SEED)),--fuzz-seed "$(E2E_FUZZ_SEED)")

export UV_CACHE_DIR

DOCKER_JOBS_DIR ?= $(shell mktemp -d /tmp/pl-docker-jobs.XXXXXX)

export DOCKER_JOBS_DIR

.PHONY: clean deps venv install-prairielearn require-jq require-prairielearn-path require-prairielearn add-e2e-regression-seed test run-ci-test-suite test-helpers test-e2e test-e2e-fuzz test-e2e-fuzz-diff-only test-content test-smoke test-regression test-unit test-publication typecheck format-py format-json format-html format check-format check-pl-schemas sync-vendor verify-vendor ci-dryrun fetch-pl-schemas dev docker

# install deps, RUN ME FIRST
# requires pnpm and uv to be installed on the commandline
deps: fetch-pl-schemas
	pnpm install
	uv sync --active 
	@$(MAKE) sync-vendor

venv: deps
	uv venv --refresh

install-prairielearn: require-prairielearn-path
	@if [ -e "$(PRAIRIELEARN_PATH)" ]; then \
		echo 'PRAIRIELEARN_PATH already exists: $(PRAIRIELEARN_PATH)' >&2; \
		exit 2; \
	fi
	@git clone https://github.com/PrairieLearn/PrairieLearn.git \
		"$(PRAIRIELEARN_PATH)"

fetch-pl-schemas:
	uv run --active scripts/pull_down_prairielearn_schemas.py --write


# testing and validation
require-jq:
	@if ! command -v jq >/dev/null 2>&1; then \
		echo 'jq is required; install it and retry' >&2; \
		exit 2; \
	fi

require-prairielearn-path:
	@if [ -z "$(PRAIRIELEARN_PATH)" ]; then \
		echo 'PRAIRIELEARN_PATH must be exported or passed to make' >&2; \
		exit 2; \
	fi

require-prairielearn: require-prairielearn-path
	@if ! git -C "$(PRAIRIELEARN_PATH)" rev-parse --git-dir >/dev/null 2>&1; then \
		echo 'PRAIRIELEARN_PATH must name a Git clone: $(PRAIRIELEARN_PATH)' >&2; \
		exit 2; \
	fi
	@pl_commit=$$(uv run --active python -c \
		'from pathlib import Path; from prairielearn_e2e.backend import installed_prairielearn_commit; print(installed_prairielearn_commit(Path.cwd()))'); \
	if ! git -C "$(PRAIRIELEARN_PATH)" cat-file -e "$$pl_commit^{commit}" \
		>/dev/null 2>&1; then \
		echo "PrairieLearn clone does not contain pinned revision $$pl_commit" >&2; \
		echo "Fetch it with: git -C $(PRAIRIELEARN_PATH) fetch origin $$pl_commit" >&2; \
		exit 2; \
	fi

add-e2e-regression-seed: require-jq
	@bash scripts/add_e2e_regression_seed.sh \
		"$(QUESTION_PATH)" "$(VARIANT_SEED)"

test: require-prairielearn
	uv run --active pytest $(LIB_TEST_PATHS) $(CONTENT_TEST_PATHS) \
		$(E2E_TEST_ARGS) --fuzz-seeds --seed-replay-target "$@" \
		$(E2E_FUZZ_SEED_ARG) $(PYTEST_ARGS)

run-ci-test-suite:
	@$(MAKE) test
	@$(MAKE) test-e2e-fuzz

test-helpers:
	uv run --active pytest $(LIB_TEST_PATHS) $(PYTEST_ARGS)

test-e2e: require-prairielearn
	uv run --active pytest $(CONTENT_TEST_PATHS) $(E2E_TEST_ARGS) \
		--fuzz-seeds --seed-replay-target "$@" $(E2E_FUZZ_SEED_ARG) $(PYTEST_ARGS)

test-e2e-fuzz: require-prairielearn
	@MAKE_COMMAND="$(MAKE)" bash scripts/run_e2e_fuzz_tests.sh

test-e2e-fuzz-diff-only: require-prairielearn
	@uv run --active python scripts/run_e2e_fuzz_diff_only.py \
		--base "$(E2E_DIFF_BASE)" \
		--head "$(E2E_DIFF_HEAD)" \
		--seed-count "$(E2E_FUZZ_SEED_COUNT)" \
		$(E2E_FUZZ_SEED_ARG) \
		--prairielearn-path "$(PRAIRIELEARN_PATH)" $(PYTEST_ARGS)

test-content: test-e2e

test-smoke:
	uv run --active pytest -m smoke $(LIB_TEST_PATHS) $(PYTEST_ARGS)

test-regression:
	uv run --active pytest -m regression $(LIB_TEST_PATHS) $(PYTEST_ARGS)

test-unit:
	uv run --active pytest -m unit $(LIB_TEST_PATHS) $(PYTEST_ARGS)

test-publication: test typecheck check-format check-pl-schemas
	git diff --check

typecheck:
	uv run --active pyright

check-format:
	uv run --active ruff format --check .

check-pl-schemas:
	uv run --active scripts/pull_down_prairielearn_schemas.py

sync-vendor:
	uv run --active --locked --no-sync pl-vendor sync

verify-vendor:
	uv run --active --locked --no-sync pl-vendor verify

ci-dryrun: run-ci-test-suite typecheck check-format check-pl-schemas verify-vendor


# format source
format: format-py format-json format-html

format-py:
	uv run --active ruff format .

format-json:
	pnpm dlx prettier --write "{.vscode,courseInstances,elements,questions}/**/*.{json,jsonc}"

format-html:
	pnpm dlx prettier --write "{elements,questions}/**/*.{html,mustache,mu}"


# launch prairielearn
dev:
	pnpm dlx @sybelblue/prairielearn-runner@latest

docker:
	docker run -it --rm --pull=always \
		-p 3000:3000 \
		-v ".:/course" \
		-v "$(DOCKER_JOBS_DIR):/jobs" \
		-e HOST_JOBS_DIR="$(DOCKER_JOBS_DIR)" \
		-v /var/run/docker.sock:/var/run/docker.sock \
		--add-host=host.docker.internal:172.17.0.1 \
		prairielearn/prairielearn:us-prod-live

# Remove project-local caches, build outputs, and installed dependencies.
clean:
	rm -rf .venv node_modules build dist htmlcov .prairielearn/schemas .pnpm-store
	find . -type d \( \
		-name __pycache__ -o \
		-name .pytest_cache -o \
		-name .ruff_cache -o \
		-name .mypy_cache -o \
		-name '*.egg-info' \
	\) -prune -exec rm -rf {} +
	find . -type f \( \
		-name '*.py[co]' -o \
		-name .coverage -o \
		-name 'coverage.*' \
	\) -delete
