# Copr SRPM entry point.
#
# Copr (and the top-level Makefile) invoke this from inside a package
# subdirectory as:
#
#     make -f <clone>/.copr/Makefile srpm outdir=<dir> spec=<name>.spec
#
# It downloads the remote Source files referenced by the spec and builds a
# source RPM. Local sources committed next to the spec (wrapper scripts,
# .desktop files, gradle init scripts) and the downloaded ones share the
# package directory, which is used as %_sourcedir.

spec   ?= $(firstword $(wildcard *.spec))
outdir ?= $(CURDIR)

srpm:
	# Copr's SRPM builder is minimal; install the tooling when missing.
	command -v spectool >/dev/null 2>&1 || dnf -y install rpm-build rpmdevtools
	spectool -g -R --define "_sourcedir $(CURDIR)" $(spec)
	rpmbuild -bs \
	  --define "_sourcedir $(CURDIR)" \
	  --define "_srcrpmdir $(outdir)" \
	  --define "_topdir $(CURDIR)/.rpmbuild" \
	  $(spec)

.PHONY: srpm
