#! /usr/bin/python
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
Puts it all together.
"""
import datetime
import getopt
import os
import sys
import re
import shutil
import time

from audio_convert_mod.i18n import _
from audio_convert_mod.const import *

if MSWINDOWS:
  # Fetchs gtk2 path from registry
  import _winreg
  import msvcrt
  try:
    k = _winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE, "Software\\GTK\\2.0")
  except EnvironmentError:
    print _('You must install the GTK+ Runtime Environment v2.6 or higher to run this program.')
    sys.exit(1)
  gtkdir = _winreg.QueryValueEx(k, "Path")
  os.environ['PATH'] += ";%s\\lib;%s\\bin;%s" % (gtkdir[0], gtkdir[0], INSTALL_DIR)
  _winreg.CloseKey(k)

try:        
  import gtk
  import gobject
except:
  print _("An error occurred while importing gtk/gobject.")
  print _("Please make sure you have a valid GTK+ Runtime Environment.")
  sys.exit(1)
#--
import audio_convert_mod
from audio_convert_mod import interface
from audio_convert_mod import widgets

def reportBug(etype=None, evalue=None, tb=None):
  """ Report a bug dialog """
  import traceback
  c = interface.Controller('%s/BugReport.glade' % INSTALL_DIR, 'bugreport')
  if not etype and not evalue and not tb:
    (etype, evalue, tb) = sys.exc_info()
  if etype == KeyboardInterrupt:
    sys.exit(1)
  tracebackText = ''.join(traceback.format_exception(etype, evalue, tb))
  reportWindow = widgets.bugReport(c.ui.bugreport, c.ui.bugreportTextview, None, tracebackText)
  response = reportWindow.runAndDestroy()
  if response == gtk.RESPONSE_OK:
    filename = widgets.saveFilename(c.ui.bugreport)
    if not filename:
      sys.exit(1)
    if audio_convert_mod.CheckPerms(filename):
      fh = open(filename, 'w')
      time = datetime.datetime.today().strftime('%I:%M %p, %Y-%m-%d')
      fh.write(_('audio-convert-mod v%(a)s bug report written saved at %(b)s\n\n' % {'a': audio_convert_mod.__version__, 'b': time}))
      fh.write(tracebackText)
      fh.close()
      sys.exit(1)
    else:
      print _('WARNING: Couldn\'t write bug report - Insufficient permissions!')
      sys.exit(1)
  elif response == gtk.RESPONSE_CLOSE:
    sys.exit(1)
  print tracebackText

sys.excepthook = reportBug
gobject.threads_init()
# Import these last so that any errors popup in the GUI
from audio_convert_mod import acmlogger
from audio_convert_mod import config
from audio_convert_mod import formats

def usage(error):
  """ Print the application usage """
  if error:
    print _('Invalid usage: %s'  % error)
  print _("""Usage: audio-convert-mod [OPTIONS] File1 [File2 File3 ...]
  Options:
    -v, --verbose  :  Enable debug messages
    -h, --help  :  Print this message and exit
""")

def escape(uri):
    "Convert each space to %20, etc"
    _to_utf8 = codecs.getencoder('utf-8')
    return re.sub('[^:-_./a-zA-Z0-9]',
        lambda match: '%%%02x' % ord(match.group(0)),
        _to_utf8(uri)[0])

def unescape(uri):
    "Convert each %20 to a space, etc"
    if '%' not in uri: return uri
    return re.sub('%[0-9a-fA-F][0-9a-fA-F]',
        lambda match: chr(int(match.group(0)[1:], 16)),
        uri)

def get_local_path(uri):
    """Convert 'uri' to a local path and return, if possible. If 'uri'
    is a resource on a remote machine, return None. URI is in the escaped form
    (%20 for space)."""
    if not uri:
        return None

    if uri[0] == '/':
        if uri[1:2] != '/':
            return unescape(uri)    # A normal Unix pathname
        i = uri.find('/', 2)
        if i == -1:
            return None    # //something
        if i == 2:
            return unescape(uri[2:])    # ///path
        remote_host = uri[2:i]
        if remote_host == our_host_name():
            return unescape(uri[i:])    # //localhost/path
        # //otherhost/path
    elif uri[:5].lower() == 'file:':
        if uri[5:6] == '/':
            return get_local_path(uri[5:])
    elif uri[:2] == './' or uri[:3] == '../':
        return unescape(uri)
    return None

# ***********************************************************************

class acmApp(interface.Controller):
  """ Main program """
  def addToSelectFilesFilesTreeview(self, paths):
    """ Adds a file to the Select Files treeview """
    model = self.ui.main1FilesTreeview.get_model()
    # don't sort as we add
    model.set_default_sort_func(lambda *args: -1) 
    # don't refresh as we add
    self.ui.main1FilesTreeview.freeze_child_notify()
    # detach model
    self.ui.main1FilesTreeview.set_model(None)
    errors = []
    for i in paths:
      fileType, path, filename = formats.getFileType(i), os.sep.join(i.split(os.sep)[:-1]), i.split(os.sep)[-1]
      array, coord = audio_convert_mod.liststoreIndex(model, filename)
      if False == True: # coord != []:
        # a filename match was found, now compare paths
        array2, coord2 = audio_convert_mod.liststoreIndex(model, path)
        if coord2 != []:
          errors.append( _('Skipping duplicate file `%(a)s%(b)s%(c)s`' % {'a': array2[coord2[0][0]][coord2[0][1]],
                                                                          'b': os.sep,
                                                                        'c': array[coord[0][0]][coord[0][1]]
                                                                         } ) )
      else:
        # No duplicate because array[coord[0][0]][coord[0][1]] isn't there
        if formats.decodable(i) and not os.path.isdir(i):
          model.append([fileType.__class__.__name__, path, filename])
        else:
          errors.append( _('Skipping non-decodable file `%(a)s`' % {'a': i} ) )
    # okay, now you can sort.
    model.set_sort_column_id(-1, gtk.SORT_ASCENDING)
    # okay, now you can refresh.
    self.ui.main1FilesTreeview.thaw_child_notify()
    # attach model
    self.ui.main1FilesTreeview.set_model(model)
    return errors
  
  def showError(self, parent, header, text, details=''):
    """ Shows an error in the HIG-style error dialog """
    dialog = widgets.GenericDia(self.ui.errorDialog, _('Error'), parent)
    self.ui.errorDialogHeaderLabel.set_text('<span size="large" weight="bold">%s</span>' % header)
    self.ui.errorDialogHeaderLabel.set_use_markup(True)
    self.ui.errorDialogTextLabel.set_text(text)
    self.ui.errorDialogDetailsTextview.get_buffer().set_text(details)
    if details:
      self.ui.errorDialogExpander.show()
    else:
      self.ui.errorDialogExpander.hide()
    dialog.runAndDestroy()
  
  def showWarning(self, parent, header, text, details=''):
    """ Shows an error in the HIG-style error dialog """
    dialog = widgets.GenericDia(self.ui.warningDialog, _('Warning'), parent)
    self.ui.warningDialogHeaderLabel.set_text('<span size="large" weight="bold">%s</span>' % header)
    self.ui.warningDialogHeaderLabel.set_use_markup(True)
    self.ui.warningDialogTextLabel.set_text(text)
    self.ui.warningDialogDetailsTextview.get_buffer().set_text(details)
    if details:
      self.ui.warningDialogExpander.show()
    else:
      self.ui.warningDialogExpander.hide()
    dialog.runAndDestroy()
  
  def __init__(self, verbose, paths):
    """ Initialize a new instance. """
    interface.Controller.__init__(self, '%s/audio-convert-mod.glade' % INSTALL_DIR, 'main')
    # Setup configuration directory
    config.initConfigDir()
    # Load preferences
    prefs = config.PreferencesConf(create=True)
    # clear log for new session
    logfh = open(LOGLOC, 'w')
    logfh.write('')
    logfh.close()
    # Enable debug messages if verbose was selected
    if verbose:
      level = acmlogger.L_DEBUG
    else:
      level = acmlogger.L_INFO
    # create the logger
    self.logger = acmlogger.getLogger()
    self.logger.setLevel(level)
    self.logger.setPrintToo(True)
    self.logger.logmsg("INFO", _("audio-convert-mod version %s initialized") % audio_convert_mod.__version__)
    try:
      import pynotify
      pynotify.init('audio-convert-mod')
      self.PYNOTIFY_AVAIL = True
      self.ui.prefsNotifyInTrayCheck.set_label(_('Display noticiations in the tray area'))
    except:
      self.PYNOTIFY_AVAIL = False
      self.ui.prefsNotifyInTrayCheck.set_label(_('Blink the tray icon to notify me of important status changes'))
    
    # Transient Windows
    self.ui.about.set_transient_for(self.ui.main)
    self.ui.license.set_transient_for(self.ui.about)
    self.ui.credits.set_transient_for(self.ui.about)
    self.ui.chooser.set_transient_for(self.ui.main)
    self.ui.features.set_transient_for(self.ui.main)
    self.ui.tags.set_transient_for(self.ui.main)
    self.ui.prefs.set_transient_for(self.ui.main)
    
    # liststore
    liststore = gtk.ListStore(gobject.TYPE_STRING, gobject.TYPE_STRING)
    self.ui.main2QualityCombobox.set_model(liststore)
    cell = gtk.CellRendererText()
    self.ui.main2QualityCombobox.clear()
    self.ui.main2QualityCombobox.pack_start(cell, True)
    self.ui.main2QualityCombobox.add_attribute(cell, 'text', 1)
    
    import pango
    # Selected Files Treeview
    liststore = gtk.ListStore(gobject.TYPE_STRING, gobject.TYPE_STRING, gobject.TYPE_STRING)
    # Column: Format
    cell = gtk.CellRendererText()
    cell.set_property('ellipsize', pango.ELLIPSIZE_END)
    col = gtk.TreeViewColumn(_('Format'), cell, text=0)
    col.set_resizable(True)
    col.set_sort_column_id(0)
    col.set_min_width(75)
    self.ui.main1FilesTreeview.append_column(col)
    # Column: Path
    cell = gtk.CellRendererText()
    cell.set_property('ellipsize', pango.ELLIPSIZE_MIDDLE)
    col = gtk.TreeViewColumn(_('Path'), cell, text=1)
    col.set_resizable(True)
    col.set_sort_column_id(1)
    col.set_min_width(150)
    self.ui.main1FilesTreeview.append_column(col)
    # Column: Filename
    cell = gtk.CellRendererText()
    cell.set_property('ellipsize', pango.ELLIPSIZE_START)
    col = gtk.TreeViewColumn(_('Filename'), cell, text=2)
    col.set_resizable(True)
    col.set_sort_column_id(2)
    self.ui.main1FilesTreeview.append_column(col)
    # Finally...
    self.ui.main1FilesTreeview.set_model(liststore)
    selection = self.ui.main1FilesTreeview.get_selection()
    selection.set_mode(gtk.SELECTION_MULTIPLE)
    self.ui.main1FilesTreeview.set_reorderable(False)
    liststore.set_sort_column_id(0, gtk.SORT_ASCENDING)
    # Allow enable drag and drop of rows including row move
    target = [('text/uri-list', 0, 0)]
    self.ui.main1FilesTreeview.drag_dest_set(gtk.DEST_DEFAULT_ALL, target, gtk.gdk.ACTION_COPY)
    # /Selected Files Treeview
    
    # Formats treeview
    liststore = gtk.ListStore(gobject.TYPE_STRING,
                              gobject.TYPE_STRING, gobject.TYPE_STRING,
                              gobject.TYPE_STRING, gobject.TYPE_STRING,
                              gobject.TYPE_STRING, gobject.TYPE_STRING)
    # Column: Format
    cell = gtk.CellRendererText()
    cell.set_property('ellipsize', pango.ELLIPSIZE_MIDDLE)
    col = gtk.TreeViewColumn(_('Format'), cell, text=0)
    col.set_resizable(False)
    col.set_sort_column_id(0)
    col.set_min_width(100)
    self.ui.featuresFeaturesTreeview.append_column(col)
    # Column: Decode
    pcell = gtk.CellRendererPixbuf()
    pcell.set_property('stock-size', gtk.ICON_SIZE_BUTTON)
    tcell = gtk.CellRendererText()
    col = gtk.TreeViewColumn(_('Decode'))
    col.pack_start(pcell, expand=False)
    col.pack_start(tcell, expand=False)
    col.set_attributes(pcell, stock_id=1)
    col.set_attributes(tcell, text=2)
    col.set_resizable(True)
    col.set_min_width(85)
    self.ui.featuresFeaturesTreeview.append_column(col)
    # Column: Encode
    pcell = gtk.CellRendererPixbuf()
    pcell.set_property('stock-size', gtk.ICON_SIZE_BUTTON)
    tcell = gtk.CellRendererText()
    col = gtk.TreeViewColumn(_('Encode'))
    col.pack_start(pcell, expand=False)
    col.pack_start(tcell, expand=False)
    col.set_attributes(pcell, stock_id=3)
    col.set_attributes(tcell, text=4)
    col.set_resizable(False)
    col.set_min_width(85)
    self.ui.featuresFeaturesTreeview.append_column(col)
    # Column: Tags
    pcell = gtk.CellRendererPixbuf()
    pcell.set_property('stock-size', gtk.ICON_SIZE_BUTTON)
    tcell = gtk.CellRendererText()
    col = gtk.TreeViewColumn(_('Tags'))
    col.pack_start(pcell, expand=False)
    col.pack_start(tcell, expand=False)
    col.set_attributes(pcell, stock_id=5)
    col.set_attributes(tcell, text=6)
    col.set_resizable(False)
    col.set_min_width(85)
    self.ui.featuresFeaturesTreeview.append_column(col)
    # Lastly...
    self.ui.featuresFeaturesTreeview.set_model(liststore)
    self.ui.featuresFeaturesTreeview.set_reorderable(False)
    liststore.set_sort_column_id(0, gtk.SORT_ASCENDING)
    # /Formats treeview
    
    self.processId = None
    # Labels, defaults
    self.ui.aboutVersionLabel.set_text('<span size="xx-large" weight="bold">audio-convert-mod %s</span>' % audio_convert_mod.__version__)
    self.ui.aboutVersionLabel.set_use_markup(True)
    self.ui.mainControlNotebook.set_show_tabs(False)
    if MSWINDOWS:
      self.ui.prefsFileManagerIntegrationFrame.set_sensitive(False)
    self.prepareForNewConversion()
    # /Set defaults
    
    self._setupTrayIcon()
    if int(prefs.get('Preferences', 'ShowTrayIcon')) == 1:
      self.trayicon.set_visible(True)
    else:
      self.trayicon.set_visible(False)

    # now add those paths
    if paths != []:
      fileList = []
      for path in paths:
        if os.path.exists(path):
          if os.path.isdir(path): # a dir
            files = os.listdir(path)
            files.sort()
            for filename in files:
              fileList.append('%s/%s' % (path, filename) )
          else: # a file
            fileList.append('%s' % path )
        else: # file didn't exist
          self.logger.logmsg("DEBUG", _("Will not add non-existant file `%s\'") % path)
      errors = self.addToSelectFilesFilesTreeview(fileList)
      if errors != []:
        self.showError(self.ui.main, _('Could not add all of the requested files'), _('Not all files could be added.'), details='\n'.join(errors))
    self.ui.main1FilesTreeview.connect('drag_data_received', self.drag_data_received)

  def drag_data_received(self, w, context, x, y, data, info, time):
    """ DnD control """
    paths = []
    if data and data.format == 8:
      for i in data.data.split('\r\n'):
        if i != "" or i != None:
          path = get_local_path(i)
          if path != None and os.path.isfile(path):
            paths.append(path)
          elif path != None and os.path.isdir(path):
            files = os.listdir(path)
            files.sort()
            for filename in files:
              if not os.path.isdir(os.path.join(path, filename)):
                paths.append(os.path.join(path, filename))
    self.addToSelectFilesFilesTreeview(paths)
    context.finish(True, False, time)
  
  def prepareForNewConversion(self):
    """ Prepares the program for a new conversion """
    self.ui.mainControlNotebook.set_current_page(0)
    self.ui.main3CurrentFileLabel.set_label(_('None'))
    self.ui.main2OutputFolderFilechooser.set_current_folder(USERHOME)
    self.ui.main2SuccessOutputFolderFilechooser.set_current_folder(USERHOME)
    self.ui.main1FilesTreeview.get_model().clear()
    self.ui.featuresFeaturesTreeview.get_model().clear()
    self.checkFormats()
    self.refreshFeatures()
  
  def _setupTrayIcon(self):
    """ Sets up the tray icon """
    pix = self.ui.main.render_icon(gtk.STOCK_CONVERT, gtk.ICON_SIZE_MENU)
    #pix = gtk.gdk.pixbuf_new_from_file("/usr/share/pixmaps/audio-convert-mod.svg")
    self.trayicon = gtk.status_icon_new_from_pixbuf(pix)
    self.trayicon.set_from_pixbuf(pix)
    self.trayicon.connect("popup_menu", self._Popup)
    self.trayicon.connect("activate", self._clicked)
    self.setStatus(_('Idle'))

  def trayNotify(self, summary, body, timeout=10):
    """ Display a notification attached to the tray icon if applicable """
    # see /usr/share/doc/python-notify/examples for API
    #n.set_urgency(pynotify.URGENCY_NORMAL)
    #n.set_timeout(pynotify.EXPIRES_NEVER)
    #n.add_action("clicked","Button text", callback_function, None)
    if not int(config.PreferencesConf().get('Preferences', 'TrayIconNotifications')):
      return
    if self.PYNOTIFY_AVAIL:
      import pynotify
      notify = pynotify.Notification(summary, body)
      # icon
      pix = self.ui.main.render_icon(gtk.STOCK_CONVERT, gtk.ICON_SIZE_DIALOG)
      notify.set_icon_from_pixbuf(pix)
      # location
      tray = self.trayicon
      if tray.get_visible():
        notify.set_property('status-icon', tray)
      # timeout?
      if timeout != 0:
        notify.set_timeout(int(timeout) * 1000)
      # finally, show it
      try:
        notify.show()
      except:
        self.trayicon.set_blinking(True)
    else:
      self.trayicon.set_blinking(True)

  def setStatus(self, status):
    """ Sets the status icon and tray label """
    self.trayicon.set_tooltip(_('audio-convert-mod - %s' % status))
    self.ui.main3StatusLabel.set_text(status)

  def _clicked(self, status):
    """ Tray icon is clicked.
      status: the gtk.StatusIcon
    """
    # use me for menu on left click
    def menu_pos(menu):
      return gtk.status_icon_position_menu(menu, self.trayicon)
    self.ui.trayMenu.popup(None, None, menu_pos, 0, gtk.get_current_event_time())
    if self.trayicon.get_blinking():
      self.trayicon.set_blinking(False)
        

  def _Popup(self, status, button, time):
    """ Popup the menu at the right position """
    def menu_pos(menu):
      return gtk.status_icon_position_menu(menu, self.trayicon)
    if MSWINDOWS:
      self.ui.trayMenu.popup(None, None, None, button, time)
    else:
      self.ui.trayMenu.popup(None, None, menu_pos, button, time)
    self.ui.trayMenu.show()

  ### TRAY ICON ###

  def on_show_conversion_window1_activate(self, widget, event=None):
    """ Hide/show the main window """
    if self.ui.show_conversion_window1.get_active():
      self.ui.main.show()
    else:
      self.ui.main.hide()

  def on_show_tray_icon1_activate(self, widget, event=None):
    """ Hide/show the main window """
    active = self.ui.show_tray_icon1.get_active()
    self.ui.prefsShowTrayIconCheck.set_active(active)
    self.trayicon.set_visible(active)
  # --

  def on_preferences2_activate(self, widget, event=None):
    """ Show preferences """
    self.on_preferences1_activate(None)

  def on_show_features2_activate(self, widget, event=None):
    """ Show features """
    self.on_show_features1_activate(widget)

  # --
  def on_quit2_activate(self, widget):
    """ Quit """
    self.main_close(self)
    return False

  def checkFormats(self):
    formats.recheck()
    active = self.ui.main2FormatCombobox.get_active()
    model = self.ui.main2QualityCombobox.get_model().clear()
    model = self.ui.main2FormatCombobox.get_model()
    model.clear()
    for format in formats.FORMATS.values():
      if format.get()[0] == True:
        model.append([format.__class__.__name__.upper()])
    if active >= 0:
      self.ui.main2FormatCombobox.set_active(active)
    else:
      self.ui.main2FormatCombobox.set_active(0)

  def refreshFeatures(self):
    """ Refreshes the checkmarks in Features window """
    def convert(formatObj, decodeLabel, encodeLabel, tagsLabel):
      """ Get an object, return the right liststore entry """
      encode, decode, tags = gtk.STOCK_NO, gtk.STOCK_NO, gtk.STOCK_NO
      if formatObj.get()[0] == True:
        encode = gtk.STOCK_YES
      if formatObj.get()[1] == True:
        decode = gtk.STOCK_YES
      if formatObj.get()[2] == True:
        tags = gtk.STOCK_YES
      return [formatObj.__class__.__name__.upper(),
              decode, decodeLabel,
              encode, encodeLabel,
              tags, tagsLabel]
    model = self.ui.featuresFeaturesTreeview.get_model()
    model.clear()
    model.append(convert(formats.FORMATS['mp3'], 'lame', 'lame', 'mutagen'))
    model.append(convert(formats.FORMATS['ogg'], 'oggenc', 'oggdec', 'mutagen'))
    model.append(convert(formats.FORMATS['mpc'], 'mppdec', 'mppenc', 'mutagen'))
    model.append(convert(formats.FORMATS['ape'], 'mac', 'mac', 'mutagen'))
    model.append(convert(formats.FORMATS['aac'], 'faad', 'faac', 'mutagen'))
    model.append(convert(formats.FORMATS['ac3'], 'a52dec', 'ffmpeg', _('N/A')))
    model.append(convert(formats.FORMATS['flac'], 'flac', 'flac', 'mutagen'))
    model.append(convert(formats.FORMATS['wv'], 'wavunpak', 'wavpack', 'mutagen'))
    if which('ffmpeg'):
      icon = gtk.STOCK_YES
    else:
      icon = gtk.STOCK_NO
    model.append([_('(Resampling)'), icon, 'ffmpeg', icon, 'ffmpeg', gtk.STOCK_YES, _('N/A')])


  ###
  ### WINDOW WRAPPERS ###
  ###

  def hide(self, widget, event=None):
    """ Wrapper for closing a window non-destructively """
    widget.hide()
    # return True so we don't kill the window
    return True

  def main_close(self, widget, event=None):
    """ Wrapper for quitting """
    if gtk.main_level() > 1:
      gtk.main_quit()
      gobject.idle_add(self.main_close, 100)
    else:
      # do normal stuff I do when the app quits...
      try:
        self.trayicon.set_visible(False)
        gtk.main_quit()
      except RuntimeError, errormesg:
        self.logger.logmsg("INFO", _('gtk.main_quit() encountered a RuntimeError: %s') % errormesg)
    return False


  ## FILE MENU ##
  def on_show_features1_activate(self, widget):
    """ File > Show Features """
    self.refreshFeatures()
    self.ui.features.show()
  
  def remove_filemanager_integration_helper(self, paths):
    """ Helper, holds common parts of the remove integration functions """
    oldLocations = ['%s/.audio-convert-mod/acm-script.sh' % USERHOME,
                    '%s/.audio-convert-mod/remove-converted.sh' % USERHOME]
    for i in paths+oldLocations:
      if os.path.exists(i) and os.path.isfile(i):
        try:
          self.logger.logmsg("INFO", _('Removing file from older release: %s.' % i))
          os.remove(i)
        except Exception, error:
          self.logger.logmsg("WARNING", _('Could not remove file %(a)s: %(b)s') % {'a': i, 'b': error})
      if os.path.exists(i) and os.path.isdir(i):
        try:
          self.logger.logmsg("INFO", _('Removing directory from older release: %s.' % i))
          shutil.rmtree(i)
        except Exception, error:
          self.logger.logmsg("WARNING", _('Could not remove directory %(a)s: %(b)s') % {'a': i, 'b': error})
    return True
  
  def remove_gnome_filemanager_integration(self):
    """ Removes all gnome user scripts/file manager integration """
    self.remove_filemanager_integration_helper(['%s/.gnome2/nautilus-scripts/audio-convert-mod/' % USERHOME])
  
  def remove_kde3_filemanager_integration(self):
    """ Removes all kde3 user scripts/file manager integration """
    paths = ['%s/.kde/share/apps/konqueror/servicemenus/audio-convert-mod.desktop' % USERHOME,
             '%s/.kde/share/apps/konqueror/servicemenus/audio-convert-mod-nofolder.desktop' % USERHOME,
             '%s/.kde/share/apps/konqueror/servicemenus/audio-convert-mod-kde.desktop' % USERHOME]
    self.remove_filemanager_integration_helper(paths)
  
  def remove_kde4_filemanager_integration(self):
    """ Removes all kde4 user scripts/file manager integration """
    self.remove_filemanager_integration_helper(['%s/.kde/share/kde4/services/ServiceMenus/audio-convert-mod-kde.desktop' % USERHOME])
  
  def install_gnome_filemanager_integration(self):
    """ Adds integration to Nautilus in GNOME """
    self.remove_gnome_filemanager_integration()
    # GNOME
    wrapperLocation = formats.which('audio-convert-mod')
    if not wrapperLocation:
      self.logger.logmsg("WARNING", _('Skipping GNOME file manager integration: Could not find audio-convert-mod in $PATH!'))
      return -1
    if os.path.exists('%s/.gnome2/nautilus-scripts/' % USERHOME):
      if not os.path.exists('%s/.gnome2/nautilus-scripts/audio-convert-mod' % USERHOME):
        os.mkdir('%s/.gnome2/nautilus-scripts/audio-convert-mod' % USERHOME, 0755)
      os.symlink(wrapperLocation, '%s/.gnome2/nautilus-scripts/audio-convert-mod/%s' % (USERHOME, _('Convert Files')))
      self.logger.logmsg("INFO", _('Installed GNOME file manager integration'))
    else:
      self.logger.logmsg("WARNING", _('Skipping GNOME file manager integration: nautilus-scripts directory not found'))
      return -2
    return True
  
  def install_kde3_filemanager_integration(self):
    """ Adds integration to Konqueor in KDE3 """
    self.remove_kde3_filemanager_integration()
    if not os.path.exists('%s/audio-convert-mod-kde3.desktop' % INSTALL_DIR):
      self.logger.logmsg("WARNING", _('Skipping KDE file manager integration: KDE desktop file is missing!'))
      return -1
    if os.path.exists('%s/.kde/share/apps/konqueror/servicemenus/' % USERHOME):
      shutil.copy('%s/audio-convert-mod-kde3.desktop' % INSTALL_DIR,
                  '%s/.kde/share/apps/konqueror/servicemenus/audio-convert-mod-kde.desktop' % USERHOME)
      self.logger.logmsg("INFO", _('Installed KDE3 file manager integration'))
    else:
      self.logger.logmsg("WARNING", _('Skipping KDE3 file manager integration: servicemenus directory not found'))
      return -2
    return True

  def install_kde4_filemanager_integration(self):
    """ Adds integration to Dolphin and Konqueor in KDE4 """
    self.remove_kde4_filemanager_integration()
    if not os.path.exists('%s/audio-convert-mod-kde4.desktop' % INSTALL_DIR):
      self.logger.logmsg("WARNING", _('Skipping KDE file manager integration: KDE desktop file is missing!'))
      return -1
    if os.path.exists('%s/.kde/share/kde4/services/ServiceMenus/' % USERHOME):
      shutil.copy('%s/audio-convert-mod-kde4.desktop' % INSTALL_DIR,
                  '%s/.kde/share/kde4/services/ServiceMenus/audio-convert-mod-kde.desktop' % USERHOME)
      self.logger.logmsg("INFO", _('Installed KDE4 file manager integration'))
    else:
      self.logger.logmsg("WARNING", _('Skipping KDE4 file manager integration: ServiceMenu directory not found'))
      return -2
    return True

  def on_quit1_activate(self, widget):
    """ File > Quit """
    self.main_close(widget)

  ## EDIT MENU ##
  def on_preferences1_activate(self, widget):
    """ Open preferences """
    prefs = config.PreferencesConf()
    if int(prefs.get('Preferences', 'ShowTrayIcon')):
      self.ui.prefsShowTrayIconCheck.set_active(True)
    else:
      self.ui.prefsShowTrayIconCheck.set_active(False)

    if int(prefs.get('Preferences', 'TrayIconNotifications')):
      self.ui.prefsNotifyInTrayCheck.set_active(True)
    else:
      self.ui.prefsNotifyInTrayCheck.set_active(False)

    if int(prefs.get('Preferences', 'PauseOnErrors')):
      self.ui.prefsPauseOnErrorsCheck.set_active(True)
    else:
      self.ui.prefsPauseOnErrorsCheck.set_active(False)
    
    # Gnome FMI
    self.ui.prefsIntegrateWithGNOMECheck.set_active(
        os.path.exists('%s/.gnome2/nautilus-scripts/audio-convert-mod/%s' % (USERHOME, _('Convert Files')))
                                                   )
    self.ui.prefsIntegrateWithKDE3Check.set_active(
        os.path.exists('%s/.kde/share/apps/konqueror/servicemenus/audio-convert-mod-kde.desktop' % USERHOME)
                                                  )
    # KDE4 FMI
    self.ui.prefsIntegrateWithKDE4Check.set_active(
        os.path.exists('%s/.kde/share/kde4/services/ServiceMenus/audio-convert-mod-kde.desktop' % USERHOME)
                                                  )
    self.ui.prefsTempFolderEntry.set_text(config.PreferencesConf().get('Preferences', 'TemporaryDirectory'))
    
    self.ui.prefs.show()
  
  def on_prefsTempFolderBrowseButton_clicked(self, widget):
    """ Browse for a temp folder """
    pathBrowser = widgets.PathBrowser(self.ui.chooser, self.ui.prefs)
    pathBrowser.set_action(gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER)
    pathBrowser.set_select_multiple(False)
    response = pathBrowser.run()
    paths = pathBrowser.get_filenames()
    paths.sort()
    pathBrowser.destroy()
    if response != gtk.RESPONSE_OK or not paths:
      return
    self.ui.prefsTempFolderEntry.set_text(paths[0])
    

  ## HELP MENU ##

  def on_about1_activate(self, widget):
    """ Help > About """
    self.ui.about.show()

  ###########
  ## PREFS ##
  ###########

  def on_prefsShowTrayIconCheck_clicked(self, widget):
    prefs = config.PreferencesConf()
    active = self.ui.prefsShowTrayIconCheck.get_active()
    if active:
      prefs.set('Preferences', 'ShowTrayIcon', 1)
    else:
      prefs.set('Preferences', 'ShowTrayIcon', 0)
    self.trayicon.set_visible(active)
    self.ui.show_tray_icon1.set_active(active)
    if not self.ui.main.get_property('visible'):
      self.ui.main.show()

  def on_prefsNotifyInTrayCheck_clicked(self, widget):
    prefs = config.PreferencesConf()
    active = self.ui.prefsNotifyInTrayCheck.get_active()
    if active:
      prefs.set('Preferences', 'TrayIconNotifications', 1)
    else:
      prefs.set('Preferences', 'TrayIconNotifications', 0)
      self.trayicon.set_blinking(False)

  def on_prefsPauseOnErrorsCheck_clicked(self, widget):
    prefs = config.PreferencesConf()
    active = self.ui.prefsShowTrayIconCheck.get_active()
    if active:
      prefs.set('Preferences', 'PauseOnErrors', 1)
    else:
      prefs.set('Preferences', 'PauseOnErrors', 0)
  
  def on_prefsIntegrateWithGNOMECheck_clicked(self, widget):
    if self.ui.prefsIntegrateWithGNOMECheck.get_active():
      self.install_gnome_filemanager_integration()
    else:
      self.remove_gnome_filemanager_integration()
  
  def on_prefsIntegrateWithKDE3Check_clicked(self, widget):
    if self.ui.prefsIntegrateWithKDE3Check.get_active():
      self.install_kde3_filemanager_integration()
    else:
      self.remove_kde3_filemanager_integration()
    
  
  def on_prefsIntegrateWithKDE4Check_clicked(self, widget):
    if self.ui.prefsIntegrateWithKDE4Check.get_active():
      self.install_kde4_filemanager_integration()
    else:
      self.remove_kde4_filemanager_integration()
  
  def on_prefsCloseButton_clicked(self, widget):
    """ close prefs """
    tempdir = self.ui.prefsTempFolderEntry.get_text()
    if not os.path.exists(tempdir):
      self.showError(self.ui.prefs, _('Could not find temporary folder'), _('The temporary folder you have entered does not exist or could not be found. Please choose another.'))
      return False
    if not audio_convert_mod.CheckPerms(tempdir):
      self.showError(self.ui.prefs, _('Invalid temporary folder'), _('Files cannot be saved to this temporary folder. Please choose another.'))
      return False
    prefs = config.PreferencesConf()
    prefs.set('Preferences', 'TemporaryDirectory', self.ui.prefsTempFolderEntry.get_text())
    self.ui.prefs.hide()

  ## ABOUT ##

  def on_aboutWebsiteButton_clicked(self, widget):
    import webbrowser
    webbrowser.open_new('http://www.diffingo.com/opensource/')

  def on_aboutLicenseButton_clicked(self, widget):
    self.ui.license.show()
  
  def on_aboutCreditsButton_clicked(self, widget):
    self.ui.credits.show()
    
  def on_creditsCloseButton_clicked(self, widget):
    self.ui.credits.hide()
  
  def on_licenseCloseButton_clicked(self, widget):
    self.ui.license.hide()
  
  def on_aboutCloseButton_clicked(self, widget):
    self.ui.license.hide()
    self.ui.credits.hide()
    self.ui.about.hide()

  ## FEATURES ##

  def on_featuresCloseButton_clicked(self, widget):
    """ Close features window """
    self.ui.features.hide()

  def on_featuresRefreshButton_clicked(self, widget):
    """ Refresh features """
    self.checkFormats()
    self.refreshFeatures()
  
  ## MAIN ##

  def on_mainBackButton_clicked(self, widget):
    """ Back to previous page """
    currPage = self.ui.mainControlNotebook.get_current_page()
    if self.trayicon.get_blinking():
      self.trayicon.set_blinking(False)
    self.ui.mainControlNotebook.set_current_page(currPage - 1)
    if currPage == 1:
      # if we hit back on second page
      self.ui.mainBackButton.set_sensitive(False)
      self.ui.main2SaveDefaultsButton.hide()
    elif currPage == 3:
      # if we hit back on conversion page
      self.ui.main2SaveDefaultsButton.show()
      if not self.ui.main2advancedSettingsCheck.get_active(): # skip extra page
        self.ui.mainControlNotebook.set_current_page(self.ui.mainControlNotebook.get_current_page() - 1)
    self.ui.mainNextButton.set_sensitive(True)

  def on_mainNextButton_clicked(self, widget):
    """ Advance to next page """
    currPage = self.ui.mainControlNotebook.get_current_page()
    if self.trayicon.get_blinking():
      self.trayicon.set_blinking(False)
    if currPage == 0:
      # on the first page with no files in the treeview
      model = self.ui.main1FilesTreeview.get_model()
      array = audio_convert_mod.liststoreIntoArray(model)
      if array == []:
        self.showError(self.ui.main, _("At least one file is required for a conversion"),
          _("Please select at least one file to convert."))
        return
      else: # retrieve preferences
        prefs = config.PreferencesConf()
        formatName = prefs.get('Defaults', 'Format')
        quality = prefs.get('Defaults', 'Quality')
        extension = prefs.get('Defaults', 'Extension')
        whenExists = prefs.get('Defaults', 'FileExists')
        metadata = prefs.get('Defaults', 'Metadata')
        successfulConversion = prefs.get('Defaults', 'SuccessfulConversion')
        successfulConversionDest = prefs.get('Defaults', 'SuccessfulConversionDest')
        outputFolder = prefs.get('Defaults', 'OutputFolder')
        resample = prefs.get('Defaults', 'Resample')
        model = self.ui.main2FormatCombobox.get_model()
        iter = model.get_iter_first()
        format = formats.FORMATS[formatName.lower()]
        if format.get()[0] == True: # if we can encode to this format, select it
          while iter:
            if model.get_value(iter, 0).lower() == formatName.lower():
              self.ui.main2FormatCombobox.set_active_iter(iter)
              self.ui.main2ExtensionCombobox.set_active(int(extension))
              active = 0
              for pair in format.get()[3]: # for i in format.__qualities
                if pair[0] == quality:
                  self.ui.main2QualityCombobox.set_active(active)
                else:
                  active += 1
              break
            iter = model.iter_next(iter)
        else: # otherwise, ignore
          self.ui.main2FormatCombobox.set_active(0)
          self.ui.main2QualityCombobox(0)
          self.ui.main2ExtensionCombobox.set_active(0)
        
        self.ui.__getattr__('main2ExistsRadio%s' % whenExists).set_active(True)
        self.ui.__getattr__('main2MetatagRadio%s' % metadata).set_active(True)
        self.ui.__getattr__('main2UponSuccessRadio%s' % successfulConversion).set_active(True)
        if resample == '-1':
          self.ui.main2ResampleCheck.set_active(False)
        else:
          self.ui.main2ResampleCheck.set_active(True)
          self.ui.main2ResampleCombo.set_active(int(resample))
        self.ui.main2RemoveDiacriticsCheck.set_active(prefs.get('Defaults', 'RemoveDiacritics') == '1')
        if outputFolder.lower() == 'off':
          self.ui.main2OutputFolderRadio1.set_active(True)
        else:
          self.ui.main2OutputFolderRadio2.set_active(True)
          self.ui.main2OutputFolderFilechooser.set_current_folder(outputFolder)
        if successfulConversion.lower() == '2':
          self.ui.main2SuccessOutputFolderFilechooser.set_current_folder(successfulConversionDest)
      # either way, we need to show button...
      self.ui.mainBackButton.set_sensitive(True)
      self.ui.main2SaveDefaultsButton.show()
    elif currPage == 1 and not self.ui.main2advancedSettingsCheck.get_active():
      self.ui.mainControlNotebook.set_current_page(currPage + 1)
    elif currPage == 3:
      # if we hit next on conversion page
      self.ui.mainNextButton.set_sensitive(False)
      self.ui.mainBackButton.set_sensitive(False)
    # Don't use currPage below otherwise the if check for not advanced settings won't work
    self.ui.mainControlNotebook.set_current_page(self.ui.mainControlNotebook.get_current_page() + 1)
    # this comes on it's own because it needs to happen _after_ page change
    if (currPage == 1 and not self.ui.main2advancedSettingsCheck.get_active()) \
    or (currPage == 2 and self.ui.main2advancedSettingsCheck.get_active()):
      # if we hit next to start the conversion
      self.ui.main2SaveDefaultsButton.hide()
      self.ui.mainNextButton.set_sensitive(False)
      self.ui.mainBackButton.set_sensitive(False)
      try:
        self.startConversion()
      except:
        import traceback
        etb = traceback.extract_tb(sys.exc_info()[2])
        traceback = _('Traceback:\n')
        for tub in etb:
          f, l, m, c = tub # file, lineno, function, codeline
          traceback += _('File: %(a)s, line %(b)s, in %(c)s\n') % {'a': f, 'b': l, 'c': m}
          traceback += ' %s \n' % c
        traceback += '%s: %s\n' % (sys.exc_info()[0], sys.exc_info()[1]) #etype, evalue
        self.showError(self.ui.main,
                       _('An error occurred while converting files'),
                       _('An unexpected error occurred while converting files.\n' + \
                         'The current file may left in an incomplete state.'),
                       details=traceback)
        self.ui.mainNextButton.set_sensitive(True)
        self.ui.mainBackButton.set_sensitive(True)

  def on_main2ResampleCheck_toggled(self, widget):
    if self.ui.main2ResampleCheck.get_active():
      self.ui.main2ResampleCombo.set_sensitive(True) # 44100 Hz
      self.ui.main2ResampleCombo.set_active(4)
    else:
      self.ui.main2ResampleCombo.set_sensitive(False)
      self.ui.main2ResampleCombo.set_active(-1)

  def on_main2SaveDefaultsButton_clicked(self, widget):
    """ Save preferences """
    prefs = config.PreferencesConf()
    prefs.set('Defaults', 'Format', self.ui.main2FormatCombobox.get_active_text())
    model = self.ui.main2QualityCombobox.get_model()
    iter = self.ui.main2QualityCombobox.get_active_iter()
    prefs.set('Defaults', 'Quality', model.get_value(iter, 0))
    prefs.set('Defaults', 'Extension', self.ui.main2ExtensionCombobox.get_active())
    prefs.set('Defaults', 'RemoveDiacritics', int(self.ui.main2RemoveDiacriticsCheck.get_active()))
    active = None
    if self.ui.main2ExistsRadio1.get_active():
      active = 1
    elif self.ui.main2ExistsRadio2.get_active():
      active = 2
    elif self.ui.main2ExistsRadio3.get_active():
      active = 3
    prefs.set('Defaults', 'FileExists', active)
    active = None
    if self.ui.main2MetatagRadio1.get_active():
      active = 1
    elif self.ui.main2MetatagRadio2.get_active():
      active = 2
    prefs.set('Defaults', 'Metadata', active)
    active = None
    if self.ui.main2UponSuccessRadio1.get_active():
      active = 1
    elif self.ui.main2UponSuccessRadio2.get_active():
      active = 2
      prefs.set('Defaults', 'SuccessfulConversionDest', self.ui.main2SuccessOutputFolderFilechooser.get_current_folder())
    elif self.ui.main2UponSuccessRadio3.get_active():
      active = 3
    prefs.set('Defaults', 'SuccessfulConversion', active)
    if self.ui.main2OutputFolderRadio1.get_active():
      prefs.set('Defaults', 'OutputFolder', 'Off')
    elif self.ui.main2OutputFolderRadio2.get_active():
      prefs.set('Defaults', 'OutputFolder', self.ui.main2OutputFolderFilechooser.get_current_folder())
    if not self.ui.main2ResampleCheck.get_active():
      prefs.set('Defaults', 'Resample', '-1')
    else:
      prefs.set('Defaults', 'Resample', self.ui.main2ResampleCombo.get_active())

  def on_main1AddButton_clicked(self, widget):
    """ Add file(s) """
    ffilterList = []
    for key in formats.FORMATS.keys():
      if formats.FORMATS[key].get()[1]:
        for extension in formats.FORMATS[key].extensions:
          ffilterList.append('*.%s' % extension.lower())
          ffilterList.append('*.%s' % extension.upper())
    ffilterList.append(_('Supported Audio Files'))
    pathBrowser = widgets.PathBrowser(self.ui.chooser, self.ui.main, ffilterList)
    pathBrowser.set_action(gtk.FILE_CHOOSER_ACTION_OPEN)
    pathBrowser.set_select_multiple(True)
    response = pathBrowser.run()
    paths = pathBrowser.get_filenames()
    pathBrowser.destroy()
    if response != gtk.RESPONSE_OK:
      return
    errors = self.addToSelectFilesFilesTreeview(paths)
    if errors != []:
      self.showError(self.ui.main, _('Could not add all of the requested files'), _('Not all files could be added.'), details='\n'.join(errors))

  def on_main1AddDirectoryButton_clicked(self, widget):
    """ Add files by selecting a folder """
    pathBrowser = widgets.PathBrowser(self.ui.chooser, self.ui.main)
    pathBrowser.set_action(gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER)
    pathBrowser.set_select_multiple(True)
    response = pathBrowser.run()
    paths = pathBrowser.get_filenames()
    paths.sort()
    pathBrowser.destroy()
    if response != gtk.RESPONSE_OK:
      return
    fileList = []
    for folder in paths:
      files = os.listdir(folder)
      files.sort()
      for filename in files:
        if not os.path.isdir(os.path.join(folder, filename)):
          fileList.append(os.path.join(folder, filename) )
    errors = self.addToSelectFilesFilesTreeview(fileList)
    if errors != []:
      self.showError(self.ui.main, _('Could not add all of the requested files'), _('Not all files could be added.'), details='\n'.join(errors))

  def on_main1RemoveButton_clicked(self, widget):
    """ Remove all selected files """
    model, paths = self.ui.main1FilesTreeview.get_selection().get_selected_rows()
    for i in paths:
      model, paths = self.ui.main1FilesTreeview.get_selection().get_selected_rows()
      model.remove(model.get_iter(paths[0]))

  def on_main2FormatRefreshButton_clicked(self, widget):
    """ Refresh the list of valid formats """
    self.checkFormats()

  def on_main2FormatCombobox_changed(self, widget):
    """ The format changed, update qualities and extensions combobox """
    formatModel = self.ui.main2FormatCombobox.get_model()
    formatActive = self.ui.main2FormatCombobox.get_active()
    if formatActive == -1:
      return
    formatIter = formatModel.get_iter(formatActive)
    formatValue = formatModel.get_value(formatIter, 0).split(' ')[0]
    if formatValue == 'MP3' or formatValue == 'OGG' or formatValue == 'FLAC' or formatValue == 'AAC': # supports tags
      self.ui.main2MetatagRadio1.set_sensitive(True)
      self.ui.main2MetatagRadio2.set_sensitive(True)
    else:
      self.ui.main2MetatagRadio1.set_sensitive(False)
      self.ui.main2MetatagRadio2.set_sensitive(False)

    qualityModel = self.ui.main2QualityCombobox.get_model()
    qualityModel.clear()

    extensionModel = self.ui.main2ExtensionCombobox.get_model()
    extensionModel.clear()
    for row in formats.FORMATS[formatValue.lower()].get()[3]:
      qualityModel.append(row)
    for i in formats.FORMATS[formatValue.lower()].extensions:
      extensionModel.append(['.%s' % i])
    self.ui.main2QualityCombobox.set_active(0)
    self.ui.main2ExtensionCombobox.set_active(0)

  def on_main2OutputFolderFilechooser_current_folder_changed(self, widget):
    """ Set the appropriate radiobutton """
    self.ui.main2OutputFolderRadio2.set_active(True)

  def on_main2SuccessOutputFolderFilechooser_current_folder_changed(self, widget):
    """ Set the appropriate radiobutton """
    self.ui.main2UponSuccessRadio2.set_active(True)

  def startConversion(self):
    """ Runs the conversion """
    def callback(model, path, iter, user_data):
      """ Append value to user_data """
      files = user_data[0]
      directory = model.get_value(iter, 1)
      filename = model.get_value(iter, 2)
      files.append('%s/%s' % (directory, filename))

    def updateProgress(user_data):
      """ Updates current file progress """
      self = user_data
      if self.fraction == -1:
        # this means we're pulsing, so don't interfere.
        self.ui.main3FileProgress.set_text('Please wait...')
        return True
      if self.fraction == 100 or self.fraction == "":
        self.ui.main3FileProgress.set_fraction(float(1))
        self.ui.main3FileProgress.set_text('100%')
        self.logger.logmsg("DEBUG", _("No longer updating the progressbar"))
        return False
      self.ui.main3FileProgress.set_fraction(float(self.fraction))
      self.ui.main3FileProgress.set_text('%i%%' % int(float(self.fraction)*100))
      return True
    
    def nextFile(currFile):
      self.ui.main3FileProgress.set_fraction(float(1))
      self.ui.main3FileProgress.set_text('100%')
      self.setStatus(_('Idle'))
      while gtk.events_pending():
        gtk.main_iteration()
      return currFile+1
    
    def escape(name):
      """ escape special characters """
      return '&amp;'.join(name.split('&'))

    def escapeSingleQuote(name):
      """ escape single quotes """
      return '\'\\\'\''.join(name.split('\''))

    def badExitValue(sub):
      """ Popup notification for bad exit value """
      self.showWarning(self.ui.main,
                      _('An error occurred while converting files'),
                      _('There was an error while running the conversion, or the process was stopped unexpectedly.'),
                      details=_("The process returned non-zero value `%i'." % sub.poll())
                      )
      stderr = sub.stderr.readlines()
      stdout = sub.stdout.readlines()
      self.logger.logmsg("DEBUG", _("An unexpected error occurred while running command: %s") % command)
      self.logger.logmsg("DEBUG", _("stderr: %s") % '\n'.join(stderr))
      self.logger.logmsg("DEBUG", _("stdout: %s") % '\n'.join(stdout))

    def refreshCurrentFile(self, i, currFile, total):
      """ Refreshes labels for the current file """
      self.ui.main3CurrentFileLabel.set_label(i.split(os.sep)[-1])
      self.ui.main3ConvertProgress.set_text( _('%(a)i/%(b)i file(s) completed' % {'a': currFile, 'b': total} ) )
      self.ui.main3ConvertProgress.set_fraction(float(currFile)/float(total))

    self.processId = None
    self.ui.main3SkipFileButton.set_sensitive(True)
    self.ui.main3CancelButton.set_sensitive(True)
    # get output name and object
    outputFormat = self.ui.main2FormatCombobox.get_active_text()
    outputFormatObject = formats.FORMATS[outputFormat.lower()]

    self.setStatus(_('Idle'))

    # decode only?
    self.decodeonly = False
    if outputFormat == 'WAV':
      self.decodeonly = True

    # quality for label
    iter = self.ui.main2QualityCombobox.get_active_iter()
    quality = self.ui.main2QualityCombobox.get_model().get_value(iter, 1)
    self.ui.main3ConvertToLabel.set_text('%(a)s @ %(b)s' % {'a': outputFormat, 'b': quality})
    # numberic quality only
    quality = int(self.ui.main2QualityCombobox.get_model().get_value(iter, 0))
    
    tempdir = config.PreferencesConf().get('Preferences', 'TemporaryDirectory')
    
    # setup
    files = []
    model = self.ui.main1FilesTreeview.get_model()
    model.foreach(callback, [files])
    self.fraction = 0
    # update file progress every 500 miliseconds
    gobject.timeout_add(100, updateProgress, self)
    total = len(files)
    currFile = 0
    progressBar = widgets.ProgressBar(self.ui.main3FileProgress)
    for i in files:
      if self.processId == -1:
        # don't continue onto next file if we hit cancel
        return
      self.setStatus(_('Initializing'))
      # get input format and object
      inputFormat = formats.getFileType(i).__class__.__name__.upper()
      inputFormatObject = formats.getFileType(i)

      # encode only?
      self.encodeonly = False
      if inputFormat == 'WAV':
        self.encodeonly = True
      # update file labels
      refreshCurrentFile(self, i, currFile, total)
      
      if inputFormat == outputFormat:
        self.logger.logmsg("DEBUG", _('Input format == output format! Skipping %s.' % i))
        currFile = nextFile(currFile)
        continue
      
      #decode
      tags = None
      if outputFormatObject.get()[2] and inputFormatObject.get()[2]: # only if tags are supported on both sides
        self.logger.logmsg("DEBUG", _("Retrieving tags/metadata"))
        self.setStatus(_('Retrieving tags/metadata'))
        if self.ui.main2MetatagRadio1.get_active():
          tags = inputFormatObject.getTags(i)
        elif self.ui.main2MetatagRadio2.get_active():
          self.ui.tags.show()
          title = self.ui.tagsTitleEntry.set_text('')
          artist = self.ui.tagsArtistEntry.set_text('')
          album = self.ui.tagsAlbumEntry.set_text('')
          year = self.ui.tagsYearEntry.set_text('')
          track = self.ui.tagsTrackEntry.set_text('')
          genre = self.ui.tagsGenreEntry.set_text('')
          bounds = self.ui.tagsCommentsTextview.get_buffer().set_text('')
          response = self.ui.tags.run()
          self.ui.tags.hide()
          title = self.ui.tagsTitleEntry.get_text()
          artist = self.ui.tagsArtistEntry.get_text()
          album = self.ui.tagsAlbumEntry.get_text()
          year = self.ui.tagsYearEntry.get_text()
          track = self.ui.tagsTrackEntry.get_text()
          genre = self.ui.tagsGenreEntry.get_text()
          bounds = self.ui.tagsCommentsTextview.get_buffer().get_bounds()
          comments = self.ui.tagsCommentsTextview.get_buffer().get_text(bounds[0], bounds[1])
          tags = [title, artist, album, year, track, genre, comments]
      if not self.encodeonly:
        self.logger.logmsg("DEBUG", _("Decoding file"))
        self.setStatus(_('Decoding'))
        if self.decodeonly:
          if self.ui.main2ExistsRadio3.get_active(): # wav exists, skip file selected...
            currFile = nextFile(currFile)
            continue
          wavfile = formats.getNewExt('wav', i)
          # FIXME FIXME FIXME
          #outputFolder = self.ui.main2OutputFolderFilechooser.get_current_folder()
          #newname = os.path.join(outputFolder, os.path.split(formats.getNewExt(extension.lower(), i))[1])
          while os.path.exists(wavfile):
            if self.ui.main2ExistsRadio1.get_active(): # append .converted
              wavfile += '.converted'
            elif self.ui.main2ExistsRadio2.get_active(): # overwrite
              try:
                self.logger.logmsg("DEBUG", _("Removing existing file %s") % newname)
                os.remove(wavfile)
              except Exception, errormsg:
                self.logger.logmsg("WARNING", _("Could not remove existing file: %s") % errormsg)
              break
            else: # just incase
              wavfile += '.converted'
        else:
          wavfile = os.path.join(tempdir, 'acm-%s' % os.path.split(formats.getNewExt('wav', i))[1])
        sub, command = inputFormatObject.decode(escapeSingleQuote(i), escapeSingleQuote(wavfile))
        self.logger.logmsg("DEBUG", _("Executing command: %s") % command)
        self.processId = sub.pid
        if inputFormat == 'AC3': # a52dec doesn't support progress
          self.fraction = -1
          progressBar.startPulse()
          while sub.poll() == None:  
            while gtk.events_pending():
              gtk.main_iteration()
            time.sleep(0.01)
          progressBar.stopPulse()
        else:
          while sub.poll() == None:
            try:
              if self.decodeonly:
                self.fraction = float(''.join(sub.stdout.readline().split('\n')[:-1]))
              else:
                self.fraction = float(''.join(sub.stdout.readline().split('\n')[:-1]))/2
            except ValueError:
              self.fraction = '.5'
            while gtk.events_pending():
              gtk.main_iteration()
            # FIXME: This causes lame encode to lag
            #time.sleep(0.01)
        if sub.poll() != 0 and sub.poll() != -9:
          badExitValue(sub)
      if self.processId == -1:
        # don't continue onto next file if we hit cancel
        return
      if self.processId == -2:
        # skip current file
        currFile = nextFile(currFile)
        continue

      #options
      # we can't escape now, otherwise the path.exists will fail when quotes are in the filename
      self.logger.logmsg("DEBUG", _("Retrieving options"))
      self.setStatus(_('Retrieving options'))
      extension = self.ui.main2ExtensionCombobox.get_active_text().strip('.')
      if self.ui.main2OutputFolderRadio1.get_active():
        newname = formats.getNewExt(extension.lower(), i)
      elif self.ui.main2OutputFolderRadio2.get_active():
        outputFolder = self.ui.main2OutputFolderFilechooser.get_current_folder()
        newname = os.path.join(outputFolder, os.path.split(formats.getNewExt(extension.lower(), i))[1])
      else: # just incase
        newname = formats.getNewExt(extension.lower(), i)
      if self.ui.main2RemoveDiacriticsCheck.get_active():
        newname = audio_convert_mod.remove_diacritics(newname)
      if not self.ui.main2ExistsRadio3.get_active(): # otherwise, this skips encode
        while os.path.exists(newname):
          if self.ui.main2ExistsRadio1.get_active(): # append .converted
            newname += '.converted'
            if outputFormat == 'MPC' and not newname.endswith('.mpc'):
              # a stupid hack because mpc can't encode to something that doesn't end in .mpc
              newname += '.mpc'
          elif self.ui.main2ExistsRadio2.get_active() and os.path.exists(newname) and outputFormat != 'WAV': #overwrite
            try:
              self.logger.logmsg("DEBUG", _("Removing existing file %s") % newname)
              os.remove(newname)
            except Exception, errormsg:
              self.logger.logmsg("WARNING", _("Could not remove existing file: %s") % errormsg)
            break
          else: # we should NEVER be here, but just incase.
            newname += '.converted'
        # Resample audio
        if self.ui.main2ResampleCheck.get_active():
          resampleHz = self.ui.main2ResampleCombo.get_active_text()[:-3]
          self.setStatus(_('Resampling'))
          self.logger.logmsg("DEBUG", _("Resampling WAV file %s") % wavfile)
          sub, command = formats.resample(escapeSingleQuote(wavfile), resampleHz)
          self.logger.logmsg("DEBUG", _("Executing command: %s") % command)
          self.fraction = -1
          progressBar.startPulse()
          while sub.poll() == None:
            while gtk.events_pending():
              gtk.main_iteration()
            time.sleep(0.01)
          progressBar.stopPulse()
          tmpfile = os.path.splitext(wavfile)
          tmpfile = '%s.tmp%s' % tmpfile
          # Move resampled wav over original
          os.rename(tmpfile, wavfile)
        if not self.decodeonly:
          if self.encodeonly:
            wavfile = i
          #encode
          self.logger.logmsg("DEBUG", _("Encoding %(a)s to %(b)s @ %(c)s %(d)s") % {'a': wavfile, 'b': newname, 'c': quality, 'd': outputFormat})
          self.setStatus(_('Encoding'))
          # escape quotes with escapeSingleQuote(newname)
          sub, command = outputFormatObject.encode(escapeSingleQuote(wavfile), escapeSingleQuote(newname), quality)
          self.logger.logmsg("DEBUG", _("Executing command: %s") % command)
          self.processId = sub.pid
          if outputFormat == 'AC3': # ffmpeg doesn't support progress
            self.fraction = -1
            progressBar.startPulse()
            while sub.poll() == None:
              while gtk.events_pending():
                gtk.main_iteration()
              time.sleep(0.01)
            progressBar.stopPulse()
          else:
            while sub.poll() == None:
              try:
                if self.encodeonly:
                  self.fraction = float(''.join(sub.stdout.readline().split('\n')[:-1]))
                else:
                  self.fraction = float(''.join(sub.stdout.readline().split('\n')[:-1]))/2 + .5
              except ValueError:
                self.fraction = 1
              while gtk.events_pending():
                gtk.main_iteration()
              # See FIXME about Lame
              #time.sleep(0.01)
          if sub.poll() != 0 and sub.poll() != -9:
            badExitValue(sub)
        #tags
        self.logger.logmsg("DEBUG", _("Setting tags/metadata: %s") % tags)
        self.setStatus(_('Setting tags/metadata'))
        if tags and outputFormatObject.get()[2]: # if tags are supported:
          outputFormatObject.setTags(newname, tags)
        
        
        if sub.poll() == 0:
          if os.path.exists(i):
            if self.ui.main2UponSuccessRadio2.get_active():
              successDest = self.ui.main2SuccessOutputFolderFilechooser.get_current_folder()
              self.logger.logmsg("DEBUG", _("Moving original file `%(a)s\' to `%(b)s\'") % {'a': i, 'b': successDest})
              try:
                shutil.move(i, successDest)
              except OSError:
                self.logger.logmsg("DEBUG", _("File `%s\' could not be moved! Ignoring.") % i)
            elif self.ui.main2UponSuccessRadio3.get_active():
              if self.ui.main2ExistsRadio2.get_active():
                self.logger.logmsg("DEBUG", _("Skipping removing original file `%s\', it was overwriten!") % i)
              else:
                self.logger.logmsg("DEBUG", _("Removing original file `%s\'") % i)
                try:
                  os.remove(i)
                except OSError:
                  self.logger.logmsg("WARNING", _("File `%s\' could not be removed! Ignoring.") % i)
        elif sub.poll() == -9: # file skipped, process killed
          if os.path.exists(newname):
            try:
              os.remove(newname)
            except OSError:
              self.logger.logmsg("DEBUG", _("Converted file `%s\' was skipped, but could not be removed! Ignoring.") % i)
        else:
          self.logger.logmsg("ERROR", _("Bad exit status %(a)s on conversion `%(b)s\', skipping (re)move options if any") % {'a': sub.poll(), 'b': i})
      
      # setup for next file
      self.logger.logmsg("DEBUG", _("Cleaning up"))
      self.setStatus(_('Cleanup'))
      if outputFormat != 'WAV' and inputFormat != 'WAV': # if the source or out is wave, don't delete!
        self.logger.logmsg("DEBUG", _("Removing wav file `%s\'") % wavfile)
        try:
          os.remove(wavfile)
        except OSError:
          self.logger.logmsg("WARNING", _("File `%s\' not found! Ignoring.") % wavfile)
      if os.path.exists(newname):
        if outputFormat == 'MPC' and newname.endswith('.mpc.converted.mpc'):
          # because mppenc can't encode to something that doesn't end in .mpc
          newname2 = newname
          newname = '.converted'.join(newname.split('.converted.mpc'))
          try:
            os.rename(newname2, newname)
          except OSError:
            self.logger.logmsg("DEBUG", _("Could not move `%(a)s\' to `%(b)s\'! Ignoring.") % {'a': newname2, 'b': newname})
      currFile = nextFile(currFile)
      # end of loop
    self.fraction = 100
    self.ui.main3ConvertProgress.set_text( _('%(a)i/%(b)i file(s) completed' % {'a': currFile, 'b': total} ) )
    self.ui.main3ConvertProgress.set_fraction(float(currFile)/float(total))
    self.ui.main3SkipFileButton.set_sensitive(False)
    self.ui.main3CancelButton.set_sensitive(False)
    self.ui.mainBackButton.set_sensitive(True)
    self.ui.mainNextButton.set_sensitive(True)
    self.trayNotify(_('Conversion Complete'),
                      _('Converting files to %(a)s @ %(b)s has completed.') % {'a': outputFormat, 'b': self.ui.main2QualityCombobox.get_model().get_value(iter, 1)})

  def on_main3CancelButton_clicked(self, widget):
    """ Cancel All """
    self.on_main3SkipFileButton_clicked(None)
    self.processId = -1
    self.ui.main3ConvertProgress.set_text(_('Cancelled.'))
    self.ui.main3ConvertProgress.set_fraction(float(1))
    self.ui.mainBackButton.set_sensitive(True)
    self.ui.mainNextButton.set_sensitive(True)


  def on_main3SkipFileButton_clicked(self, widget):
    """ Skip current file """
    self.ui.main3FileProgress.set_text(_('Cancelled.'))
    self.ui.main3FileProgress.set_fraction(float(1))
    if self.processId >= 2 and self.processId != None:
      try:
        os.kill(self.processId, 9)
      except:
        self.logger.logmsg("DEBUG", _("Could not kill process with PID %s") % self.processId)
    self.processId = -2

  def on_main4NewButton_clicked(self, widget):
    """ Start over """
    self.ui.mainBackButton.set_sensitive(True)
    self.ui.mainNextButton.set_sensitive(True)
    self.prepareForNewConversion()
  
  def on_main4QuitButton_clicked(self, widget):
    """ Quit """
    self.main_close(None)

# ***********************************************************************

# Only if we're in main execution
if __name__ == "__main__":
  verbose = False
  
  try:
    avalableOptions = ["help", "verbose"]
    # letter = plain options, letter: = option with an arg
    (opts, rest_args) = getopt.gnu_getopt(sys.argv[1:],"hv", avalableOptions)
  except (getopt.GetoptError), error:
    usage(str(error))
    sys.exit(1)
  
  # Remove options from paths
  paths = sys.argv[1:] # includes everything
  for opt in opts:
    for opt2 in opt:
      try:
        paths.remove(opt2) # removes valid options from paths
      except:
        pass
  
  # Parse args, take action
  if opts:
    for (opt, value) in opts:
      if opt == "-h" or opt == "--help":
        usage('')
        sys.exit(1)
      if opt == "-v" or opt == "--verbose":
        verbose = True
  try:
    # Startup the application and call the gtk event loop
    MainApp = acmApp(verbose, paths)
    gtk.main()
  except KeyboardInterrupt:
    # ctrl+c?
    MainApp.main_close(None)

