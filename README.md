# emerald-glb-r

Unofficial LineageOS 24.0 notes and tooling for the **Redmi Note 14S global** (`2502FRA65G`, SKU `glb_r`, variant `emerald_r_global`) on the stock **WFOMIXM** base.

> **Status: experimental, one device tested. No public flashable build is provided yet.**
> This is not an official LineageOS, Xiaomi, RamDll, or emerald-lineage project.

An experimental vanilla candidate was generated and verified offline on 2026-11-16. It also completed Android userspace setup in a DSU guest on that date; on 2026-11-17 the device owner confirmed that the Quick Settings QR scanner worked there. This exercises userspace over the host's existing kernel and Magisk-patched `vendor_boot`, not a full OTA boot with the candidate's clean `vendor_boot`. The [preparation notes](docs/vanilla.md) cover the removal tool, retained optional components and verification evidence. The vanilla candidate is not ready for general flashing. The tested configuration below describes the earlier non-vanilla working installation.

## What this is

This repository documents a community test of LineageOS 24.0 running on the Redmi Note 14S global while keeping the stock `OS3.0.306.0.WFOMIXM` vendor and kernel 6.12.30. It is based on the RamDll 2.20 build and is intended to become the home for:

- the reproducible `glb_r` / WFOMIXM compatibility changes;
- test reports and verification hashes;
- sanitized packaging and verification tooling;
- a future unofficial build, if it can be distributed safely.

It is **not** an official LineageOS port and does **not** include proprietary firmware, GApps, signing keys, or a flashable ZIP.

## Tested configuration

| Item | Value |
|---|---|
| Device | Redmi Note 14S global |
| Model | `2502FRA65G` |
| Variant / SKU | `emerald_r_global` / `glb_r` |
| Stock base | `OS3.0.306.0.WFOMIXM` |
| Build | `LineageOS 24.0-20261106-UNOFFICIAL-emerald` |
| Android | 17 |
| Security patch | `2026-10-05` |
| Kernel | `6.12.30-android16-5-g6e872b4863d6-ab13847919-4k` |
| Slot tested | `_b` |
| SELinux | `Enforcing` |
| GApps | MindTheGapps, inherited from the donor build |

**Tested on one device only.** LTE/IMS and Wi-Fi hotspot were checked. A second device and a longer soak test are still pending.

Build fingerprint reported by the running system:

```text
Redmi/emerald_r_global/emerald:16/BP2A.250605.031.A3/OS3.0.305.0.WNFMIXM:user/release-keys
```

The fingerprint still carries the donor's `WNFMIXM` string because the donor system runs over the stock vendor. The actual vendor/ODM incremental is `OS3.0.306.0.WFOMIXM`.

## Why this variant is different

The current RamDll instructions target `OS3.0.305.0.WNFMIXM`. This test keeps the **WFOMIXM 306 vendor and kernel**, uses the RamDll userspace, and applies the compatibility and mount adjustments needed for `glb_r`:

- VINTF compatibility configuration for the vendor's AIDL interfaces;
- mount-policy adjustments for the `mi_ext` overlay paths;
- test notes and input hashes.

The exact patch series will be published in `patches/` before a PR is sent upstream.

## Status and roadmap

- [x] Clean install from stock `OS3.0.306.0.WFOMIXM`
- [x] Two consecutive boots from slot B
- [x] SELinux `Enforcing`
- [x] LTE / IMS
- [x] Wi-Fi hotspot
- [ ] Second Redmi Note 14S of the same model
- [ ] Longer soak test (calls, camera, video, charging, suspend)
- [ ] Minimal patch series for upstream review
- [ ] Draft PR to `emerald-lineage/android_device_xiaomi_emerald`
- [ ] General-use build with validated recovery and documented redistribution rights

See [`docs/roadmap.md`](docs/roadmap.md) for details.

## Links

- [Experimental ZIP and test notes on SourceForge](https://sourceforge.net/projects/emerald-glb-r/files/experimental-20261118/)
- Upstream device tree: https://github.com/emerald-lineage/android_device_xiaomi_emerald
- Upstream issue for this variant: https://github.com/emerald-lineage/android_device_xiaomi_emerald/issues/1
- RamDll releases: https://github.com/RamDll/emerald-ota/releases
- LineageOS: https://lineageos.org

## Contributing

Test reports, documentation, and small reproducible patches are welcome. Read [`CONTRIBUTING.md`](CONTRIBUTING.md) first. Please do not attach proprietary firmware, GApps, signing keys, or personal data.

## Credits

- **RamDll** for the LineageOS 24.0 donor build and release notes.
- **emerald-lineage** for the upstream device tree.
- **LineageOS** and **AOSP** for the platform.

## License

Original documentation and tooling in this repository are licensed under the Apache License 2.0. See [`LICENSE`](LICENSE). Patches intended for upstream are provided for review under the upstream project's terms. This repository does not grant rights to third-party proprietary components.

---

## Resumen en español

Repositorio no oficial con notas y herramientas para LineageOS 24.0 en el **Redmi Note 14S global** (`2502FRA65G`, SKU `glb_r`) usando la base stock **WFOMIXM 306**. Probado en un solo equipo; todavía no hay ZIP público ni build oficial. Los cambios reproducibles, el informe de pruebas y los scripts se publicarán aquí antes de mandar el PR a `emerald-lineage`.
