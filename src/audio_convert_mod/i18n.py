# -*- coding: utf-8 -*-
#  Copyright (C) 2007, 2008, 2009 Stewart Adam
#  This file is part of audio-convert-mod.

#  audio-convert-mod is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.

#  audio-convert-mod is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.

#  You should have received a copy of the GNU General Public License
#  along with audio-convert-mod; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
"""
This file is a slighlty modified version of the yum i18n.py file. Setups up the
audio-convert-mod translation domain and makes _() available. Uses ugettext to
make sure translated strings are in Unicode.
"""

try: 

  import gettext
  t = gettext.translation('audio-convert-mod')
  _ =  t.ugettext
except:
  # Oops! Better return the string as it is so we don't break things
  def _(str):
    """ [Wrapper] Returns the same string """
    return str
