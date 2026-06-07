%global commit      6deb3e17a4cdb97ccc2e2946f7aaafb8e5fa2ba6
%global shortcommit 6deb3e1
%global snapdate    20260512

Name:           b2program
Version:        0.1.0
Release:        0.1.%{snapdate}git%{shortcommit}%{?dist}
Summary:        Multi-target code generator from high-level B to Java, C++, Python, Rust, TS

# B2Program declares no license: it is a read-only mirror of the STUPS GitLab
# repository, which ships none. Upstream makes no license grant, so this is
# recorded as such rather than guessed. Packaged for Copr only; adjust if
# upstream clarifies licensing.
License:        LicenseRef-None
URL:            https://github.com/favu100/b2program
# B2Program publishes no tagged releases (a perpetual 0.1.0-SNAPSHOT), so this
# is pinned to a known-good master commit (dated 2026-05-12).
Source0:        https://github.com/favu100/b2program/archive/%{commit}.tar.gz#/%{name}-%{shortcommit}.tar.gz

BuildArch:      noarch
# Built from source with Gradle (downloads the Gradle distribution + Maven
# dependencies, including a Sonatype snapshot, so the Copr project needs network
# access). The Gradle 9.4 wrapper does not run on JDK 25/26 and B2Program
# targets Java 17 bytecode, so the build uses Temurin 21 from Adoptium.
BuildRequires:  temurin-21-jdk
BuildRequires:  javapackages-filesystem
Requires:       java-headless >= 1:17
Requires:       javapackages-filesystem

%description
B2Program generates source code in Java, C++, Python, Rust or TypeScript from
high-level formal B machines. It is the code-generation backend developed at the
University of Düsseldorf (STUPS group).

%prep
%autosetup -n %{name}-%{commit}

%build
export JAVA_HOME=/usr/lib/jvm/java-21-temurin-jdk
export GRADLE_USER_HOME="$(pwd)/.gradle"
./gradlew --no-daemon fatJar -x test

%install
install -dm 0755 %{buildroot}%{_javadir}/%{name}
install -pm 0644 build/libs/B2Program-all-*.jar \
    %{buildroot}%{_javadir}/%{name}/%{name}.jar

install -dm 0755 %{buildroot}%{_bindir}
cat > %{buildroot}%{_bindir}/%{name} <<'EOF'
#!/bin/sh
exec /usr/bin/java -jar %{_javadir}/b2program/b2program.jar "$@"
EOF
chmod 0755 %{buildroot}%{_bindir}/%{name}

%files
%doc README.md
%dir %{_javadir}/%{name}
%{_javadir}/%{name}/%{name}.jar
%{_bindir}/%{name}

%changelog
* Sun Jun 07 2026 Denis Efremov <efremov@linux.com> - 0.1.0-0.1.20260512git6deb3e1
- Initial package, pinned to master commit 6deb3e1
