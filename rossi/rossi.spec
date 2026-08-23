Name:           rossi
Version:        0.2.0
Release:        1%{?dist}
Summary:        Rust toolchain for Event-B: parser, static checker, CLI, and language server

License:        Apache-2.0 OR MIT
URL:            https://github.com/eventb-rossi/rossi
Source0:        https://github.com/eventb-rossi/rossi/archive/refs/tags/v%{version}.tar.gz#/%{name}-%{version}.tar.gz

# Built from source with Cargo. The build fetches crate dependencies from
# crates.io, so the Copr project must have network access enabled (the same
# requirement the Gradle-built packages already rely on).
BuildRequires:  cargo
# zstd-sys and other -sys crates compile bundled C sources via the cc crate.
BuildRequires:  gcc
# llvm-profdata, to merge PGO profiles in %build. Fedora keeps rustc and llvm
# in lockstep, so the system llvm package's LLVM major always matches rustc's.
BuildRequires:  llvm

%description
Rossi is a Rust toolchain for Event-B providing a parser, a static checker, a
command-line interface, and a language server. It validates Event-B models,
converts between Event-B text and Rodin archives, reformats models, and powers
editor integration over the Language Server Protocol.

%prep
%autosetup -n %{name}-%{version}

%build
# Keep cargo's registry/cache inside the build tree; pick up Fedora's build
# flags when rust-srpm-macros defines them (empty otherwise).
export CARGO_HOME="$(pwd)/.cargo"
base_rustflags="%{?build_rustflags}"

# Two-phase PGO build, mirroring rossi's own release workflow
# (scripts/pgo-train.sh + -Cprofile-generate/-Cprofile-use): build an
# instrumented rossi, train it on the in-repo example models, merge the
# profile, then rebuild both binaries reading it back. The instrument and
# profile-use invocations must differ ONLY in that RUSTFLAGS value -- any
# other difference changes -Cmetadata, which is baked into the mangled
# symbol names rustc matches profiles by, and the profile silently stops
# applying. Older source tags don't carry the training script yet, so fall
# back to a plain build when it's absent.
if [ -x scripts/pgo-train.sh ] && [ -d crates/rossi/examples ]; then
    pgodir="$(pwd)/pgo-data"
    RUSTFLAGS="$base_rustflags -Cprofile-generate=$pgodir" \
      cargo build --release --locked --bin rossi
    ./scripts/pgo-train.sh target/release/rossi
    llvm-profdata merge -o pgo-merged.profdata "$pgodir"
    RUSTFLAGS="$base_rustflags -Cprofile-use=$(pwd)/pgo-merged.profdata" \
      cargo build --release --locked --bin rossi --bin eventb-language-server
else
    RUSTFLAGS="$base_rustflags" cargo build --release --locked
fi

%install
install -Dpm 0755 target/release/rossi %{buildroot}%{_bindir}/rossi
install -Dpm 0755 target/release/eventb-language-server %{buildroot}%{_bindir}/eventb-language-server

# Shell completions, generated from the freshly built binary so they always
# match the installed CLI version (rossi completions <shell> -> stdout, via
# clap_complete). The dir macros come from redhat-rpm-config, always present in
# the buildroot. Filenames follow each shell's lookup convention: the command
# name for bash, _-prefixed for zsh, .fish suffix for fish.
install -d %{buildroot}%{bash_completions_dir} \
           %{buildroot}%{zsh_completions_dir} \
           %{buildroot}%{fish_completions_dir}
./target/release/rossi completions bash > %{buildroot}%{bash_completions_dir}/rossi
./target/release/rossi completions zsh  > %{buildroot}%{zsh_completions_dir}/_rossi
./target/release/rossi completions fish > %{buildroot}%{fish_completions_dir}/rossi.fish

%check
# Smoke test the freshly built binaries (mirrors the Homebrew formula's test).
./target/release/rossi --version
./target/release/eventb-language-server --version

%files
%license LICENSE-APACHE LICENSE-MIT
%doc README.md
%{_bindir}/rossi
%{_bindir}/eventb-language-server
%{bash_completions_dir}/rossi
%{zsh_completions_dir}/_rossi
%{fish_completions_dir}/rossi.fish

%changelog
* Sun Aug 23 2026 Denis Efremov <efremov@linux.com> - 0.2.0-1
- Update to 0.2.0

* Sun Aug 23 2026 Denis Efremov <efremov@linux.com> - 0.1.9-2
- Build with PGO when the source tarball carries scripts/pgo-train.sh, mirroring
  upstream's release workflow (falls back to a plain build on older tags)

* Tue Aug 18 2026 Denis Efremov <efremov@linux.com> - 0.1.9-1
- Update to 0.1.9

* Tue Aug 11 2026 Denis Efremov <efremov@linux.com> - 0.1.8-1
- Update to 0.1.8

* Mon Jul 27 2026 Denis Efremov <efremov@linux.com> - 0.1.7-1
- Update to 0.1.7

* Tue Jul 21 2026 Denis Efremov <efremov@linux.com> - 0.1.6-1
- Update to 0.1.6

* Sun Jul 19 2026 Denis Efremov <efremov@linux.com> - 0.1.5-1
- Update to 0.1.5

* Mon Jul 06 2026 Denis Efremov <efremov@linux.com> - 0.1.4-1
- Update to 0.1.4

* Mon Jun 29 2026 Denis Efremov <efremov@linux.com> - 0.1.3-2
- Install bash, zsh, and fish shell completions

* Mon Jun 29 2026 Denis Efremov <efremov@linux.com> - 0.1.3-1
- Update to 0.1.3

* Fri Jun 26 2026 Denis Efremov <efremov@linux.com> - 0.1.2-1
- Update to 0.1.2

* Tue Jun 23 2026 Denis Efremov <efremov@linux.com> - 0.1.1-1
- Update to 0.1.1

* Sat Jun 20 2026 Denis Efremov <efremov@linux.com> - 0.1.0-1
- Initial package
