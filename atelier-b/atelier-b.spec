%global abver    24.04.2
%global abdir    /opt/atelierb-free-%{abver}
%global vendor_rpm atelierb-free-%{abver}-fedora-39.rpm

# Repackaged prebuilt vendor binaries: keep them intact and do not let rpm
# generate Provides/Requires from the bundled tree under /opt (the external
# deps are declared manually below; the bundled ICU 73 is found at runtime).
%global debug_package %{nil}
%global __brp_strip %{nil}
%global __brp_strip_static_archive %{nil}
%global __brp_strip_comment_note %{nil}
%global __brp_check_rpaths %{nil}
%global __provides_exclude_from ^/opt/.*$
%global __requires_exclude_from ^/opt/.*$

Name:           atelier-b
Version:        %{abver}
Release:        1%{?dist}
Summary:        Atelier B Community Edition - IDE for the B method

# Atelier B Community Edition is proprietary freeware (no open-source license);
# the EULA is shipped under share/doc/licensing/ inside the install tree.
License:        LicenseRef-Atelier-B-Community
URL:            https://www.atelierb.eu/
# Source0 is ClearSy's official Fedora 39 binary RPM, repackaged here.
Source0:        https://www.atelierb.eu/wp-content/uploads/2024/10/%{vendor_rpm}
# Atelier B's binaries link ICU 73 (the soname shipped on Fedora 39); Fedora now
# ships ICU 77, so the three ICU 73 libraries are bundled from the Fedora 39
# package and found through the launcher's LD_LIBRARY_PATH.
Source1:        https://dl.fedoraproject.org/pub/archive/fedora/linux/releases/39/Everything/x86_64/os/Packages/l/libicu-73.2-2.fc39.x86_64.rpm
Source2:        atelier-b.desktop

ExclusiveArch:  x86_64
BuildRequires:  cpio
BuildRequires:  desktop-file-utils

# Qt5 runtime (the vendor GUI is built against Qt 5.15).
Requires:       qt5-qtbase-gui
Requires:       qt5-qtsvg
Requires:       qt5-qtxmlpatterns
Requires:       gmp
Requires:       hicolor-icon-theme

%description
Atelier B is an IDE for the B method: it supports writing B and Event-B models,
type-checking them, generating proof obligations and discharging them with
automatic and interactive provers. This package repackages ClearSy's official
Community Edition Linux build. It bundles the ICU 73 runtime the binaries
require (Fedora ships a newer ICU) and uses the system Qt 5.

%prep
%autosetup -c -T

%build
# Nothing to build; this repackages ClearSy's prebuilt binary distribution.

%install
# Unpack ClearSy's vendor RPM payload into the buildroot (/opt + /usr/lib).
( cd %{buildroot} && rpm2cpio %{SOURCE0} | cpio -idmu --quiet )
# Drop the vendor's build-id symlinks (they would clash with rpm's own handling).
rm -rf %{buildroot}%{_prefix}/lib/.build-id

# Bundle the ICU 73 libraries the binaries need, next to libFastCgiQt.so.
mkdir -p %{_builddir}/icu73
( cd %{_builddir}/icu73 && rpm2cpio %{SOURCE1} | cpio -idmu --quiet )
install -dm 0755 %{buildroot}%{abdir}/lib64
cp -a %{_builddir}/icu73%{_libdir}/libicudata.so.73* %{buildroot}%{abdir}/lib64/
cp -a %{_builddir}/icu73%{_libdir}/libicuuc.so.73*   %{buildroot}%{abdir}/lib64/
cp -a %{_builddir}/icu73%{_libdir}/libicui18n.so.73* %{buildroot}%{abdir}/lib64/

# Launcher: make AtelierB (and its child processes) find the bundled ICU 73.
install -dm 0755 %{buildroot}%{_bindir}
cat > %{buildroot}%{_bindir}/%{name} <<EOF
#!/bin/sh
export LD_LIBRARY_PATH=%{abdir}/lib64\${LD_LIBRARY_PATH:+:\$LD_LIBRARY_PATH}
exec %{abdir}/bin/AtelierB "\$@"
EOF
chmod 0755 %{buildroot}%{_bindir}/%{name}

# Desktop entry and icon.
desktop-file-install --dir=%{buildroot}%{_datadir}/applications %{SOURCE2}
install -Dpm 0644 %{buildroot}%{abdir}/share/icons/AtelierB128.png \
    %{buildroot}%{_datadir}/icons/hicolor/128x128/apps/%{name}.png

# Expose the EULA as the package license too.
cp -p %{buildroot}%{abdir}/share/doc/licensing/LicenseAtelierB_en.pdf .

%check
desktop-file-validate %{buildroot}%{_datadir}/applications/%{name}.desktop

%files
%license LicenseAtelierB_en.pdf
%{abdir}
%{_bindir}/%{name}
%{_datadir}/applications/%{name}.desktop
%{_datadir}/icons/hicolor/128x128/apps/%{name}.png

%changelog
* Sun Jun 07 2026 Denis Efremov <efremov@linux.com> - 24.04.2-1
- Initial package: repackage ClearSy's Community Edition Linux build,
  bundling ICU 73 for current Fedora
