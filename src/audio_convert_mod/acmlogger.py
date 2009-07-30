# -*- coding: utf-8 -*-
#  Copyright (C) 2005, 2006, 2007, 2008, 2009 Stewart Adam
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
The audio-convert-mod logger
Based on fwbackups's fwlogger.py file (2009-07-29)
"""
import datetime
import logging
import types

from audio_convert_mod.const import *
from audio_convert_mod.i18n import _

L_DEBUG = logging.DEBUG
L_INFO = logging.INFO
L_WARNING = logging.WARNING
L_ERROR = logging.ERROR
L_CRITICAL = logging.CRITICAL
LOGGERS = {'main': 'acm-main'}
LEVELS = {'debug': 10,
          'info': 20,
          'warning': 30,
          'error': 40,
          'critical': 50}

def getLogger():
  """Retrieve the audio-convert-mod logger"""
  logging.setLoggerClass(acmLogger)
  logger = logging.getLogger(LOGGERS['main'])
  # reset to prevent excessive logging from other applications
  logging.setLoggerClass(logging.Logger)
  return logger

def shutdown():
  """Shut down the logging system"""
  logging.shutdown()

class acmLogger(logging.Logger):
  """A subclass to logging.Logger"""
  def __init__(self, name, level=logging.DEBUG):
    """Setup the audio-convert-mod logger, text mode"""
    logging.Logger.__init__(self, name, level)
    self.__printToo = False
    self.__functions = []
    self.__newmessages = False
    try:
      # need a handler
      loghandler = logging.FileHandler(LOGLOC, 'a')
      # Create formatter & add formatter to handler
      logformatter = logging.Formatter("%(message)s")
      loghandler.setFormatter(logformatter)
      # add handler to logger
      self.addHandler(loghandler)
    except Exception, error:
      print _('Could not set up the logger!')
      raise

  def setPrintToo(self, printToo):
    """If printToo is True, print messages to stdout as we log them"""
    self.__printToo = printToo
    
  def getPrintToo(self):
    """Retrieves the printToo property"""
    return self.__printToo
  
  def unconnect(self, function):
    """Disconnects a function from logmsg. Returns true if disconnected, false
        if that function was not connected."""
    try:
      self.__functions.remove(function)
      return True
    except ValueError:
      return False

  def connect(self, function):
    """Connects a function to logmsg. `function' must be passed as an instance,
        not the function() call itself.

        Function will be given the severity and message as arguments:
        def callback(severity, message)"""
    self.__functions.append(function)

  def logmsg(self, severity, message):
    """Logs a message. Severity is one of 'debug', 'info', 'warning', 'error'
    or 'critical'."""
    date = datetime.datetime.now().strftime('%b %d %H:%M:%S')
    level = self.getEffectiveLevel()
    if level <= LEVELS[severity.lower()]:
      entry = '%s :: %s : %s' % (date, _(severity.upper()), message)
      # pull in & execute the appropriate function
      getattr(self, severity.lower())(entry)
      if self.__printToo:
        print entry
      for i in self.__functions:
        i(severity.lower(), entry)

