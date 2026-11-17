#!/usr/bin/env python3
"""Offline, plan-gated filtering of the Redmi Note 14S PAX overlay archives.

This tool never extracts archive members.  Dry-run is the default and prints a
JSON plan to stdout.  Applying requires the exact digest from a fresh plan and
writes only to a new output directory.
"""

from __future__ import annotations

import argparse
import copy
import fnmatch
import hashlib
import json
import os
import re
import sys
import tarfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, BinaryIO, Mapping


SCHEMA_VERSION = 1
SCOPE_ORDER = ("product", "system_ext")
DEFAULT_MANIFEST = Path(__file__).with_name("manifest.json")
WORKSPACE_ROOT = Path(__file__).resolve().parent.parent


class PlanError(Exception):
    """Input or plan validation failed."""


class ApplyError(Exception):
    """An output could not be created or verified."""


@dataclass
class ScannedMember:
    info: tarfile.TarInfo
    path: str
    metadata: dict[str, Any]


@dataclass
class ArchiveScan:
    scope: str
    path: Path
    members: list[ScannedMember]
    by_path: dict[str, ScannedMember]
    sha256: str


class HashingReader:
    """File-like wrapper that hashes exactly the bytes tarfile reads."""

    def __init__(self, source: BinaryIO) -> None:
        self.source = source
        self.hasher = hashlib.sha256()
        self.bytes_read = 0

    def read(self, size: int = -1) -> bytes:
        data = self.source.read(size)
        self.hasher.update(data)
        self.bytes_read += len(data)
        return data


def _json_bytes(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _canonical_name(raw_name: str) -> str:
    """Return a safe archive-root-relative POSIX name or reject it."""
    if not raw_name or "\x00" in raw_name or "\\" in raw_name:
        raise PlanError(f"unsafe archive member name: {raw_name!r}")
    if raw_name.startswith("/") or re.match(r"^[A-Za-z]:", raw_name):
        raise PlanError(f"absolute archive member name: {raw_name!r}")

    name = raw_name
    if name in (".", "./", "./."):
        return "."
    if name.startswith("./"):
        name = name[2:]
    if name.endswith("/"):
        name = name[:-1]
    parts = name.split("/")
    if not name or any(part in ("", ".", "..") for part in parts):
        raise PlanError(f"unsafe archive member name: {raw_name!r}")
    return "/".join(parts)


def _validate_member(info: tarfile.TarInfo) -> tuple[str, dict[str, Any]]:
    path = _canonical_name(info.name)
    if getattr(info, "sparse", None):
        raise PlanError(f"sparse member is unsupported: {info.name!r}")
    if info.islnk():
        _canonical_name(info.linkname)
    metadata = {
        "archive_name": info.name,
        "type": info.type.decode("ascii", "backslashreplace")
        if isinstance(info.type, bytes)
        else str(info.type),
        "size": int(info.size),
        "mode": int(info.mode),
        "uid": int(info.uid),
        "gid": int(info.gid),
        "uname": info.uname,
        "gname": info.gname,
        "mtime": info.mtime,
        "linkname": info.linkname,
        "devmajor": int(info.devmajor),
        "devminor": int(info.devminor),
        # This includes SCHILY.xattr.* and other PAX extended fields.
        "pax_headers": dict(sorted(info.pax_headers.items())),
    }
    return path, metadata


def _scan_archive(scope: str, path: Path) -> ArchiveScan:
    if not path.is_file():
        raise PlanError(f"{scope} archive is not a readable regular file: {path}")
    try:
        digest = _sha256_file(path)
        members: list[ScannedMember] = []
        by_path: dict[str, ScannedMember] = {}
        with tarfile.open(path, mode="r:*") as archive:
            for info in archive.getmembers():
                canonical, metadata = _validate_member(info)
                if canonical in by_path:
                    raise PlanError(
                        f"duplicate normalized member name in {scope}: {info.name!r}"
                    )
                scanned = ScannedMember(info=info, path=canonical, metadata=metadata)
                members.append(scanned)
                by_path[canonical] = scanned
        # Hard links are archive-root-relative and must resolve to a member.
        for member in members:
            if member.info.islnk():
                target = _canonical_name(member.info.linkname)
                if target not in by_path:
                    raise PlanError(
                        f"hard-link target is absent in {scope}: "
                        f"{member.info.name!r} -> {member.info.linkname!r}"
                    )
        return ArchiveScan(scope, path, members, by_path, digest)
    except PlanError:
        raise
    except (OSError, tarfile.TarError, EOFError) as exc:
        raise PlanError(f"could not read {scope} PAX archive: {exc}") from exc


def _load_manifest(path: Path) -> tuple[dict[str, Any], bytes]:
    try:
        raw = path.read_bytes()
        manifest = json.loads(raw.decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise PlanError(f"could not read manifest {path}: {exc}") from exc
    if not isinstance(manifest, dict) or manifest.get("schema_version") != SCHEMA_VERSION:
        raise PlanError("manifest schema_version must be 1")
    if set(manifest.get("default_archives", {})) != set(SCOPE_ORDER):
        raise PlanError("manifest must name both product and system_ext archives")
    for key in ("core_removals", "optional_removals"):
        if not isinstance(manifest.get(key), dict):
            raise PlanError(f"manifest {key} must be an object")
    for scope in SCOPE_ORDER:
        if not isinstance(manifest["core_removals"].get(scope), list):
            raise PlanError(f"manifest core_removals.{scope} must be a list")
    return manifest, raw


def _selector_matches(selector: Mapping[str, str], path: str) -> bool:
    kind = selector.get("kind")
    value = selector.get("path") if kind in ("tree", "exact") else selector.get("pattern")
    if not isinstance(value, str) or not value:
        raise PlanError(f"invalid manifest selector: {selector!r}")
    if "\\" in value or value.startswith("/") or re.match(r"^[A-Za-z]:", value):
        raise PlanError(f"unsafe manifest selector: {value!r}")
    if kind == "tree":
        base = _canonical_name(value)
        return path == base or path.startswith(base + "/")
    if kind == "exact":
        return path == _canonical_name(value)
    if kind == "glob":
        # Patterns are relative POSIX member paths and cannot escape the root.
        for part in value.split("/"):
            if part in ("", ".", ".."):
                raise PlanError(f"unsafe glob selector: {value!r}")
        path_parts, pattern_parts = path.split("/"), value.split("/")
        return len(path_parts) == len(pattern_parts) and all(
            fnmatch.fnmatchcase(path_part, pattern_part)
            for path_part, pattern_part in zip(path_parts, pattern_parts)
        )
    raise PlanError(f"unsupported manifest selector kind: {kind!r}")


def _find_matches(scan: ArchiveScan, selector: Mapping[str, str]) -> list[ScannedMember]:
    return [m for m in scan.members if _selector_matches(selector, m.path)]


def _content_digest(archive: tarfile.TarFile, member: ScannedMember) -> tuple[str, str]:
    info = member.info
    if info.type in (tarfile.REGTYPE, tarfile.AREGTYPE):
        stream = archive.extractfile(info)
        if stream is None:
            raise PlanError(f"regular member has no data: {info.name!r}")
        digest = hashlib.sha256()
        remaining = info.size
        while remaining:
            chunk = stream.read(min(1024 * 1024, remaining))
            if not chunk:
                raise PlanError(f"truncated member payload: {info.name!r}")
            digest.update(chunk)
            remaining -= len(chunk)
        if stream.read(1):
            raise PlanError(f"member exceeds declared size: {info.name!r}")
        return digest.hexdigest(), "file_bytes"
    if info.issym():
        link = info.linkname.encode("utf-8", "surrogateescape")
        return hashlib.sha256(link).hexdigest(), "symlink_target_bytes"
    return hashlib.sha256(b"").hexdigest(), "empty_nonregular_payload"


def _content_records(
    scan: ArchiveScan, selected_paths: set[str]
) -> dict[str, dict[str, Any]]:
    records: dict[str, dict[str, Any]] = {}
    with tarfile.open(scan.path, mode="r:*") as archive:
        for path in sorted(selected_paths):
            member = scan.by_path[path]
            digest, kind = _content_digest(archive, member)
            records[path] = {
                "scope": scan.scope,
                "path": path,
                "size": int(member.info.size),
                "content_sha256": digest,
                "content_kind": kind,
                "metadata": member.metadata,
            }
    return records


def _scope_removals(
    manifest: dict[str, Any],
    scans: dict[str, ArchiveScan],
    remove_talkback: bool,
    remove_dialer_support: bool,
) -> tuple[
    dict[str, set[str]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]
]:
    removals = {scope: set() for scope in SCOPE_ORDER}
    root_inventory: list[dict[str, Any]] = []
    optional_inventory: list[dict[str, Any]] = []

    for scope in SCOPE_ORDER:
        for root in manifest["core_removals"][scope]:
            matches = _find_matches(scans[scope], root)
            if not matches:
                raise PlanError(f"required core removal root is absent: {scope}:{root}")
            paths = sorted(m.path for m in matches)
            removals[scope].update(paths)
            root_inventory.append(
                {"group": "core", "scope": scope, "selector": root,
                 "root_exists": True, "members": paths}
            )

    selected_optional = {
        "talkback": remove_talkback,
        "dialer_support": remove_dialer_support,
    }
    for group, enabled in selected_optional.items():
        config = manifest["optional_removals"].get(group, {})
        group_matches: set[tuple[str, str]] = set()
        for scope, selectors in config.items():
            if scope not in SCOPE_ORDER or not isinstance(selectors, list):
                raise PlanError(f"invalid optional removal configuration for {group}")
            for selector in selectors:
                matches = _find_matches(scans[scope], selector)
                paths = sorted(m.path for m in matches)
                group_matches.update((scope, path) for path in paths)
                root_inventory.append(
                    {"group": group, "scope": scope, "selector": selector,
                     "root_exists": bool(matches), "members": paths}
                )
        if enabled and not group_matches:
            raise PlanError(f"optional removal group has no matching members: {group}")
        if enabled:
            for scope, path in group_matches:
                removals[scope].add(path)
        optional_inventory.append(
            {"group": group,
             "state": "selected_for_removal" if enabled else "retained_by_default",
             "candidate_members": [
                 {"scope": scope, "path": path}
                 for scope, path in sorted(group_matches)
             ]}
        )

    for scope in SCOPE_ORDER:
        for member in scans[scope].members:
            if member.info.islnk() and member.path not in removals[scope]:
                target = _canonical_name(member.info.linkname)
                if target in removals[scope]:
                    raise PlanError(
                        f"retained hard link points to a removed member: "
                        f"{scope}:{member.path} -> {target}"
                    )

    for item in manifest.get("required_retained", []):
        scope = item.get("scope")
        selector = item.get("selector")
        if scope not in SCOPE_ORDER or not isinstance(selector, dict):
            raise PlanError(f"invalid required_retained entry: {item!r}")
        matches = _find_matches(scans[scope], selector)
        if not matches:
            raise PlanError(f"required retained path is absent: {scope}:{selector}")
        removed = removals[scope]
        lost = sorted(m.path for m in matches if m.path in removed)
        if lost:
            raise PlanError(f"required retained paths are selected for removal: {scope}:{lost}")

    retained_with_reason: list[dict[str, Any]] = []
    for item in manifest.get("retained_with_reason", []):
        scope, selector = item.get("scope"), item.get("selector")
        if scope not in SCOPE_ORDER or not isinstance(selector, dict):
            raise PlanError(f"invalid retained_with_reason entry: {item!r}")
        matches = _find_matches(scans[scope], selector)
        if not matches:
            raise PlanError(f"required retained-with-reason path is absent: {scope}:{selector}")
        lost = sorted(m.path for m in matches if m.path in removals[scope])
        if lost:
            raise PlanError(f"retained-with-reason paths are selected for removal: {scope}:{lost}")
        retained_with_reason.append({
            "scope": scope,
            "selector": selector,
            "members": sorted(m.path for m in matches),
            "reason": item.get("reason", ""),
        })

    return removals, root_inventory, optional_inventory, retained_with_reason


def _inventory_records(
    manifest: dict[str, Any], scans: dict[str, ArchiveScan], removals: dict[str, set[str]]
) -> list[dict[str, Any]]:
    inventory: list[dict[str, Any]] = []
    for item in manifest.get("inventory_only", []):
        scope, selector = item.get("scope"), item.get("selector")
        if scope not in SCOPE_ORDER or not isinstance(selector, dict):
            raise PlanError(f"invalid inventory_only entry: {item!r}")
        matches = _find_matches(scans[scope], selector)
        if item.get("required", False) and not matches:
            raise PlanError(f"required inventory-only path is absent: {scope}:{selector}")
        paths = sorted(m.path for m in matches)
        if any(path in removals[scope] for path in paths):
            raise PlanError(f"inventory-only path is selected for removal: {scope}:{paths}")
        row: dict[str, Any] = {
            "label": item.get("label", ""),
            "scope": scope,
            "selector": selector,
            "members": paths,
        }
        reference_file = item.get("reference_file")
        if reference_file:
            matches_file = _find_matches(scans[scope], {"kind": "exact", "path": reference_file})
            if matches_file:
                with tarfile.open(scans[scope].path, mode="r:*") as archive:
                    content = archive.extractfile(matches_file[0].info)
                    raw = b"" if content is None else content.read()
                row["reference_file"] = reference_file
                row["google_sans_reference_count"] = raw.count(b"GoogleSans")
        inventory.append(row)
    return inventory


def build_plan(
    manifest: dict[str, Any],
    manifest_bytes: bytes,
    archive_paths: Mapping[str, Path],
    *,
    remove_talkback: bool = False,
    remove_dialer_support: bool = False,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Create a fresh plan and runtime scan state without writing any files."""
    if set(archive_paths) != set(SCOPE_ORDER):
        raise PlanError("both product and system_ext archive paths are required")
    scans = {
        scope: _scan_archive(scope, Path(archive_paths[scope]))
        for scope in SCOPE_ORDER
    }
    removals, roots, optional, retained_with_reason = _scope_removals(
        manifest, scans, remove_talkback, remove_dialer_support
    )
    inventory = _inventory_records(manifest, scans, removals)
    removal_records: list[dict[str, Any]] = []
    for scope in SCOPE_ORDER:
        removal_records.extend(_content_records(scans[scope], removals[scope]).values())
    removal_records.sort(key=lambda row: (row["scope"], row["path"]))

    archive_records = []
    for scope in SCOPE_ORDER:
        scan = scans[scope]
        archive_records.append({
            "scope": scope,
            "source_archive_name": scan.path.name,
            "source_archive_sha256": scan.sha256,
            "member_count": len(scan.members),
            "included_member_count": len(scan.members) - len(removals[scope]),
            "removed_member_count": len(removals[scope]),
        })
    removed_bytes = sum(record["size"] for record in removal_records)
    plan: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "mode": "offline_pax_member_filter",
        "manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
        "options": {
            "remove_talkback": remove_talkback,
            "remove_dialer_support": remove_dialer_support,
        },
        "archives": archive_records,
        "removal_roots": roots,
        "optional_groups": optional,
        "retained_with_reason": retained_with_reason,
        "inventory_only": inventory,
        "removals": removal_records,
        "summary": {
            "input_members": sum(len(scans[s].members) for s in SCOPE_ORDER),
            "output_members": sum(len(scans[s].members) - len(removals[s]) for s in SCOPE_ORDER),
            "removed_members": len(removal_records),
            "removed_payload_bytes": removed_bytes,
        },
        "notes": list(manifest.get("notes", [])),
    }
    plan["plan_sha256"] = hashlib.sha256(_json_bytes(plan)).hexdigest()
    runtime = {"scans": scans, "removals": removals}
    return plan, runtime


def _approved_digest(value: str) -> str:
    digest = value.strip().lower()
    if not re.fullmatch(r"[0-9a-f]{64}", digest):
        raise PlanError("--approved-plan must be a 64-character SHA-256 hex digest")
    return digest


def _member_content_hash(archive: tarfile.TarFile, info: tarfile.TarInfo) -> str:
    if info.type not in (tarfile.REGTYPE, tarfile.AREGTYPE):
        return hashlib.sha256(b"").hexdigest()
    source = archive.extractfile(info)
    if source is None:
        raise ApplyError(f"regular member has no readable payload: {info.name!r}")
    digest = hashlib.sha256()
    remaining = info.size
    while remaining:
        chunk = source.read(min(1024 * 1024, remaining))
        if not chunk:
            raise ApplyError(f"truncated member payload while copying: {info.name!r}")
        digest.update(chunk)
        remaining -= len(chunk)
    return digest.hexdigest()


def _copy_filtered_archive(
    scan: ArchiveScan, remove_paths: set[str], destination: Path
) -> dict[str, Any]:
    source_hashes: dict[str, str] = {}
    expected: dict[str, dict[str, Any]] = {}
    try:
        with tarfile.open(scan.path, mode="r:*") as source, tarfile.open(
            destination, mode="w", format=tarfile.PAX_FORMAT
        ) as output:
            for member in scan.members:
                if member.path in remove_paths:
                    continue
                expected[member.path] = member.metadata
                clone = copy.copy(member.info)
                clone.pax_headers = dict(member.info.pax_headers)
                if member.info.type in (tarfile.REGTYPE, tarfile.AREGTYPE):
                    payload = source.extractfile(member.info)
                    if payload is None:
                        raise ApplyError(f"could not read member payload: {member.info.name!r}")
                    hashed = HashingReader(payload)
                    output.addfile(clone, hashed)
                    if hashed.bytes_read != member.info.size:
                        raise ApplyError(f"short copy for member: {member.info.name!r}")
                    source_hashes[member.path] = hashed.hasher.hexdigest()
                else:
                    output.addfile(clone)
                    source_hashes[member.path] = hashlib.sha256(b"").hexdigest()
        actual: dict[str, dict[str, Any]] = {}
        output_hashes: dict[str, str] = {}
        with tarfile.open(destination, mode="r:*") as written:
            for info in written.getmembers():
                path, metadata = _validate_member(info)
                if path in actual:
                    raise ApplyError(f"duplicate output member after filtering: {info.name!r}")
                actual[path] = metadata
                output_hashes[path] = _member_content_hash(written, info)
        if set(actual) != set(expected):
            missing = sorted(set(expected) - set(actual))[:10]
            extra = sorted(set(actual) - set(expected))[:10]
            raise ApplyError(f"output member set mismatch; missing={missing}, extra={extra}")
        for path, expected_metadata in expected.items():
            if actual[path] != expected_metadata:
                raise ApplyError(f"member metadata/PAX headers changed: {path}")
            if output_hashes[path] != source_hashes[path]:
                raise ApplyError(f"member payload changed: {path}")
        if any(path in actual for path in remove_paths):
            raise ApplyError("one or more expected removals are still present")
        return {
            "member_count": len(actual),
            "removed_member_count": len(remove_paths),
            "verified_unchanged_members": len(actual),
            "verified_absent_removals": len(remove_paths),
            "output_archive_sha256": _sha256_file(destination),
        }
    except ApplyError:
        raise
    except (OSError, tarfile.TarError, EOFError) as exc:
        raise ApplyError(f"could not copy or verify {scan.scope} archive: {exc}") from exc


def _write_json_new(path: Path, payload: Any) -> None:
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(payload, stream, ensure_ascii=False, indent=2, sort_keys=True)
        stream.write("\n")


def apply_plan(plan: dict[str, Any], runtime: dict[str, Any], output: Path) -> dict[str, Any]:
    """Create, verify, and atomically publish a new filtered-archive directory."""
    target = output.expanduser().resolve(strict=False)
    partial = target.with_name(target.name + ".partial")
    if os.path.lexists(target) or os.path.lexists(partial):
        raise ApplyError("output and sibling .partial paths must both be new")
    for scope in SCOPE_ORDER:
        scan: ArchiveScan = runtime["scans"][scope]
        if _sha256_file(scan.path) != scan.sha256:
            raise ApplyError(f"pinned {scope} source archive changed after plan generation")
    target.parent.mkdir(parents=True, exist_ok=True)
    try:
        partial.mkdir()
        archive_reports: list[dict[str, Any]] = []
        output_names = {
            "product": "product-vanilla.pax.tar",
            "system_ext": "system_ext-vanilla.pax.tar",
        }
        for scope in SCOPE_ORDER:
            scan: ArchiveScan = runtime["scans"][scope]
            destination = partial / output_names[scope]
            result = _copy_filtered_archive(scan, runtime["removals"][scope], destination)
            archive_reports.append({
                "scope": scope,
                "archive": output_names[scope],
                "source_archive_sha256": scan.sha256,
                **result,
            })

        for scope in SCOPE_ORDER:
            scan = runtime["scans"][scope]
            if _sha256_file(scan.path) != scan.sha256:
                raise ApplyError(f"pinned {scope} source archive changed during apply")

        report = {
            "schema_version": SCHEMA_VERSION,
            "status": "success",
            "artifact_type": "filtered_overlay_archives",
            "flashable": False,
            "plan_sha256": plan["plan_sha256"],
            "archives": archive_reports,
            "notes": list(plan.get("notes", [])),
            "required_follow_up": [
                "Regenerate apex_info.pb for the eventual image build.",
                "First boot has not been tested.",
                "The Google Play services QR provider is removed; retained Aperture may supply the independent default scanner.",
            ],
            "optional_removal_audit": {
                "dialer_support_dependency_audit": (
                    "pending" if plan["options"]["remove_dialer_support"] else "not_removed"
                )
            },
        }
        _write_json_new(partial / "plan.json", plan)
        if os.path.lexists(target):
            raise ApplyError("output path appeared during apply; refusing to overwrite")
        partial.rename(target)
        pending_report = target / "report.json.pending"
        _write_json_new(pending_report, report)
        pending_report.rename(target / "report.json")
        return {
            "status": "success",
            "output_directory": str(target),
            "report": str(target / "report.json"),
            "plan_sha256": plan["plan_sha256"],
            "summary": plan["summary"],
        }
    except Exception as exc:
        failure_dir = partial if partial.exists() else target if target.exists() else None
        if failure_dir is not None:
            try:
                _write_json_new(failure_dir / "FAILED.json", {
                    "status": "partial_not_consumable",
                    "error": str(exc),
                    "plan_sha256": plan.get("plan_sha256"),
                })
            except OSError:
                pass
        if isinstance(exc, ApplyError):
            raise
        raise ApplyError(str(exc)) from exc


def _default_archive_paths(manifest: dict[str, Any], workspace_root: Path) -> dict[str, Path]:
    return {
        scope: (workspace_root / manifest["default_archives"][scope]).resolve()
        for scope in SCOPE_ORDER
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="print a JSON plan (default)")
    mode.add_argument("--apply", action="store_true", help="write filtered archives after plan approval")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--product-tar", type=Path, help="source product PAX archive")
    parser.add_argument("--system-ext-tar", type=Path, help="source system_ext PAX archive")
    parser.add_argument("--remove-talkback", action="store_true")
    parser.add_argument("--remove-dialer-support", action="store_true")
    parser.add_argument("--approved-plan", help="approved fresh plan SHA-256; required with --apply")
    parser.add_argument("--output", type=Path, help="new output directory; required with --apply")
    parser.add_argument("--workspace-root", type=Path, default=WORKSPACE_ROOT,
                        help=argparse.SUPPRESS)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        manifest, manifest_bytes = _load_manifest(args.manifest)
        archive_paths = _default_archive_paths(manifest, args.workspace_root.resolve())
        if args.product_tar is not None:
            archive_paths["product"] = args.product_tar.expanduser().resolve()
        if args.system_ext_tar is not None:
            archive_paths["system_ext"] = args.system_ext_tar.expanduser().resolve()
        plan, runtime = build_plan(
            manifest, manifest_bytes, archive_paths,
            remove_talkback=args.remove_talkback,
            remove_dialer_support=args.remove_dialer_support,
        )
        if not args.apply:
            print(json.dumps(plan, ensure_ascii=False, indent=2, sort_keys=True))
            return 0
        if args.output is None or args.approved_plan is None:
            raise PlanError("--apply requires both --approved-plan and --output")
        approved = _approved_digest(args.approved_plan)
        if approved != plan["plan_sha256"]:
            raise PlanError(
                f"approved plan digest does not match fresh plan "
                f"({plan['plan_sha256']})"
            )
        result = apply_plan(plan, runtime, args.output)
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
        return 0
    except (PlanError, ApplyError, OSError) as exc:
        print(json.dumps({"status": "error", "error": str(exc)}, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
