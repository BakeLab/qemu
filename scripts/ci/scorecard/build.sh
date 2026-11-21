#!/usr/bin/env bash
set -euo pipefail
# Temporary patch against Scorecard v5.7.0. Reassess and remove when upstream
# avoids cross-repository GraphQL prefetch failures. Keep tests with the patch.
readonly commit=d7552fb3cdc05e9f6426177d3328887304fce554
readonly source_sha=c52762474028b16d0baf140c71ee787aa66c9be7b46018d7b2254a76f359368c
patch_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
tool_dir=${1:?usage: build.sh OUTPUT_DIRECTORY}
mkdir -p "$tool_dir"
tool_dir=$(cd -- "$tool_dir" && pwd)
build_dir=$(mktemp -d)
trap 'rm -rf "$build_dir"' EXIT
curl --fail --silent --show-error --location \
  --proto '=https' --proto-redir '=https' \
  --connect-timeout 20 --max-time 180 --retry 2 \
  "https://codeload.github.com/ossf/scorecard/tar.gz/$commit" \
  -o "$build_dir/source.tar.gz"
printf '%s  %s\n' "$source_sha" "$build_dir/source.tar.gz" | sha256sum --check
tar -xzf "$build_dir/source.tar.gz" -C "$build_dir"
cd "$build_dir/scorecard-$commit"
git apply --check "$patch_dir/checkruns-repo-fallback.patch"
git apply "$patch_dir/checkruns-repo-fallback.patch"
go test -mod=readonly ./clients/githubrepo -run '^TestCheckRunsIPPolicyFallback$' -count=1
CGO_ENABLED=0 go build -mod=readonly -trimpath -o "$tool_dir/scorecard" .
printf 'upstream_commit=%s\nsource_sha256=%s\n' "$commit" "$source_sha" > "$tool_dir/source.txt"
sha256sum "$patch_dir/checkruns-repo-fallback.patch" >> "$tool_dir/source.txt"
"$tool_dir/scorecard" version
