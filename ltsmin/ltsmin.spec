# Upstream ships already-stripped executables without matching debug sources.
# Do not emit an empty, unusable debuginfo package; all BRP checks remain active.
%global debug_package %{nil}
%global probextdir %{_prefix}/lib/prob/lib

Name:           ltsmin
Version:        3.0.2
Release:        1%{?dist}
Summary:        High-performance language-independent model checking tools

# The binary-release component and static-link inventory is documented in
# Source19. DiVinE's complete multi-component notice is shipped as Source14.
License:        0BSD AND Apache-2.0 AND BSD-2-Clause AND BSD-3-Clause AND BSL-1.0 AND GPL-2.0-only AND GPL-2.0-or-later AND GPL-3.0-or-later AND (GPL-3.0-or-later WITH GCC-exception-3.1) AND LGPL-2.1-only AND LGPL-2.1-or-later AND LGPL-3.0-or-later AND (LGPL-3.0-or-later WITH Independent-modules-exception) AND LicenseRef-DiVinE-Murphi AND MIT AND MPL-2.0 AND Zlib
URL:            https://ltsmin.utwente.nl/
# Repackage the complete official x86_64 build. The matching source release is
# included for its generated manual pages, bash completion and license notices.
Source0:        https://github.com/utwente-fmt/ltsmin/releases/download/v%{version}/%{name}-v%{version}-linux.tgz
Source1:        https://github.com/utwente-fmt/ltsmin/releases/download/v%{version}/%{name}-v%{version}-source.tgz
# The binary/source releases omit the full texts for these bundled components.
Source2:        https://raw.githubusercontent.com/spdx/license-list-data/main/text/GPL-2.0-or-later.txt#/%{name}-%{version}-GPL-2.0-or-later.txt
Source3:        https://raw.githubusercontent.com/spdx/license-list-data/main/text/Apache-2.0.txt#/%{name}-%{version}-Apache-2.0.txt
Source4:        https://raw.githubusercontent.com/spdx/license-list-data/main/text/BSL-1.0.txt#/%{name}-%{version}-BSL-1.0.txt
Source5:        https://raw.githubusercontent.com/spdx/license-list-data/main/text/BSD-2-Clause.txt#/%{name}-%{version}-BSD-2-Clause.txt
Source6:        https://raw.githubusercontent.com/spdx/license-list-data/main/text/GPL-3.0-or-later.txt#/%{name}-%{version}-GPL-3.0-or-later.txt
Source7:        https://raw.githubusercontent.com/spdx/license-list-data/main/text/GCC-exception-3.1.txt#/%{name}-%{version}-GCC-exception-3.1.txt
Source8:        https://raw.githubusercontent.com/spdx/license-list-data/main/text/LGPL-2.1-or-later.txt#/%{name}-%{version}-LGPL-2.1-or-later.txt
Source9:        https://raw.githubusercontent.com/spdx/license-list-data/main/text/LGPL-3.0-or-later.txt#/%{name}-%{version}-LGPL-3.0-or-later.txt
Source10:       https://raw.githubusercontent.com/spdx/license-list-data/main/text/MIT.txt#/%{name}-%{version}-MIT.txt
Source11:       https://raw.githubusercontent.com/spdx/license-list-data/main/text/MPL-2.0.txt#/%{name}-%{version}-MPL-2.0.txt
Source12:       https://raw.githubusercontent.com/spdx/license-list-data/main/text/Zlib.txt#/%{name}-%{version}-Zlib.txt
Source13:       https://raw.githubusercontent.com/spdx/license-list-data/main/text/0BSD.txt#/%{name}-%{version}-0BSD.txt
# Exact component notices omitted from the binary and source release archives.
Source14:       https://raw.githubusercontent.com/utwente-fmt/divine2/1.3/COPYING#/%{name}-%{version}-DiVinE-COPYING
Source15:       https://raw.githubusercontent.com/utwente-fmt/spins/bfca30be3ce81fd77b31b9d47043145ae66ddc96/doc/LICENSE.txt#/%{name}-%{version}-SpinS-LICENSE.txt
Source16:       https://raw.githubusercontent.com/utwente-fmt/spins/bfca30be3ce81fd77b31b9d47043145ae66ddc96/lib/javacc.LICENSE#/%{name}-%{version}-SpinS-JavaCC-LICENSE
Source17:       https://raw.githubusercontent.com/zeromq/zeromq4-1/v4.1.5/README.md#/%{name}-%{version}-ZeroMQ-README.md
Source18:       https://raw.githubusercontent.com/mCRL2org/mCRL2/mcrl2-201707.1/3rd-party/dparser/COPYRIGHT#/%{name}-%{version}-dparser-COPYRIGHT
Source19:       %{name}-%{version}-bundled-components.md

ExclusiveArch:  x86_64
# Used in %%check to exercise the bundled DiVinE helper, which links the
# ncurses 5 ABI and gains an automatic hard dependency on its sonames.
BuildRequires:  ncurses-compat-libs
BuildRequires:  chrpath
BuildRequires:  binutils

# The official Linux release is mostly statically linked. These versions are
# taken from the v3.0.2 release build scripts and Ubuntu 14.04 build root; see
# Source19 for the complete audit and license mapping.
Provides:       bundled(boost) = 1.54.0
Provides:       bundled(czmq) = 3.0.2
Provides:       bundled(dparser) = 1.26
Provides:       bundled(gcc-runtime) = 7.3.0
Provides:       bundled(gmp) = 5.1.3
Provides:       bundled(hwloc) = 1.8
Provides:       bundled(libltdl) = 2.4.2
Provides:       bundled(libnuma) = 2.0.9
Provides:       bundled(libxml2) = 2.9.1
Provides:       bundled(mcrl2) = 201707.1
Provides:       bundled(popt) = 1.16
Provides:       bundled(spot) = 2.3.3
Provides:       bundled(spot-buddy) = 2.3.3
Provides:       bundled(sylvan) = 1.1.1
Provides:       bundled(viennacl) = 1.7.1
Provides:       bundled(xz-libs) = 5.1.1alpha
Provides:       bundled(zeromq) = 4.1.5
Provides:       bundled(zlib) = 1.2.8

# The bundled DiVinE helper's automatically generated libncurses.so.5 and
# libtinfo.so.5 requirements resolve to ncurses-compat-libs on Fedora.
# Optional language front-ends: prob2lts-* launches probcli through the CZMQ
# protocol, while SpinS uses Java to emit C and GCC to compile the model.
Recommends:     prob
Recommends:     java-headless
Recommends:     gcc

%description
LTSmin provides language-independent tools for manipulating and analyzing
labeled transition systems. It includes sequential, multi-core, symbolic and
distributed model-checking backends, with front-ends for formats and tools
including ETF, DVE, Promela, PNML, mCRL2 and ProB.

This package repackages the complete official Linux binary release. The public
PINS development headers are intentionally not included.

%prep
# Source1 is unpacked inside the binary release directory so its generated
# documentation can be installed without building the legacy source tree.
%autosetup -n v%{version} -a 1

# Surface all applicable license texts for the binary RPM.
cp -p share/doc/%{name}/COPYING LICENSE-LTSmin
cp -p %{name}-%{version}/ltl2ba/README LICENSE-ltl2ba
cp -p %{SOURCE2} LICENSE-GPL-2.0-or-later
cp -p %{SOURCE3} LICENSE-Apache-2.0
cp -p %{SOURCE4} LICENSE-BSL-1.0
cp -p %{SOURCE5} LICENSE-BSD-2-Clause
cp -p %{SOURCE6} LICENSE-GPL-3.0-or-later
cp -p %{SOURCE7} LICENSE-GCC-exception-3.1
cp -p %{SOURCE8} LICENSE-LGPL-2.1-or-later
cp -p %{SOURCE9} LICENSE-LGPL-3.0-or-later
cp -p %{SOURCE10} LICENSE-MIT
cp -p %{SOURCE11} LICENSE-MPL-2.0
cp -p %{SOURCE12} LICENSE-Zlib
cp -p %{SOURCE13} LICENSE-0BSD
cp -p %{SOURCE14} LICENSE-DiVinE
cp -p %{SOURCE15} LICENSE-SpinS
cp -p %{SOURCE16} LICENSE-SpinS-JavaCC
cp -p %{SOURCE17} LICENSE-ZeroMQ-exception
cp -p %{SOURCE18} LICENSE-dparser
cp -p %{SOURCE19} BUNDLED-COMPONENTS.md

%build
# Nothing to build; this is the complete upstream binary distribution.

%install
install -dm 0755 %{buildroot}%{_bindir}
install -pm 0755 bin/* %{buildroot}%{_bindir}/
# Remove build-host RPATHs from mCRL2 helpers and LTSmin's mCRL2 front-ends.
# The packaged programs resolve all remaining dependencies through the system
# loader and do not install private libraries.
for command in txt2lps txt2pbes \
               lps2lts-seq lps2lts-mc lps2lts-sym lps2lts-dist \
               pbes2lts-seq pbes2lts-mc pbes2lts-sym pbes2lts-dist; do
    chrpath --delete "%{buildroot}%{_bindir}/$command"
done
install -Dpm 0644 share/%{name}/spins.jar \
    %{buildroot}%{_datadir}/%{name}/spins.jar

# Install release-matched manual pages for every shipped command that has one,
# plus the shared LTSmin and ETF format documentation.
docdir=%{name}-%{version}/doc
for command in bin/*; do
    page="$docdir/$(basename "$command").1"
    if [ -f "$page" ]; then
        install -Dpm 0644 "$page" \
            "%{buildroot}%{_mandir}/man1/$(basename "$page")"
    fi
done
for page in "$docdir"/ltsmin.7 "$docdir"/ltsmin-*.5 "$docdir"/etf.5; do
    install -Dpm 0644 "$page" \
        "%{buildroot}%{_mandir}/man${page##*.}/$(basename "$page")"
done

install -Dpm 0644 %{name}-%{version}/contrib/bash-completion/%{name} \
    %{buildroot}%{_datadir}/bash-completion/completions/%{name}

# ProB discovers an installed LTSmin through these three entry points in its
# private extension directory. Keep them as links to the canonical commands;
# the directory is harmless when the weakly recommended prob package is absent.
install -dm 0755 %{buildroot}%{probextdir}
ln -s %{_bindir}/prob2lts-seq \
    %{buildroot}%{probextdir}/prob2lts-seq
ln -s %{_bindir}/prob2lts-sym \
    %{buildroot}%{probextdir}/prob2lts-sym
ln -s %{_bindir}/ltsmin-printtrace \
    %{buildroot}%{probextdir}/ltsmin-printtrace

# Keep the large command suite maintainable without using a shared-directory
# glob in %%files (which rpmlint correctly discourages).
for command in bin/*; do
    echo "%{_bindir}/$(basename "$command")"
done > %{name}.files

%check
# Cover the principal backend families, every binary modified by the RPATH
# cleanup, and the helper with a non-default compatibility dependency.
for command in ltsmin-convert pins2lts-seq pins2lts-mc pins2lts-sym \
               pins2lts-dist \
               lps2lts-seq lps2lts-mc lps2lts-sym lps2lts-dist \
               pbes2lts-seq pbes2lts-mc pbes2lts-sym pbes2lts-dist \
               txt2lps txt2pbes divine; do
    if output="$(%{buildroot}%{_bindir}/$command --version 2>&1)"; then
        status=0
    else
        status=$?
    fi
    test -n "$output"
    if [ "$command" = divine ]; then
        # DiVinE follows the conventional successful --version status.
        test "$status" -eq 0
    elif [ "$command" = txt2lps ] || [ "$command" = txt2pbes ]; then
        # The standalone mCRL2 helpers also use a conventional status.
        test "$status" -eq 0
        printf '%%s\n' "$output" | grep -Fq 'mCRL2 toolset 201707.1'
    else
        # LTSmin 3.0.2 reports --version through its fatal-exit path.
        test "$status" -eq 255
        test "$(printf '%%s\n' "$output" | tail -n 1)" = "v%{version}"
    fi
    printf '%%s\n' "$output" | head -n 1
done

# No executable may retain an RPATH or RUNPATH after installation.
for command in %{buildroot}%{_bindir}/*; do
    if readelf --file-header "$command" >/dev/null 2>&1; then
        ! readelf --dynamic "$command" 2>/dev/null | \
            grep -Eq '\((RPATH|RUNPATH)\)'
    fi
done

for link in prob2lts-seq prob2lts-sym ltsmin-printtrace; do
    test -L "%{buildroot}%{probextdir}/$link"
    test "$(readlink "%{buildroot}%{probextdir}/$link")" = "%{_bindir}/$link"
done

%files -f %{name}.files
%license LICENSE-LTSmin LICENSE-ltl2ba LICENSE-GPL-2.0-or-later
%license LICENSE-Apache-2.0 LICENSE-BSL-1.0 LICENSE-BSD-2-Clause
%license LICENSE-GPL-3.0-or-later LICENSE-GCC-exception-3.1
%license LICENSE-LGPL-2.1-or-later LICENSE-LGPL-3.0-or-later
%license LICENSE-MIT LICENSE-MPL-2.0 LICENSE-Zlib LICENSE-0BSD
%license LICENSE-DiVinE LICENSE-SpinS LICENSE-SpinS-JavaCC
%license LICENSE-ZeroMQ-exception LICENSE-dparser
%doc share/doc/%{name}/AUTHORS share/doc/%{name}/README.md
%doc share/doc/%{name}/CODING-STANDARDS
%doc BUNDLED-COMPONENTS.md
%{_datadir}/%{name}/
%{_datadir}/bash-completion/completions/%{name}
%dir %{_prefix}/lib/prob
%dir %{probextdir}
%{probextdir}/prob2lts-seq
%{probextdir}/prob2lts-sym
%{probextdir}/ltsmin-printtrace
%{_mandir}/man1/*
%{_mandir}/man5/*
%{_mandir}/man7/*

%changelog
* Sat Jul 18 2026 Denis Efremov <efremov@linux.com> - 3.0.2-1
- Initial package: repackage the complete upstream Linux release
