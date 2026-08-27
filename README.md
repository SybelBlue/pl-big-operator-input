# pl-big-operator-input

This directory is a course demo of a new element.

To include the element in your course, use:

```sh
$ git submodule add -b release https://github.com/SybelBlue/pl-big-operator-input.git elements/pl-big-operator-input
```

## Developer Prerequisites

Install the following tools before getting started:

- [Python](https://www.python.org/) 3.13 or newer
- [uv](https://docs.astral.sh/uv/)
- [pnpm](https://pnpm.io/) 11.19 or newer
- [GNU Make](https://www.gnu.org/software/make/)
- [Docker](https://www.docker.com/) (optional, for running PrairieLearn in a container)

## Developer Quickstart

Clone the repository, enter its directory, and install the project dependencies:

```sh
make deps
```

Run the test suite:

```sh
make test
```

Start PrairieLearn for local development:

```sh
make dev
```

The development runner will print the local URL to open. To run the official PrairieLearn Docker image instead, use:

```sh
make docker
```

## Repository layout

```text
courseInstances/    Course instances and assessments
elements/           Course-specific PrairieLearn elements and tests
questions/          PrairieLearn questions
serverFilesCourse/  Shared Python helpers and tests
scripts/            Repository maintenance scripts
infoCourse.json     Course metadata, topics, tags, and modules
```

Start customizing the template by updating `infoCourse.json`, the starter course instance under `courseInstances/StarterSemester`, and the example content under `questions/starter`.

## Make targets

| Command | Description |
| --- | --- |
| `make deps` | Fetch PrairieLearn schemas and install Python and Node dependencies |
| `make test` | Run helper, element, and question tests |
| `make test-helpers` | Run tests for shared helpers and custom elements |
| `make test-content` | Run question tests |
| `make typecheck` | Type-check Python code with Pyright |
| `make format` | Format Python, JSON, HTML, and Mustache files |
| `make dev` | Launch the local PrairieLearn development runner |
| `make docker` | Launch PrairieLearn using the official Docker image |
| `make fetch-pl-schemas` | Refresh the local PrairieLearn schemas |
| `make check-prairielearn-pin` | Verify the vendored symbolic input and Python dependency share one upstream commit |
| `make update-prairielearn-pin PL_REF=<ref>` | Vendor a PrairieLearn ref and regenerate the Python lock |
| `make clean` | Remove local dependencies, caches, and build artifacts |

Pass additional options to pytest with `PYTEST_ARGS`. For example:

```sh
make test PYTEST_ARGS="-x -vv"
```

## Typical development workflow

1. Add or edit questions in `questions/`.
2. Reference them from an assessment in `courseInstances/`.
3. Preview the course with `make dev`.
4. Run `make format`, `make typecheck`, and `make test` before committing.

The default `make` target is `test`, so running `make` by itself executes the complete test suite.
