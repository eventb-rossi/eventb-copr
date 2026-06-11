Name:           prob2-ui
Version:        1.3.1
Release:        1%{?dist}
Summary:        JavaFX-based animator and model checker built on ProB

License:        EPL-2.0
URL:            https://prob.hhu.de/
# Multi-platform fat jar: it bundles the JavaFX runtime for every platform, so a
# plain JRE is enough. ~235 MB; fetched at build time by spectool (not committed).
Source0:        https://stups.hhu-hosting.de/downloads/prob2/%{version}/prob2-ui-%{version}-multi.jar
Source1:        prob2-ui.desktop
# The jar bundles only its dependencies' licences; ship the project's own EPL-2.0
# text from the GitHub tag.
Source2:        https://raw.githubusercontent.com/hhu-stups/prob2_ui/v%{version}/LICENSE

BuildArch:      noarch
BuildRequires:  javapackages-filesystem
BuildRequires:  desktop-file-utils
BuildRequires:  unzip
# JavaFX GUI: needs a full JRE (not -headless). The bundled JavaFX natives load
# system libraries gtk3 does not pull in: the glass GTK windowing backend
# (libglassgtk3.so) needs libXtst, and the es2 hardware-rendering pipeline
# (libprism_es2.so) needs libGL and libXxf86vm. ProB2-UI requires Java 21+.
Requires:       java >= 1:21
Requires:       gtk3
Requires:       libXtst
Requires:       mesa-libGL
Requires:       libXxf86vm
Requires:       javapackages-filesystem
Requires:       hicolor-icon-theme

%description
ProB2-UI is a modern JavaFX user interface for the ProB animator, constraint
solver and model checker. It supports the B method, Event-B, CSP-M, TLA+ and Z,
offering interactive animation, model checking, LTL/CTL verification, trace
recording and replay, and visualisation. On first use it downloads the matching
ProB kernel into ~/.prob.

%prep
%autosetup -c -T
cp -p %{SOURCE2} LICENSE

%build
# Nothing to build; the upstream release is a ready-to-run jar.

%install
install -Dpm 0644 %{SOURCE0} %{buildroot}%{_javadir}/%{name}/%{name}.jar

install -dm 0755 %{buildroot}%{_bindir}
# --enable-native-access=ALL-UNNAMED silences the warning from the bundled JavaFX
# native loader and pre-empts the future JDK hard block on restricted native
# methods; supported by all JDKs >= 17.
cat > %{buildroot}%{_bindir}/%{name} <<'EOF'
#!/bin/sh
exec /usr/bin/java --enable-native-access=ALL-UNNAMED -jar %{_javadir}/%{name}/%{name}.jar "$@"
EOF
chmod 0755 %{buildroot}%{_bindir}/%{name}

# Application icon, extracted from the jar (256x256 PNG).
install -dm 0755 %{buildroot}%{_datadir}/icons/hicolor/256x256/apps
unzip -p %{SOURCE0} de/prob2/ui/ProB_Icon.png \
    > %{buildroot}%{_datadir}/icons/hicolor/256x256/apps/%{name}.png

desktop-file-install --dir=%{buildroot}%{_datadir}/applications %{SOURCE1}

%check
desktop-file-validate %{buildroot}%{_datadir}/applications/%{name}.desktop

%files
%license LICENSE
%dir %{_javadir}/%{name}
%{_javadir}/%{name}/%{name}.jar
%{_bindir}/%{name}
%{_datadir}/icons/hicolor/256x256/apps/%{name}.png
%{_datadir}/applications/%{name}.desktop

%changelog
* Thu Jun 11 2026 Denis Efremov <efremov@linux.com> - 1.3.1-1
- Initial package: repackage the upstream multi-platform fat jar
