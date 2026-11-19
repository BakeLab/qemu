#!/usr/bin/env python3
"""Smoke-test QEMU's native fuzz targets for Breadboard's virtio devices."""

from __future__ import annotations

import argparse
import os
import pathlib
import signal
import subprocess

TARGETS = (
    "virtio-net-socket-check-used",
    "virtio-blk-flags-fuzz",
    "virtio-scsi-flags-fuzz",
    "generic-fuzz-virtio-blk",
    "generic-fuzz-virtio-rng",
    "generic-fuzz-virtio-balloon",
)


def main(build: pathlib.Path) -> None:
    binary = build / "qemu-fuzz-x86_64"
    if not binary.is_file() or not os.access(binary, os.X_OK):
        raise RuntimeError(f"QEMU fuzz executable missing: {binary}")

    for target in TARGETS:
        workdir = build / "breadboard-fuzz-work" / target
        workdir.mkdir(parents=True, exist_ok=True)
        env = os.environ.copy()
        env["TMPDIR"] = str(workdir)
        command = [str(binary), f"--fuzz-target={target}", "-runs=100"]
        process = subprocess.Popen(command, cwd=workdir, env=env, start_new_session=True)
        try:
            status = process.wait(timeout=180)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait()
            raise RuntimeError(f"fuzz smoke exceeded its 180 second limit: {target}") from None
        if status:
            raise subprocess.CalledProcessError(status, command)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("build_dir", type=pathlib.Path)
    main(parser.parse_args().build_dir.resolve())
