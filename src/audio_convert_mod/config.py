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
Configuration classes for audio-convert-mod
"""
import ConfigParser
import os
import audio_convert_mod
from audio_convert_mod.const import *
from audio_convert_mod.i18n import _

class ConfigError(Exception):
  """ Errors in the configuration file. """
  def __init__(self, value):
    self.value = value
  def __str__(self):
    return repr(self.value)

def initConfigDir():
  """ Setup the configuration directory """
  configDir = os.path.normpath('%s/.audio-convert-mod' % USERHOME)
  if not os.path.exists(configDir):
    try:
      os.mkdir(configDir, 0755)
    except OSError, error:
      raise ConfigError(_('Could not create configuration directory: %s' % error))
      sys.exit(1)
  elif not audio_convert_mod.CheckPerms(configDir):
    raise ConfigError(_('You do not have read and write permissions to `%s\'.') % configDir)
    sys.exit(1)

class ConfigFile(ConfigParser.ConfigParser):
  """ A more sane ConfigParser. It commits changes immediately,
    and also re-parses after each action so
    what-you-see-is-what's-in-the-file.
  """
  # Basic setup.
  def __init__(self, conffile, create=False):
    ConfigParser.ConfigParser.__init__(self)
    self.config = ConfigParser.ConfigParser()
    ConfigParser.ConfigParser.optionxform = self.optionxform
    self.conffile = conffile
    self.create = create
    # Finally...
    self.read()

  def optionxform(self, option):
     """ Case sensitive! """
     return str(option)

  def set_conffile(self, conffile, create=True):
    """ Use a new config file.
      conffile: the path to the new configuration file
      create: If it doesn't exist, create a new config?
    """
    self.conffile = conffile
    self.read()

  def get_conffile(self):
    """ Returns the config file path. """
    return self.conffile

  def read(self):
    """ Read & parse the config file."""
    if self.create == True and not os.path.exists(self.conffile):
      self.fh = open(self.conffile,'w')
      self.fh.write('')
      self.fh.close()
    elif self.create == False and not os.path.exists(self.conffile):
      raise ConfigError(_('Attempted to read non-existant file \'%s\'') % self.conffile)
    self.fh = open(self.conffile,'r')
    self.config.readfp(self.fh)
    self.fh.close()

  def write(self):
    """ Write the config file, then reparse. """
    try:
      self.fh = open(self.conffile,'w')
      self.config.write(self.fh)
      self.fh.close()
      self.read()
    except:
      raise ConfigError(_('Cannot write to file \'%s\'') % self.conffile)

  def set(self, section, prop, value):
    """ Set a value in a given section and save. """
    self.config.set(section, prop, value)
    self.write()
    return True

  def get(self, section, prop):
    """ Returns the value for a given option in a section """
    value = self.config.get(section, prop)
    return value

  def remove_option(self, sectname, optionname):
    """ Remove a property & it's value, then save. """
    self.config.remove_option(sectname, optionname)
    self.write()
    return True

  def add_section(self, sectname):
    """ Add a section and save. """
    self.config.add_section(sectname)
    self.write()
    return True

  def remove_section(self, sectname):
    """ Remove a section and save. """
    self.config.remove_section(sectname)
    self.write()
    return True

  def sections(self):
    """ Returns the sections in the file """
    return self.config.sections()

  def options(self, section):
    """ Returns the options in a section of the file """
    return self.config.options(section)

  def has_section(self, section):
    """ Has section x? """
    return self.config.has_section(section)

  def has_option(self, section, option):
    """ Has option x in section y? """
    return self.config.has_option(section, option)

class PreferencesConf(ConfigFile):
  """ Preferences configuration file """
  def __init__(self, create=True):
    """ Checks for previous versions, incomplete confs, etc """
    ConfigFile.__init__(self, PREFLOC, create)
    if self.sections() == []:
      self.initialize()
    for i in ['Preferences', 'Defaults']:
      if not self.has_section(i):
        raise ConfigError(_('Configuration file is missing section \'%(a)s\'!') % {'a': i})
    self.patchConfiguration()

  def initialize(self):
    """ Creates a basic set configuration file """
    # Preferences section
    self.add_section('Preferences')
    import tempfile
    for pair in [['ShowTrayIcon', 1], ['TrayIconNotifications', 1], ['PauseOnErrors', 1],
                 ['TemporaryDirectory', tempfile.gettempdir()]]:
      self.set('Preferences', pair[0], pair[1])
    
    # Defaults section
    self.add_section('Defaults')
    # FileExists=1 --> append
    # Metadata=1 --> Copy
    # successfulConversion=1 --> leave converted files inplace
    # outputFolder=Off --> save to home
    for pair in [['Format', 'WAV'], ['Quality', 0], ['Extension', 0],
                ['FileExists', 1], ['Metadata', 1], ['SuccessfulConversion', 1],
                ['SuccessfulConversionDest', USERHOME], ['OutputFolder', 'Off'],
                ['RemoveDiacritics', 0], ['Resample', -1]]:
      self.set('Defaults', pair[0], pair[1])
    self.set('Preferences', 'Version', audio_convert_mod.__version__)

  def patchConfiguration(self):
    """ Import old configurations. Only runs if not current version """
    if not self.has_option('Preferences', 'Version'):
      # version was added in 3.45.1 so we import everything
      self.set('Preferences', 'Version', '3.45.0')
    try:
      oldVersion = self.get('Preferences', 'Version')
    except: # old config from beta3
      oldVersion = self.get('Preferences', 'version')

    # only if it's a version mismatch should we import
    if oldVersion == audio_convert_mod.__version__:
      return True

    # This lets us do what needs to be done for version X and _above_
    fromHereUp = False

    if oldVersion != audio_convert_mod.__version__:
      # This lets us do what needs to be done for version X and _above_
      fromHereUp = False
      # --------------------------------------------------------
      # oldest first, newest last in for the order of IF clauses
      # --------------------------------------------------------
      if oldVersion == '3.45.0' or fromHereUp == True:
        fromHereUp = True
        if not self.has_section('Defaults'):
          self.add_section('Defaults')
        for pair in [['format', 'WAV'], ['quality', 0], ['extension', 0],
                ['fileexists', 1], ['metadata', 1], ['successfulconversion', 1],
                ['successfulconversiondest', USERHOME], ['outputfolder', 'Off']]:
          self.set('Defaults', pair[0], pair[1])
      
      if oldVersion == '3.45.1' or fromHereUp == True:
        fromHereUp = True
      if oldVersion == '3.45.2' or fromHereUp == True:
        fromHereUp = True
        self.set('Defaults', 'successfulconversiondest', USERHOME)
      if oldVersion == '3.45.3' or fromHereUp == True:
        fromHereUp = True
        if not self.has_option('Defaults', 'successfulconversiondest'): # fix oops
          self.set('Defaults', 'successfulconversiondest', USERHOME)
      if oldVersion == '3.45.3' or fromHereUp == True:
        fromHereUp = True
      if oldVersion == '3.45.4' or fromHereUp == True:
        fromHereUp = True
        # Case sensitivity
        for option in ['Version', 'ShowTrayIcon', 'BlinkTrayIcon', 'PauseOnErrors']:
          self.set('Preferences', option, self.get('Preferences', option.lower()))
          self.remove_option('Preferences', option.lower())
        for option in ['Format', 'Quality', 'Extension', 'FileExists', 'Metadata', 'SuccessfulConversion', 'SuccessfulConversionDest', 'OutputFolder']:
          self.set('Defaults', option, self.get('Defaults', option.lower()))
          self.remove_option('Defaults', option.lower())
        # rename BlinkTrayicon
        self.set('Preferences', 'TrayIconNotifications', self.get('Preferences', 'BlinkTrayIcon'))
        self.remove_option('Preferences', 'BlinkTrayIcon')
        # add "remove diacritics" option
        self.set('Defaults', 'RemoveDiacritics', 0)
        # add temp dir option
        import tempfile
        self.set('Defaults', 'TemporaryDirectory', tempfile.gettempdir())
      if oldVersion == '3.45.5' or fromHereUp == True:
        fromHereUp = True
        self.set('Defaults', 'Resample', -1)
      if oldVersion in ['3.46.0', '3.46.0a'] or fromHereUp == True:
        fromHereUp = True
        
    return self.set('Preferences', 'Version', audio_convert_mod.__version__)

