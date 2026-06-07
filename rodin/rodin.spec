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
Release:        1%{?dist}
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
exec /usr/lib/rodin/rodin "$@"
EOF
chmod 0755 %{buildroot}%{_bindir}/%{name}

# Icon and desktop entry.
install -Dpm 0644 icon.xpm %{buildroot}%{_datadir}/pixmaps/%{name}.xpm
desktop-file-install --dir=%{buildroot}%{_datadir}/applications %{SOURCE1}

%check
desktop-file-validate %{buildroot}%{_datadir}/applications/%{name}.desktop

%files
%license epl-2.0.html
%{_bindir}/%{name}
%{rodindir}
%{_datadir}/pixmaps/%{name}.xpm
%{_datadir}/applications/%{name}.desktop

%changelog
* Sun Jun 07 2026 Denis Efremov <efremov@linux.com> - 3.9-1
- Initial package: repackage the upstream Linux build
