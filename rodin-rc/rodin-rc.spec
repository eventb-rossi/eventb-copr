%global rodindir   %{_prefix}/lib/rodin
%global sfdir      3.10-RC2
%global buildid    3.10.0.202605210654-RC2-881664d81
%global tarball    rodin-%{buildid}-linux.gtk.x86_64.tar.gz

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
Version:        3.10
Release:        0.2.RC2%{?dist}
Summary:        Rodin Platform release candidate (Event-B IDE)

License:        EPL-1.0 AND EPL-2.0
URL:            https://wiki.event-b.org/
# Release-candidate build; the filename embeds an opaque build id.
Source0:        https://downloads.sourceforge.net/rodin-b-sharp/Core_Rodin_Platform/%{sfdir}/%{tarball}
Source1:        rodin.desktop

# Upstream ships only a Linux x86_64 build for this release candidate.
ExclusiveArch:  x86_64
BuildRequires:  desktop-file-utils
BuildRequires:  ImageMagick

# rodin-rc is a drop-in pre-release of the same IDE: it installs to the same
# paths as the stable rodin package, so the two cannot be installed together.
Conflicts:      rodin

Requires:       java-headless >= 1:17
Requires:       gtk3
Requires:       hicolor-icon-theme
Recommends:     webkit2gtk4.1

%description
The Rodin Platform is an Eclipse-based IDE for Event-B. This package provides
the 3.10-RC2 release candidate, repackaged from the official upstream Linux
build. It bundles no Java runtime and needs a system Java 17 or newer. It
installs as a drop-in replacement for the stable "rodin" package (only one at a
time).

%prep
%autosetup -n rodin
cp -p "$(find features -name 'epl-2.0.html' | head -1)" epl-2.0.html

%build
# Nothing to build; this is a repackaged binary distribution.

%install
install -dm 0755 %{buildroot}%{rodindir}
cp -a . %{buildroot}%{rodindir}/
rm -f %{buildroot}%{rodindir}/epl-2.0.html

install -dm 0755 %{buildroot}%{_bindir}
cat > %{buildroot}%{_bindir}/rodin <<'EOF'
#!/bin/sh
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
* Sun Jun 14 2026 Denis Efremov <efremov@linux.com> - 3.10-0.2.RC2
- Install icon into hicolor theme as PNG (fixes missing icon in GNOME)

* Sun Jun 07 2026 Denis Efremov <efremov@linux.com> - 3.10-0.1.RC2
- Initial package: repackage the 3.10-RC2 upstream Linux build
