if unpack_edk2_blobs and get_option('install_blobs')
  foreach f: firmware_descriptors
    configure_file(input: files(f),
                   output: f,
                   configuration: {'DATADIR': get_option('prefix') / qemu_datadir},
                   install: true,
                   install_dir: qemu_datadir / 'firmware')
  endforeach
endif
