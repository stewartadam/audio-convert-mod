ACMPYTHON_FILES = \
    const.py      \
    config.py     \
    formats.py    \
    i18n.py       \
    __init__.py   \
    interface.py  \
    widgets.py    

EXTRA_DIST = \
    $(ACMPYTHON_FILES) \
    __init__.py.in

acmpythondir = $(pkgdatadir)/audio_convert_mod
acmpython_DATA = $(ACMPYTHON_FILES)

uninstall-local:
	rmdir $(DESTDIR)$(pkgdatadir)/audio_convert_mod
	rmdir $(DESTDIR)$(pkgdatadir)
	
#PYTHON_FILES =   \
#    const.py     \
#    config.py    \
#    formats.py   \
#    i18n.py      \
#    __init__.py  \
#    interface.py \
#    widgets.py   
#
#EXTRA_DIST = \
#    $(PYTHON_FILES) \
#    __init__.py.in
#
#pydir = $(pythondir)/audio_convert_mod
#py_PYTHON = $(PYTHON_FILES)
