# Contributing

Contributions are welcome, especially test reports from other Redmi Note 14S units of the same model.

## Useful contributions

- Test reports with exact model, SKU, stock base, build, and results.
- Documentation fixes and translations.
- Small, reproducible patches for the `glb_r` variant.
- Sanitized verification or packaging scripts.
- Logs with personal data removed.

## Please do not submit

- Stock firmware, vendor images, or other proprietary binaries.
- GApps or Google application packages.
- Private signing keys or keystores.
- OTA ZIPs or large build artifacts.
- Logs containing IMEI, serial numbers, account data, or personal paths.
- Changes that mix multiple unrelated fixes in one patch.

## Test report template

```markdown
### Device
- Model:
- Variant / SKU:
- Stock base:
- Slot:
- SELinux:

### Build
- LineageOS version:
- Security patch:
- Kernel:
- Build fingerprint:

### Results
- Clean install:
- First boot:
- Second boot:
- LTE / IMS:
- Wi-Fi hotspot:
- Camera / video:
- Charging:
- Other:

### Notes
- What worked, what failed, and any logs (sanitized).
```

## Licensing

Original documentation and tooling are contributed under the Apache License 2.0. Patches intended for upstream are provided for review under the upstream project's terms. By contributing, you confirm that you have the right to submit the material.
