%global probdir   %{_prefix}/lib/%{name}

# Repackaged prebuilt SICStus-Prolog binaries: keep them intact (no debuginfo,
# no stripping, no rpath check) and do not let rpm generate Provides/Requires
# from the bundled native helpers (z3, zmq, bliss, cspmf, libczmq) under the
# install tree. The real external dependencies are listed manually below.
%global debug_package %{nil}
%global __brp_strip %{nil}
%global __brp_strip_static_archive %{nil}
%global __brp_strip_comment_note %{nil}
%global __brp_check_rpaths %{nil}
%global __provides_exclude_from ^%{probdir}/.*$
%global __requires_exclude_from ^%{probdir}/.*$

Name:           prob
Version:        1.15.1
Release:        1%{?dist}
Summary:        Animator, constraint solver and model checker for B, Event-B, CSP, TLA+, Z

License:        EPL-1.0
URL:            https://prob.hhu.de/
# The release asset is an unversioned filename under a versioned path; rename it
# to a versioned local name with #/. The tarball extracts to a top dir "ProB".
Source0:        https://stups.hhu-hosting.de/downloads/prob/tcltk/releases/%{version}/ProB.linux64.tar.gz#/%{name}-%{version}.linux64.tar.gz
Source1:        prob.desktop

ExclusiveArch:  x86_64
BuildRequires:  desktop-file-utils

# Parser components (lib/*.jar) need a JRE; the Tcl/Tk GUI binary dlopens
# libtcl8.6.so / libtk8.6.so, so it needs the Tcl/Tk 8.6 compat packages
# (Fedora's default tk/tcl are now 9.0, which ship only libtcl9tk9.0.so). tk8
# pulls in tcl8 (libtcl8.6.so).
Requires:       java-headless >= 1:1.8
Requires:       tk8
# The bundled cspmf links libgmp; the bundled libczmq links libuuid.
Requires:       gmp
Requires:       libuuid
Requires:       hicolor-icon-theme
# Optional graph and state-space visualisation.
Recommends:     graphviz

%description
ProB is an animator, constraint solver and model checker for the B method. It
supports classical B, Event-B, CSP-M, TLA+ and Z, with animation and automated
or guided model checking (invariant and deadlock checking). This package
repackages the official upstream Linux build and provides both the Tcl/Tk GUI
(prob) and the command-line tool (probcli).

%prep
%autosetup -n ProB
# Surface the bundled licences for the %%license directive.
cp -p tcl/licence.txt licence.txt
cp -p tcl/LICENSE-nauty.txt LICENSE-nauty.txt

%build
# Nothing to build; this is a repackaged binary distribution.

%install
install -dm 0755 %{buildroot}%{probdir}
cp -a . %{buildroot}%{probdir}/
# Drop the top-level licence copies added in %%prep (the originals stay under
# %%{probdir}/tcl/); they are shipped via %%license instead.
rm -f %{buildroot}%{probdir}/licence.txt %{buildroot}%{probdir}/LICENSE-nauty.txt

install -dm 0755 %{buildroot}%{_bindir}
# GUI launcher: StartProB.sh exports TRAILSTKSIZE then execs ./prob, resolving
# its directory from $0, so exec'ing it by absolute path is sufficient.
cat > %{buildroot}%{_bindir}/%{name} <<'EOF'
#!/bin/sh
exec %{probdir}/StartProB.sh "$@"
EOF
chmod 0755 %{buildroot}%{_bindir}/%{name}
# CLI launcher: wrap the binary directly. probcli.sh chmods its own binary under
# `set -e`, which fails against the read-only install for a non-root user.
cat > %{buildroot}%{_bindir}/probcli <<'EOF'
#!/bin/sh
exec %{probdir}/probcli "$@"
EOF
chmod 0755 %{buildroot}%{_bindir}/probcli

# Icon and desktop entry.
install -Dpm 0644 tcl/icons/prob.xpm %{buildroot}%{_datadir}/pixmaps/%{name}.xpm
desktop-file-install --dir=%{buildroot}%{_datadir}/applications %{SOURCE1}

%check
desktop-file-validate %{buildroot}%{_datadir}/applications/%{name}.desktop

%files
%license licence.txt LICENSE-nauty.txt
%{_bindir}/%{name}
%{_bindir}/probcli
%{probdir}
%{_datadir}/pixmaps/%{name}.xpm
%{_datadir}/applications/%{name}.desktop

%changelog
* Thu Jun 11 2026 Denis Efremov <efremov@linux.com> - 1.15.1-1
- Initial package: repackage the upstream ProB Tcl/Tk Linux build (prob + probcli)
