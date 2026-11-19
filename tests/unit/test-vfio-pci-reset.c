/* SPDX-License-Identifier: GPL-2.0-or-later */
#include <stdbool.h>
#include <glib.h>
#include "hw/vfio/pci-reset-order.h"

struct VFIOPCIDevice {
    GString *calls;
    int function_result;
    int bus_result;
};

static int function_reset(VFIOPCIDevice *dev, bool initial, bool pm)
{
    g_string_append_c(dev->calls, pm ? 'P' : 'F');
    return dev->function_result;
}

static int bus_reset(VFIOPCIDevice *dev)
{
    g_string_append_c(dev->calls, 'B');
    return dev->bus_result;
}

static void test_reset_sequence(void)
{
    static const struct {
        bool works, flr, pm;
        int function_result, bus_result;
        const char *calls;
    } cases[] = {
        { true, true, true, -1, -1, "FB" },
        { true, true, true, 0, -1, "F" },
        { true, true, false, -1, 0, "FB" },
        { true, false, false, -1, -1, "FB" },
        { true, false, true, -1, -1, "BP" },
        { true, false, true, -1, 0, "B" },
        { false, true, true, -1, -1, "B" },
    };

    for (size_t i = 0; i < G_N_ELEMENTS(cases); i++) {
        VFIOPCIDevice dev = { g_string_new(NULL), cases[i].function_result,
                              cases[i].bus_result };

        vfio_pci_try_resets(&dev, cases[i].works, cases[i].flr, cases[i].pm,
                            false, function_reset, bus_reset);
        g_assert_cmpstr(dev.calls->str, ==, cases[i].calls);
        g_string_free(dev.calls, true);
    }
}

int main(int argc, char **argv)
{
    g_test_init(&argc, &argv, NULL);
    g_test_add_func("/vfio/pci/reset-sequence", test_reset_sequence);
    return g_test_run();
}
