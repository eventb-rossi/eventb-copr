import contextlib
import io
import json
import os
import subprocess
import tarfile
import tempfile
import unittest
import urllib.error
import zipfile
from pathlib import Path
from unittest.mock import patch

import version_check


class ReachabilityTest(unittest.TestCase):
    def test_missing_artifacts(self):
        for code in (404, 410):
            error = urllib.error.HTTPError("https://example.test", code, "missing", {}, io.BytesIO())
            self.addCleanup(error.close)
            with self.subTest(code=code), patch.object(
                version_check.urllib.request, "urlopen", side_effect=error,
            ):
                self.assertIs(version_check.url_reachable("https://example.test"), False)

    def test_head_falls_back_to_get(self):
        for code in (403, 405, 501):
            response = io.BytesIO()
            error = urllib.error.HTTPError("https://example.test", code, "no HEAD", {}, io.BytesIO())
            self.addCleanup(error.close)
            with self.subTest(code=code), patch.object(
                version_check.urllib.request, "urlopen", side_effect=[error, response],
            ) as request:
                self.assertIs(version_check.url_reachable("https://example.test"), True)
                self.assertEqual([c.args[0].method for c in request.call_args_list], ["HEAD", "GET"])

    def test_transient_failure_is_inconclusive(self):
        for error in (urllib.error.URLError("offline"), TimeoutError("timeout"),
                      urllib.error.HTTPError("https://example.test", 503, "unavailable", {}, io.BytesIO())):
            if isinstance(error, urllib.error.HTTPError):
                self.addCleanup(error.close)
            with self.subTest(error=error), patch.object(
                version_check.urllib.request, "urlopen", side_effect=error,
            ):
                self.assertIsNone(version_check.url_reachable("https://example.test"))


class BumpTest(unittest.TestCase):
    def setUp(self):
        self.work = tempfile.TemporaryDirectory()
        self.addCleanup(self.work.cleanup)
        self.root = Path(self.work.name)
        self.outputs = self.root / "outputs"

    def write_spec(self, pkg, url="https://example.test/%{name}-%{version}.tar.gz", text=None):
        path = self.root / pkg / f"{pkg}.spec"
        path.parent.mkdir(exist_ok=True)
        path.write_text(text or (
            f"Name: {pkg}\nVersion: 1.3.1\nRelease: 7%{{?dist}}\nSource0: {url}\n"
            "%changelog\n* Thu Jun 11 2026 Test - 1.3.1-7\n- Previous release\n"
        ))
        return path

    def bump(self, pkg, latest="1.4.0", record=None):
        out, err = io.StringIO(), io.StringIO()
        with patch.object(version_check, "REPO_ROOT", self.root), \
                patch.object(version_check, "latest_version",
                             return_value=record or {"version": latest}), \
                patch.dict(os.environ, {"GITHUB_OUTPUT": str(self.outputs)}), \
                contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            status = version_check.cmd_bump(pkg)
        return status, err.getvalue()

    def assert_rejected(self, path, original, status):
        self.assertEqual(status, 1)
        self.assertEqual(path.read_text(), original)
        self.assertEqual(self.outputs.read_text(), "bumped=false\n")

    def test_missing_source_fails_every_bump_package(self):
        for pkg in version_check.PACKAGES:
            if pkg["mode"] != "bump" or pkg["pkg"] == "prob2-ui":
                continue
            with self.subTest(pkg=pkg["pkg"]):
                path = self.write_spec(pkg["pkg"])
                original = path.read_text()
                self.outputs.write_text("")
                with patch.object(version_check, "url_reachable", return_value=False):
                    status, error = self.bump(pkg["pkg"])
                self.assert_rejected(path, original, status)
                self.assertIn(f"::error::{pkg['pkg']}: upstream 1.4.0", error)
                self.assertIn(f"https://example.test/{pkg['pkg']}-1.4.0.tar.gz", error)

    def test_inconclusive_ordinary_check_warns_and_bumps(self):
        path = self.write_spec("prob")
        with patch.object(version_check, "url_reachable", return_value=None):
            status, error = self.bump("prob")
        self.assertEqual(status, 0)
        self.assertIn("::warning::prob", error)
        self.assertIn("Version: 1.4.0\nRelease: 1%{?dist}", path.read_text())
        self.assertIn("- Update to 1.4.0", path.read_text())
        self.assertIn("bumped=true", self.outputs.read_text())

    def test_unresolved_source_fails(self):
        path = self.write_spec("prob", "https://example.test/%{unknown}")
        original = path.read_text()
        status, error = self.bump("prob")
        self.assert_rejected(path, original, status)
        self.assertIn("could not resolve Source0", error)

    def test_up_to_date_does_not_fetch_or_validate(self):
        path = self.write_spec("prob2-ui")
        original = path.read_text()
        with patch.object(version_check, "validate_prob2_deb") as validate, \
                patch.object(version_check, "url_reachable") as reachable:
            status, _ = self.bump("prob2-ui", latest="1.3.1")
        self.assertEqual(status, 0)
        self.assertEqual(path.read_text(), original)
        validate.assert_not_called()
        reachable.assert_not_called()
        self.assertEqual(self.outputs.read_text(), "bumped=false\n")

    def make_deb(self, jar=None):
        payload = io.BytesIO()
        with tarfile.open(fileobj=payload, mode="w") as tf:
            if jar is not None:
                entry = tarfile.TarInfo("./opt/prob2-ui/lib/app/prob2-ui-1.4.0-linux.jar")
                entry.size = len(jar)
                tf.addfile(entry, io.BytesIO(jar))
        data = subprocess.run(["zstd", "-q", "-c"], input=payload.getvalue(),
                              stdout=subprocess.PIPE, check=True).stdout
        archive = self.root / "release.deb"
        # A Debian archive is an ar container. Build the two members needed by
        # the extractor without requiring Debian's dpkg tooling on Fedora.
        with archive.open("wb") as fh:
            fh.write(b"!<arch>\n")
            for name, content in (("debian-binary", b"2.0\n"), ("data.tar.zst", data)):
                header = f"{name + '/':<16}{0:<12}{0:<6}{0:<6}{'100644':<8}{len(content):<10}`\n"
                fh.write(header.encode("ascii"))
                fh.write(content)
                if len(content) % 2:
                    fh.write(b"\n")
        return archive

    def make_jar(self, *, main="de.prob2.ui.Main", omit=None):
        output = io.BytesIO()
        with zipfile.ZipFile(output, "w") as zf:
            entries = {
                "META-INF/MANIFEST.MF": f"Manifest-Version: 1.0\r\nMain-Class: {main}\r\n",
                "de/prob2/ui/Main.class": b"test bytecode",
                "de/prob2/ui/ProB_Icon.png": b"test icon",
            }
            for name, content in entries.items():
                if name != omit:
                    zf.writestr(name, content)
        return output.getvalue()

    def test_invalid_prob2_release_never_changes_spec(self):
        corrupt = bytearray(self.make_jar())
        with zipfile.ZipFile(io.BytesIO(corrupt)) as zf:
            entry = zf.getinfo("de/prob2/ui/Main.class")
            offset = entry.header_offset + 30 + len(entry.filename.encode())
        corrupt[offset] ^= 1
        cases = {
            "missing jar": None,
            "invalid zip": b"not a jar",
            "bad crc": bytes(corrupt),
            "missing manifest": self.make_jar(omit="META-INF/MANIFEST.MF"),
            "wrong main class": self.make_jar(main="other.Main"),
            "missing main class": self.make_jar(omit="de/prob2/ui/Main.class"),
            "missing icon": self.make_jar(omit="de/prob2/ui/ProB_Icon.png"),
        }
        for name, jar in cases.items():
            with self.subTest(case=name):
                archive = self.make_deb(jar)
                path = self.write_spec("prob2-ui", archive.as_uri())
                original = path.read_text()
                self.outputs.write_text("")
                status, error = self.bump("prob2-ui")
                self.assert_rejected(path, original, status)
                self.assertIn("::error::prob2-ui: upstream 1.4.0", error)
                self.assertIn(archive.as_uri(), error)

    def test_prob2_download_failure_is_strict(self):
        for error in (urllib.error.URLError("offline"),
                      urllib.error.HTTPError("https://example.test", 404, "missing", {}, io.BytesIO())):
            if isinstance(error, urllib.error.HTTPError):
                self.addCleanup(error.close)
            with self.subTest(error=error):
                path = self.write_spec("prob2-ui")
                original = path.read_text()
                self.outputs.write_text("")
                with patch.object(version_check.urllib.request, "urlopen", side_effect=error):
                    status, _ = self.bump("prob2-ui")
                self.assert_rejected(path, original, status)

    def test_invalid_debian_archive_never_changes_spec(self):
        archive = self.root / "release.deb"
        archive.write_bytes(b"not a Debian archive")
        path = self.write_spec("prob2-ui", archive.as_uri())
        original = path.read_text()
        status, _ = self.bump("prob2-ui")
        self.assert_rejected(path, original, status)

    def test_valid_prob2_release_bumps_after_validation(self):
        archive = self.make_deb(self.make_jar())
        path = self.write_spec("prob2-ui", archive.as_uri())
        status, error = self.bump("prob2-ui")
        self.assertEqual((status, error), (0, ""))
        self.assertIn("Version: 1.4.0\nRelease: 1%{?dist}", path.read_text())
        self.assertIn("- Update to 1.4.0", path.read_text())
        self.assertIn("Previous release", path.read_text())
        self.assertIn("bumped=true\npn=prob2-ui\nold=1.3.1\nnew=1.4.0\n", self.outputs.read_text())


def bundle_release(tag, *, prerelease=False, draft=False, assets=None):
    if assets is None:
        assets = ["rodin-3.10.0.202612010000-abc1234-rossi-linux.gtk.x86_64.tar.gz",
                  "rodin-3.10.0.202612010000-abc1234-rossi-win32.win32.x86_64.zip",
                  "SHA256SUMS"]
    return {"tag_name": tag, "prerelease": prerelease, "draft": draft,
            "assets": [{"name": name} for name in assets]}


class RodinBundleVersionTest(unittest.TestCase):
    def setUp(self):
        version_check.bundle_releases.cache_clear()
        self.addCleanup(version_check.bundle_releases.cache_clear)

    def latest(self, releases, **source):
        with patch.object(version_check, "http_get", return_value=json.dumps(releases).encode()):
            return version_check.latest_rodin_bundle({"type": "rodin_bundle", **source})

    def test_rpm_rendering(self):
        for tag, rpm in (("v3.10.0-2611", "3.10.0^2611"),
                         ("v3.10.0-2609.2", "3.10.0^2609.2"),
                         ("v3.10.0-2611-rc1", "3.10.0^2611~rc1"),
                         ("v3.10.0-2609.2-rc3", "3.10.0^2609.2~rc3")):
            with self.subTest(tag=tag):
                version_check.bundle_releases.cache_clear()
                self.assertEqual(self.latest([bundle_release(tag)], prerelease=True)["version"], rpm)

    def test_ordering(self):
        ordered = ["3.9", "3.10", "3.10.0^2609", "3.10.0^2609.2", "3.10.0^2611~rc1",
                   "3.10.0^2611~rc2", "3.10.0^2611", "3.10.0^2611.1", "3.10.0^2612~rc1",
                   "3.10.0^2612", "3.11.0^2701~rc1"]
        self.assertEqual(sorted(reversed(ordered), key=version_check.bundle_key), ordered)
        source = {"type": "rodin_bundle"}
        # The switch from vanilla Rodin (Version: 3.10) is itself an update.
        self.assertTrue(version_check.is_outdated(source, "3.10.0^2611", "3.10"))
        self.assertTrue(version_check.is_outdated(source, "3.10.0^2612", "3.10.0^2611"))
        self.assertTrue(version_check.is_outdated(source, "3.10.0^2611", "3.10.0^2611~rc2"))
        self.assertFalse(version_check.is_outdated(source, "3.10.0^2611~rc2", "3.10.0^2611"))
        self.assertFalse(version_check.is_outdated(source, "3.10.0^2611", "3.10.0^2611"))

    def test_latest_release(self):
        releases = [bundle_release("v3.10.0-2612-rc1", prerelease=True),
                    bundle_release("v3.10.0-2611"),
                    bundle_release("v3.10.0-2609.2")]
        self.assertEqual(self.latest(releases), {
            "version": "3.10.0^2611",
            "globals": {"tag": "v3.10.0-2611", "buildid": "3.10.0.202612010000-abc1234"},
            "note": "Update to Rodin-Bundle v3.10.0-2611"})
        self.assertEqual(self.latest(releases, prerelease=True)["version"], "3.10.0^2612~rc1")

    def test_releases_list_is_fetched_once(self):
        payload = json.dumps([bundle_release("v3.10.0-2611")]).encode()
        with patch.object(version_check, "http_get", return_value=payload) as get:
            version_check.latest_rodin_bundle({"type": "rodin_bundle"})
            version_check.latest_rodin_bundle({"type": "rodin_bundle", "prerelease": True})
        get.assert_called_once()

    def test_skips_incomplete_or_foreign_releases(self):
        releases = [bundle_release("v3.10.0-2613", assets=["SHA256SUMS"]),
                    bundle_release("v3.10.0-2612", assets=[
                        "rodin-3.10.0.202612010000-abc1234-rossi-linux.gtk.x86_64.tar.gz"]),
                    bundle_release("v3.10.0-2614", draft=True),
                    bundle_release("v3.11.0-2615", assets=[
                        "rodin-3.10.0.202612010000-abc1234-rossi-linux.gtk.x86_64.tar.gz",
                        "SHA256SUMS"]),
                    bundle_release("nightly"),
                    bundle_release("v3.10.0-2611")]
        self.assertEqual(self.latest(releases)["version"], "3.10.0^2611")
        version_check.bundle_releases.cache_clear()
        with self.assertRaises(ValueError):
            self.latest(releases[:2])

    def test_old_bare_hash_qualifier(self):
        releases = [bundle_release("v3.10.0-2609", assets=[
            "rodin-3.10.0.9cd92c4-rossi-linux.gtk.x86_64.tar.gz", "SHA256SUMS"])]
        self.assertEqual(self.latest(releases)["globals"]["buildid"], "3.10.0.9cd92c4")


BUNDLE_SPEC = ("%global tag        v3.10.0-2611\n"
               "%global buildid    3.10.0.202611160826-a263a14\n"
               "%global tarball    rodin-%{buildid}-rossi-linux.gtk.x86_64.tar.gz\n"
               "Name:           rodin\n"
               "Version:        3.10.0^2611\n"
               "Release:        3%{?dist}\n"
               "Source0:        https://github.com/eventb-rossi/Rodin-Bundle/releases/download/%{tag}/%{tarball}\n"
               "%changelog\n* Mon Nov 16 2026 Test - 3.10.0^2611-3\n- Previous release\n")
BUNDLE_RECORD = {"version": "3.10.0^2612.1~rc2",
                 "globals": {"tag": "v3.10.0-2612.1-rc2", "buildid": "3.10.0.202612050101-0123abc"},
                 "note": "Update to Rodin-Bundle v3.10.0-2612.1-rc2"}


class RodinBundleBumpTest(unittest.TestCase):
    setUp = BumpTest.setUp
    write_spec = BumpTest.write_spec
    bump = BumpTest.bump
    assert_rejected = BumpTest.assert_rejected

    def test_bump_rewrites_globals_version_and_changelog(self):
        for pkg in ("rodin", "rodin-rc"):
            with self.subTest(pkg=pkg):
                path = self.write_spec(pkg, text=BUNDLE_SPEC.replace("rodin\n", f"{pkg}\n", 1))
                self.outputs.write_text("")
                with patch.object(version_check, "url_reachable", return_value=True) as reachable:
                    status, error = self.bump(pkg, record=BUNDLE_RECORD)
                self.assertEqual((status, error), (0, ""))
                reachable.assert_called_once_with(
                    "https://github.com/eventb-rossi/Rodin-Bundle/releases/download/v3.10.0-2612.1-rc2/"
                    "rodin-3.10.0.202612050101-0123abc-rossi-linux.gtk.x86_64.tar.gz")
                text = path.read_text()
                self.assertIn("%global tag        v3.10.0-2612.1-rc2\n", text)
                self.assertIn("%global buildid    3.10.0.202612050101-0123abc\n", text)
                self.assertIn("Version:        3.10.0^2612.1~rc2\nRelease:        1%{?dist}\n", text)
                self.assertIn("- 3.10.0^2612.1~rc2-1\n- Update to Rodin-Bundle v3.10.0-2612.1-rc2\n", text)
                self.assertIn("Previous release", text)
                self.assertEqual(self.outputs.read_text(),
                                 f"bumped=true\npn={pkg}\nold=3.10.0^2611\n"
                                 "new=3.10.0^2612.1~rc2\nref=3.10.0-2612.1-rc2\n")

    def test_up_to_date_bundle_is_left_alone(self):
        path = self.write_spec("rodin", text=BUNDLE_SPEC)
        with patch.object(version_check, "url_reachable") as reachable:
            status, _ = self.bump("rodin", record={**BUNDLE_RECORD, "version": "3.10.0^2611~rc2"})
        self.assertEqual(status, 0)
        self.assertEqual(path.read_text(), BUNDLE_SPEC)
        reachable.assert_not_called()

    def test_missing_or_duplicate_global_fails(self):
        for name, text in (("no buildid", BUNDLE_SPEC.replace("%global buildid", "%global build_id")),
                           ("two tags", "%global tag v1\n" + BUNDLE_SPEC)):
            with self.subTest(case=name):
                path = self.write_spec("rodin", text=text)
                self.outputs.write_text("")
                with patch.object(version_check, "url_reachable", return_value=True):
                    status, error = self.bump("rodin", record=BUNDLE_RECORD)
                self.assert_rejected(path, text, status)
                self.assertIn("::error::rodin: upstream 3.10.0^2612.1~rc2", error)
                self.assertIn("expected exactly one %global", error)


if __name__ == "__main__":
    unittest.main()
