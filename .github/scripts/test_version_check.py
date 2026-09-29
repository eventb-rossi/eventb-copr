import contextlib
import io
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

    def write_spec(self, pkg, url="https://example.test/%{name}-%{version}.tar.gz"):
        path = self.root / pkg / f"{pkg}.spec"
        path.parent.mkdir(exist_ok=True)
        path.write_text(
            f"Name: {pkg}\nVersion: 1.3.1\nRelease: 7%{{?dist}}\nSource0: {url}\n"
            "%changelog\n* Thu Jun 11 2026 Test - 1.3.1-7\n- Previous release\n"
        )
        return path

    def bump(self, pkg, latest="1.4.0"):
        out, err = io.StringIO(), io.StringIO()
        with patch.object(version_check, "REPO_ROOT", self.root), \
                patch.object(version_check, "latest_version", return_value=latest), \
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


if __name__ == "__main__":
    unittest.main()
