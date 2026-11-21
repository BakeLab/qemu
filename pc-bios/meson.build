roms = []
if unpack_edk2_blobs
  fds = []
  firmware_descriptors = []
  foreach arch : ['aarch64', 'riscv64', 'loongarch64', 'x86_64']
    if arch + '-softmmu' in target_dirs
      fds += ['edk2-' + arch + '-code.fd']
      firmware_descriptors += ['60-edk2-' + arch + '.json']
      if arch == 'x86_64'
        fds += ['edk2-x86_64-secure-code.fd', 'edk2-i386-vars.fd']
        firmware_descriptors += ['50-edk2-x86_64-secure.json']
      else
        fds += ['edk2-' + arch + '-vars.fd']
      endif
    endif
  endforeach

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
  'hexagon_booter_qcs6490_cdsp',
  'hexagon_loadlinux_qcs6490_cdsp',
  'hexagon_booter_sm8975_nsp',
  'hexagon_loadlinux_sm8975_nsp',
  'hexagon_booter_sa8775p_cdsp',
  'hexagon_loadlinux_sa8775p_cdsp',
  'hexagon_booter_sc8480xp_nsp0',
  'hexagon_loadlinux_sc8480xp_nsp0',
  'hexagon_booter_sa8797p_nsp0',
  'hexagon_loadlinux_sa8797p_nsp0',
  'hexagon-hypervisor-license.txt',
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
