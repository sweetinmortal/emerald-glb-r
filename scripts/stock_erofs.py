# SPDX-License-Identifier: Apache-2.0
"""Read verified Android EROFS images in a private mount namespace."""

MOUNT = r"""
set -eu
mount --make-rprivate /
mounted=$(mktemp -d)
cleanup() {
    cd /
    if mountpoint -q "$mounted"; then umount "$mounted"; fi
    rmdir "$mounted"
}
trap cleanup EXIT
mount -t erofs -o ro,loop,nodev,nosuid,noexec "$1" "$mounted"
cd "$mounted"
shift
"$@"
"""

TAR = (
    "tar", "--format=pax", "--sort=name", "--numeric-owner", "--xattrs",
    "--xattrs-include=*", "--pax-option=delete=atime,delete=ctime", "-cf", "-", ".",
)


def mount_command(distro, image, *command):
    prefix = []
    image_path = str(image)
    if distro:
        if len(image.drive) != 2 or image.drive[1] != ":":
            raise ValueError("WSL mode requires a Windows drive path")
        image_path = f"/mnt/{image.drive[0].lower()}{image.as_posix()[2:]}"
        prefix = ["wsl.exe", "-d", distro, "-u", "root", "--exec"]
    return [*prefix, "unshare", "--mount", "sh", "-c", MOUNT, "mount-erofs",
            image_path, *command]
