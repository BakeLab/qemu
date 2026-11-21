#include <stdio.h>
#include <stdlib.h>

void formatting(char *dst, size_t size, const char *src)
{
    // ruleid: qemu-unbounded-format
    sprintf(dst, "%s", src);
    // ok: qemu-unbounded-format
    snprintf(dst, size, "%s", src);
}

void shell(const char *cmd)
{
    // ruleid: qemu-shell-command
    system(cmd);
}
