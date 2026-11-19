/* SPDX-License-Identifier: GPL-2.0-or-later */
#ifndef HW_VFIO_PCI_RESET_ORDER_H
#define HW_VFIO_PCI_RESET_ORDER_H

typedef struct VFIOPCIDevice VFIOPCIDevice;

static inline void vfio_pci_try_resets(VFIOPCIDevice *dev, bool reset_works,
                                       bool flr, bool pm, bool initial,
                                       int (*function)(VFIOPCIDevice *, bool,
                                                       bool),
                                       int (*bus)(VFIOPCIDevice *))
{
    /* VFIO_DEVICE_RESET has no method selector. Try it only once. */
    bool pm_only = pm && !flr;

    if (reset_works && !pm_only && !function(dev, initial, false)) {
        return;
    }
    if (bus(dev) == 0) {
        return;
    }
    if (reset_works && pm_only) {
        function(dev, initial, true);
    }
}

#endif
