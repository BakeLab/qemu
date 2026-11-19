"""Run QEMU unit/qtest suites, excluding tests that require unavailable host KVM."""

from __future__ import annotations

import argparse
import logging
import subprocess
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


KVM_ONLY_TESTS = {"bios-tables-test", "migration-test"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("build_dir", type=Path)
    build = parser.parse_args().build_dir
    meson = build / "pyvenv/bin/meson"
    listed = subprocess.run(
        [
            str(meson),
            "test",
            "-C",
            str(build),
            "--suite",
            "unit",
            "--suite",
            "qtest",
            "--list",
        ],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    tests = [line.strip() for line in listed.splitlines() if line.strip().startswith("qemu:")]
    if not tests:
        raise RuntimeError(f"Meson did not list unit/qtest tests for {build}")

    excluded = [
        test
        for test in tests
        if test.startswith("qemu:qtest") and test.rsplit("/", maxsplit=1)[-1] in KVM_ONLY_TESTS
    ]
    selected = [test for test in tests if test not in excluded]
    if excluded:
        logger.info("Skipping QEMU qtests requiring host KVM, unavailable in the CI runner:")
        for test in excluded:
            logger.info("  %s", test)
    subprocess.run(
        [str(meson), "test", "-C", str(build), "--print-errorlogs", *selected],
        check=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
