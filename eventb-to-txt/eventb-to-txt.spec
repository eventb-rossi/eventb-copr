%global pkg_name eventb_to_txt

Name:           eventb-to-txt
Version:        1.7
Release:        1%{?dist}
Summary:        Convert Rodin Event-B models to CamilleX plain-text format

License:        MIT
URL:            https://github.com/eventb-rossi/eventb-to-txt
Source0:        https://files.pythonhosted.org/packages/86/3e/c74b2cfefbabd4476e37fd05afd1fec2934efff4cea359bdbb821565c2b3/%{pkg_name}-%{version}.tar.gz

BuildArch:      noarch
BuildRequires:  python3-devel
BuildRequires:  pyproject-rpm-macros

%description
eventb-to-txt converts Event-B machines and contexts (Rodin .bum and .buc
files, or a zip archive of them) into plain text. The generated text is itself
a valid Event-B model in CamilleX notation that can be opened in the CamilleX
editor. Compatible with models created by Rodin 3.0 and later.

%prep
%autosetup -n %{pkg_name}-%{version}
# __main__.py carries a shebang but is imported as a module (run through the
# console script or `python -m eventb_to_txt`); drop it so it is not flagged as
# a non-executable script under site-packages.
sed -i '1{/^#!/d}' %{pkg_name}/__main__.py

%generate_buildrequires
%pyproject_buildrequires

%build
%pyproject_wheel

%install
%pyproject_install
%pyproject_save_files -l %{pkg_name}

%check
%pyproject_check_import
# The console entry point must report the packaged version. Invoke the installed
# script (not `python -m`): the version lookup keys off the top-level import
# name, which is only "eventb_to_txt" when imported through the entry point.
PYTHONPATH=%{buildroot}%{python3_sitelib} %{buildroot}%{_bindir}/%{name} --version | \
    grep -qx 'eventb-to-txt %{version}'

%files -f %{pyproject_files}
%doc README.md
%{_bindir}/eventb-to-txt

%changelog
* Sun Jun 07 2026 Denis Efremov <efremov@linux.com> - 1.7-1
- Initial package
