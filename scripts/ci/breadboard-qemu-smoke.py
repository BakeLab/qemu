#!/usr/bin/env python3
"""Exercise the Breadboard QEMU machine/device setup through real QMP startup."""

from __future__ import annotations

import argparse
import json
import pathlib
import socket
import subprocess
import tempfile
import time


def qmp_command(sock: socket.socket, command: str, arguments: dict | None = None) -> dict:
    request: dict = {"execute": command}
    if arguments is not None:
        request["arguments"] = arguments
    sock.sendall(json.dumps(request).encode() + b"\r\n")
    stream = sock.makefile("rb")
    while line := stream.readline():
        message = json.loads(line)
        if "return" in message:
            return message["return"]
        if "error" in message:
            raise RuntimeError(f"QMP {command} failed: {message['error']}")
    raise RuntimeError(f"QMP closed before replying to {command}")


def boot_probe(binary: pathlib.Path, machine: str, devices: list[str]) -> None:
    with tempfile.TemporaryDirectory(prefix="bb-qemu-qmp-") as temp:
        qmp_path = pathlib.Path(temp) / "qmp.sock"
        argv = [
            str(binary),
            "-machine",
            f"{machine},accel=tcg",
            "-nodefaults",
            "-no-user-config",
            "-display",
            "none",
            "-S",
            "-m",
            "256",
            "-smp",
            "1",
            "-qmp",
            f"unix:{qmp_path},server=on,wait=off",
            "-drive",
            "file=null-co://,if=none,id=bbdisk,format=raw",
            "-netdev",
            "socket,id=bbnet,listen=127.0.0.1:0",
        ]
        for device in devices:
            argv.extend(["-device", device])
        process = subprocess.Popen(
            argv, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True
        )
        try:
            deadline = time.monotonic() + 20
            while time.monotonic() < deadline:
                if process.poll() is not None:
                    raise RuntimeError(f"{binary.name} exited early: {process.stderr.read()}")
                try:
                    connection = socket.socket(socket.AF_UNIX)
                    connection.connect(str(qmp_path))
                    break
                except OSError:
                    connection.close()
                    time.sleep(0.1)
            else:
                raise RuntimeError(f"{binary.name} did not create its QMP socket")

            stream = connection.makefile("rb")
            greeting = json.loads(stream.readline())
            if "QMP" not in greeting:
                raise RuntimeError(f"invalid QMP greeting: {greeting}")
            # Commands are sent/read by helpers sharing the same socket stream.
            # Stash the greeting stream and use a small synchronous exchange loop.
            connection.sendall(b'{"execute":"qmp_capabilities"}\r\n')
            if "return" not in json.loads(stream.readline()):
                raise RuntimeError("QMP capability negotiation failed")
            for command in ("query-status", "query-pci"):
                connection.sendall(json.dumps({"execute": command}).encode() + b"\r\n")
                response = json.loads(stream.readline())
                if "return" not in response:
                    raise RuntimeError(f"QMP {command} failed: {response}")
            connection.sendall(b'{"execute":"quit"}\r\n')
            connection.close()
            process.wait(timeout=10)
            if process.returncode != 0:
                raise RuntimeError(f"{binary.name} quit with status {process.returncode}")
        finally:
            if process.poll() is None:
                process.kill()
                process.wait()


def main(x86_build: pathlib.Path, arm_build: pathlib.Path) -> None:
    x86 = x86_build / "qemu-system-x86_64"
    arm = arm_build / "qemu-system-aarch64"
    if not x86.is_file() or not arm.is_file():
        raise RuntimeError("expected x86_64 and aarch64 system emulators in build directory")
    boot_probe(
        x86,
        "q35",
        [
            "virtio-balloon,free-page-reporting=on",
            "virtio-rng-pci",
            "virtio-blk-pci,drive=bbdisk",
            "virtio-net-pci,netdev=bbnet",
        ],
    )
    boot_probe(
        arm,
        "virt,gic-version=3",
        [
            "virtio-balloon-device",
            "virtio-rng-device",
            "virtio-blk-device,drive=bbdisk",
            "virtio-net-device,netdev=bbnet",
        ],
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("x86_build", type=pathlib.Path)
    parser.add_argument("arm_build", type=pathlib.Path)
    args = parser.parse_args()
    main(args.x86_build.resolve(), args.arm_build.resolve())
