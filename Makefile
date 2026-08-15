SHELL := /bin/bash
.SHELLFLAGS := -euo pipefail -c

.DEFAULT_GOAL := test

UV_CACHE_DIR ?= /private/tmp/learnvia_uv_cache

LIB_TEST_PATHS := \
	elements/**/tests \
	serverFilesCourse/**/tests

CONTENT_TEST_PATHS := questions

export UV_CACHE_DIR

DOCKER_JOBS_DIR ?= $(shell mktemp -d /tmp/pl-docker-jobs.XXXXXX)

export DOCKER_JOBS_DIR

.PHONY: clean deps venv test test-helpers test-content typecheck format-py format-json format-html format fetch-pl-schemas

# install deps, RUN ME FIRST
# requires pnpm and uv to be installed on the commandline
deps: fetch-pl-schemas
	pnpm install
	uv sync

venv: deps
	uv venv --refresh

fetch-pl-schemas:
	uv run --active scripts/pull_down_prairielearn_schemas.py --write


# Run tests
test:
	uv run --active pytest $(LIB_TEST_PATHS) $(CONTENT_TEST_PATHS) $(PYTEST_ARGS)

test-helpers:
	uv run --active pytest $(LIB_TEST_PATHS) $(PYTEST_ARGS)

test-content:
	uv run --active pytest $(CONTENT_TEST_PATHS) $(PYTEST_ARGS)


# typecheck python
typecheck:
	uv run --active pyright .


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
	rm -rf .venv node_modules build dist htmlcov .prairielearn/schemas
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