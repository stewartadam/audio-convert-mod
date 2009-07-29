AC_INIT([audio-convert-mod], 3.45.6)
AM_INIT_AUTOMAKE([dist-bzip2 no-dist-gzip])
AC_CONFIG_SRCDIR(src/audio_convert_mod/__init__.py.in)

# Search for Python >= 2.4
AM_PATH_PYTHON([2.4])

# Dependencies
PKG_CHECK_MODULES(SHELL, pygtk-2.0 gtk+-2.0)

AC_CONFIG_MACRO_DIR([m4])

# Setup gettext translation
ALL_LINGUAS="zh_CN"
GETTEXT_PACKAGE=audio-convert-mod
AC_SUBST(GETTEXT_PACKAGE)
# Use intltool
AC_PROG_INTLTOOL

# Output files
AC_CONFIG_FILES([
bin/Makefile
bin/audio-convert-mod
po/Makefile.in
src/Makefile
src/audio_convert_mod/Makefile
src/audio_convert_mod/__init__.py
Makefile
audio-convert-mod.spec
])

# ...Ready, set, go!
AC_OUTPUT
