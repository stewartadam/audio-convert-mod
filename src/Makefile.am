ACMDATA_FILES = \
    BugReport.glade \
    audio-convert-mod.glade \
    audio-convert-mod-kde3.desktop \
    audio-convert-mod-kde4.desktop \
    acm-runapp.pyw

EXTRA_DIST = \
    $(ACMDATA_FILES) \
    audio-convert-mod.desktop

acmdatadir = $(pkgdatadir)
acmdata_DATA = $(ACMDATA_FILES)

install-data-local:
	$(mkinstalldirs) $(DESTDIR)$(datadir)/applications
	$(INSTALL) -m 644 audio-convert-mod.desktop $(DESTDIR)$(datadir)/applications/audio-convert-mod.desktop

uninstall-local:
	rm -f $(DESTDIR)$(datadir)/applications/audio-convert-mod.desktop

clean:
	rm -f *~ *.bak *.gladep
