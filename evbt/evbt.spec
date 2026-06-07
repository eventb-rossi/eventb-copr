Name:           evbt
Version:        1.5.0
Release:        1%{?dist}
Summary:        Event-B tool for code generation and documentation (EventBTool)

License:        AGPL-3.0-or-later
URL:            https://codeberg.org/viklauverk/EventBTool
# Upstream ships a single self-executable jar as the release asset (a shell
# stub prepended to the jar). Store it under #/ with a .jar name; `java -jar`
# reads the zip from the end, so the stub is ignored.
Source0:        https://github.com/viklauverk/EventBTool/releases/download/v%{version}/evbt#/%{name}-%{version}.jar
# The jar bundles no license text; ship the upstream AGPL from the GitHub tag.
Source1:        https://raw.githubusercontent.com/viklauverk/EventBTool/v%{version}/LICENSE

BuildArch:      noarch
# javapackages-filesystem defines the %%{_javadir} macro and owns /usr/share/java.
BuildRequires:  javapackages-filesystem
# Prebuilt jar: no compilation. EventBTool requires Java 22 or later.
Requires:       java-headless >= 1:22
Requires:       javapackages-filesystem

%description
EventBTool (evbt) reads Event-B models and generates source code and
documentation from them. It is distributed as a single self-contained jar
(a Spring Boot application launcher).

%prep
%autosetup -c -T
cp -p %{SOURCE1} LICENSE

%build
# Nothing to build; the upstream release is a ready-to-run jar.

%install
install -Dpm 0644 %{SOURCE0} %{buildroot}%{_javadir}/%{name}/%{name}.jar

# Wrapper pinning /usr/bin/java (the Requires guarantees Java >= 22).
install -dm 0755 %{buildroot}%{_bindir}
cat > %{buildroot}%{_bindir}/%{name} <<'EOF'
#!/bin/sh
exec /usr/bin/java -jar %{_javadir}/evbt/evbt.jar "$@"
EOF
chmod 0755 %{buildroot}%{_bindir}/%{name}

%files
%license LICENSE
%dir %{_javadir}/%{name}
%{_javadir}/%{name}/%{name}.jar
%{_bindir}/%{name}

%changelog
* Sun Jun 07 2026 Denis Efremov <efremov@linux.com> - 1.5.0-1
- Initial package
