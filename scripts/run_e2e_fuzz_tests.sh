#!/usr/bin/env bash

set -euo pipefail

root=$(git rev-parse --show-toplevel)
cd "$root"

default_branch=${CI_DEFAULT_BRANCH:-main}
head=${E2E_DIFF_HEAD:-${GITHUB_SHA:-HEAD}}
make_command=${MAKE_COMMAND:-make}
pytest_args=${PYTEST_ARGS:-}
fuzz_seed=${E2E_FUZZ_SEED:-}

git_fetch() {
    local -a git_command=(git)

    if [[ -n ${GH_TOKEN:-} ]]; then
        local auth_header
        auth_header=$(printf 'x-access-token:%s' "$GH_TOKEN" | base64 | tr -d '\n')
        git_command+=(-c "http.extraheader=AUTHORIZATION: basic $auth_header")
    fi

    "${git_command[@]}" fetch "$@"
}

resolve_diff_base() {
    if [[ -n ${E2E_DIFF_BASE:-} ]]; then
        git merge-base "$E2E_DIFF_BASE" "$head"
        return
    fi

    if [[ -n ${PULL_REQUEST_BASE_SHA:-} ]]; then
        git_fetch --no-tags --depth=1 origin "$PULL_REQUEST_BASE_SHA"
        printf '%s\n' "$PULL_REQUEST_BASE_SHA"
        return
    fi

    git merge-base "$default_branch" "$head"
}

diff_base=$(resolve_diff_base)
make_args=(
    test-e2e-fuzz-diff-only
    "E2E_DIFF_BASE=$diff_base"
    "E2E_DIFF_HEAD=$head"
    "PYTEST_ARGS=$pytest_args"
)
if [[ -n $fuzz_seed ]]; then
    make_args+=("E2E_FUZZ_SEED=$fuzz_seed")
fi
"$make_command" "${make_args[@]}"
