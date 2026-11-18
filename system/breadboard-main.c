/* SPDX-License-Identifier: GPL-2.0-or-later */
extern int bb_qemu_system_main(int argc, char **argv);

int main(int argc, char **argv)
{
    return bb_qemu_system_main(argc, argv);
}
