#!/usr/bin/env bash
set -euo pipefail

report="${RUNNER_TEMP:?}/dependency-audit"
mkdir -p "$report"
version=0.76.2
case "$(uname -s)/$(uname -m)" in
  Linux/x86_64)
    platform=Linux-64bit
    checksum=bc0fc726e017b8927a62b2d3531d7a84ee01769daf5c99ed866dced54089fdbf ;;
  Linux/aarch64)
    platform=Linux-ARM64
    checksum=ab9d51f86e6a5fb936f605faff6b593ac51bc378fff4d3e8b9d58358b9c367c3 ;;
  Darwin/arm64)
    platform=macOS-ARM64
    checksum=ae7ea358326960406b703c77b2ac490190797d80b306b5b50c2a27221da0a5b8 ;;
  *) echo 'Unsupported Trivy runner platform' >&2; exit 1 ;;
esac

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
curl --fail --silent --show-error --location --proto '=https' --proto-redir '=https' \
  --connect-timeout 20 --max-time 180 --retry 2 \
  "https://github.com/aquasecurity/trivy/releases/download/v${version}/trivy_${version}_${platform}.tar.gz" \
  -o "$tmp/trivy.tar.gz"
# BSD check mode can return success for an improperly formatted checksum line.
[[ "$checksum" =~ ^[[:xdigit:]]{64}$ ]] || { echo 'Invalid Trivy SHA-256 pin' >&2; exit 1; }
if command -v sha256sum >/dev/null; then
  # macOS sha256sum supports -c, but not GNU's --check spelling.
  printf '%s  %s\n' "$checksum" "$tmp/trivy.tar.gz" | sha256sum -c -
else
  printf '%s  %s\n' "$checksum" "$tmp/trivy.tar.gz" | shasum -a 256 -c -
fi
tar -xzf "$tmp/trivy.tar.gz" -C "$tmp" trivy
"$tmp/trivy" --version > "$report/trivy-version.txt"
"$tmp/trivy" fs --format cyclonedx --output "$report/sbom.cdx.json" .
# Findings are advisory during rollout. Scanner/DB errors still fail the job.
# No ignore-unfixed filter: the report must include unpatched vulnerabilities.
"$tmp/trivy" sbom --cache-dir "$tmp/cache" --timeout 10m \
  --exit-code 0 --format json --output "$report/trivy.json" "$report/sbom.cdx.json"
"$tmp/trivy" convert --format table --output "$report/trivy.txt" "$report/trivy.json"
cat "$report/trivy.txt"
