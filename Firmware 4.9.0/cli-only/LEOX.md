# LEOX GPON profile for CLI-only bank1

This is the profile discussed for the previous LEOX LXT-010G-D ONT. **Verify all values with the user's own previous device and service provider before applying.** Copy/pasting a profile may prevent registration, and it does not fix the `MIB_GetAttrFromBuf` size assertion.

Expected values in the discussed profile:
- GPON SN: `LEOXA210B19E` (raw 8-byte hex `4C454F58A210B19E`)
- Vendor ID: `LEOX`
- `OMCI_OLT_MODE=0`; `OMCI_FAKE_OK=0`
- LOID `user` (configured in the existing `omci_app -l user` invocation, not by this script)
- PLOAM: ten ASCII spaces (**not automatically applied**; must be verified against OLT requirements)

On Ubuntu download the script or copy it from this repository, then:

```bash
scp -O "Firmware 4.9.0/cli-only/configure-leox.sh" ubnt@192.168.1.1:/tmp/configure-leox.sh
```

On UF-Instant running modified bank1:

```sh
sh /tmp/configure-leox.sh --show
sh /tmp/configure-leox.sh --apply
```

The script only changes the SN override file in shared `/var/config` and specified firmware `flash` keys. It does not erase MTD or change hardware identity storage. The shared settings may also affect future boots and firmware banks. Backup config before applying. If the CLI prints unknown-key errors, do not assume the value was stored.

Verify with `flash get` (not a guarantee of actual OMCI advertising), then restart OMCI and inspect logs. Device-unique serial/MAC and optical calibration must not be overwritten.
