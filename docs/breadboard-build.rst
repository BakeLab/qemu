Breadboard fork build defaults
=============================

This fork defaults to x86_64 and aarch64 system targets with a native hardware
accelerator. Targets without an available host accelerator are skipped when no
``--target-list`` is supplied. TCG software translation is disabled, so a missing
KVM device cannot silently turn a Breadboard VM into software emulation. An
explicit non-native target needs a suitable accelerator or an explicit
``--enable-tcg``; its source code remains available.

Pixman, Capstone, GIO, libbpf, GnuTLS, libgcrypt and Nettle default to disabled.
These defaults apply to the existing Breadboard wheel command using
``--target-list=<arch>-softmmu --without-default-devices
--with-devices-<arch>=breadboard`` once its QEMU source pin is updated. They are
not merely settings in a separate, unused build wrapper.

The two Breadboard device profiles retain KVM, VFIO PCI, PCIe root ports, USB
XHCI, virtio block/network, vsock and vhost-user filesystem support. GLib remains
required and supplies the hash/HMAC implementation. ``qemu-img``, unencrypted
qcow2 and zstd compression remain available; Breadboard enables zstd explicitly.
The optional TLS and disk-encryption backends are unavailable by default. This
does not change Breadboard's separate HTTPS clients or its Unix-socket QMP
transport. Deployments requiring QEMU TLS or encrypted disks must opt back into
the appropriate backend.

libbpf supplies QEMU's optional eBPF networking features; it is separate from
seccomp-BPF. Seccomp build detection and runtime sandbox controls are unchanged.
Compiling seccomp support does not itself activate a runtime sandbox. Removing
unused emulation, disassembly, display and protocol libraries reduces code and
dependencies; it does not replace host privilege restrictions or device isolation.

Firmware is independent of target executable selection in upstream QEMU. This
fork installs EDK2 blobs and their descriptors only for configured system
targets, including the shared ARM/i386 variable templates required by aarch64
and x86_64. OpenSBI is installed only for the corresponding RISC-V system target.
Thus an x86_64 Breadboard wheel no longer includes ARM, RISC-V or LoongArch
EDK2 images, and an aarch64 wheel retains its own firmware. Explicit RISC-V or
LoongArch builds still receive matching firmware and descriptors.

``tests/breadboard/test-firmware.py`` exercises the real Meson install rules.
The native Linux CI matrix builds both device profiles, checks their accelerator
and device lists, checks linked libraries, runs the crypto hash unit test, and
round-trips a real zstd-compressed qcow2 image with ``qemu-img``. These are build
and disk-tool checks; GPU/USB passthrough workloads still need real KVM hardware.
