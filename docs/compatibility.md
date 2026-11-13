# Compatibility

## Supported by this test

- Redmi Note 14S **global**
- Model: `2502FRA65G`
- Variant: `emerald_r_global`
- SKU: `glb_r`
- Stock base: `OS3.0.306.0.WFOMIXM`
- Kernel: `6.12.30-android16-5-g6e872b4863d6-ab13847919-4k`
- Slot tested: `_b`
- SELinux: `Enforcing`
- Bootloader: unlocked

## Not covered

- `emerald` global on `OS3.0.305.0.WNFMIXM`
- Other model numbers or SKUs
- HyperOS 2 bases
- Locked bootloaders
- Devices with modified or unknown vendor/kernel images

## Requirements for a future test

1. Verify the exact model, variant, and SKU before flashing.
2. Start from stock `OS3.0.306.0.WFOMIXM` that boots normally.
3. Keep the bootloader unlocked and **never relock it** with this build.
4. Have the stock fastboot rescue package available.
5. Make a full backup; a clean install wipes data.
6. Use a stable USB connection and sufficient battery.

## Warnings

- This is an experimental community test, not an official LineageOS build.
- Do not mix OTA packages from different signing identities.
- Do not flash firmware images from another variant.
- If the device does not boot, restore the stock fastboot package before trying anything else.
- No warranty is provided; flashing can brick the device or delete data.
