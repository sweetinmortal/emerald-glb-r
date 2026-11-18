# SPDX-License-Identifier: Apache-2.0

$(call inherit-product, $(SRC_TARGET_DIR)/product/core_64_bit.mk)
$(call inherit-product, $(SRC_TARGET_DIR)/product/full_base_telephony.mk)
$(call inherit-product, $(SRC_TARGET_DIR)/product/generic_ramdisk.mk)
$(call inherit-product, $(SRC_TARGET_DIR)/product/emulated_storage.mk)
$(call inherit-product, $(SRC_TARGET_DIR)/product/virtual_ab_ota/launch_with_vendor_ramdisk.mk)
$(call inherit-product, frameworks/native/build/phone-xhdpi-6144-dalvik-heap.mk)
$(call inherit-product, vendor/lineage/config/common_full_phone.mk)

PRODUCT_NAME := lineage_emerald_wfomixm
PRODUCT_DEVICE := emerald
PRODUCT_MANUFACTURER := Xiaomi
PRODUCT_BRAND := Redmi
PRODUCT_MODEL := 2502FRA65G
PRODUCT_SHIPPING_API_LEVEL := 34

PRODUCT_USE_DYNAMIC_PARTITIONS := true
PRODUCT_BUILD_RAMDISK_IMAGE := true
PRODUCT_BUILD_VENDOR_BOOT_IMAGE := true
PRODUCT_BUILD_INIT_BOOT_IMAGE := false
PRODUCT_OTA_ENFORCE_VINTF_KERNEL_REQUIREMENTS := true
PRODUCT_ENFORCE_VINTF_MANIFEST := true

PRODUCT_PACKAGES += \
    init.recovery.usb.rc \
    update_engine \
    update_engine_sideload \
    update_verifier

PRODUCT_COPY_FILES += \
    device/xiaomi/emerald/skip_mount.cfg:$(TARGET_COPY_OUT_SYSTEM_EXT)/etc/init/config/skip_mount.cfg \
    $(EMERALD_WFOMIXM_FSTABS)/fstab.mt6789:$(TARGET_COPY_OUT_VENDOR_RAMDISK)/first_stage_ramdisk/fstab.mt6789
