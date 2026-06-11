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

| Package | Version | Description |
| ------- | ------- | ----------- |
| `eventb-checker` | 1.3 | Validate Event-B models (`.bum`/`.buc`/`.eventb` or `.zip`) without a Rodin install |
| `evbt` | 1.5.0 | [EventBTool](https://codeberg.org/viklauverk/EventBTool) — code generation and documentation from Event-B models |
| `tlc4b` | 1.2.3 | [TLC4B](https://github.com/hhu-stups/tlc4b) — model-check classical B by translating to TLA+ and running TLC |
| `b2program` | 0.1.0 (snapshot) | [B2Program](https://github.com/favu100/b2program) — generate Java/C++/Python/Rust/TypeScript from high-level B |
| `eventb-animate` | 5.0 | [eventb-animate](https://github.com/eventb-rossi/eventb-animate) — animate Event-B models with the ProB model checker, no Rodin install |
| `eventb-to-txt` | 1.7 | [eventb-to-txt](https://github.com/eventb-rossi/eventb-to-txt) — convert Rodin models (`.bum`/`.buc`) to CamilleX plain text |

### GUI applications

| Package | Version | Arch | Description |
| ------- | ------- | ---- | ----------- |
| `rodin` | 3.9 | x86_64 | Rodin Platform — Event-B IDE (stable) |
| `rodin-rc` | 3.10-RC2 | x86_64, aarch64 | Rodin Platform — release candidate (conflicts with `rodin`) |
| `atelier-b` | 24.04.2 | x86_64 | Atelier B Community Edition — IDE for the B method |
| `prob` | 1.15.1 | x86_64 | [ProB](https://prob.hhu.de/) — animator/model checker; Tcl/Tk GUI (`prob`) plus the `probcli` CLI |
| `prob2-ui` | 1.3.1 | noarch | [ProB2-UI](https://prob.hhu.de/w/index.php/ProB2-UI) — JavaFX animator and model checker built on ProB |

```sh
sudo dnf install rodin        # stable 3.9
sudo dnf install rodin-rc     # 3.10 release candidate
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
