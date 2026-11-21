#!/usr/bin/env bash
set -euo pipefail
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
mkdir "$tmp/input"
printf 'read-only input\n' > "$tmp/input/fixture"
cat > "$tmp/probe.go" <<'GO'
package main

import (
    "fmt"
    "net"
    "os"
    "strings"
)

func main() {
    fail := func(message string) { fmt.Fprintln(os.Stderr, message); os.Exit(1) }
    if os.Getuid() != 65534 || os.Getgid() != 65534 { fail("unexpected scanner identity") }
    if os.Getenv("SCANNER_TEST_SECRET") != "" { fail("runner environment entered scanner") }
    status, err := os.ReadFile("/proc/self/status")
    if err != nil { fail("cannot inspect scanner privileges") }
    for _, expected := range []string{"CapEff:\t0000000000000000", "CapBnd:\t0000000000000000", "NoNewPrivs:\t1"} {
        if !strings.Contains(string(status), expected) { fail("scanner privilege restriction missing") }
    }
    interfaces, err := net.Interfaces()
    if err != nil { fail("cannot inspect scanner network") }
    for _, iface := range interfaces {
        if iface.Flags&net.FlagLoopback == 0 { fail("scanner has a non-loopback interface") }
    }
    if _, err := os.Stat("/var/run/docker.sock"); !os.IsNotExist(err) { fail("Docker socket is visible") }
    if _, err := os.ReadFile("/input/fixture"); err != nil { fail("cannot read input") }
    if err := os.WriteFile("/input/fixture", []byte("changed"), 0600); err == nil { fail("input is writable") }
    if err := os.WriteFile("/unexpected", []byte("changed"), 0600); err == nil { fail("root filesystem is writable") }
    if err := os.WriteFile("/output/passed", []byte("isolation verified\n"), 0600); err != nil { fail("cannot write report") }
}
GO
CGO_ENABLED=0 go build -o "$tmp/probe" "$tmp/probe.go"
SCANNER_TEST_SECRET=must-not-enter-scanner bash scripts/ci/offline-scanner.sh \
  "$tmp/probe" "$tmp/input" "$tmp/report"
test "$(cat "$tmp/report/passed")" = 'isolation verified'
