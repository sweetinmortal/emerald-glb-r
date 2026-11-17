from __future__ import annotations

import contextlib
import io
import json
import sys
import tarfile
import tempfile
import types
import unittest
from unittest import mock
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import degoogle


def add_member(
    archive: tarfile.TarFile,
    name: str,
    *,
    kind: bytes = tarfile.REGTYPE,
    data: bytes = b"",
    linkname: str = "",
    pax_headers: dict[str, str] | None = None,
) -> None:
    info = tarfile.TarInfo(name)
    info.type = kind
    info.mode = 0o640 if kind == tarfile.REGTYPE else 0o755
    info.uid = 123
    info.gid = 456
    info.uname = "builder"
    info.gname = "system"
    info.mtime = 1_700_000_000
    info.linkname = linkname
    info.pax_headers = dict(pax_headers or {})
    if kind == tarfile.REGTYPE:
        info.size = len(data)
        archive.addfile(info, io.BytesIO(data))
    else:
        archive.addfile(info)


def write_tar(path: Path, *, include_core: bool = True, duplicate: bool = False,
              path_escape: bool = False, retained_hardlink: bool = False,
              core_payload: bytes = b"remove-me") -> None:
    with tarfile.open(path, "w", format=tarfile.PAX_FORMAT) as archive:
        add_member(archive, "./", kind=tarfile.DIRTYPE)
        if include_core:
            add_member(archive, "./app", kind=tarfile.DIRTYPE)
            add_member(archive, "./app/GoogleRestore", kind=tarfile.DIRTYPE)
            add_member(archive, "./app/GoogleRestore/payload.apk", data=core_payload)
            if duplicate:
                add_member(archive, "app/GoogleRestore/", kind=tarfile.DIRTYPE)
        add_member(archive, "./app/talkback", kind=tarfile.DIRTYPE)
        add_member(archive, "./app/talkback/talkback.apk", data=b"talkback")
        add_member(archive, "./app/GoogleAnalytics", kind=tarfile.DIRTYPE)
        add_member(archive, "./app/GoogleAnalytics/keep.apk", data=b"keep-google")
        add_member(archive, "./framework/com.google.android.dialer.support.jar", data=b"jar")
        add_member(archive, "./framework/oat/arm64/com.google.android.dialer.support.odex", data=b"odex")
        add_member(archive, "./framework/oat/arm64/com.google.android.dialer.support.vdex", data=b"vdex")
        add_member(archive, "./etc/permissions/com.google.android.dialer.support.xml", data=b"xml")
        add_member(
            archive,
            "./keep.bin",
            data=b"keep-content",
            pax_headers={
                "SCHILY.xattr.security.selinux": "u:object_r:system_file:s0",
                "SCHILY.xattr.user.codex-test": "preserve-me",
                "comment": "custom-pax-value",
            },
        )
        add_member(
            archive,
            "./libref",
            kind=tarfile.SYMTYPE,
            linkname="/product/lib64/libjni_latinimegoogle.so",
            pax_headers={"SCHILY.xattr.security.selinux": "u:object_r:system_file:s0"},
        )
        if retained_hardlink:
            add_member(archive, "./hardref", kind=tarfile.LNKTYPE,
                       linkname="./app/GoogleRestore/payload.apk")
        if path_escape:
            add_member(archive, "../escape", data=b"bad")


def manifest_dict() -> dict:
    return {
        "schema_version": 1,
        "default_archives": {"product": "product.tar", "system_ext": "system_ext.tar"},
        "core_removals": {
            "product": [{"kind": "tree", "path": "app/GoogleRestore"}],
            "system_ext": [{"kind": "tree", "path": "priv-app/GoogleServicesFramework"}],
        },
        "optional_removals": {
            "talkback": {"product": [{"kind": "tree", "path": "app/talkback"}]},
            "dialer_support": {
                "product": [
                    {"kind": "exact", "path": "framework/com.google.android.dialer.support.jar"},
                    {"kind": "glob", "pattern": "framework/oat/arm*/com.google.android.dialer.support.odex"},
                    {"kind": "glob", "pattern": "framework/oat/arm*/com.google.android.dialer.support.vdex"},
                    {"kind": "exact", "path": "etc/permissions/com.google.android.dialer.support.xml"},
                ]
            },
        },
        "inventory_only": [],
        "required_retained": [
            {"scope": "product", "selector": {"kind": "tree", "path": "app/GoogleAnalytics"}}
        ],
        "notes": ["synthetic test plan"],
    }


class DegoogleTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.product = self.root / "product.tar"
        self.system_ext = self.root / "system_ext.tar"
        self.manifest = manifest_dict()
        self.manifest_bytes = json.dumps(self.manifest, sort_keys=True).encode("utf-8")
        self.manifest_path = self.root / "manifest.json"
        self.manifest_path.write_bytes(json.dumps(self.manifest).encode("utf-8"))
        write_tar(self.product)
        with tarfile.open(self.system_ext, "w", format=tarfile.PAX_FORMAT) as archive:
            add_member(archive, "./", kind=tarfile.DIRTYPE)
            add_member(archive, "./priv-app", kind=tarfile.DIRTYPE)
            add_member(archive, "./priv-app/GoogleServicesFramework", kind=tarfile.DIRTYPE)
            add_member(archive, "./priv-app/GoogleServicesFramework/GoogleServicesFramework.apk", data=b"framework")
            add_member(archive, "./priv-app/LineageSetupWizard", kind=tarfile.DIRTYPE)
            add_member(archive, "./priv-app/LineageSetupWizard/LineageSetupWizard.apk", data=b"lineage")
        self.archives = {"product": self.product, "system_ext": self.system_ext}

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def make_plan(self, *, talkback: bool = False, dialer: bool = False):
        return degoogle.build_plan(
            self.manifest,
            self.manifest_bytes,
            self.archives,
            remove_talkback=talkback,
            remove_dialer_support=dialer,
        )

    def test_import_from_shallow_checkout_without_workspace_ancestors(self) -> None:
        source = Path(degoogle.__file__).read_text(encoding="utf-8")
        shallow_file = Path(Path(degoogle.__file__).anchor) / "degoogle.py"
        module = types.ModuleType("degoogle_shallow_checkout_test")
        module.__file__ = str(shallow_file)
        with mock.patch.dict(sys.modules, {module.__name__: module}):
            exec(compile(source, str(shallow_file), "exec"), module.__dict__)
            args = module._parser().parse_args([
                "--product-tar", str(self.product),
                "--system-ext-tar", str(self.system_ext),
            ])
        self.assertEqual(args.product_tar, self.product)
        self.assertEqual(args.system_ext_tar, self.system_ext)

    def test_apply_preserves_pax_xattrs_symlink_and_metadata(self) -> None:
        plan, runtime = self.make_plan()
        result = degoogle.apply_plan(plan, runtime, self.root / "out")
        self.assertEqual(result["status"], "success")
        report = json.loads((self.root / "out" / "report.json").read_text(encoding="utf-8"))
        self.assertFalse(report["flashable"])
        self.assertEqual(report["status"], "success")
        with tarfile.open(self.root / "out" / "product-vanilla.pax.tar", "r:*") as out:
            by_name = {degoogle._canonical_name(m.name): m for m in out.getmembers()}
            self.assertNotIn("app/GoogleRestore/payload.apk", by_name)
            self.assertIn("app/GoogleAnalytics/keep.apk", by_name)
            kept = by_name["keep.bin"]
            self.assertEqual(kept.pax_headers["SCHILY.xattr.security.selinux"], "u:object_r:system_file:s0")
            self.assertEqual(kept.pax_headers["SCHILY.xattr.user.codex-test"], "preserve-me")
            self.assertEqual(kept.pax_headers["comment"], "custom-pax-value")
            self.assertEqual((kept.uid, kept.gid, kept.mode, kept.uname, kept.gname, kept.mtime),
                             (123, 456, 0o640, "builder", "system", 1_700_000_000))
            self.assertEqual(out.extractfile(kept).read(), b"keep-content")
            link = by_name["libref"]
            self.assertTrue(link.issym())
            self.assertEqual(link.linkname, "/product/lib64/libjni_latinimegoogle.so")
            self.assertEqual(link.pax_headers["SCHILY.xattr.security.selinux"], "u:object_r:system_file:s0")

    def test_optional_groups_are_narrow_and_retained_by_default(self) -> None:
        plan, _runtime = self.make_plan()
        removed = {(row["scope"], row["path"]) for row in plan["removals"]}
        self.assertNotIn(("product", "app/talkback/talkback.apk"), removed)
        self.assertNotIn(("product", "framework/com.google.android.dialer.support.jar"), removed)
        talkback_state = {row["group"]: row["state"] for row in plan["optional_groups"]}
        self.assertEqual(talkback_state["talkback"], "retained_by_default")
        self.assertEqual(talkback_state["dialer_support"], "retained_by_default")

        selected, _runtime = self.make_plan(talkback=True, dialer=True)
        selected_paths = {(row["scope"], row["path"]) for row in selected["removals"]}
        self.assertIn(("product", "app/talkback/talkback.apk"), selected_paths)
        self.assertIn(("product", "framework/com.google.android.dialer.support.jar"), selected_paths)
        self.assertIn(("product", "framework/oat/arm64/com.google.android.dialer.support.odex"), selected_paths)
        self.assertIn(("product", "framework/oat/arm64/com.google.android.dialer.support.vdex"), selected_paths)
        self.assertIn(("product", "etc/permissions/com.google.android.dialer.support.xml"), selected_paths)
        self.assertNotIn(("product", "app/GoogleAnalytics/keep.apk"), selected_paths)

    def test_duplicate_missing_and_escape_archives_fail_before_output(self) -> None:
        output = self.root / "must-not-exist"
        write_tar(self.product, duplicate=True)
        with self.assertRaises(degoogle.PlanError):
            self.make_plan()
        self.assertFalse(output.exists())

        write_tar(self.product, include_core=False)
        with self.assertRaisesRegex(degoogle.PlanError, "required core removal root"):
            self.make_plan()
        self.assertFalse(output.exists())

        write_tar(self.product, path_escape=True)
        with self.assertRaisesRegex(degoogle.PlanError, "unsafe archive member name"):
            self.make_plan()
        self.assertFalse(output.exists())

    def test_retained_hardlink_to_removed_member_is_rejected(self) -> None:
        write_tar(self.product, retained_hardlink=True)
        with self.assertRaisesRegex(degoogle.PlanError, "retained hard link points to a removed member"):
            self.make_plan()

    def test_source_change_after_approval_is_rejected_before_output(self) -> None:
        plan, runtime = self.make_plan()
        write_tar(self.product, core_payload=b"changed-payload")
        output = self.root / "changed-source"
        with self.assertRaisesRegex(degoogle.ApplyError, "source archive changed after plan generation"):
            degoogle.apply_plan(plan, runtime, output)
        self.assertFalse(output.exists())
        self.assertFalse(Path(str(output) + ".partial").exists())

    def test_source_change_during_copy_leaves_only_failed_partial(self) -> None:
        plan, runtime = self.make_plan()
        output = self.root / "changed-during-copy"
        original_copy = degoogle._copy_filtered_archive

        def mutate_source(scan, remove_paths, destination):
            result = original_copy(scan, remove_paths, destination)
            if scan.scope == "product":
                write_tar(self.product, core_payload=b"changed-mid-copy")
            return result

        with mock.patch.object(degoogle, "_copy_filtered_archive", side_effect=mutate_source):
            with self.assertRaisesRegex(degoogle.ApplyError, "source archive changed during apply"):
                degoogle.apply_plan(plan, runtime, output)
        partial = Path(str(output) + ".partial")
        self.assertTrue(partial.is_dir())
        self.assertFalse((partial / "report.json").exists())
        failed = json.loads((partial / "FAILED.json").read_text(encoding="utf-8"))
        self.assertEqual(failed["status"], "partial_not_consumable")

    def test_publish_failure_never_leaves_a_success_report(self) -> None:
        plan, runtime = self.make_plan()
        output = self.root / "publish-failure"
        original_rename = Path.rename

        def fail_directory_publish(path, target):
            if path.name == output.name + ".partial":
                raise OSError("simulated directory publish failure")
            return original_rename(path, target)

        with mock.patch.object(Path, "rename", autospec=True, side_effect=fail_directory_publish):
            with self.assertRaisesRegex(degoogle.ApplyError, "simulated directory publish failure"):
                degoogle.apply_plan(plan, runtime, output)
        partial = Path(str(output) + ".partial")
        self.assertTrue(partial.is_dir())
        self.assertFalse((partial / "report.json").exists())
        failed = json.loads((partial / "FAILED.json").read_text(encoding="utf-8"))
        self.assertEqual(failed["status"], "partial_not_consumable")

    def test_changed_archive_invalidates_approved_digest_before_any_output(self) -> None:
        plan, _runtime = self.make_plan()
        approved_digest = plan["plan_sha256"]
        write_tar(self.product, core_payload=b"changed-payload")
        changed_plan, _runtime = self.make_plan()
        self.assertNotEqual(approved_digest, changed_plan["plan_sha256"])

        output = self.root / "stale-approval-output"
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            code = degoogle.main([
                "--apply", "--manifest", str(self.manifest_path),
                "--product-tar", str(self.product), "--system-ext-tar", str(self.system_ext),
                "--approved-plan", approved_digest, "--output", str(output),
            ])
        self.assertEqual(code, 2)
        response = json.loads(stdout.getvalue())
        self.assertEqual(response["status"], "error")
        self.assertIn("does not match fresh plan", response["error"])
        self.assertFalse(output.exists())
        self.assertFalse(Path(str(output) + ".partial").exists())

    def test_default_cli_prints_json_plan_without_creating_outputs(self) -> None:
        before = {path.name for path in self.root.iterdir()}
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            code = degoogle.main([
                "--manifest", str(self.manifest_path),
                "--product-tar", str(self.product), "--system-ext-tar", str(self.system_ext),
            ])
        self.assertEqual(code, 0)
        plan = json.loads(stdout.getvalue())
        self.assertIn("plan_sha256", plan)
        self.assertEqual({path.name for path in self.root.iterdir()}, before)

    def test_apply_refuses_existing_output(self) -> None:
        plan, runtime = self.make_plan()
        output = self.root / "already-there"
        output.mkdir()
        marker = output / "keep.txt"
        marker.write_text("untouched", encoding="utf-8")
        with self.assertRaisesRegex(degoogle.ApplyError, "must both be new"):
            degoogle.apply_plan(plan, runtime, output)
        self.assertEqual(marker.read_text(encoding="utf-8"), "untouched")


if __name__ == "__main__":
    unittest.main()
