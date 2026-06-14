Name:           eventb-checker
Version:        1.6
Release:        1%{?dist}
Summary:        Standalone validator for Event-B models, no Rodin installation required

License:        MIT
URL:            https://github.com/eventb-rossi/eventb-checker
Source0:        https://github.com/eventb-rossi/eventb-checker/archive/refs/tags/v%{version}.tar.gz#/%{name}-%{version}.tar.gz

BuildArch:      noarch
# Built from source with Gradle. The build downloads the Gradle distribution
# and Maven dependencies, so the Copr project must have network access enabled.
# The Gradle toolchain pins Java 21 with auto-download disabled, so a JDK 21
# must be present; Fedora ships only JDK 25, hence Temurin from Adoptium.
BuildRequires:  temurin-21-jdk
BuildRequires:  javapackages-filesystem
# The resulting shadow jar runs on any modern JDK.
Requires:       java-headless >= 1:21
Requires:       javapackages-filesystem

%description
eventb-checker validates Event-B models (Rodin .bum/.buc/.eventb files, Camille
text, or a zip archive of them) and reports whether they are well-formed and
type-correct, without requiring a Rodin installation. It is a self-contained
command-line tool.

%prep
%autosetup -n %{name}-%{version}

%build
export JAVA_HOME=/usr/lib/jvm/java-21-temurin-jdk
export GRADLE_USER_HOME="$(pwd)/.gradle"
./gradlew --no-daemon shadowJar -x test

%install
install -Dpm 0644 build/libs/%{name}-%{version}-all.jar \
    %{buildroot}%{_javadir}/%{name}/%{name}.jar

# Wrapper in %{_bindir}. --enable-native-access=ALL-UNNAMED silences the JNA
# native-access warnings emitted by the bundled Rodin AST libraries (and
# pre-empts their hard removal in a future JDK).
install -dm 0755 %{buildroot}%{_bindir}
cat > %{buildroot}%{_bindir}/%{name} <<'EOF'
#!/bin/sh
exec /usr/bin/java --enable-native-access=ALL-UNNAMED -jar %{_javadir}/eventb-checker/eventb-checker.jar "$@"
EOF
chmod 0755 %{buildroot}%{_bindir}/%{name}

%files
%license LICENSE
%doc README.md
%dir %{_javadir}/%{name}
%{_javadir}/%{name}/%{name}.jar
%{_bindir}/%{name}

%changelog
* Sun Jun 14 2026 Denis Efremov <efremov@linux.com> - 1.6-1
- Update to 1.6

* Thu Jun 11 2026 Denis Efremov <efremov@linux.com> - 1.5-1
- Update to 1.5

* Sun Jun 07 2026 Denis Efremov <efremov@linux.com> - 1.3-1
- Initial package
