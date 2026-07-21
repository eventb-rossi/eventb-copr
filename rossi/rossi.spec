Name:           rossi
Version:        0.1.6
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
export RUSTFLAGS="%{?build_rustflags}"
cargo build --release --locked

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
