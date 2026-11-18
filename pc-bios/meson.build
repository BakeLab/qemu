roms = []
if unpack_edk2_blobs
  # Install firmware only for the system targets that survived accelerator
  # selection. Keep descriptors with their blobs so they cannot dangle.
  fds = []
  firmware_descriptors = []
  if 'aarch64-softmmu' in target_dirs
    fds += ['edk2-aarch64-code.fd']
    firmware_descriptors += ['60-edk2-aarch64.json']
  endif
  if 'arm-softmmu' in target_dirs
    fds += ['edk2-arm-code.fd']
    firmware_descriptors += ['60-edk2-arm.json']
  endif
  if 'aarch64-softmmu' in target_dirs or 'arm-softmmu' in target_dirs
    fds += ['edk2-arm-vars.fd']
  endif
  if 'i386-softmmu' in target_dirs
    fds += ['edk2-i386-code.fd', 'edk2-i386-secure-code.fd']
    firmware_descriptors += ['60-edk2-i386.json', '50-edk2-i386-secure.json']
  endif
  if 'x86_64-softmmu' in target_dirs
    fds += ['edk2-x86_64-code.fd', 'edk2-x86_64-secure-code.fd']
    firmware_descriptors += ['60-edk2-x86_64.json', '50-edk2-x86_64-secure.json']
  endif
  if 'i386-softmmu' in target_dirs or 'x86_64-softmmu' in target_dirs
    fds += ['edk2-i386-vars.fd']
  endif
  if 'riscv64-softmmu' in target_dirs
    fds += ['edk2-riscv-code.fd', 'edk2-riscv-vars.fd']
    firmware_descriptors += ['60-edk2-riscv64.json']
  endif
  if 'loongarch64-softmmu' in target_dirs
    fds += ['edk2-loongarch64-code.fd', 'edk2-loongarch64-vars.fd']
    firmware_descriptors += ['60-edk2-loongarch64.json']
  endif

  foreach f : fds
    roms += custom_target(f,
                  build_by_default: have_system,
                  output: f,
                  input: files('@0@.bz2'.format(f)),
                  capture: true,
                  install: get_option('install_blobs'),
                  install_dir: qemu_datadir,
                  command: [ bzip2, '-dc', '@INPUT0@' ])
  endforeach
endif

blobs = [
  'ast27x0_bootrom.bin',
  'bios.bin',
  'bios-256k.bin',
  'bios-microvm.bin',
  'qboot.rom',
  'vgabios.bin',
  'vgabios-cirrus.bin',
  'vgabios-stdvga.bin',
  'vgabios-vmware.bin',
  'vgabios-qxl.bin',
  'vgabios-virtio.bin',
  'vgabios-ramfb.bin',
  'vgabios-bochs-display.bin',
  'vgabios-ati.bin',
  'openbios-sparc32',
  'openbios-sparc64',
  'openbios-ppc',
  'QEMU,tcx.bin',
  'QEMU,cgthree.bin',
  'pxe-e1000.rom',
  'pxe-eepro100.rom',
  'pxe-ne2k_pci.rom',
  'pxe-pcnet.rom',
  'pxe-rtl8139.rom',
  'pxe-virtio.rom',
  'efi-e1000.rom',
  'efi-eepro100.rom',
  'efi-ne2k_pci.rom',
  'efi-pcnet.rom',
  'efi-rtl8139.rom',
  'efi-virtio.rom',
  'efi-e1000e.rom',
  'efi-vmxnet3.rom',
  'qemu-nsis.bmp',
  'multiboot_dma.bin',
  'linuxboot_dma.bin',
  'kvmvapic.bin',
  'pvh.bin',
  's390-ccw.img',
  'slof.bin',
  'skiboot.lid',
  'pnv-pnor.bin',
  'palcode-clipper',
  'u-boot.e500',
  'u-boot-sam460.bin',
  'qemu_vga.ndrv',
  'edk2-licenses.txt',
  'hppa-firmware.img',
  'hppa-firmware64.img',
  'npcm7xx_bootrom.bin',
  'npcm8xx_bootrom.bin',
  'vof.bin',
  'vof-nvram.bin',
]

foreach arch : ['riscv32', 'riscv64']
  if arch + '-softmmu' in target_dirs
    blobs += ['opensbi-' + arch + '-generic-fw_dynamic.bin']
  endif
endforeach

if get_option('install_blobs')
  install_data(blobs, install_dir: qemu_datadir, install_mode: 'rw-r--r--')
endif

subdir('descriptors')
subdir('dtb')
subdir('keymaps')
