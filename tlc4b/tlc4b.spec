Name:           tlc4b
Version:        1.2.3
Release:        1%{?dist}
Summary:        Model-check classical B specifications by translating them to TLA+/TLC

# Upstream ships no LICENSE file; the Maven Central POM declares the Eclipse
# Public License v1.0 (matching the other STUPS tools). The canonical EPL-1.0
# text is bundled as a packaging source.
License:        EPL-1.0
URL:            https://github.com/hhu-stups/tlc4b
Source0:        https://github.com/hhu-stups/tlc4b/archive/refs/tags/%{version}.tar.gz#/%{name}-%{version}.tar.gz
Source1:        fatjar-init.gradle
Source2:        LICENSE-EPL-1.0.txt

BuildArch:      noarch
# Built from source with Gradle (downloads the Gradle distribution + Maven
# dependencies, so the Copr project needs network access). The Gradle 8.14
# wrapper does not run on JDK 25/26 and TLC4B targets Java 8 bytecode, so the
# build uses Temurin 21 from Adoptium (Fedora ships only JDK 25).
BuildRequires:  temurin-21-jdk
BuildRequires:  javapackages-filesystem
# The fat jar runs on any modern JDK.
Requires:       java-headless
Requires:       javapackages-filesystem

%description
TLC4B translates a classical B specification into TLA+, runs the TLC model
checker on it, and translates any counterexample found back to the level of the
B model. It checks invariant violations, deadlocks, assertion errors and
well-definedness.

%prep
%autosetup -n %{name}-%{version}
cp -p %{SOURCE2} LICENSE-EPL-1.0.txt

%build
export JAVA_HOME=/usr/lib/jvm/java-21-temurin-jdk
export GRADLE_USER_HOME="$(pwd)/.gradle"
# TLC4B has no fat-jar task; the init script folds the runtime classpath into
# the standard `jar` task to produce one self-contained runnable jar.
./gradlew --no-daemon -I %{SOURCE1} jar -x test

%install
install -Dpm 0644 build/libs/%{name}-%{version}.jar \
    %{buildroot}%{_javadir}/%{name}/%{name}.jar

install -dm 0755 %{buildroot}%{_bindir}
cat > %{buildroot}%{_bindir}/%{name} <<'EOF'
#!/bin/sh
exec /usr/bin/java -jar %{_javadir}/tlc4b/tlc4b.jar "$@"
EOF
chmod 0755 %{buildroot}%{_bindir}/%{name}

%files
%license LICENSE-EPL-1.0.txt
%doc README.md
%dir %{_javadir}/%{name}
%{_javadir}/%{name}/%{name}.jar
%{_bindir}/%{name}

%changelog
* Sun Jun 07 2026 Denis Efremov <efremov@linux.com> - 1.2.3-1
- Initial package
