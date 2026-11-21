#!/usr/bin/env bash
# The caller verifies the static Linux binary before supplying it here.
set -euo pipefail

tool="$(realpath "${1:?static scanner binary}")"
input="$(realpath "${2:?input directory}")"
output="${3:?private report directory}"
shift 3
[[ "$(uname -s)" == Linux && -f "$tool" && -d "$input" ]]
umask 077
mkdir -p "$output"
output="$(realpath "$output")"
context="$(mktemp -d)"
name="bb-scan-$(basename "$context" | tr '[:upper:]' '[:lower:]')"
container=
trap '
  if [[ -n "$container" ]]; then docker rm --force "$container" >/dev/null 2>&1 || true; fi
  docker volume rm "$name" >/dev/null 2>&1 || true
  docker image rm "$name" >/dev/null 2>&1 || true
  find "$context" -type d -exec chmod 0700 {} +
  rm -rf "$context"
' EXIT
mkdir "$context/input" "$context/output"
cp "$tool" "$context/scanner"
chmod 0555 "$context/scanner"
tar -C "$input" --exclude=.git -cf - . | tar -C "$context/input" -xf -
find "$context/input" -type d -exec chmod 0555 {} +
find "$context/input" -type f -exec chmod 0444 {} +
touch "$context/output/.keep"
chmod 1777 "$context/output"
# Import leaves no builder cache containing private source after image removal.
if ! tar -C "$context" --owner=0 --group=0 -cf - scanner input output | \
  docker import --change 'USER 65534:65534' --change 'ENV HOME=/tmp TMPDIR=/tmp' \
    --change 'WORKDIR /input' --change 'ENTRYPOINT ["/scanner"]' - "$name" > "$output/image.log" 2>&1; then
  echo 'Scanner image preparation failed; see the private report.' >&2
  exit 1
fi
docker volume create "$name" >/dev/null
container="$(docker create --network=none --read-only --user=65534:65534 \
  --cap-drop=ALL --security-opt=no-new-privileges:true --pids-limit=256 --memory=4g \
  --tmpfs /tmp:rw,nosuid,nodev,noexec,size=512m,mode=1777 \
  --mount "type=volume,source=$name,target=/output" "$name" "$@")"
status=0
timeout --signal=TERM --kill-after=10s 10m docker start --attach "$container" > "$output/scanner.log" 2>&1 || status=$?
docker cp "$container:/output/." "$output/"
printf '%s\n' "$status" > "$output/exit-code.txt"
if (( status != 0 )); then
  echo "Scanner returned $status; see the private report." >&2
fi
exit "$status"
