#!/usr/bin/env bash
set -euo pipefail

project_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
output_dir="$project_dir/site"

if [[ "$output_dir" != "$project_dir/site" ]]; then
  echo "Refusing to replace an unexpected export directory: $output_dir" >&2
  exit 1
fi

rm -rf -- "$output_dir"
cd "$project_dir"

uv run shinylive export dashboard "$output_dir"
touch "$output_dir/.nojekyll"
