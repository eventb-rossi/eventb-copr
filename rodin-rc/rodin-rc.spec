%global rodindir   %{_prefix}/lib/rodin
# Rodin-Bundle release tag, and the build id its tarball name embeds (base
# version + commit date/hash qualifier, not derivable from the tag). Both are
# rewritten by the version-check workflow on bumps.
%global tag        v3.10.0-2611
%global buildid    3.10.0.202611160826-a263a14
%global tarball    rodin-%{buildid}-rossi-linux.gtk.x86_64.tar.gz

# Repackaged prebuilt Eclipse RCP product: keep the upstream binaries intact and
# do not let rpm generate Provides/Requires from the bundled private libraries.
%global debug_package %{nil}
%global __brp_strip %{nil}
%global __brp_strip_static_archive %{nil}
%global __brp_strip_comment_note %{nil}
%global __brp_check_rpaths %{nil}
%global __provides_exclude_from ^%{rodindir}/.*$
%global __requires_exclude_from ^%{rodindir}/.*$

Name:           rodin-rc
# Follows the newest Rodin-Bundle build, release candidates included: tag
# vX.Y.Z-YYMM[.N][-rcN] -> X.Y.Z^YYMM[.N][~rcN], so a candidate sorts before
# its final release and the final release replaces it.
Version:        3.10.0^2611
Release:        1%{?dist}
Summary:        Rodin Platform release candidates (Event-B IDE)

# Eclipse platform and the PO Cleaner / Rossi bridge plug-ins are EPL-2.0; the
# Rodin core and ProB plug-ins are EPL-1.0; the bundled SMT solvers are MIT (Z3)
# and BSD-3-Clause (CVC3, CVC4, veriT).
License:        EPL-1.0 AND EPL-2.0 AND MIT AND BSD-3-Clause
URL:            https://github.com/eventb-rossi/Rodin-Bundle
Source0:        https://github.com/eventb-rossi/Rodin-Bundle/releases/download/%{tag}/%{tarball}
Source1:        rodin.desktop

# Rodin-Bundle ships a single Linux build, for x86_64.
ExclusiveArch:  x86_64
BuildRequires:  desktop-file-utils
BuildRequires:  ImageMagick

# rodin-rc is a drop-in pre-release of the same IDE: it installs to the same
# paths as the stable rodin package, so the two cannot be installed together.
Conflicts:      rodin

Requires:       java-headless >= 1:21
Requires:       gtk3
Requires:       hicolor-icon-theme
Recommends:     webkit2gtk4.1

%description
The Rodin Platform is an Eclipse-based IDE for Event-B. This package follows
the newest eventb-rossi Rodin Bundle build, release candidates included, so it
is the place to try a bundle before it becomes the stable "rodin" package. It
bundles no Java runtime and needs a system Java 21 or newer. It installs as a
drop-in replacement for the stable "rodin" package (only one at a time).

%prep
%autosetup -n rodin
cp -p "$(find features -name 'epl-2.0.html' | head -1)" epl-2.0.html

# Rodin's Eclipse UI has no working dark theme: pin the e4 CSS light theme so
# Eclipse-drawn widgets stay light regardless of the desktop theme. The property
# must follow -vmargs to reach the JVM.
sed -i '/^-vmargs$/a -Dorg.eclipse.e4.ui.css.swt.theme=org.eclipse.e4.ui.css.theme.e4_default' rodin.ini

%build
# Nothing to build; this is a repackaged binary distribution.

%install
install -dm 0755 %{buildroot}%{rodindir}
cp -a . %{buildroot}%{rodindir}/
rm -f %{buildroot}%{rodindir}/epl-2.0.html

install -dm 0755 %{buildroot}%{_bindir}
cat > %{buildroot}%{_bindir}/rodin <<'EOF'
#!/bin/sh
# Rodin has no working dark theme; force a light GTK theme so native SWT/GTK
# widgets match the light e4 CSS theme pinned in rodin.ini.
export GTK_THEME=Adwaita:light
exec /usr/lib/rodin/rodin "$@"
EOF
chmod 0755 %{buildroot}%{_bindir}/rodin

# Icon: convert the upstream 32x32 XPM to PNG and install into the hicolor theme.
for size in 32 48; do
    install -dm 0755 %{buildroot}%{_datadir}/icons/hicolor/${size}x${size}/apps
    magick convert -resize ${size}x${size} icon.xpm \
        %{buildroot}%{_datadir}/icons/hicolor/${size}x${size}/apps/rodin.png
done
desktop-file-install --dir=%{buildroot}%{_datadir}/applications --set-key=Name --set-value="Rodin Platform (RC)" %{SOURCE1}
# desktop-file-install keeps the source basename (rodin.desktop).

%posttrans
/usr/bin/gtk-update-icon-cache -f -t %{_datadir}/icons/hicolor &>/dev/null || :

%postun
if [ $1 -eq 0 ]; then
    /usr/bin/gtk-update-icon-cache -f -t %{_datadir}/icons/hicolor &>/dev/null || :
fi

%check
desktop-file-validate %{buildroot}%{_datadir}/applications/rodin.desktop

%files
%license epl-2.0.html
%{_bindir}/rodin
%{rodindir}
%{_datadir}/icons/hicolor/32x32/apps/rodin.png
%{_datadir}/icons/hicolor/48x48/apps/rodin.png
%{_datadir}/applications/rodin.desktop

%changelog
* Mon Nov 16 2026 Denis Efremov <efremov@linux.com> - 3.10.0^2611-1
- Switch to the eventb-rossi Rodin Bundle: follow its newest build, release
  candidates included (now v3.10.0-2611)

* Thu Jul 02 2026 Denis Efremov <efremov@linux.com> - 3.10-0.4.RC2
- Raise the runtime baseline to Java 21 (matches upstream 3.10-RC2)

* Thu Jun 18 2026 Denis Efremov <efremov@linux.com> - 3.10-0.3.RC2
- Force light theme (Rodin has no dark theme): pin e4 CSS theme in rodin.ini
  and export GTK_THEME=Adwaita:light in the launcher

* Sun Jun 14 2026 Denis Efremov <efremov@linux.com> - 3.10-0.2.RC2
- Install icon into hicolor theme as PNG (fixes missing icon in GNOME)

* Sun Jun 07 2026 Denis Efremov <efremov@linux.com> - 3.10-0.1.RC2
- Initial package: repackage the 3.10-RC2 upstream Linux build
