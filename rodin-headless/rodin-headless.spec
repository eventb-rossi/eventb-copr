Name:           rodin-headless
Version:        4.0
Release:        1%{?dist}
Summary:        Headless toolchain to build, model-check, and prove Rodin Event-B models

License:        MIT
URL:            https://github.com/eventb-rossi/rodin-headless
Source0:        https://github.com/eventb-rossi/rodin-headless/archive/refs/tags/v%{version}.tar.gz#/%{name}-%{version}.tar.gz

BuildArch:      noarch
# Pure-shell toolchain; the upstream GNU Makefile does the install.
BuildRequires:  make
# No hard runtime Requires (Homebrew-style): the wrapper bundles no runtime and
# picks one at run time — native mode needs a JDK (javac compiles a plugin),
# Xvfb and GTK 3; container mode needs Docker/Podman. See %description.

%description
rodin-headless drives the Rodin Platform from the command line to build,
model-check, and prove Event-B models without a graphical session. It takes
.zip archives of Event-B projects, runs a full Rodin workspace build in headless
mode, and writes the static-checked artifacts back into the archives. Beyond
plain builds it can model-check and validate models with ProB and automatically
discharge proof obligations with Rodin.

It bundles no Rodin, ProB, or Java. Run `rodin-headless-install` once to fetch
the Rodin and ProB runtimes into your per-user data directory (native mode,
which needs a JDK 17+, Xvfb and GTK 3), or point the wrapper at a Docker/Podman
container image. Run `rodin-headless-install --check-deps` to report anything
that is missing.

%prep
%autosetup -n %{name}-%{version}

%build
# Nothing to compile; the upstream `make all` only prints a notice.

%install
%make_install prefix=%{_prefix}

%check
# Smoke test from the unpacked source tree, not the buildroot: %make_install
# rewrites the wrappers' libexec sentinel to the final absolute /usr/libexec,
# which does not exist at build time. In-tree the script falls back to its own
# directory and finds rodin-headless-lib.sh + VERSION beside it.
./rodin-headless --version | grep -F 'rodin-headless %{version}'

%files
%license LICENSE
%doc README.md
%{_bindir}/rodin-headless
%{_bindir}/rodin-headless-install
%{_libexecdir}/rodin-headless/
%{_datadir}/rodin-headless/
%{_mandir}/man1/rodin-headless.1*
%{_mandir}/man1/rodin-headless-install.1*

%changelog
* Thu Jun 25 2026 Denis Efremov <efremov@linux.com> - 4.0-1
- Initial package
