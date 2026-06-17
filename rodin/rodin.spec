%global rodindir   %{_prefix}/lib/%{name}
%global buildid    3.9.0.202406100806-9b87fe13d
%global tarball    rodin-%{buildid}-linux.gtk.x86_64.tar.gz

# Repackaged prebuilt Eclipse RCP product: keep the upstream binaries intact
# (no debuginfo, no stripping, no rpath check) and do not let rpm generate
# automatic Provides/Requires from the bundled private libraries.
%global debug_package %{nil}
%global __brp_strip %{nil}
%global __brp_strip_static_archive %{nil}
%global __brp_strip_comment_note %{nil}
%global __brp_check_rpaths %{nil}
%global __provides_exclude_from ^%{rodindir}/.*$
%global __requires_exclude_from ^%{rodindir}/.*$

Name:           rodin
Version:        3.9
Release:        3%{?dist}
Summary:        IDE for formal modelling and verification with Event-B

# Eclipse platform components are EPL-2.0; the Rodin-specific plugins are EPL-1.0.
License:        EPL-1.0 AND EPL-2.0
URL:            https://wiki.event-b.org/
# The filename embeds an opaque build id (timestamp + git hash); update it on
# version bumps. Upstream ships a Linux x86_64 build only for the 3.9 release.
Source0:        https://downloads.sourceforge.net/rodin-b-sharp/Core_Rodin_Platform/%{version}/%{tarball}
Source1:        rodin.desktop

ExclusiveArch:  x86_64
BuildRequires:  desktop-file-utils
BuildRequires:  ImageMagick

# Rodin bundles no JRE and requires Java 17 or newer.
Requires:       java-headless >= 1:17
Requires:       gtk3
Requires:       hicolor-icon-theme
# Browser-backed views (e.g. some help/preview widgets) need WebKitGTK.
Recommends:     webkit2gtk4.1

%description
The Rodin Platform is an Eclipse-based IDE for Event-B that provides effective
support for refinement and mathematical proof. This package repackages the
official upstream Linux build; it bundles no Java runtime and needs a system
Java 17 or newer.

%prep
%autosetup -n %{name}
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

# Launcher wrapper. The Eclipse native launcher resolves its install tree from
# /proc/self/exe, so exec'ing the real binary by absolute path is sufficient.
install -dm 0755 %{buildroot}%{_bindir}
cat > %{buildroot}%{_bindir}/%{name} <<'EOF'
#!/bin/sh
# Rodin has no working dark theme; force a light GTK theme so native SWT/GTK
# widgets match the light e4 CSS theme pinned in rodin.ini.
export GTK_THEME=Adwaita:light
exec /usr/lib/rodin/rodin "$@"
EOF
chmod 0755 %{buildroot}%{_bindir}/%{name}

# Icon: convert the upstream 32x32 XPM to PNG and install into the hicolor theme.
for size in 32 48; do
    install -dm 0755 %{buildroot}%{_datadir}/icons/hicolor/${size}x${size}/apps
    magick convert -resize ${size}x${size} icon.xpm \
        %{buildroot}%{_datadir}/icons/hicolor/${size}x${size}/apps/%{name}.png
done
desktop-file-install --dir=%{buildroot}%{_datadir}/applications %{SOURCE1}

%posttrans
/usr/bin/gtk-update-icon-cache -f -t %{_datadir}/icons/hicolor &>/dev/null || :

%postun
if [ $1 -eq 0 ]; then
    /usr/bin/gtk-update-icon-cache -f -t %{_datadir}/icons/hicolor &>/dev/null || :
fi

%check
desktop-file-validate %{buildroot}%{_datadir}/applications/%{name}.desktop

%files
%license epl-2.0.html
%{_bindir}/%{name}
%{rodindir}
%{_datadir}/icons/hicolor/32x32/apps/%{name}.png
%{_datadir}/icons/hicolor/48x48/apps/%{name}.png
%{_datadir}/applications/%{name}.desktop

%changelog
* Thu Jun 18 2026 Denis Efremov <efremov@linux.com> - 3.9-3
- Force light theme (Rodin has no dark theme): pin e4 CSS theme in rodin.ini
  and export GTK_THEME=Adwaita:light in the launcher

* Sun Jun 14 2026 Denis Efremov <efremov@linux.com> - 3.9-2
- Install icon into hicolor theme as PNG (fixes missing icon in GNOME)

* Sun Jun 07 2026 Denis Efremov <efremov@linux.com> - 3.9-1
- Initial package: repackage the upstream Linux build
