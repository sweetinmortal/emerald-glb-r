#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Prepare a verified kernel and module bundle from the emerald_r HyperOS 3 OTA."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import shutil
import stat
import struct
import subprocess
import tempfile


SOURCE_BUILD = 'OS3.0.306.0.WFOMIXM'
KERNEL_RELEASE = '6.12.30-android16-5-g6e872b4863d6-ab13847919-4k'
BOOT_IMAGES = {
    'boot': 'ab65b9073d4a6356dd59a50d13860ef7583896aebb0433e3228e1a6e5d8bb930',
    'vendor_boot': 'ddf2a0f14afa434eb0096338b75df3cd6cfbc1dc18ec7f0d93a76a9238135af2',
    'dtbo': 'bcf2689e91b0d929be20d794c7f2d797718ad734e61bea24b3de0e80c1ce865e',
}
DLKM_IMAGES = {
    'system_dlkm': 'c3e10a0b08cd7845453482e11b5fa8a3cbb182559100d0617b259ad5c61efcb3',
    'vendor_dlkm': '209697de53096e46ae058e0942134f51ca65025959db937a49b5c68b84ab702b',
    'odm_dlkm': '0c2782432531f7a1f3cd494756780dc24cb9cbcaf04ea2ffc502aaea99acd05e',
}
KERNEL_SHA256 = 'e4121682a5dc9e637710642eb4daaea57697f3b501a959715c4cc323f3e15e35'
RAW_KERNEL_SHA256 = '0e7049221a75e9801d62a98cd6e4b2f7ce57304aae7e6e5e9957658fa67f09d0'
MODULE_SIGNATURE = b'~Module signature appended~\n'


def sha256(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def verify_image(directory, partition, expected):
    image = directory / (partition + '.img')
    if sha256(image) != expected:
        raise ValueError('Image is not from the pinned OTA: ' + partition)
    return image


def align(size, page):
    return (size + page - 1) // page * page


def kernel_from_boot(image):
    with image.open('rb') as stream:
        header = stream.read(4096)
        kernel_size, ramdisk_size = struct.unpack_from('<II', header, 8)
        version = struct.unpack_from('<I', header, 40)[0]
        if header[:8] != b'ANDROID!' or version != 4 or ramdisk_size != 0:
            raise ValueError('Unexpected stock boot header')
        return stream.read(kernel_size)


def copy_boot_body(image, destination):
    # Keep all manufacturer bytes covered by the outer AVB descriptor,
    # including the GKI certificate beyond the page-aligned kernel.
    with image.open('rb') as stream:
        footer_offset = stream.seek(-64, 2)
        magic, major, minor, body_size, vbmeta_offset, vbmeta_size = struct.unpack(
            '>4sIIQQQ28x', stream.read(64))
        if ((magic, major, minor) != (b'AVBf', 1, 0)
                or not 4096 < body_size <= vbmeta_offset < footer_offset
                or not 0 < vbmeta_size <= footer_offset - vbmeta_offset):
            raise ValueError('Invalid outer AVB footer for stock boot')
        stream.seek(vbmeta_offset)
        if stream.read(4) != b'AVB0':
            raise ValueError('Missing outer vbmeta for stock boot')
        stream.seek(0)
        destination.write_bytes(stream.read(body_size))


def vendor_boot_parts(image):
    with image.open('rb') as stream:
        header = stream.read(4096)
        version, page, kernel_addr, ramdisk_addr, ramdisk_size = struct.unpack_from('<5I', header, 8)
        header_size, dtb_size, dtb_addr, table_size, count, entry_size, config_size = struct.unpack_from(
            '<IIQIIII', header, 2096)
        if (header[:8] != b'VNDRBOOT' or (version, page, header_size) != (4, 4096, 2128)
                or count != 2 or entry_size != 108 or table_size != count * entry_size):
            raise ValueError('Unexpected stock vendor_boot layout')
        stream.seek(page + align(ramdisk_size, page))
        dtb = stream.read(dtb_size)
        table_offset = page + align(ramdisk_size, page) + align(dtb_size, page)
        stream.seek(table_offset)
        table = stream.read(table_size)
        stream.seek(table_offset + align(table_size, page))
        bootconfig = stream.read(config_size)
        fragments = {}
        for index in range(count):
            size, offset, kind = struct.unpack_from('<III', table, index * entry_size)
            if kind in fragments or kind not in (1, 2) or offset + size > ramdisk_size:
                raise ValueError('Invalid vendor ramdisk fragment')
            stream.seek(page + offset)
            fragments[kind] = stream.read(size)
    layout = {'header_version': version, 'page_size': page, 'kernel_addr': kernel_addr,
              'ramdisk_addr': ramdisk_addr, 'dtb_addr': dtb_addr,
              'cmdline': header[28:2076].rstrip(b'\0').decode(),
              'vendor_ramdisk_fragment_bytes': {str(kind): len(data) for kind, data in fragments.items()}}
    return dtb, bootconfig, fragments, layout


def fdt_entry(table):
    magic, size, header_size, entry_size, count, entries, _, version = struct.unpack_from('>8I', table)
    if (magic != 0xd7b7ab1e or version != 0 or count != 1 or header_size != 32
            or entry_size != 32 or not header_size <= entries <= size - entry_size or size > len(table)):
        raise ValueError('Unexpected Android device-tree table')
    length, offset = struct.unpack_from('>II', table, entries)
    if not entries + entry_size <= offset < offset + length <= size or table[offset:offset + 4] != b'\xd0\x0d\xfe\xed':
        raise ValueError('Invalid FDT entry extent')
    return table[offset:offset + length]


def is_module_input(path):
    return path.suffix == '.ko' or path.name.startswith(('modules.', 'fstab.'))


def extract_ramdisk(archive, destination):
    init_paths = []
    with archive.open('rb') as stream:
        limit = archive.stat().st_size
        while stream.tell() + 110 <= limit:
            header = stream.read(110)
            if header[:6] not in (b'070701', b'070702'):
                raise ValueError('Invalid cpio header')
            mode = int(header[14:22], 16)
            size = int(header[54:62], 16)
            name_size = int(header[94:102], 16)
            if not 1 <= name_size <= 4096:
                raise ValueError('Invalid cpio path length')
            name = PurePosixPath(stream.read(name_size).rstrip(b'\0').decode())
            start = align(stream.tell(), 4)
            if name.is_absolute() or '..' in name.parts or start + size > limit:
                raise ValueError('Invalid cpio member extent or path')
            if name.name == 'TRAILER!!!':
                return init_paths
            if name.name == 'init':
                init_paths.append(name.as_posix())
            stream.seek(start)
            if stat.S_ISREG(mode) and is_module_input(name):
                path = destination.joinpath(*name.parts)
                path.parent.mkdir(parents=True, exist_ok=True)
                with path.open('xb') as output:
                    output.write(stream.read(size))
            stream.seek(align(start + size, 4))
    raise ValueError('Missing cpio trailer')


def decompress_lz4(data, destination):
    with destination.open('wb') as stream:
        subprocess.run(['lz4', '-dc', '-'], input=data, stdout=stream, check=True)


def read_module_report(output):
    modules = []
    for path in sorted(output.glob('modules/**/*.ko')):
        with path.open('rb') as stream:
            header = stream.read(64)
            if header[:6] != b'\x7fELF\x02\x01' or struct.unpack_from('<H', header, 18)[0] != 183:
                raise ValueError('Expected a little-endian ARM64 kernel module: ' + path.name)
            stream.seek(-len(MODULE_SIGNATURE), 2)
            signed = stream.read() == MODULE_SIGNATURE
        vermagic = subprocess.check_output(['modinfo', '-F', 'vermagic', str(path)], text=True).strip()
        modules.append({'path': path.relative_to(output).as_posix(), 'sha256': sha256(path),
                        'vermagic': vermagic, 'signature_trailer_present': signed})
    if not modules:
        raise ValueError('No stock modules were extracted')
    return modules


def validate_module_lists(directory, installed_path, list_names):
    installed = {path.name for path in directory.glob('*.ko')}
    dependencies = {}
    dependency_file = directory / 'modules.dep'
    for line in dependency_file.read_text().splitlines():
        module, required = line.split(':', 1)
        paths = [PurePosixPath(path) for path in [module, *required.split()]]
        if any(path.parent != installed_path or path.name not in installed for path in paths):
            raise ValueError('Module dependency points outside the stock module set: ' + line)
        if paths[0].name in dependencies:
            raise ValueError('Duplicate dependency row: ' + module)
        dependencies[paths[0].name] = {path.name for path in paths[1:]}

    lists = {}
    for name in list_names:
        path = directory / name
        requested = path.read_text().split()
        if (not requested or len(requested) != len(set(requested))
                or not set(requested) <= dependencies.keys()):
            raise ValueError('Invalid stock module load list: ' + str(path))
        closure = set(requested)
        pending = requested.copy()
        while pending:
            module = pending.pop()
            if module not in dependencies:
                raise ValueError('Missing dependency metadata: ' + module)
            additional = dependencies[module] - closure
            closure.update(additional)
            pending.extend(additional)
        implicit = closure - set(requested)
        lists[name] = {'entries': len(requested), 'implicit_dependencies': sorted(implicit),
                       'sha256': sha256(path)}
    return {'modules': len(installed), 'modules_dep_sha256': sha256(dependency_file), 'lists': lists}


def prepare_module_layout(output):
    modules = output / 'modules'
    platform = modules / 'platform-ramdisk'
    layout = {
        'platform_ramdisk': validate_module_lists(
            platform / 'lib/modules', PurePosixPath('/lib/modules'),
            ('modules.load', 'modules.load.recovery')),
    }
    for name in ('system_dlkm', 'vendor_dlkm'):
        layout[name] = validate_module_lists(
            modules / name / 'lib/modules', PurePosixPath(f'/{name}/lib/modules'), ('modules.load',))
    if any((modules / 'odm_dlkm').rglob('*.ko')):
        raise ValueError('Unexpected modules in the pinned odm_dlkm image')
    layout['odm_dlkm'] = {'modules': 0}

    # Preserve the mount policy for the three verified EROFS module images.
    fstab = platform / 'first_stage_ramdisk/fstab.mt6789'
    entries = []
    for line in fstab.read_text().splitlines():
        fields = line.split()
        if fields and fields[0] in DLKM_IMAGES and len(fields) >= 3 and fields[2] == 'erofs':
            entries.append(fields)
    expected = {'wait', 'slotselect', 'avb', 'logical', 'first_stage_mount'}
    if (len(entries) != len(DLKM_IMAGES) or {entry[0] for entry in entries} != set(DLKM_IMAGES)
            or any(len(entry) != 5 or entry[1] != '/' + entry[0] or entry[3] != 'ro'
                   or set(entry[4].split(',')) != expected for entry in entries)):
        raise ValueError('Unexpected stock DLKM mount policy')
    fstab_fragment = output / 'fstab.dlkm'
    fstab_fragment.write_text(''.join(' '.join(entry) + '\n' for entry in entries), newline='\n')
    layout['fstab_dlkm_sha256'] = sha256(fstab_fragment)
    (output / 'module-layout.json').write_text(json.dumps(layout, indent=2) + '\n', newline='\n')


def write_checksums(output):
    files = sorted(path for path in output.rglob('*') if path.is_file())
    with (output / 'SHA256SUMS').open('x', newline='\n') as stream:
        for path in files:
            stream.write(f'{sha256(path)}  {path.relative_to(output).as_posix()}\n')


def prepare_bundle(boot_directory, dlkm_directory, output, scratch):
    boot = {name: verify_image(boot_directory, name, digest) for name, digest in BOOT_IMAGES.items()}
    dlkm = {name: verify_image(dlkm_directory, name, digest) for name, digest in DLKM_IMAGES.items()}

    kernel = output / 'Image.lz4'
    kernel.write_bytes(kernel_from_boot(boot['boot']))
    if sha256(kernel) != KERNEL_SHA256:
        raise ValueError('Stock compressed kernel hash mismatch')
    boot_body = output / 'boot.pre-avb.img'
    copy_boot_body(boot['boot'], boot_body)
    raw_kernel = scratch / 'Image'
    decompress_lz4(kernel.read_bytes(), raw_kernel)
    if sha256(raw_kernel) != RAW_KERNEL_SHA256:
        raise ValueError('Stock uncompressed kernel hash mismatch')

    dtb, bootconfig, fragments, layout = vendor_boot_parts(boot['vendor_boot'])
    (output / 'dtb').mkdir()
    (output / 'dtb/mt6789.dtb').write_bytes(dtb)
    (output / 'bootconfig').write_bytes(bootconfig)
    shutil.copyfile(boot['dtbo'], output / 'dtbo.img')
    base, overlay = scratch / 'base.dtb', scratch / 'overlay.dtbo'
    base.write_bytes(fdt_entry(dtb))
    overlay.write_bytes(fdt_entry(boot['dtbo'].read_bytes()))
    subprocess.run(['fdtoverlay', '-i', str(base), '-o', str(scratch / 'merged.dtb'), str(overlay)], check=True)

    layout['boot_ramdisk_bytes'] = 0
    layout['vendor_ramdisk_init_paths'] = {}
    for kind, data in fragments.items():
        name = {1: 'platform-ramdisk', 2: 'recovery-ramdisk'}[kind]
        archive = scratch / (name + '.cpio')
        decompress_lz4(data, archive)
        layout['vendor_ramdisk_init_paths'][name] = extract_ramdisk(archive, output / 'modules' / name)

    (output / 'images').mkdir()
    dlkm_links = {}
    for name, image in dlkm.items():
        extracted = scratch / name
        extracted.mkdir()
        subprocess.run(['fsck.erofs', '--no-preserve', '--extract=' + str(extracted), str(image)], check=True)
        shutil.copyfile(image, output / 'images' / image.name)
        links = {}
        for path in sorted(extracted.rglob('*')):
            relative = path.relative_to(extracted)
            if path.is_symlink():
                links[relative.as_posix()] = str(path.readlink())
            elif path.is_file() and is_module_input(path):
                target = output / 'modules' / name / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(path, target)
        dlkm_links[name] = links

    modules = read_module_report(output)
    prepare_module_layout(output)
    different_build_releases = [row['path'] for row in modules
                                if row['vermagic'].split()[:1] != [KERNEL_RELEASE]]
    report = {'source_build': SOURCE_BUILD, 'kernel_release': KERNEL_RELEASE,
              'input_image_sha256': {**BOOT_IMAGES, **DLKM_IMAGES}, 'kernel_sha256': KERNEL_SHA256,
              'boot_body_sha256': sha256(boot_body),
              'module_layout_sha256': sha256(output / 'module-layout.json'),
              'dtb_sha256': sha256(output / 'dtb/mt6789.dtb'), 'dtb_dtbo_merge_verified': True,
              'boot_layout': layout, 'modules': modules,
              'modules_with_different_build_release': different_build_releases,
              'dlkm_symlinks': dlkm_links, 'full_abi_verified': False, 'ready_to_flash': False}
    (output / 'bundle.json').write_text(json.dumps(report, indent=2) + '\n')
    write_checksums(output)
    return {'kernel_release': KERNEL_RELEASE, 'modules': len(modules),
            'modules_with_different_build_release': len(different_build_releases), 'dtb_dtbo_merge_verified': True,
            'ready_to_flash': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--boot-images', required=True, type=Path)
    parser.add_argument('--module-images', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    output = args.output.resolve()
    if output.exists():
        raise FileExistsError(output)
    with tempfile.TemporaryDirectory(prefix='.stock612-', dir=output.parent) as staging_dir:
        with tempfile.TemporaryDirectory(prefix='stock612-unpack-') as scratch_dir:
            staging = Path(staging_dir) / 'bundle'
            staging.mkdir()
            result = prepare_bundle(args.boot_images, args.module_images, staging, Path(scratch_dir))
            staging.rename(output)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
