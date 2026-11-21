#!/usr/bin/env python3
"""Exercise the real pc-bios Meson install rules without building a VM."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

SOURCE = Path(__file__).resolve().parents[2]


class FirmwareInstall(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.root = Path(cls.tmp.name)
        shutil.copytree(SOURCE / 'pc-bios', cls.root / 'pc-bios')
        (cls.root / 'meson.options').write_text(
            "option('targets', type: 'array', value: [])\n"
            "option('install_blobs', type: 'boolean', value: true)\n")
        (cls.root / 'meson.build').write_text("""
project('firmware-install-regression')
fs = import('fs')
target_dirs = get_option('targets')
have_system = target_dirs.length() > 0
unpack_edk2_blobs = true
qemu_datadir = 'share/qemu'
bzip2 = find_program('bzip2')
xkbcommon = disabler()
subdir('pc-bios')
""")

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def manifests(self, targets):
        build = self.root / ('build-' + '-'.join(targets))
        subprocess.run(['meson', 'setup', str(build), str(self.root),
                        '-Dtargets=' + ','.join(targets)],
                       check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        installed = json.loads(subprocess.check_output(
            ['meson', 'introspect', '--installed', str(build)]))
        names = {Path(dest).name for dest in installed.values()}
        # Every installed descriptor must resolve to an installed blob.
        for src in installed:
            if src.endswith('.json') and 'descriptors' in src:
                descriptor = json.loads(Path(src).read_text())
                mapping = descriptor['mapping']
                for key in ['executable', 'nvram-template']:
                    self.assertIn(Path(mapping[key]['filename']).name, names)
        return {n for n in names if n.endswith('.fd')}, names

    def test_linux_kvm_device_profiles_without_tcg_or_pixman(self):
        for arch in ['x86_64', 'aarch64']:
            with self.subTest(arch=arch):
                output = self.root / (arch + '-devices.mak')
                result = subprocess.run([
                    sys.executable, str(SOURCE / 'scripts/minikconf.py'),
                    '--allnoconfig', str(output), str(output) + '.d',
                    str(SOURCE / 'configs/devices' / (arch + '-softmmu') / 'breadboard.mak'),
                    str(SOURCE / 'Kconfig'), 'CONFIG_LINUX=y', 'CONFIG_KVM=y',
                    'CONFIG_FDT=y', 'CONFIG_VHOST_KERNEL=y', 'CONFIG_VHOST_USER=y',
                    'CONFIG_' + arch.upper() + '=y',
                ], check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                config = result.stdout.decode().splitlines()
                for device in ['VFIO_PCI', 'USB_XHCI_PCI', 'PCIE_PORT',
                               'VIRTIO_BLK', 'VIRTIO_NET', 'VHOST_VSOCK', 'VHOST_USER_FS']:
                    self.assertIn('CONFIG_' + device + '=y', config)
                self.assertNotIn('CONFIG_TCG=y', config)
                self.assertNotIn('CONFIG_PIXMAN=y', config)

    def test_native_x86(self):
        fds, names = self.manifests(['x86_64-softmmu'])
        self.assertEqual(fds, {'edk2-x86_64-code.fd', 'edk2-x86_64-secure-code.fd',
                               'edk2-i386-vars.fd'})
        self.assertFalse(any('riscv' in n or 'loongarch' in n or 'edk2-arm' in n
                             or 'edk2-aarch64' in n for n in names))

    def test_native_arm(self):
        fds, names = self.manifests(['aarch64-softmmu'])
        self.assertEqual(fds, {'edk2-aarch64-code.fd', 'edk2-aarch64-vars.fd'})
        self.assertFalse(any('riscv' in n or 'loongarch' in n or 'edk2-i386' in n
                             or 'edk2-x86_64' in n for n in names))

    def test_explicit_riscv_and_loongarch(self):
        fds, names = self.manifests(['riscv32-softmmu', 'riscv64-softmmu',
                                    'loongarch64-softmmu'])
        self.assertEqual(fds, {'edk2-riscv64-code.fd', 'edk2-riscv64-vars.fd',
                               'edk2-loongarch64-code.fd', 'edk2-loongarch64-vars.fd'})
        self.assertIn('opensbi-riscv32-generic-fw_dynamic.bin', names)
        self.assertIn('opensbi-riscv64-generic-fw_dynamic.bin', names)

    def test_combined_native_targets_share_no_duplicate_vars(self):
        fds, _ = self.manifests(['i386-softmmu', 'x86_64-softmmu',
                                 'arm-softmmu', 'aarch64-softmmu'])
        self.assertEqual(len(fds), 5)

    def test_tools_only(self):
        fds, names = self.manifests([])
        self.assertFalse(fds)
        self.assertFalse(any('opensbi-' in n or n.endswith('.json') for n in names))


if __name__ == '__main__':
    unittest.main()
