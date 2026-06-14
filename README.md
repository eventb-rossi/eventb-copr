# Fedora Copr packaging for Event-B / B-method tools

RPM packaging for the [Event-B](https://www.event-b.org/) / B-method ecosystem —
the Rodin Platform IDE, ClearSy's Atelier B, the ProB model checker, and a set of
command-line tools for code generation, model checking and validation.

## Install

```sh
sudo dnf copr enable @eventb-rossi/eventb-copr
sudo dnf install eventb-checker evbt tlc4b b2program eventb-animate eventb-to-txt
```

### Command-line tools

| Package | Description |
| ------- | ----------- |
| `eventb-checker` | [eventb-checker](https://github.com/eventb-rossi/eventb-checker) — validate Event-B models (`.bum`/`.buc`/`.eventb` or `.zip`) without a Rodin install |
| `evbt` | [EventBTool](https://codeberg.org/viklauverk/EventBTool) — code generation and documentation from Event-B models |
| `tlc4b` | [TLC4B](https://github.com/hhu-stups/tlc4b) — model-check classical B by translating to TLA+ and running TLC |
| `b2program` | [B2Program](https://github.com/favu100/b2program) — generate Java/C++/Python/Rust/TypeScript from high-level B |
| `eventb-animate` | [eventb-animate](https://github.com/eventb-rossi/eventb-animate) — animate Event-B models with the ProB model checker, no Rodin install |
| `eventb-to-txt` | [eventb-to-txt](https://github.com/eventb-rossi/eventb-to-txt) — convert Rodin models (`.bum`/`.buc`) to CamilleX plain text |

### GUI applications

| Package | Arch | Description |
| ------- | ---- | ----------- |
| `rodin` | x86_64 | Rodin Platform — Event-B IDE (stable) |
| `rodin-rc` | x86_64, aarch64 | Rodin Platform — release candidate (conflicts with `rodin`) |
| `atelier-b` | x86_64 | Atelier B Community Edition — IDE for the B method |
| `prob` | x86_64 | [ProB](https://prob.hhu.de/) — animator/model checker; Tcl/Tk GUI (`prob`) plus the `probcli` CLI |
| `prob2-ui` | noarch | [ProB2-UI](https://prob.hhu.de/w/index.php/ProB2-UI) — JavaFX animator and model checker built on ProB |

```sh
sudo dnf install rodin        # stable
sudo dnf install rodin-rc     # release candidate
sudo dnf install atelier-b    # Atelier B Community Edition
sudo dnf install prob         # ProB (probcli + Tcl/Tk GUI)
sudo dnf install prob2-ui     # ProB2-UI (JavaFX)
```

`rodin` and `rodin-rc` both provide the Rodin IDE and therefore conflict — install
only one at a time.

## Requirements

- The command-line Java tools (`eventb-checker`, `evbt`, `tlc4b`, `b2program`,
  `eventb-animate`) pull in a JRE automatically. `evbt` needs Java 22+, the others Java 21+.
- `eventb-to-txt` is a pure-Python tool; it pulls in `python3` automatically.
- **Rodin** needs a system **Java 17 or newer** (it bundles none) and GTK 3.
- **ProB** (`prob`) needs **Java 8 or newer** and Tcl/Tk 8.6; it pulls in `tk8`,
  `gmp` and `libuuid`, and recommends `graphviz` for graph/state-space visualisation.
- **ProB2-UI** (`prob2-ui`) needs **Java 21 or newer**, GTK 3 and the X11/OpenGL
  libraries its bundled JavaFX runtime loads (`libXtst`, `mesa-libGL`, `libXxf86vm`).

## Repository layout

One directory per package, each holding its `.spec` and any local sources. The shared
[`.copr/Makefile`](.copr/Makefile) generates the SRPM (used by both Copr and the local
[`Makefile`](Makefile)).

```
<pkg>/<pkg>.spec        # plus wrapper scripts, .desktop files, gradle init scripts
.copr/Makefile          # Copr SRPM entry point
Makefile                # local: srpm-<pkg>, mock-<pkg>, lint-<pkg>
.github/workflows/      # version-check (upstream tracker) + sanity (rpmlint)
```

## Building locally

```sh
sudo dnf install rpm-build rpmdevtools mock rpmlint copr-cli
sudo usermod -aG mock "$USER"      # then re-login

make srpm-eventb-to-txt            # build a source RPM
make mock-eventb-to-txt            # build it in a mock chroot
make lint-eventb-to-txt            # rpmlint
```

The four Gradle-built tools (`eventb-checker`, `tlc4b`, `b2program`, `eventb-animate`)
compile from upstream source: their mock builds enable network access and add the Adoptium
Temurin repo (for JDK 21, which Fedora no longer ships). The top-level `Makefile` wires this
up automatically for those targets.

## Maintainers

Builds are hosted on Copr at
[`@eventb-rossi/eventb-copr`](https://copr.fedorainfracloud.org/coprs/g/eventb-rossi/eventb-copr/).
Each package is registered as an SCM package pointing at its subdirectory here, using
the `make srpm` method; the project has network access enabled and the Adoptium repo
added as an external repository.

## Continuous integration

Two GitHub Actions workflows (mirroring the `homebrew-tap` and `gentoo-overlay` repos):

- **`version-check`** — runs daily and on demand. It detects new upstream releases via
  [`.github/scripts/version_check.py`](.github/scripts/version_check.py): packages with a
  clean `%{version}`-templated `Source0` are auto-bumped into a pull request (the spec's
  `Version:`/`Release:`/`%changelog` are rewritten — no source artifact is committed, Copr
  re-fetches `Source0` at build time), while packages with opaque build ids or
  non-derivable URLs (`rodin`, `rodin-rc`, `atelier-b`, `tlc4b`, `eventb-to-txt`) get a
  tracking issue labelled `version-bump`. `b2program` (pinned master commit) is not tracked.
- **`sanity`** — runs on every push/PR. In a Fedora container it parses every spec
  (`rpmspec -P`) and runs `rpmlint -c .rpmlint.toml`, failing only on error-severity
  diagnostics (accepted warnings are filtered by [`.rpmlint.toml`](.rpmlint.toml)).

[`.github/dependabot.yml`](.github/dependabot.yml) keeps the workflows' actions current
(the only ecosystem applicable here — spec upstreams are handled by `version-check`).

To let auto-bump PRs re-trigger `sanity` (the default `GITHUB_TOKEN` cannot trigger
workflows from bot-authored PRs), add a repository secret **`VERSION_BUMP_TOKEN`** — a PAT
with `Contents` + `Pull requests: write`. Without it the PRs still open, just without CI.
