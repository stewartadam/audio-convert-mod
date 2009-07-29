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
Custom widgets.
"""
import gtk
import gobject

import audio_convert_mod
from audio_convert_mod.i18n import _
from audio_convert_mod.const import *
from audio_convert_mod import formats

class StatusBar(gtk.Statusbar):
    def __init__(self, widget):
        """ Initialize.
            widget: GTK widget to use as the statusbar
        """
        gtk.Statusbar.__init__(self)
        self.statusbar = widget

    def newmessage(self, message, seconds=3):
        """ New message in status bar.
            message: Message to display
            seconds: number of seconds to display the message
                     defaults to three.
        """
        try:
            self.message_timeout()
        # Just means there was no existing message.
        except AttributeError:
            pass
        self.statusbar.push(1, message)
        self.message_timer = gobject.timeout_add(seconds*1000, self.message_timeout)

    def message_timeout(self):
        """ Remove a message from the statusbar """
        self.statusbar.pop(1)
        gobject.source_remove(self.message_timer)
        return True

class ProgressBar(gtk.ProgressBar):
    def __init__(self, widget, ms=15):
        """ Initialize.
            widget: GTK widget to use as the progressbar
            ms: Pulse step is every this many miliseconds
        """
        gtk.ProgressBar.__init__(self)
        self.progressbar = widget
        self.ms = ms
        self.pulsing = False
        self.progressbar.set_pulse_step(0.01)

    def _pulse(self):
        """ Pulse the progressbar. """
        self.progressbar.pulse()
        # Has to return true to happen again
        return True

    def startPulse(self):
        """ Start auto-pulsing the progressbar """
        if self.pulsing:
            self.stopPulse()
        self.pulsing = True
        self.pulsetimer = gobject.timeout_add(self.ms, self._pulse)

    def stopPulse(self):
        """ Stop auto-pulsing the progressbar """
        gobject.source_remove(self.pulsetimer)
        self.progressbar.set_fraction(0)
        self.pulsing = False
        return True

    def setMs(self, ms):
        """ Set the ms value (see __init__) """ 
        self.ms = int(ms)
        if self.pulsing:
            self.stopPulse()
            self.startPulse()

class GenericDia:
  """ Wrapper for the generic dialog """
  def __init__(self, dialog, title, parent):
    """ Initialize """
    self.dialog = dialog
    self.dialog.set_title(title)
    self.dialog.set_transient_for(parent)
    
  def run(self):
    """ Run the dialog """
    self.dialog.show()
    try:
      return self.dialog.run()
    except:
      self.destroy()
      raise
      
  def destroy(self):
    """ Hide the dialog, don't kill it! """
    self.dialog.hide()
    
  def runAndDestroy(self):
    """ Executes run() and destroy() """
    response = self.run()
    self.destroy()
    return response

class PathBrowser(GenericDia, gtk.FileChooserDialog):
  """ Wrapper for generic path dialogs """
  def __init__(self, dialog, parent, ffilter=None):
    """ Initialize.
      widget: The widget to use
      ffilter: List for filter creation.
          > 1st value is filter pattern
          > 2nd value is the description
    """
    GenericDia.__init__(self, dialog, _('Choose a file or folder'), parent)
    if ffilter:
      self.ffilter = gtk.FileFilter()
      for pattern in ffilter[:-1]:
        self.ffilter.add_pattern(pattern)
      self.ffilter.set_name(ffilter[-1])
      self.dialog.add_filter(self.ffilter)
    else:
      self.ffilter = None

  def destroy(self):
    """ Destroy the dialog and the filter """
    GenericDia.destroy(self)
    if self.ffilter:
      self.dialog.remove_filter(self.ffilter)
  
  def set_current_folder(self, path):
    """ Wrapper: See GTK+ help. """
    return self.dialog.set_current_folder(path)
  
  def set_select_multiple(self, multipleBool):
    """ Wrapper: See GTK+ help. """
    return self.dialog.set_select_multiple(multipleBool)

  def set_do_overwrite_confirmation(self, overwriteBool):
    """ Wrapper: See GTK+ help. """
    return self.dialog.set_do_overwrite_confirmation(overwriteBool)
    
  def set_action(self, action):
    """ Wrapper: See GTK+ help. """
    return self.dialog.set_action(action)
  
  def set_title(self, title):
    """ Wrapper: See GTK+ help. """
    return self.dialog.set_title(title)
  
  def get_filename(self):
    """ Wrapper: See GTK+ help. """
    return self.dialog.get_filenames()
  
  def get_filenames(self):
    """ Wrapper: See GTK+ help. """
    return self.dialog.get_filenames()
  
  def set_filename(self, filename):
    """ Wrapper: See GTK+ help. """
    return self.dialog.set_filename(filename)
  
  def add_filter(self, ffilter):
    """ Wrapper: See GTK+ help. """
    return self.dialog.add_filter(ffilter)
  
  def remove_filter(self, ffilter):
    """ Wrapper: See GTK+ help. """
    return self.dialog.remove_filter(ffilter)
  
# *-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*

class bugReport(GenericDia):
  """ Wrapper for a bug report dialog """
  def __init__(self, dialog, textview, parent, tracebackText):
    """ Uses `dialog' to show bug report `traceback' in `textview' on top
        of `parent' """
    GenericDia.__init__(self, dialog, _('Bug Report'), parent)
    textview.get_buffer().set_text(tracebackText)

def saveFilename(parent):
  """ Displays a filechooser (save) and returns the chosen filename """
  fileChooser = gtk.FileChooserDialog(title=_('Save As...'),
                                      parent=parent,
                                      action=gtk.FILE_CHOOSER_ACTION_SAVE,
                                      buttons=(gtk.STOCK_CANCEL,
                                                 gtk.RESPONSE_CANCEL,
                                               gtk.STOCK_SAVE,
                                                 gtk.RESPONSE_OK))
  fileChooser.set_do_overwrite_confirmation(True)
  if fileChooser.run() in [gtk.RESPONSE_CANCEL, gtk.RESPONSE_DELETE_EVENT]:
    filename = None
  else:
    filename = fileChooser.get_filename()
  fileChooser.destroy()
  return filename

