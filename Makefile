# Local development helpers for the rossi-copr package set.
#
# The authoritative SRPM build logic lives in .copr/Makefile (Copr uses the
# same file). This Makefile wraps it for local SRPM builds, mock chroot builds
# and rpmlint.
#
#   make srpm-<pkg>     build a source RPM into build/srpm/
#   make mock-<pkg>     build the package in a mock chroot
#   make lint-<pkg>     rpmlint the spec (and any built rpms)
#   make all-srpm       SRPMs for every package
#   make all-mock       mock-build every package
#   make clean

PKGS        := eventb-to-txt evbt eventb-checker tlc4b b2program eventb-animate rodin rodin-rc atelier-b prob
GRADLE_PKGS := eventb-checker tlc4b b2program eventb-animate   # built from source: need JDK 21 + network

MOCK_ROOT   ?= fedora-44-x86_64
BUILDDIR    := $(abspath build)
SRPMDIR     := $(BUILDDIR)/srpm
COPRMK      := $(CURDIR)/.copr/Makefile

# Adoptium Temurin supplies the JDK 21 the Gradle wrappers require (Fedora ships
# only JDK 25). This mirrors the Copr project's external-repo + network options.
ADOPTIUM_REPO ?= https://packages.adoptium.net/artifactory/rpm/fedora/44/x86_64
ADOPTIUM_ROOT := $(MOCK_ROOT)-adoptium

.PHONY: help all-srpm all-mock clean adoptium-config
help:
	@echo "Targets:  srpm-<pkg> | mock-<pkg> | lint-<pkg> | all-srpm | all-mock | clean"
	@echo "Packages: $(PKGS)"

# --- SRPM -------------------------------------------------------------------
srpm-%:
	@mkdir -p $(SRPMDIR)
	$(MAKE) -C $* -f $(COPRMK) srpm outdir=$(SRPMDIR) spec=$*.spec

# --- Mock build -------------------------------------------------------------
# Gradle packages build in a chroot that layers in the Adoptium repo + network.
$(addprefix mock-,$(GRADLE_PKGS)): MOCK_R   := $(ADOPTIUM_ROOT)
$(addprefix mock-,$(GRADLE_PKGS)): MOCK_NET := --enable-network
$(addprefix mock-,$(GRADLE_PKGS)): adoptium-config

mock-%: srpm-%
	sg mock -c 'mock -r $(or $(MOCK_R),$(MOCK_ROOT)) $(MOCK_NET) --resultdir=$(BUILDDIR)/$* $(SRPMDIR)/$*-*.src.rpm'

# Layer the Adoptium repo onto $(MOCK_ROOT) as a local mock config.
adoptium-config:
	@printf "%s\n" \
	  "include('/etc/mock/$(MOCK_ROOT).cfg')" \
	  "config_opts['root'] = '$(ADOPTIUM_ROOT)'" \
	  "config_opts['dnf.conf'] += '''" \
	  "[adoptium]" \
	  "name=Adoptium Temurin" \
	  "baseurl=$(ADOPTIUM_REPO)" \
	  "enabled=1" \
	  "gpgcheck=0" \
	  "'''" \
	  | sudo tee /etc/mock/$(ADOPTIUM_ROOT).cfg >/dev/null

# --- Lint -------------------------------------------------------------------
lint-%:
	rpmlint $*/$*.spec $(wildcard $(BUILDDIR)/$*/*.rpm)

# --- Aggregates -------------------------------------------------------------
all-srpm: $(addprefix srpm-,$(PKGS))
all-mock: $(addprefix mock-,$(PKGS))
clean:
	rm -rf $(BUILDDIR) $(addsuffix /.rpmbuild,$(PKGS))
