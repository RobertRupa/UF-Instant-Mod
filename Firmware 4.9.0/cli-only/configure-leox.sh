#!/bin/sh
# Configure UF-Instant 4.9.0 CLI-only as the previously discussed LEOX profile.
# Run ON THE STICK via telnet/ssh: sh /tmp/configure-leox.sh --apply
# This does not alter hardware SN, EEPROM, mtd8, or boot bank.
set -eu

SN_HEX='4C454F58A210B19E'
SN_ASCII='LEOXA210B19E'
VENDOR='LEOX'
LOID='user'

case "${1:---show}" in
  --show)
    echo "Proposed LEOX profile: SN=$SN_ASCII; SN override hex=$SN_HEX; vendor=$VENDOR; OMCI_OLT_MODE=0; OMCI_FAKE_OK=0; LOID=$LOID"
    echo "PLOAM is ten ASCII spaces (must be confirmed with the operator)."
    echo "No changes made; use --apply to write configuration."
    exit 0
    ;;
  --apply) ;;
  *) echo "Usage: sh $0 [--show|--apply]" >&2; exit 2 ;;
esac

[ -d /var/config ] || { echo "Missing mounted /var/config; STOP" >&2; exit 1; }
[ -x /bin/flash ] || { echo "Missing /bin/flash; STOP" >&2; exit 1; }
grep -q 'root=31:7' /proc/cmdline || { echo "CLI-only modified bank1 required; STOP" >&2; exit 1; }

echo "Writing GPON SN override..."
printf '%s\n' "$SN_HEX" > /var/config/gpon_sn_override
echo "Configuring supported flash keys; errors are not suppressed..."
/bin/flash set PON_VENDOR_ID "$VENDOR"
/bin/flash set GPON_SN "$SN_ASCII"
/bin/flash set OMCI_OLT_MODE 0
/bin/flash set OMCI_FAKE_OK 0

# Do not set PLOAM automatically: key/value handling can vary with Realtek firmware.
# To set *after checking operator requirements*, manually run:
# /bin/flash set GPON_PLOAM_PASSWD '          '

echo "Verify stored values:"
cat /var/config/gpon_sn_override
/bin/flash get PON_VENDOR_ID
/bin/flash get GPON_SN
/bin/flash get OMCI_OLT_MODE
/bin/flash get OMCI_FAKE_OK
echo "LOID currently configured by omci_app command line must remain: -l $LOID"
echo "Restart omci_app or reboot for changes to take effect. OMCI SIGABRT is not fixed by this profile."
