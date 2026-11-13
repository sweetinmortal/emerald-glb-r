# Test report — 2026-11-08

## Device

| Property | Value |
|---|---|
| Device | Redmi Note 14S global |
| Model | `2502FRA65G` |
| Variant | `emerald_r_global` |
| SKU | `glb_r` |
| SoC | `mt6789` |
| Stock base | `OS3.0.306.0.WFOMIXM` |
| Slot tested | `_b` |
| SELinux | `Enforcing` |

## Build

| Property | Value |
|---|---|
| Build | `LineageOS 24.0-20261106-UNOFFICIAL-emerald` |
| `ro.lineage.version` | `24.0-20261106-UNOFFICIAL-emerald` |
| `ro.lineage.releasetype` | `UNOFFICIAL` |
| `ro.build.display.id` | `CP2A.260605.016` |
| `ro.build.version.release` | `17` |
| `ro.build.version.sdk` | `37` |
| `ro.build.version.security_patch` | `2026-10-05` |
| `ro.build.date` | `Sat Nov  7 00:55:00 MSK 2026` |
| `ro.build.type` | `user` |
| `ro.build.tags` | `release-keys` |
| `ro.build.flavor` | `lineage_emerald-userdebug` |
| Kernel | `6.12.30-android16-5-g6e872b4863d6-ab13847919-4k` |
| `ro.odm.build.version.incremental` | `OS3.0.306.0.WFOMIXM` |

Build fingerprint:

```text
Redmi/emerald_r_global/emerald:16/BP2A.250605.031.A3/OS3.0.305.0.WNFMIXM:user/release-keys
```

The fingerprint carries the donor's `WNFMIXM` string because the donor system runs over the stock vendor. The actual vendor/ODM incremental is `OS3.0.306.0.WFOMIXM`.

## Checklist

| Test | Result |
|---|---|
| Clean install from stock `OS3.0.306.0.WFOMIXM` | Pass |
| First boot from slot B | Pass |
| Second consecutive boot from slot B | Pass |
| SELinux `Enforcing` | Pass |
| LTE / IMS | Pass |
| Wi-Fi hotspot | Pass |
| Second device of the same model | Pending |
| Long soak (calls, camera, video, charging, suspend) | Pending |

## Limitations

- One device only.
- No IMEI, serial number, account data, or personal identifiers are recorded here.
- The test does not prove compatibility with other variants, bases, or hardware revisions.
