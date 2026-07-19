Name:           eventb-animate
Version:        6.1
Release:        1%{?dist}
Summary:        Animate Event-B models with the ProB model checker, no Rodin required

License:        Apache-2.0
URL:            https://github.com/eventb-rossi/eventb-animate
Source0:        https://github.com/eventb-rossi/eventb-animate/archive/refs/tags/v%{version}.tar.gz#/%{name}-%{version}.tar.gz

BuildArch:      noarch
# Built from source with Gradle. The build downloads the Gradle distribution
# and Maven dependencies (including the ProB kernel), so the Copr project must
# have network access enabled. The Gradle toolchain pins Java 21 with
# auto-download disabled, so a JDK 21 must be present; Fedora ships only JDK 25,
# hence Temurin from Adoptium.
BuildRequires:  temurin-21-jdk
BuildRequires:  javapackages-filesystem
# The resulting shadow jar runs on any modern JDK.
Requires:       java-headless >= 1:21
Requires:       javapackages-filesystem

%description
eventb-animate animates Event-B models with the ProB model checker without a
Rodin installation: it performs random animation, checks invariants and
coverage, saves and replays JSON traces, exports model visualisations, and
converts Event-B models to classical B. It is a self-contained command-line
tool; the model path may be a .bum/.buc file, a .zip archive, or a Rodin
project directory.

%prep
%autosetup -n %{name}-%{version}

%build
export JAVA_HOME=/usr/lib/jvm/java-21-temurin-jdk
export GRADLE_USER_HOME="$(pwd)/.gradle"
./gradlew --no-daemon shadowJar -x test

%install
install -Dpm 0644 build/libs/%{name}-%{version}.jar \
    %{buildroot}%{_javadir}/%{name}/%{name}.jar

# Wrapper in %{_bindir}. --sun-misc-unsafe-memory-access=allow silences the
# sun.misc.Unsafe deprecation warnings the bundled Guice (ProB kernel) emits on
# JDK 23+; the option is itself recognised only by JDK 23 and newer.
install -dm 0755 %{buildroot}%{_bindir}
cat > %{buildroot}%{_bindir}/%{name} <<'EOF'
#!/bin/sh
exec /usr/bin/java --sun-misc-unsafe-memory-access=allow -jar %{_javadir}/eventb-animate/eventb-animate.jar "$@"
EOF
chmod 0755 %{buildroot}%{_bindir}/%{name}

%check
# Validate the built jar offline: picocli answers --version before the ProB
# kernel (which would fetch probcli at runtime) is touched. The build JDK is 21,
# which does not accept --sun-misc-unsafe-memory-access, so invoke java plainly.
/usr/lib/jvm/java-21-temurin-jdk/bin/java -jar \
    %{buildroot}%{_javadir}/%{name}/%{name}.jar --version | grep -F "%{name} %{version}"

%files
%license LICENSE
%doc README.md
%dir %{_javadir}/%{name}
%{_javadir}/%{name}/%{name}.jar
%{_bindir}/%{name}

%changelog
* Sun Jul 19 2026 Denis Efremov <efremov@linux.com> - 6.1-1
- Update to 6.1

* Tue Jul 07 2026 Denis Efremov <efremov@linux.com> - 6.0-1
- Update to 6.0

* Thu Jun 25 2026 Denis Efremov <efremov@linux.com> - 5.1-1
- Update to 5.1

* Sun Jun 07 2026 Denis Efremov <efremov@linux.com> - 5.0-1
- Initial package
