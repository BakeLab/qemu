#!/usr/bin/env python3
"""Check a real native Linux build; does not boot or simulate a guest."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

build = Path(sys.argv[1]).resolve()
arch = sys.argv[2]
options = {o['name']: o['value'] for o in json.loads(
    (build / 'meson-info/intro-buildoptions.json').read_text())}
for feature in ['tcg', 'pixman', 'capstone', 'gio', 'bpf', 'gnutls', 'gcrypt', 'nettle',
                'bochs', 'cloop', 'dmg', 'qcow1', 'vdi', 'vhdx', 'vmdk', 'vpc',
                'vvfat', 'qed', 'parallels']:
    assert options[feature] == 'disabled', (feature, options[feature])
for feature in ['kvm', 'libusb', 'seccomp', 'zstd']:
    assert options[feature] == 'enabled', (feature, options[feature])
config = (build / f'{arch}-softmmu-config-devices.mak').read_text().splitlines()
for device in ['VFIO_PCI', 'USB_XHCI_PCI', 'PCIE_PORT', 'VIRTIO_PCI',
               'VIRTIO_BLK', 'VIRTIO_NET', 'VHOST_VSOCK', 'VHOST_USER_FS']:
    assert f'CONFIG_{device}=y' in config, device
qemu = str(build / f'qemu-system-{arch}')
accels = subprocess.check_output([qemu, '-accel', 'help'], text=True).splitlines()
names = {line.split()[0] for line in accels[1:] if line.split()}
assert 'kvm' in names and 'tcg' not in names, accels
help_text = subprocess.check_output([qemu, '-device', 'help'], text=True)
for device in ['vfio-pci', 'qemu-xhci', 'usb-host', 'pcie-root-port',
               'virtio-blk-pci', 'virtio-net-pci', 'vhost-vsock-pci', 'vhost-user-fs-pci']:
    assert f'name "{device}"' in help_text, device
libraries = subprocess.check_output(['ldd', qemu], text=True)
for unwanted in ['pixman', 'capstone', 'libgio-', 'libbpf', 'gnutls', 'gcrypt', 'nettle']:
    assert unwanted not in libraries, libraries
assert 'libglib-2.0' in libraries and 'libseccomp' in libraries, libraries

# Keep the actual unencrypted qcow2/zstd path used by Breadboard functional.
img = str(build / 'qemu-img')
for protocol in ('nbd', 'nbd+tcp', 'nbd+unix', 'nvme'):
    probe = subprocess.run([img, 'info', f'{protocol}://localhost/disk'],
                           capture_output=True, text=True, env={**os.environ, 'LC_ALL': 'C'})
    assert probe.returncode and 'Unknown protocol' in probe.stderr, probe.stderr
with tempfile.TemporaryDirectory() as temp:
    raw = Path(temp) / 'source.raw'
    qcow = Path(temp) / 'compressed.qcow2'
    raw.write_bytes(bytes(range(256)) * 16384)
    subprocess.run([img, 'convert', '-f', 'raw', '-O', 'qcow2', '-c',
                    '-o', 'compression_type=zstd', str(raw), str(qcow)], check=True)
    subprocess.run([img, 'check', str(qcow)], check=True)
    subprocess.run([img, 'compare', '-f', 'raw', '-F', 'qcow2',
                    str(raw), str(qcow)], check=True)
    info = json.loads(subprocess.check_output([img, 'info', '--output=json', str(qcow)]))
    assert info['format'] == 'qcow2'
    assert info['format-specific']['data']['compression-type'] == 'zstd'

# Hash/HMAC uses GLib when the optional encryption libraries are absent.
subprocess.run([str(build / 'tests/unit/test-crypto-hash')], check=True)
print(f'{arch}: native KVM/device support, slim dependencies, and qcow2/zstd verified')
