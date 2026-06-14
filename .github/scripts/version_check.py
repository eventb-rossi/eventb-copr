#!/usr/bin/env python3
"""Upstream version monitor for the eventb-rossi Copr package set.

Two responsibilities, mirroring the two halves of homebrew-tap's release tracker
and gentoo-overlay's version-check:

  * "bump" packages have a single Source0 with a clean %{version}-templated URL,
    so a version bump is mechanical and spec-only: rewrite Version:, reset
    Release:, and prepend a %changelog entry. RPM specs carry no source
    checksums (Copr re-downloads Source0 via spectool at build time, and the
    repo .gitignores the artifacts), so nothing else needs regenerating. These
    are turned into pull requests.

  * "track" packages embed opaque build ids (rodin), bundle vendored archives
    (atelier-b), or carry a non-version-derivable URL (eventb-to-txt's hashed
    PyPI path), so they can't be bumped blindly. We only detect the new version
    and file a GitHub issue for a human to handle.

Subcommands:
  check        Print a JSON report of every package (current/latest/outdated).
  bump <pkg>   For one outdated "bump" package, rewrite its spec in place.
               No-op (exit 0) if already up to date.
"""

from __future__ import annotations

import datetime
import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

REPO_ROOT = Path(os.environ.get("COPR_ROOT") or Path(__file__).resolve().parents[2])

# Changelog author for automated bumps (matches the existing %changelog entries).
CHANGELOG_AUTHOR = "Denis Efremov <efremov@linux.com>"

# --- package configuration -------------------------------------------------
# mode: "bump"  -> auto-bump into a PR (single distfile, clean %{version} URL)
#       "track" -> detect only, file an issue (opaque/complex bump)
#       "skip"  -> not monitored (moving-master snapshot)
#
# source.type:
#   github         -> latest non-prerelease GitHub release tag (repo = owner/name)
#   sourceforge    -> newest plain X.Y.Z version dir under a SourceForge path
#   sourceforge_rc -> newest X.Y-RCn release-candidate dir under a SourceForge path
#   atelierb       -> scrape the Atelier B download page for the free version
#   apache_index   -> newest X.Y.Z subdirectory in an Apache/nginx autoindex
#
# current_macro: read the packaged version from this spec %global instead of the
#                Version: field (rodin-rc keeps its RC build line in %{sfdir}).
PACKAGES = [
    {"pkg": "eventb-checker", "mode": "bump",
     "source": {"type": "github", "repo": "eventb-rossi/eventb-checker"}},
    {"pkg": "eventb-animate", "mode": "bump",
     "source": {"type": "github", "repo": "eventb-rossi/eventb-animate"}},
    {"pkg": "evbt", "mode": "bump",
     "source": {"type": "github", "repo": "viklauverk/EventBTool"}},
    # Both detect the version from the same host the distfile lives on, so a
    # detected version implies its release directory (and artifact) exists.
    {"pkg": "prob", "mode": "bump",
     "source": {"type": "apache_index",
                "url": "https://stups.hhu-hosting.de/downloads/prob/tcltk/releases/"}},
    {"pkg": "prob2-ui", "mode": "bump",
     "source": {"type": "apache_index",
                "url": "https://stups.hhu-hosting.de/downloads/prob2/"}},

    # eventb-to-txt's Source0 is a content-hashed pythonhosted path that is not
    # derivable from the version, so detect via the upstream repo and track.
    {"pkg": "eventb-to-txt", "mode": "track",
     "source": {"type": "github", "repo": "eventb-rossi/eventb-to-txt"}},
    {"pkg": "tlc4b", "mode": "track",
     "source": {"type": "github", "repo": "hhu-stups/tlc4b"}},
    {"pkg": "rodin", "mode": "track",
     "source": {"type": "sourceforge", "project": "rodin-b-sharp",
                "path": "/Core_Rodin_Platform"}},
    {"pkg": "rodin-rc", "mode": "track", "current_macro": "sfdir",
     "source": {"type": "sourceforge_rc", "project": "rodin-b-sharp",
                "path": "/Core_Rodin_Platform"}},
    {"pkg": "atelier-b", "mode": "track",
     "source": {"type": "atelierb",
                "url": "https://www.atelierb.eu/en/atelier-b-support-maintenance/download-atelier-b/"}},

    {"pkg": "b2program", "mode": "skip", "source": {}},
]

UA = {"User-Agent": "eventb-rossi-version-check/1 (+https://github.com/eventb-rossi/eventb-copr)"}


# --- helpers ---------------------------------------------------------------
def http_get(url: str, *, headers: dict | None = None, timeout: int = 60) -> bytes:
    req = urllib.request.Request(url, headers={**UA, **(headers or {})})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def gh_headers() -> dict:
    h = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token:
        h["Authorization"] = f"Bearer {token}"
    return h


# Leading dotted-numeric run of a version-ish string (drops a v-prefix / suffix).
VERSION_RE = re.compile(r"\d+(?:\.\d+)*")
RC_RE = re.compile(r"[-_.]?RC(\d+)", re.IGNORECASE)


def version_tuple(s: str) -> tuple[int, ...]:
    """`s` as ints, e.g. 'v3.10.0_rc2' -> (3,10,0).

    Numeric, not lexical, so 3.10 > 3.9. Suffixes (_rc, _p, -beta) are ignored.
    """
    m = VERSION_RE.search(s)
    return tuple(int(p) for p in m.group(0).split(".")) if m else ()


def version_newer(latest: str, current: str) -> bool:
    """True if `latest` is a newer release than `current`.

    Components are zero-padded to equal length before comparing, so a shorter
    string isn't treated as older than its own longer-but-equal form
    (3.10 == 3.10.0, while 3.10 > 3.9.0). Suffixes are ignored, so this can't
    tell a release from its own _rc (a known limitation of the track path).
    """
    a, b = version_tuple(latest), version_tuple(current)
    n = max(len(a), len(b))
    return a + (0,) * (n - len(a)) > b + (0,) * (n - len(b))


def rc_num(s: str) -> int:
    """Trailing RC number of a version string, e.g. '3.10-RC2' -> 2 (0 if none)."""
    m = RC_RE.search(s)
    return int(m.group(1)) if m else 0


def version_newer_rc(latest: str, current: str) -> bool:
    """RC-aware comparison: compare the X.Y base first, then the RC number.

    Lets the tracker notice 3.10-RC2 -> 3.10-RC3 (same numeric base, higher RC),
    which the suffix-blind version_newer() would miss, while still ordering
    3.11-RC1 above 3.10-RC9 by base.
    """
    base_l, base_c = version_tuple(latest), version_tuple(current)
    if base_l != base_c:
        return version_newer(latest, current)
    return rc_num(latest) > rc_num(current)


def clean_pv(tag: str) -> str:
    """Upstream tag -> dotted version, e.g. 'v1.4' -> '1.4'. Empty if no number."""
    m = VERSION_RE.search(tag)
    return m.group(0) if m else ""


# --- current (packaged) version -------------------------------------------
GLOBAL_RE = re.compile(r"^\s*%(?:global|define)\s+(\w+)\s+(\S.*?)\s*$", re.MULTILINE)
VERSION_FIELD_RE = re.compile(r"^Version:\s*(\S+)\s*$", re.MULTILINE)


def spec_path(pkg: str) -> Path:
    return REPO_ROOT / pkg / f"{pkg}.spec"


def spec_macros(text: str) -> dict[str, str]:
    """Collect simple `%global NAME VALUE` / `%define NAME VALUE` definitions."""
    return {m.group(1): m.group(2) for m in GLOBAL_RE.finditer(text)}


def expand_macros(value: str, macros: dict[str, str]) -> str:
    """Resolve %{NAME} references against `macros` (a few passes for nesting)."""
    for _ in range(5):
        new = re.sub(r"%\{(\w+)\}", lambda m: macros.get(m.group(1), m.group(0)), value)
        if new == value:
            break
        value = new
    return value


def current_version(pkg: dict) -> str | None:
    """Packaged version from the spec: a %global named by current_macro, else
    the Version: field, with simple %{macro} indirection resolved."""
    path = spec_path(pkg["pkg"])
    if not path.exists():
        return None
    text = path.read_text()
    macros = spec_macros(text)
    if pkg.get("current_macro"):
        raw = macros.get(pkg["current_macro"])
    else:
        m = VERSION_FIELD_RE.search(text)
        raw = m.group(1) if m else None
    return expand_macros(raw, macros) if raw else None


# --- latest (upstream) version --------------------------------------------
# The trailing lookahead anchors the token so a stable tag like "preview-2.0" or
# "developer-1.0" is not mistaken for a "pre"/"dev" pre-release; a real marker is
# followed by a digit, a separator, or end-of-string (rc1, -beta, .dev3, beta).
PRERELEASE_RE = re.compile(r"(?:^|[-_.])(?:rc|alpha|beta|pre|dev|snapshot)(?=\d|[-_.]|$)",
                           re.IGNORECASE)


def latest_github(repo: str) -> str:
    """Latest release tag, falling back to the highest stable tag.

    Not every repo marks a "latest" release (some only push tags, some publish
    only pre-releases), so `releases/latest` 404s there -> fall back to tags.
    """
    try:
        data = json.loads(http_get(f"https://api.github.com/repos/{repo}/releases/latest",
                                   headers=gh_headers()))
        return clean_pv(data["tag_name"])
    except urllib.error.HTTPError as exc:
        if exc.code != 404:
            raise
    tags = json.loads(http_get(f"https://api.github.com/repos/{repo}/tags?per_page=100",
                               headers=gh_headers()))
    names = [t["name"] for t in tags if not PRERELEASE_RE.search(t["name"])]
    if not names:
        raise ValueError(f"{repo}: no stable tags found")
    return clean_pv(max(names, key=version_tuple))


def latest_sourceforge(project: str, path: str) -> str:
    """Newest plain version directory directly under a SourceForge files path.

    Matches `<path>/<X.Y.Z>/` in the files RSS; a trailing `/` is required, so
    decorated dirs like `3.10-RC2/` (release candidates) are skipped.
    """
    rss = http_get(f"https://sourceforge.net/projects/{project}/rss?path={path}").decode("utf-8", "replace")
    pat = re.escape(path.rstrip("/")) + r"/(\d+(?:\.\d+)*)/"
    versions = re.findall(pat, rss)
    if not versions:
        raise ValueError(f"no versions matched under {path}")
    return max(versions, key=version_tuple)


def latest_sourceforge_rc(project: str, path: str) -> str:
    """Newest X.Y[.Z]-RCn release-candidate directory under a SourceForge path.

    The plain sourceforge rule deliberately skips decorated dirs, so RC tracks
    need their own matcher. Ordered by (numeric base, RC number).
    """
    rss = http_get(f"https://sourceforge.net/projects/{project}/rss?path={path}").decode("utf-8", "replace")
    pat = re.escape(path.rstrip("/")) + r"/(\d+(?:\.\d+)*-RC\d+)/"
    versions = re.findall(pat, rss, re.IGNORECASE)
    if not versions:
        raise ValueError(f"no release-candidate versions matched under {path}")
    return max(versions, key=lambda v: (version_tuple(v), rc_num(v)))


def latest_atelierb(url: str) -> str:
    page = http_get(url).decode("utf-8", "replace")
    versions = re.findall(r"atelierb-free-(\d+(?:\.\d+)+)-", page)
    if not versions:
        raise ValueError("no atelierb-free-<version> link found")
    return max(versions, key=version_tuple)


def latest_apache_index(url: str) -> str:
    """Newest multi-component version subdirectory in an Apache/nginx autoindex.

    Only dotted-numeric names with at least two components count: the trailing
    `/"` anchor skips decorated siblings (betas, rcs, 'final', 'profile'), and
    requiring a dot skips non-version dirs such as a bare year archive.
    """
    page = http_get(url).decode("utf-8", "replace")
    versions = re.findall(r'href="(\d+(?:\.\d+)+)/"', page)
    if not versions:
        raise ValueError(f"no version directories found at {url}")
    return max(versions, key=version_tuple)


def latest_version(source: dict) -> str:
    t = source["type"]
    if t == "github":
        return latest_github(source["repo"])
    if t == "sourceforge":
        return latest_sourceforge(source["project"], source["path"])
    if t == "sourceforge_rc":
        return latest_sourceforge_rc(source["project"], source["path"])
    if t == "atelierb":
        return latest_atelierb(source["url"])
    if t == "apache_index":
        return latest_apache_index(source["url"])
    raise ValueError(f"unknown source type {t!r}")


def is_outdated(source: dict, latest: str | None, current: str | None) -> bool:
    if not (latest and current):
        return False
    if source.get("type") == "sourceforge_rc":
        return version_newer_rc(latest, current)
    return version_newer(latest, current)


# --- Source0 -> reachability check -----------------------------------------
SOURCE0_RE = re.compile(r"^Source0:\s*(\S+)\s*$", re.MULTILINE)


def source0_url(text: str, macros: dict[str, str], pkg: str, version: str) -> str | None:
    """Resolve Source0 to a plain URL for the given version.

    Drops the `#/<rename>` fragment (rpm uses it only to rename the saved file)
    and substitutes %{name}/%{version} plus the spec's own globals.
    """
    m = SOURCE0_RE.search(text)
    if not m:
        return None
    raw = m.group(1).split("#", 1)[0]
    macros = {**macros, "name": pkg, "version": version}
    url = expand_macros(raw, macros)
    return url if "%" not in url else None


def url_reachable(url: str, timeout: int = 60) -> bool | None:
    """True/False if the artifact clearly exists / 404s, None if undetermined.

    Tries HEAD, falling back to a GET that reads nothing (some CDNs reject HEAD).
    Network hiccups return None so a bump is never blocked by a transient error.
    """
    for method in ("HEAD", "GET"):
        try:
            req = urllib.request.Request(url, method=method, headers=UA)
            with urllib.request.urlopen(req, timeout=timeout):
                return True
        except urllib.error.HTTPError as exc:
            if exc.code in (404, 410):
                return False
            if exc.code in (403, 405, 501) and method == "HEAD":
                continue  # method not allowed/forbidden for HEAD: retry with GET
            return None
        except OSError:
            # URLError, socket.timeout and ssl errors all subclass OSError; a
            # transient network failure is "undetermined", not "missing". A real
            # bug (TypeError, etc.) is intentionally NOT swallowed here.
            return None
    return None


# --- subcommands -----------------------------------------------------------
def cmd_check() -> int:
    report = []
    for pkg in PACKAGES:
        entry = {"pkg": pkg["pkg"], "mode": pkg["mode"], "current": None,
                 "latest": None, "outdated": False, "error": None}
        # Best-effort per package: a single unreadable/malformed spec or a network
        # blip records an error for that entry but never aborts the whole report
        # (the workflow surfaces .error rows without failing the run).
        try:
            entry["current"] = current_version(pkg)
            if pkg["mode"] != "skip":
                latest = latest_version(pkg["source"])
                entry["latest"] = latest
                entry["outdated"] = is_outdated(pkg["source"], latest, entry["current"])
        except Exception as exc:
            entry["error"] = f"{type(exc).__name__}: {exc}"
        report.append(entry)
    print(json.dumps(report, indent=2))
    return 0


def emit_outputs(**kv: str) -> None:
    """Append key=value lines to $GITHUB_OUTPUT when running under Actions."""
    path = os.environ.get("GITHUB_OUTPUT")
    if path:
        with open(path, "a") as fh:
            for k, v in kv.items():
                fh.write(f"{k}={v}\n")


def bump_spec_text(text: str, new: str) -> str:
    """Return `text` with Version: set to `new`, Release: reset to 1, and a new
    %changelog entry prepended. Whitespace/alignment of the fields is preserved."""
    text, n = re.subn(r"^(Version:[ \t]*).*$", lambda m: m.group(1) + new, text,
                      count=1, flags=re.MULTILINE)
    if n != 1:
        raise ValueError("Version: field not found")
    text, n = re.subn(r"^(Release:[ \t]*).*$", lambda m: m.group(1) + "1%{?dist}", text,
                      count=1, flags=re.MULTILINE)
    if n != 1:
        raise ValueError("Release: field not found")

    date = datetime.date.today().strftime("%a %b %d %Y")
    entry = (f"* {date} {CHANGELOG_AUTHOR} - {new}-1\n"
             f"- Update to {new}\n\n")
    # Normalise the header to "%changelog\n" before inserting, so a spec whose
    # %changelog line is the last line with no trailing newline still works
    # (the `\n?` keeps the match optional) without doubling the separator.
    text, n = re.subn(r"^%changelog[ \t]*\n?", lambda *_: "%changelog\n" + entry, text,
                      count=1, flags=re.MULTILINE)
    if n != 1:
        raise ValueError("%changelog section not found")
    return text


def cmd_bump(pkg_name: str) -> int:
    pkg = next((p for p in PACKAGES if p["pkg"] == pkg_name), None)
    if not pkg or pkg["mode"] != "bump":
        print(f"refusing to bump {pkg_name!r}: not a configured bump package", file=sys.stderr)
        return 2

    current = current_version(pkg)
    latest = latest_version(pkg["source"])
    if not (current and latest and is_outdated(pkg["source"], latest, current)):
        print(f"{pkg_name}: up to date ({current}, upstream {latest})")
        emit_outputs(bumped="false")
        return 0

    path = spec_path(pkg_name)
    text = path.read_text()

    # Belt-and-suspenders: confirm the new artifact exists before opening a PR.
    # A definite 404 means the version dir/tag is published but the file isn't
    # there yet (or the URL template changed) -> skip; undetermined -> proceed.
    url = source0_url(text, spec_macros(text), pkg_name, latest)
    if url is not None:
        reachable = url_reachable(url)
        if reachable is False:
            print(f"{pkg_name}: upstream {latest} detected but Source0 not reachable: {url}",
                  file=sys.stderr)
            emit_outputs(bumped="false")
            return 0
        if reachable is None:
            print(f"{pkg_name}: WARNING could not verify Source0 reachability: {url}",
                  file=sys.stderr)

    path.write_text(bump_spec_text(text, latest))
    print(f"{pkg_name}: {current} -> {latest}")
    print(f"  rewrote {path.relative_to(REPO_ROOT)}")
    emit_outputs(bumped="true", pn=pkg_name, old=current, new=latest)
    return 0


def main(argv: list[str]) -> int:
    if len(argv) >= 1 and argv[0] == "check":
        return cmd_check()
    if len(argv) >= 2 and argv[0] == "bump":
        return cmd_bump(argv[1])
    print(__doc__)
    print("usage: version_check.py check | bump <package>", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
