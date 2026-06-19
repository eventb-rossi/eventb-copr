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
Release:        2%{?dist}
Summary:        Animator, constraint solver and model checker for B, Event-B, CSP, TLA+, Z

License:        EPL-1.0
URL:            https://prob.hhu.de/
# The release asset is an unversioned filename under a versioned path; rename it
# to a versioned local name with #/. The tarball extracts to a top dir "ProB".
Source0:        https://stups.hhu-hosting.de/downloads/prob/tcltk/releases/%{version}/ProB.linux64.tar.gz#/%{name}-%{version}.linux64.tar.gz
Source1:        prob.desktop

ExclusiveArch:  x86_64
BuildRequires:  desktop-file-utils
BuildRequires:  ImageMagick

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
# The %%posttrans/%%postun icon-cache scriptlets call gtk-update-icon-cache.
# Unlike Rodin (a GTK app that pulls in gtk3), the Tcl/Tk ProB drags in nothing
# that provides this tool, so require it explicitly.
Requires:       gtk-update-icon-cache
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

# Icon: convert the upstream 128x128 GIF to PNG and install into the hicolor theme.
for size in 32 48 128; do
    install -dm 0755 %{buildroot}%{_datadir}/icons/hicolor/${size}x${size}/apps
    magick convert -resize ${size}x${size} tcl/icons/prob_128.gif \
        %{buildroot}%{_datadir}/icons/hicolor/${size}x${size}/apps/%{name}.png
done

# Desktop entry.
desktop-file-install --dir=%{buildroot}%{_datadir}/applications %{SOURCE1}

%check
desktop-file-validate %{buildroot}%{_datadir}/applications/%{name}.desktop

%posttrans
/usr/bin/gtk-update-icon-cache -f -t %{_datadir}/icons/hicolor &>/dev/null || :

%postun
if [ $1 -eq 0 ]; then
    /usr/bin/gtk-update-icon-cache -f -t %{_datadir}/icons/hicolor &>/dev/null || :
fi

%files
%license licence.txt LICENSE-nauty.txt
%{_bindir}/%{name}
%{_bindir}/probcli
%{probdir}
%{_datadir}/icons/hicolor/32x32/apps/%{name}.png
%{_datadir}/icons/hicolor/48x48/apps/%{name}.png
%{_datadir}/icons/hicolor/128x128/apps/%{name}.png
%{_datadir}/applications/%{name}.desktop

%changelog
* Fri Jun 19 2026 Denis Efremov <efremov@linux.com> - 1.15.1-2
- Install the app icon into the hicolor theme as PNG (converted from the
  upstream 128x128 prob_128.gif at 32, 48 and 128 px) so Icon=prob resolves
  under modern GNOME/Wayland; refresh the icon cache via %%posttrans/%%postun.
  Drop the /usr/share/pixmaps XPM.

* Thu Jun 11 2026 Denis Efremov <efremov@linux.com> - 1.15.1-1
- Initial package: repackage the upstream ProB Tcl/Tk Linux build (prob + probcli)
