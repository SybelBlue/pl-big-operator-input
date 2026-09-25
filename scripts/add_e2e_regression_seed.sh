#!/usr/bin/env bash

set -euo pipefail

usage() {
    echo "Usage: $0 QUESTION_PATH VARIANT_SEED" >&2
}

if [[ $# -ne 2 || -z $1 || -z $2 ]]; then
    usage
    exit 2
fi

if ! command -v jq >/dev/null 2>&1; then
    echo "jq is required; install it and retry" >&2
    exit 2
fi

question_path=${1%/}
variant_seed=$2

if ! jq -e -n --arg seed "$variant_seed" \
    '($seed | test("^(0|[1-9][0-9]*)$")) and (($seed | tonumber) < 4294967296)' \
    >/dev/null; then
    echo "VARIANT_SEED must be an integer between 0 and 4294967295" >&2
    exit 2
fi

repository_root=$(git rev-parse --show-toplevel)
cd "$repository_root"

if [[ ! -d $question_path ]]; then
    echo "Question directory does not exist: $question_path" >&2
    exit 2
fi

question_directory=$(cd "$question_path" && pwd -P)
questions_root=$(cd questions && pwd -P)
case $question_directory in
    "$questions_root"/*) ;;
    *)
        echo "QUESTION_PATH must be a directory beneath questions/: $question_path" >&2
        exit 2
        ;;
esac

if [[ ! -f $question_directory/info.json ]]; then
    echo "Question directory has no info.json: $question_path" >&2
    exit 2
fi

config_path=$question_directory/.question-e2e.json
display_path=${config_path#"$repository_root"/}

if [[ -f $config_path ]]; then
    if ! jq -e 'type == "object"' "$config_path" >/dev/null; then
        echo "E2E config must contain a JSON object: $display_path" >&2
        exit 2
    fi
    if jq -e --argjson seed "$variant_seed" \
        '(.regression_seeds? // [])
        | if type == "array" then index($seed) != null else false end' \
        "$config_path" >/dev/null; then
        echo "Regression seed $variant_seed is already recorded in $display_path"
        exit 0
    fi
fi

temporary_config=$(mktemp "$question_directory/.question-e2e.json.tmp.XXXXXX")
cleanup() {
    rm -f "$temporary_config"
}
trap cleanup EXIT

if [[ -f $config_path ]]; then
    jq --argjson seed "$variant_seed" \
        '.regression_seeds = ((.regression_seeds // []) + [$seed] | unique)' \
        "$config_path" > "$temporary_config"
else
    jq -n --argjson seed "$variant_seed" \
        '{regression_seeds: [$seed]}' > "$temporary_config"
fi

chmod 0644 "$temporary_config"
mv "$temporary_config" "$config_path"
trap - EXIT

echo "Added regression seed $variant_seed to $display_path"
