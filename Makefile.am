# Clean this files on "make distclean"
DISTCLEANFILES = \
    intltool-extract \
    intltool-merge \
    intltool-update

# Do not install these files
EXTRA_DIST = \
    $(TESTS) \
    intltool-extract.in \
    intltool-merge.in \
    intltool-update.in \
    audio-convert-mod.spec.in \
    audio-convert-mod.spec \
    AUTHORS \
    ChangeLog \
    COPYING \
    INSTALL \
    NEWS \
    README \
    sample-audio.tar.bz2

SUBDIRS = \
    bin \
    po \
    src \
    src/audio_convert_mod
execdir = $(sbindir)
testsubdir = tests

TESTS_ENVIRONMENT = \
    top_builddir=$(top_builddir)

TESTS = \
    encode.py.test \
    decode.py.test

clean-local:
	rm -rf $(testsubdir)/*

rpm: dist
	@(rpmbuild -ta 	audio-convert-mod-$(PACKAGE_VERSION).tar.bz2)

srpm: dist
	@(rpmbuild -ts audio-convert-mod-$(PACKAGE_VERSION).tar.bz2)

CVS_PKGVERSION=`echo $(PACKAGE_VERSION) | sed -e 's/\./_/g'`
CVSTAG=$(PACKAGE_NAME)-$(CVS_PACKAGEVERSION)
tag:
	@cvs tag -F $(CVSTAG)

