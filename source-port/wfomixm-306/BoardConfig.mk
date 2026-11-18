# SPDX-License-Identifier: Apache-2.0

TARGET_ARCH := arm64
TARGET_ARCH_VARIANT := armv8-2a
TARGET_CPU_ABI := arm64-v8a
TARGET_CPU_VARIANT := generic
TARGET_CPU_VARIANT_RUNTIME := cortex-a76

TARGET_2ND_ARCH := arm
TARGET_2ND_ARCH_VARIANT := armv8-2a
TARGET_2ND_CPU_ABI := armeabi-v7a
TARGET_2ND_CPU_ABI2 := armeabi
TARGET_2ND_CPU_VARIANT := generic
TARGET_2ND_CPU_VARIANT_RUNTIME := cortex-a55

TARGET_BOOTLOADER_BOARD_NAME := emerald
TARGET_NO_BOOTLOADER := true
TARGET_BOARD_PLATFORM := mt6789

AB_OTA_UPDATER := true
AB_OTA_PARTITIONS := \
    boot dtbo vendor_boot vbmeta vbmeta_system vbmeta_vendor \
    odm_dlkm product system system_dlkm system_ext vendor vendor_dlkm mi_ext

BOARD_SUPER_PARTITION_SIZE := 7516192768
BOARD_SUPER_PARTITION_GROUPS := main
BOARD_MAIN_SIZE := 7505707008
BOARD_MAIN_PARTITION_LIST := odm_dlkm product system system_dlkm system_ext vendor vendor_dlkm mi_ext
BOARD_USES_METADATA_PARTITION := true

BOARD_FLASH_BLOCK_SIZE := 262144
BOARD_BOOTIMAGE_PARTITION_SIZE := 67108864
BOARD_VENDOR_BOOTIMAGE_PARTITION_SIZE := 67108864
BOARD_DTBOIMG_PARTITION_SIZE := 8388608

BOARD_SYSTEMIMAGE_FILE_SYSTEM_TYPE := erofs
BOARD_SYSTEM_EXTIMAGE_FILE_SYSTEM_TYPE := erofs
BOARD_PRODUCTIMAGE_FILE_SYSTEM_TYPE := erofs
TARGET_COPY_OUT_SYSTEM_EXT := system_ext
TARGET_COPY_OUT_PRODUCT := product
TARGET_COPY_OUT_VENDOR := vendor
TARGET_COPY_OUT_ODM := vendor/odm
TARGET_COPY_OUT_SYSTEM_DLKM := system_dlkm
TARGET_COPY_OUT_VENDOR_DLKM := vendor_dlkm
TARGET_COPY_OUT_ODM_DLKM := odm_dlkm
VENDOR_SECURITY_PATCH := 2026-06-05

ifndef EMERALD_WFOMIXM_KERNEL
$(error Set EMERALD_WFOMIXM_KERNEL to the verified stock kernel bundle)
endif
ifndef EMERALD_WFOMIXM_IMAGES
$(error Set EMERALD_WFOMIXM_IMAGES to the verified stock image directory)
endif
ifndef EMERALD_WFOMIXM_FSTABS
$(error Set EMERALD_WFOMIXM_FSTABS to the output of stage-wfomixm-fstabs.py)
endif

emerald_modules := $(EMERALD_WFOMIXM_KERNEL)/modules/platform-ramdisk/lib/modules
emerald_inputs := \
    $(addprefix $(EMERALD_WFOMIXM_KERNEL)/,boot.pre-avb.img bootconfig dtb/mt6789.dtb dtbo.img) \
    $(addprefix $(emerald_modules)/,modules.load modules.load.recovery) \
    $(addprefix $(EMERALD_WFOMIXM_IMAGES)/,vendor.img mi_ext.img system_dlkm.img vendor_dlkm.img odm_dlkm.img) \
    $(addprefix $(EMERALD_WFOMIXM_FSTABS)/,fstab.mt6789 fstab.emmc)
emerald_missing := $(filter-out $(wildcard $(emerald_inputs)),$(emerald_inputs))
ifneq ($(emerald_missing),)
$(error Missing verified WFOMIXM inputs $(emerald_missing))
endif

BOARD_BOOT_HEADER_VERSION := 4
BOARD_USES_GENERIC_KERNEL_IMAGE := true
BOARD_RAMDISK_USE_LZ4 := true
BOARD_KERNEL_PAGESIZE := 4096
BOARD_KERNEL_BASE := 0x3fff8000
BOARD_KERNEL_CMDLINE := bootopt=64S3,32N2,64N2
BOARD_BOOTCONFIG := $(strip $(shell cat $(EMERALD_WFOMIXM_KERNEL)/bootconfig))
BOARD_MKBOOTIMG_ARGS += \
    --kernel_offset 0x00008000 \
    --ramdisk_offset 0x26f08000 \
    --tags_offset 0x07c88000 \
    --dtb_offset 0x07c88000 \
    --header_version 4

# The prebuilt boot already contains the verified GKI kernel.
TARGET_NO_KERNEL_OVERRIDE := true
BOARD_PREBUILT_BOOTIMAGE := $(EMERALD_WFOMIXM_KERNEL)/boot.pre-avb.img
BOARD_INCLUDE_DTB_IN_BOOTIMG := true
BOARD_PREBUILT_DTBIMAGE_DIR := $(EMERALD_WFOMIXM_KERNEL)/dtb
BOARD_KERNEL_SEPARATED_DTBO := true
BOARD_PREBUILT_DTBOIMAGE := $(EMERALD_WFOMIXM_KERNEL)/dtbo.img

BOARD_VENDOR_RAMDISK_KERNEL_MODULES := $(wildcard $(emerald_modules)/*.ko)
BOARD_VENDOR_RAMDISK_KERNEL_MODULES_LOAD := $(strip $(shell cat $(emerald_modules)/modules.load))
BOARD_VENDOR_RAMDISK_RECOVERY_KERNEL_MODULES_LOAD := $(strip $(shell cat $(emerald_modules)/modules.load.recovery))
ifneq ($(words $(BOARD_VENDOR_RAMDISK_KERNEL_MODULES)),199)
$(error Expected 199 stock platform ramdisk modules)
endif
BOARD_DO_NOT_STRIP_VENDOR_RAMDISK_MODULES := true

BOARD_MOVE_RECOVERY_RESOURCES_TO_VENDOR_BOOT := true
BOARD_INCLUDE_RECOVERY_RAMDISK_IN_VENDOR_BOOT := true
BOARD_VENDOR_RAMDISK_FRAGMENTS := lineage_init
BOARD_VENDOR_RAMDISK_FRAGMENT.lineage_init.PREBUILT := $(PRODUCT_OUT)/ramdisk.img
BOARD_VENDOR_RAMDISK_FRAGMENT.lineage_init.MKBOOTIMG_ARGS := --ramdisk_type PLATFORM
TARGET_RECOVERY_FSTAB := $(EMERALD_WFOMIXM_FSTABS)/fstab.emmc
TARGET_RECOVERY_PIXEL_FORMAT := BGRA_8888
TARGET_USERIMAGES_USE_F2FS := true

# Use the intact OEM images during bring-up.
BOARD_PREBUILT_VENDORIMAGE := $(EMERALD_WFOMIXM_IMAGES)/vendor.img
BOARD_PREBUILT_SYSTEM_DLKMIMAGE := $(EMERALD_WFOMIXM_IMAGES)/system_dlkm.img
BOARD_PREBUILT_VENDOR_DLKMIMAGE := $(EMERALD_WFOMIXM_IMAGES)/vendor_dlkm.img
BOARD_PREBUILT_ODM_DLKMIMAGE := $(EMERALD_WFOMIXM_IMAGES)/odm_dlkm.img
BOARD_CUSTOMIMAGES_PARTITION_LIST := mi_ext
BOARD_MI_EXT_IMAGE_LIST := $(EMERALD_WFOMIXM_IMAGES)/mi_ext.img

# Match the factory chain layout with AOSP keys for engineering builds.
BOARD_AVB_ENABLE := true
BOARD_AVB_ALGORITHM := SHA256_RSA2048
BOARD_AVB_KEY_PATH := external/avb/test/data/testkey_rsa2048.pem
BOARD_AVB_ROLLBACK_INDEX := 0
BOARD_AVB_MAKE_VBMETA_IMAGE_ARGS += --include_descriptors_from_image $(BOARD_MI_EXT_IMAGE_LIST)

BOARD_AVB_VBMETA_SYSTEM := system
BOARD_AVB_VBMETA_SYSTEM_ALGORITHM := SHA256_RSA2048
BOARD_AVB_VBMETA_SYSTEM_KEY_PATH := external/avb/test/data/testkey_rsa2048.pem
BOARD_AVB_VBMETA_SYSTEM_ROLLBACK_INDEX := 0
BOARD_AVB_VBMETA_SYSTEM_ROLLBACK_INDEX_LOCATION := 2

BOARD_AVB_BOOT_ALGORITHM := SHA256_RSA2048
BOARD_AVB_BOOT_KEY_PATH := external/avb/test/data/testkey_rsa2048.pem
BOARD_AVB_BOOT_ROLLBACK_INDEX := 0
BOARD_AVB_BOOT_ROLLBACK_INDEX_LOCATION := 3

BOARD_AVB_VBMETA_VENDOR := vendor
BOARD_AVB_VBMETA_VENDOR_ALGORITHM := SHA256_RSA2048
BOARD_AVB_VBMETA_VENDOR_KEY_PATH := external/avb/test/data/testkey_rsa2048.pem
BOARD_AVB_VBMETA_VENDOR_ROLLBACK_INDEX := 0
BOARD_AVB_VBMETA_VENDOR_ROLLBACK_INDEX_LOCATION := 4

include device/mediatek/sepolicy_vndr/SEPolicy.mk
