%global rodindir   %{_prefix}/lib/%{name}
# Rodin-Bundle release tag, and the build id its tarball name embeds (base
# version + commit date/hash qualifier, not derivable from the tag). Both are
# rewritten by the version-check workflow on bumps.
%global tag        v3.10.0-2611
%global buildid    3.10.0.202611160826-a263a14
%global tarball    rodin-%{buildid}-rossi-linux.gtk.x86_64.tar.gz

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
# Tag vX.Y.Z-YYMM[.N] -> X.Y.Z^YYMM[.N]: sorts after the plain Rodin X.Y.Z the
# bundle is built from (and after the vanilla 3.10 this package used to ship).
Version:        3.10.0^2611
Release:        1%{?dist}
Summary:        IDE for formal modelling and verification with Event-B

# Eclipse platform and the PO Cleaner / Rossi bridge plug-ins are EPL-2.0; the
# Rodin core and ProB plug-ins are EPL-1.0; the bundled SMT solvers are MIT (Z3)
# and BSD-3-Clause (CVC3, CVC4, veriT).
License:        EPL-1.0 AND EPL-2.0 AND MIT AND BSD-3-Clause
URL:            https://github.com/eventb-rossi/Rodin-Bundle
# Rodin-Bundle ships a single Linux build, for x86_64.
Source0:        https://github.com/eventb-rossi/Rodin-Bundle/releases/download/%{tag}/%{tarball}
Source1:        rodin.desktop

ExclusiveArch:  x86_64
BuildRequires:  desktop-file-utils
BuildRequires:  ImageMagick

# Rodin bundles no JRE and requires Java 21 or newer.
Requires:       java-headless >= 1:21
Requires:       gtk3
Requires:       hicolor-icon-theme
# The bundled ProB's cspmf links libgmp; its libczmq/ltsmin/zmq_rpc link libuuid.
Requires:       gmp
Requires:       libuuid
# Browser-backed views (e.g. some help/preview widgets) need WebKitGTK.
Recommends:     webkit2gtk4.1

%description
The Rodin Platform is an Eclipse-based IDE for Event-B that provides effective
support for refinement and mathematical proof. This package repackages the
eventb-rossi Rodin Bundle: Rodin with parallel automatic proving, the SMT
solvers, ProB, the Proof Obligation Cleaner and the Rossi language-server
bridge. It bundles no Java runtime and needs a system Java 21 or newer.

%prep
%autosetup -n %{name}
cp -p "$(find features -name 'epl-2.0.html' | head -1)" epl-2.0.html

# Rodin's Eclipse UI has no working dark theme: pin the e4 CSS light theme so
# Eclipse-drawn widgets stay light regardless of the desktop theme. The property
# must follow -vmargs to reach the JVM.
sed -i '/^-vmargs$/a -Dorg.eclipse.e4.ui.css.swt.theme=org.eclipse.e4.ui.css.theme.e4_default' rodin.ini

%build
# Nothing to build; this is a repackaged binary distribution.

%install
install -dm 0755 %{buildroot}%{rodindir}
cp -a . %{buildroot}%{rodindir}/
rm -f %{buildroot}%{rodindir}/epl-2.0.html

# The bundled ProB plug-in ships its native tools without the executable bit,
# and probcli.sh restores it with `chmod a+x` under `set -e`. Against this
# root-owned install that chmod fails for every non-root user (even when the
# bit is already set: only the owner may chmod), so ProB never starts. Mark
# its ELF executables and #! scripts 0755, and make that chmod best-effort.
probdir=$(echo %{buildroot}%{rodindir}/plugins/de.prob.core_*/prob/linux64)
test -f "$probdir/probcli.sh"
for f in "$probdir"/* "$probdir"/lib/*; do
    [ -f "$f" ] && [ ! -L "$f" ] || continue
    case "$f" in *.so|*.so.*) continue ;; esac
    case "$(od -An -tx1 -N4 "$f" | tr -d ' \n')" in
        7f454c46|2321*) chmod 0755 "$f" ;;
    esac
done
sed -i -e '/^[[:space:]]*chmod a+x /s|$| 2>/dev/null \|\| :|' "$probdir/probcli.sh"
grep -q 'chmod a+x .* || :$' "$probdir/probcli.sh" || {
    echo "probcli.sh: chmod a+x line not found, ProB patch did not apply" >&2
    exit 1
}

# Launcher wrapper. The Eclipse native launcher resolves its install tree from
# /proc/self/exe, so exec'ing the real binary by absolute path is sufficient.
install -dm 0755 %{buildroot}%{_bindir}
cat > %{buildroot}%{_bindir}/%{name} <<'EOF'
#!/bin/sh
# Rodin has no working dark theme; force a light GTK theme so native SWT/GTK
# widgets match the light e4 CSS theme pinned in rodin.ini.
export GTK_THEME=Adwaita:light
exec /usr/lib/rodin/rodin "$@"
EOF
chmod 0755 %{buildroot}%{_bindir}/%{name}

# Icon: convert the upstream 32x32 XPM to PNG and install into the hicolor theme.
for size in 32 48; do
    install -dm 0755 %{buildroot}%{_datadir}/icons/hicolor/${size}x${size}/apps
    magick convert -resize ${size}x${size} icon.xpm \
        %{buildroot}%{_datadir}/icons/hicolor/${size}x${size}/apps/%{name}.png
done
desktop-file-install --dir=%{buildroot}%{_datadir}/applications %{SOURCE1}

%posttrans
/usr/bin/gtk-update-icon-cache -f -t %{_datadir}/icons/hicolor &>/dev/null || :

%postun
if [ $1 -eq 0 ]; then
    /usr/bin/gtk-update-icon-cache -f -t %{_datadir}/icons/hicolor &>/dev/null || :
fi

%check
desktop-file-validate %{buildroot}%{_datadir}/applications/%{name}.desktop

%files
%license epl-2.0.html
%{_bindir}/%{name}
%{rodindir}
%{_datadir}/icons/hicolor/32x32/apps/%{name}.png
%{_datadir}/icons/hicolor/48x48/apps/%{name}.png
%{_datadir}/applications/%{name}.desktop

%changelog
* Mon Nov 16 2026 Denis Efremov <efremov@linux.com> - 3.10.0^2611-1
- Switch to the eventb-rossi Rodin Bundle (v3.10.0-2611): Rodin 3.10 with
  parallel proving, SMT solvers, ProB, the PO Cleaner and the Rossi bridge
- Mark ProB's native tools executable and make probcli.sh's chmod
  best-effort, so ProB starts for non-root users; require gmp and libuuid

* Thu Jul 02 2026 Denis Efremov <efremov@linux.com> - 3.10-1
- Update to 3.10 (raises the runtime baseline to Java 21)

* Thu Jun 18 2026 Denis Efremov <efremov@linux.com> - 3.9-3
- Force light theme (Rodin has no dark theme): pin e4 CSS theme in rodin.ini
  and export GTK_THEME=Adwaita:light in the launcher

* Sun Jun 14 2026 Denis Efremov <efremov@linux.com> - 3.9-2
- Install icon into hicolor theme as PNG (fixes missing icon in GNOME)

* Sun Jun 07 2026 Denis Efremov <efremov@linux.com> - 3.9-1
- Initial package: repackage the upstream Linux build
