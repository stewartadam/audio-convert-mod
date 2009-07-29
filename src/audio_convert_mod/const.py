# -*- coding: utf-8 -*-
#    Copyright (C) 2007, 2008, 2009 Stewart Adam
#    This file is part of audio-convert-mod.

#    audio-convert-mod is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.

#    audio-convert-mod is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.

#    You should have received a copy of the GNU General Public License
#    along with audio-convert-mod; if not, write to the Free Software
#    Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

"""
All constants/shared functions in the program
"""
import os
import sys
import getpass
import ConfigParser

MSWINDOWS = sys.platform.startswith("win")
if MSWINDOWS:
  UID = 1
  ROOTDRIVE = os.path.splitdrive(sys.argv[0])[0]
else:
  UID = os.getuid()
USER = getpass.getuser()

INSTALL_DIR = os.path.dirname(os.path.abspath(os.path.dirname(__file__)))
USERHOME = os.path.expanduser('~%s' % USER)
if USERHOME == '~%s' % USER: # if os doesn't support that format
  USERHOME = os.path.expanduser('~')
PREFLOC = os.path.normpath('%s/.audio-convert-mod/prefs.conf' % USERHOME)

def which(program):
  """ Emulates unix `which` command """
  for path in os.getenv('PATH').split(os.pathsep):
    programPath = os.path.join(path, program)
    if os.path.exists(programPath) and os.path.isfile(programPath):
      return programPath
    if MSWINDOWS and os.path.isfile(programPath+'.exe'):
      return programPath
  return False
