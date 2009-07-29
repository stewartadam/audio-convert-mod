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
The various formats audio-convert-mod supports.

Each format is a class:
  __encode = bool
  __decode = bool
  extension = ['ext1', 'ext2'] /* ALL IN lowercase */
  __qualities = [['quality#','desc'], ['quality#','desc']]
  check(self): Checks for any required programs
  decode(file): (decode file into WAV)
  encode(wavfile): (encode WAV into format)

To add support for new formats, add a entry under checkFormat() and create
the new format functions.

** Remember when making new formats that Windows cannot handle single-quotes,
   only double quotes.
"""

import os
import subprocess
from audio_convert_mod.i18n import _
from audio_convert_mod.const import *

environ = {'PATH': str(os.getenv('PATH'))}

def getNewExt(ext, filename):
    return '%s.%s' % ('.'.join(filename.split('.')[:-1]), ext)

""" Check if the required programs exist """
class wav:
  """ ?wav >> ?wav  """
  def __init__(self):
    """ Initialize """
    self.__encode = True
    self.__decode = True
    self.__tags = False
    self.extensions = ['wav']
    self.check()
    self.__qualities = [
    ['0', _('(Based on original file)')]
                       ]

  def check(self):
    """ Check if the required program(s) exist """
    pass

  def decode(self, filename, newname):
    command = "echo .5"
    sub = subprocess.Popen(command, shell=True, env=environ, stderr=subprocess.PIPE, stdout=subprocess.PIPE, stdin=subprocess.PIPE)
    return sub, command

  def encode(self, filename, newname, quality):
    command = "echo 1"
    sub = subprocess.Popen(command, shell=True, env=environ, stderr=subprocess.PIPE, stdout=subprocess.PIPE, stdin=subprocess.PIPE)
    return sub, command

  def get(self):
    """ Return all information on the format """
    return [self.__encode, self.__decode, self.__tags, self.__qualities]

# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------

class mp3:
  """ Lame >> MP3 """
  def __init__(self):
    """ Initialize """
    self.__encode = False
    self.__decode = False
    self.__tags = False
    self.extensions = ['mp3']
    self.check()
    self.__qualities = [
    ['56', '56 kbps'],
    ['96', '96 kbps'],
    ['128', '128 kbps'],
    ['160', '160 kbps'],
    ['192', '192 kbps'],
    ['256', '256 kbps'],
    ['320', '320 kbps']
                       ]

  def check(self):
    """ Check if the required program(s) exist """
    if which('lame'):
      self.__encode, self.__decode = True, True
    else:
      self.__encode, self.__decode = False, False
    if which('id3info') and which('id3tag'):
      self.__tags = True
    else:
      self.__tags = False

  def get(self):
    """ Return all information on the format """
    return [self.__encode, self.__decode, self.__tags, self.__qualities]

  def decode(self, filename, newname):
    """ Decodes a MP3 file """
    if MSWINDOWS:
      command = 'lame.exe --decode --mp3input "%(a)s" "%(b)s" 2>&1 | awk.exe -vRS="\\r" -F"[ /]+" "(NR>2){print $2/$3;fflush();}"' % {'a': filename, 'b': newname}
    else:
      command = "lame --decode --mp3input '%(a)s' '%(b)s' 2>&1 | awk -vRS='\\r' -F'[ /]+' '(NR>2){print $2/$3;fflush();}'" % {'a': filename, 'b': newname}
    sub = subprocess.Popen(command, shell=True, env=environ, stderr=subprocess.PIPE, stdout=subprocess.PIPE, stdin=subprocess.PIPE)
    return sub, command

  def encode(self, filename, newname, quality):
    """ Encodes a new MP3 file """
    if MSWINDOWS:
      command = 'lame.exe -m auto --preset cbr %(a)i "%(b)s" "%(c)s" 2>&1 | awk.exe -vRS="\\r" "(NR>3){gsub(/[()%%|]/,\\" \\");if($1 != \\"\\") print $2/100;fflush();}"' % {'a': quality, 'b': filename, 'c': newname}
    else:
      command = "lame -m auto --preset cbr %(a)i '%(b)s' '%(c)s' 2>&1 | awk -vRS='\\r' '(NR>3){gsub(/[()%%|]/,\" \");if($1 != \"\") print $2/100;fflush();}'" % {'a': quality, 'b': filename, 'c': newname}
    sub = subprocess.Popen(command, shell=True, env=environ, stderr=subprocess.PIPE, stdout=subprocess.PIPE, stdin=subprocess.PIPE)
    return sub, command

  def getTags(self, filename):
    """ Retrieves the metadata from filename """
    if MSWINDOWS:
      return None
    command = "id3info '%(a)s'" % {'a': filename}
    sub = subprocess.Popen(command, shell=True, env=environ, stderr=subprocess.PIPE, stdout=subprocess.PIPE, stdin=subprocess.PIPE)
    sub.wait()
    content = sub.stdout.read().split('\n')
    tags = []
    for prefix in ['TIT2', 'TPE1', 'TALB', 'TYER', 'TRCK',
                   'TCON', 'COMM']:
      tag = ''
      for line in content:
        if line.strip().startswith('=== %s' % prefix):
          content.remove(line)
          tag = ': '.join(line.strip().split(': ')[1:])
          if prefix == 'TCON':
            tag = tag[1:-1]
          if prefix == 'COMM' and tag.startswith('()[XXX]'):
            tag = ': '.join(tag.strip().split(': ')[1:])
          break
      # we append what was found, or blank then move on to next prefix
      tags.append(tag)
    return tags

  def setTags(self, filename, tags):
    """ Sets the metadata on filename """
    if MSWINDOWS:
      return
    command = "id3tag '%(a)s' --song='%(b)s' --artist='%(c)s' --album='%(d)s' --year='%(e)s' --track='%(f)s' --genre='%(g)s' --comment='%(h)s' " % {'a': filename, 'b': tags[0], 'c': tags[1], 'd': tags[2], 'e': tags[3], 'f': tags[4], 'g': tags[5], 'h': tags[6]}
    sub = subprocess.Popen(command, shell=True, env=environ, stderr=subprocess.PIPE, stdout=subprocess.PIPE, stdin=subprocess.PIPE)
    sub.wait()

# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------

class flac:
  """ flac >> flac """
  def __init__(self):
    """ Initialize """
    self.__encode = False
    self.__decode = False
    self.__tags = False
    self.extensions = ['flac']
    self.check()
    self.__qualities = [
    ['0', _('Lossless, fastest compression (level 0)')],
    ['2', _('Lossless, fast compression (level 2)')],
    ['4', _('Lossless, moderate compression (level 4)')],
    ['6', _('Lossless, high compression (level 6)')],
    ['8', _('Lossless, highest compression (level 8)')]
                       ]

  def check(self):
    """ Check if the required program(s) exist """
    if which('flac'):
      self.__encode, self.__decode = True, True
    else:
      self.__encode, self.__decode = False, False
    if which('metaflac'):
      self.__tags = True
    else:
      self.__tags = False

  def get(self):
    """ Return all information on the format """
    return [self.__encode, self.__decode, self.__tags, self.__qualities]
    
  def getTags(self, filename):
    """ Retrieves the metadata from filename """
    if MSWINDOWS:
      return None
    tags = []
    command = "metaflac --no-filename '%(a)s' --show-tag=title --show-tag=artist --show-tag=album --show-tag=date --show-tag=tracknumber --show-tag=genre --show-tag=description" % {'a': filename}
    sub = subprocess.Popen(command, shell=True, env=environ, stderr=subprocess.PIPE, stdout=subprocess.PIPE, stdin=subprocess.PIPE)
    sub.wait()
    content = sub.stdout.read().split('\n')[:-1]
    for tag in content:
      tags.append('='.join(tag.split('=')[1:]))
    return tags

  def setTags(self, filename, tags):
    """ Sets the metadata on filename """
    if MSWINDOWS:
      return
    command = "metaflac --remove-all-tags '%(a)s' --set-tag title='%(b)s' --set-tag artist='%(c)s' --set-tag album='%(d)s' --set-tag date='%(e)s' --set-tag tracknumber='%(f)s' --set-tag genre='%(g)s' --set-tag description='%(h)s'" % {'a': filename, 'b': tags[0], 'c': tags[1], 'd': tags[2], 'e': tags[3], 'f': tags[4], 'g': tags[5], 'h': tags[6]}
    sub = subprocess.Popen(command, shell=True, env=environ, stderr=subprocess.PIPE, stdout=subprocess.PIPE, stdin=subprocess.PIPE)
    sub.wait()
    
  def decode(self, filename, newname):
    """ Decodes a FLAC file """
    if MSWINDOWS:
      command = 'flac.exe -d -f "%(a)s" -o "%(b)s" 2>&1 | awk.exe -vRS="\\r" -F":" "!/done/{gsub(/ /,\\"\\");gsub(/%% complete/,\\"\\");;gsub(/%%complete/,\\"\\");if(NR>1) print $2/100;fflush();}"' % {'a': filename, 'b': newname}
    else:
      command = "flac -d -f '%(a)s' -o '%(b)s' 2>&1 | awk -vRS='\\r' -F':' '!/done/{gsub(/ /,\"\");gsub(/%% complete/,\"\");;gsub(/%%complete/,\"\");if(NR>1) print $2/100;fflush();}'" % {'a': filename, 'b': newname}
    sub = subprocess.Popen(command, shell=True, env=environ, stderr=subprocess.PIPE, stdout=subprocess.PIPE, stdin=subprocess.PIPE)
    return sub, command

  def encode(self, filename, newname, quality):
    """ Encodes a new FLAC file """
    if MSWINDOWS:
      command = 'flac.exe -f --compression-level-%(a)i "%(b)s" -o "%(c)s" 2>&1 | awk.exe -vRS="\\r" -F":" "!/wrote/{gsub(/ /,\\"\\");if(NR>1)print $2/100;fflush();}" | awk.exe -F"%%" "{printf $1\\"\\n\\";fflush();}"' % {'a': quality, 'b': filename, 'c': newname}
    else:
      command = "flac -f --compression-level-%(a)i '%(b)s' -o '%(c)s' 2>&1 | awk -vRS='\\r' -F':' '!/wrote/{gsub(/ /,\"\");if(NR>1)print $2/100;fflush();}' | awk -F'%%' '{printf $1\"\\n\";fflush();}'" % {'a': quality, 'b': filename, 'c': newname}
    sub = subprocess.Popen(command, shell=True, env=environ, stderr=subprocess.PIPE, stdout=subprocess.PIPE, stdin=subprocess.PIPE)
    return sub, command

# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------

class ogg:
  """ oggenc >> OGG (vorbis-tools) """
  def __init__(self):
    """ Initialize """
    self.__encode = False
    self.__decode = False
    self.__tags = False
    self.check()
    self.extensions = ['ogg']
    self.__qualities = [
    ['56', '56 kbps'],
    ['96', '96 kbps'],
    ['128', '128 kbps'],
    ['160', '160 kbps'],
    ['192', '192 kbps'],
    ['256', '256 kbps'],
    ['320', '320 kbps']
                       ]

  def check(self):
    """ Check if the required program(s) exist """
    if which('oggdec'):
      self.__decode = True
    else:
      self.__decode = False
    if which('oggenc'):
      self.__encode = True
    else:
      self.__encode = False
    if which('ogginfo') and which('vorbiscomment'):
      self.__tags = True
    else:
      self.__tags = False

  def get(self):
    """ Return all information on the format """
    return [self.__encode, self.__decode, self.__tags, self.__qualities]

  def getTags(self, filename):
    """ Retrieves the metadata from filename """
    if MSWINDOWS:
      return None
    command = "ogginfo '%(a)s'" % {'a': filename}
    sub = subprocess.Popen(command, shell=True, env=environ, stderr=subprocess.PIPE, stdout=subprocess.PIPE, stdin=subprocess.PIPE)
    sub.wait()
    content = sub.stdout.read().split('\n')
    tags = []
    for prefix in ['TITLE=', 'ARTIST=', 'ALBUM=', 'DATE=', 'TRACKNUMBER=',
                   'GENRE=', 'DESCRIPTION=']:
      tag = ''
      for line in content:
        if line.strip().startswith(prefix):
          content.remove(line)
          tag = line.strip()[len(prefix):]
          break
      # we append what was found, or blank then move on to next prefix
      tags.append(tag)
    return tags
    
  def setTags(self, filename, tags):
    """ Sets the metadata on filename """
    if MSWINDOWS:
      return
    command = "vorbiscomment -w '%(a)s' -t 'TITLE=%(b)s' -t 'ARTIST=%(c)s' -t 'ALBUM=%(d)s' -t 'DATE=%(e)s' -t 'TRACKNUMBER=%(f)s' -t 'GENRE=%(g)s' -t 'DESCRIPTION=%(h)s'" % {'a': filename, 'b': tags[0], 'c': tags[1], 'd': tags[2], 'e': tags[3], 'f': tags[4], 'g': tags[5], 'h': tags[6]}
    sub = subprocess.Popen(command, shell=True, env=environ, stderr=subprocess.PIPE, stdout=subprocess.PIPE, stdin=subprocess.PIPE)
    sub.wait()
    
  def decode(self, filename, newname):
    """ Decodes a OGG file """
    if MSWINDOWS:
      command = 'oggdec.exe "%(a)s" -o "%(b)s" 2>&1 | awk.exe -vRS="\\r" "(NR>1){gsub(/%%/,\\" \\");print $2/100;fflush();}"' % {'a': filename, 'b': newname}
    else:
      command = "oggdec '%(a)s' -o '%(b)s' 2>&1 | awk -vRS='\\r' '(NR>1){gsub(/%%/,\" \");print $2/100;fflush();}'" % {'a': filename, 'b': newname}
    sub = subprocess.Popen(command, shell=True, env=environ, stderr=subprocess.PIPE, stdout=subprocess.PIPE, stdin=subprocess.PIPE)
    return sub, command

  def encode(self, filename, newname, quality):
    """ Encodes a new OGG file """
    if MSWINDOWS:
      command = 'oggenc.exe -b %(a)i "%(b)s" -o "%(c)s" 2>&1 | awk.exe -vRS="\\r" "(NR>1){gsub(/%%/,\\" \\");print $2/100;fflush();}"' % {'a': quality, 'b': filename, 'c': newname}
    else:
      command = "oggenc -b %(a)i '%(b)s' -o '%(c)s' 2>&1 | awk -vRS='\\r' '(NR>1){gsub(/%%/,\" \");print $2/100;fflush();}'" % {'a': quality, 'b': filename, 'c': newname}
    sub = subprocess.Popen(command, shell=True, env=environ, stderr=subprocess.PIPE, stdout=subprocess.PIPE, stdin=subprocess.PIPE)
    return sub, command

# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------

class mpc:
  """ mppdec >> MPC (musepack-tools) """
  def __init__(self):
    """ Initialize """
    self.__encode = False
    self.__decode = False
    self.__tags = False
    self.extensions = ['mpc']
    self.check()
    self.__qualities = [
    ['1','~30 kbps'],
    ['2','~60 kbps'],
    ['3','~90 kbps'],
    ['4','~130 kbps'],
    ['5','~180 kbps'],
    ['6','~210 kbps'],
    ['7','~240 kbps'],
    ['8','~270 kbps'],
    ['9','~300 kbps'],
    ['10','~350 kbps']
                      ]

  def check(self):
    """ Check if the required program(s) exist """
    if which('mppdec'):
      self.__decode = True
    else:
      self.__decode = False
    if which('mppenc'):
      self.__encode = True
    else:
      self.__encode = False
    self.__tags = False

  def get(self):
    """ Return all information on the format """
    return [self.__encode, self.__decode, self.__tags, self.__qualities]

  def getTags(self, filename):
    """ Retrieves the metadata from filename """
    return None
    
  def setTags(self, filename, tags):
    """ Sets the metadata on filename """
    if MSWINDOWS:
      return
    return

  def decode(self, filename, newname):
    """ Decodes a MPC file """
    if MSWINDOWS:
      command = 'mppdec.exe "%(a)s" "%(b)s" 2>&1 | awk.exe -vRS="\\r" -F"[ (]+" "!/s/{gsub(/(%%)/,\\" \\");if(NR>5)print $5/100;fflush();}"' % {'a': filename, 'b': newname}
    else:
      command = "mppdec '%(a)s' '%(b)s' 2>&1 | awk -vRS='\\r' -F'[ (]+' '!/s/{gsub(/(%%)/,\" \");if(NR>5)print $5/100;fflush();}'" % {'a': filename, 'b': newname}
    sub = subprocess.Popen(command, shell=True, env=environ, stderr=subprocess.PIPE, stdout=subprocess.PIPE, stdin=subprocess.PIPE)
    return sub, command

  def encode(self, filename, newname, quality):
    """ Encodes a new MPC file """
    if MSWINDOWS:
      command = 'mppenc.exe --quality %(a)i --overwrite "%(b)s" "%(c)s" 2>&1 | awk.exe -vRS="\\r" "!/^$/{if (NR>5) print $1/100;fflush();}"' % {'a': quality, 'b': filename, 'c': newname}
    else:
      command = "mppenc --quality %(a)i --overwrite '%(b)s' '%(c)s' 2>&1 | awk -vRS='\\r' '!/^$/{if (NR>5) print $1/100;fflush();}'" % {'a': quality, 'b': filename, 'c': newname}
    sub = subprocess.Popen(command, shell=True, env=environ, stderr=subprocess.PIPE, stdout=subprocess.PIPE, stdin=subprocess.PIPE)
    return sub, command


# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------

class ape:
  """ mac >> ape """
  def __init__(self):
    """ Initialize """
    self.__encode = False
    self.__decode = False
    self.__tags = False
    self.check()
    self.extensions = ['ape']
    self.__qualities = [
    ['1000','1000'],
    ['2000','2000'],
    ['3000','3000'],
    ['4000','4000'],
    ['5000','5000'],
                       ]

  def check(self):
    """ Check if the required program(s) exist """
    if which('mac'):
      self.__decode, self.__encode = True, True
    else:
      self.__decode, self.__encode = False, False
    self.__tags = False

  def get(self):
    """ Return all information on the format """
    return [self.__encode, self.__decode, self.__tags, self.__qualities]

  def getTags(self, filename):
    """ Retrieves the metadata from filename """
    return None
    
  def setTags(self, filename, tags):
    """ Sets the metadata on filename """
    if MSWINDOWS:
      return
    return

  def decode(self, filename, newname):
    """ Decodes a MAC file """
    if MSWINDOWS:
      command = 'mac.exe "%(a)s" "%(b)s" -d 2>&1 | awk.exe -vRS="\\r" "(NR>1){gsub(/%%/,\\" \\");print $2/100;fflush();}"' % {'a': filename, 'b': newname}
    else:
      command = "mac '%(a)s' '%(b)s' -d 2>&1 | awk -vRS='\\r' '(NR>1){gsub(/%%/,\" \");print $2/100;fflush();}'" % {'a': filename, 'b': newname}
    sub = subprocess.Popen(command, shell=True, env=environ, stderr=subprocess.PIPE, stdout=subprocess.PIPE, stdin=subprocess.PIPE)
    return sub, command

  def encode(self, filename, newname, quality):
    """ Encodes a new MAC file """
    if MSWINDOWS:
      command = 'mac.exe "%(b)s" "%(c)s" -c%(a)i 2>&1 | awk.exe -vRS="\\r" "(NR>1){gsub(/%%/,\\" \\");print $2/100;fflush();}"' % {'a': quality, 'b': filename, 'c': newname}
    else:
      command = "mac '%(b)s' '%(c)s' -c%(a)i 2>&1 | awk -vRS='\\r' '(NR>1){gsub(/%%/,\" \");print $2/100;fflush();}'" % {'a': quality, 'b': filename, 'c': newname}
    sub = subprocess.Popen(command, shell=True, env=environ, stderr=subprocess.PIPE, stdout=subprocess.PIPE, stdin=subprocess.PIPE)
    return sub, command

# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------

class aac:
  """ faad >> AAC """
  def __init__(self):
    """ Initialize """
    self.__encode = False
    self.__decode = False
    self.__tags = False
    self.extensions = ['m4a', 'aac', 'mp4']
    self.check()
    self.__qualities = [
    ['65','~96 kbps (65%)'],
    ['95','~128 kbps (95%)'],
    ['100','~160 kbps (100%)'],
    ['130','~192 kbps (130%)'],
    ['270','~256 kbps (270%)'],
    ['500','~320 kbps (500%)']
                      ]

  def check(self):
    """ Check if the required program(s) exist """
    if which('faad'):
      self.__decode = True
    else:
      self.__decode = False
    if which('faac'):
      self.__encode = True
    else:
      self.__encode = False
    if which('mp4info') and which('mp4tags'):
      self.__tags = True
    else:
      self.__tags = False

  def get(self):
    """ Return all information on the format """
    return [self.__encode, self.__decode, self.__tags, self.__qualities]

  def getTags(self, filename):
    """ Retrieves the metadata from filename """
    sub = subprocess.Popen('mp4info "%(a)s"' % {'a': filename}, shell=True, env=environ, stderr=subprocess.PIPE, stdout=subprocess.PIPE, stdin=subprocess.PIPE)
    sub.wait()
    content = sub.stdout.read().split('\n')
    tags = []
    for prefix in ['Metadata Name: ', 'Metadata Artist: ', 'Metadata Album: ',
              'Metadata Year: ', 'Metadata track: ', 'Metadata Genre: ',
              'Metadata Comment: ']:
      tag = ''
      for line in content:
        if line.strip().startswith(prefix):
          content.remove(line)
          tag = line.strip()[len(prefix):]
          if prefix == 'Metadata Year: ':
            tag = tag[:4]
          elif prefix == 'Metadata track: ':
            tag = tag.split('of')[0].strip()
          break
      # we append what was found, or blank then move on to next prefix
      tags.append(tag)
    return tags
    
  def setTags(self, filename, tags):
    """ Sets the metadata on filename """
    if MSWINDOWS:
      return
    command = "mp4tags -s '%(a)s' -a '%(b)s' -A '%(c)s' -y '%(d)s' -t '%(e)s' -g '%(f)s' -c '%(g)s' '%(h)s'" % {'a': tags[0], 'b': tags[1], 'c': tags[2], 'd': tags[3], 'e': tags[4], 'f': tags[5], 'g': tags[6], 'h': filename}
    sub = subprocess.Popen(command, shell=True, env=environ, stderr=subprocess.PIPE, stdout=subprocess.PIPE, stdin=subprocess.PIPE)
    sub.wait()

  def decode(self, filename, newname):
    """ Decodes a AAC file """
    if MSWINDOWS:
      command = 'faad.exe "%(a)s" -o "%(b)s" 2>&1 | awk.exe -vRS="\\r" "(NR>1){gsub(/%%/,\\" \\");print $1/100;fflush();}"' % {'a': filename, 'b': newname}
    else:
      command = "faad '%(a)s' -o '%(b)s' 2>&1 | awk -vRS='\\r' '(NR>1){gsub(/%%/,\" \");print $1/100;fflush();}'" % {'a': filename, 'b': newname}
    sub = subprocess.Popen(command, shell=True, env=environ, stderr=subprocess.PIPE, stdout=subprocess.PIPE, stdin=subprocess.PIPE)
    return sub, command

  def encode(self, filename, newname, quality):
    """ Encodes a new AAC file """
    if MSWINDOWS:
      command = 'faac.exe -w -q %(a)i "%(b)s" -o "%(c)s" 2>&1 | awk.exe -vRS="\\r" "(NR>1){gsub(/%%/,\\" \\");print $3/100;fflush();}"' % {'a': quality, 'b': filename, 'c': newname}
    else:
      command = "faac -w -q %(a)i '%(b)s' -o '%(c)s' 2>&1 | awk -vRS='\\r' '(NR>1){gsub(/%%/,\" \");print $3/100;fflush();}'" % {'a': quality, 'b': filename, 'c': newname}
    sub = subprocess.Popen(command, shell=True, env=environ, stderr=subprocess.PIPE, stdout=subprocess.PIPE, stdin=subprocess.PIPE)
    return sub, command

# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------

class mplayer:
  """ mplayer >> WMA, SHN """
  def __init__(self):
    """ Initialize """
    self.__encode = False
    self.__decode = False
    self.__tags = False
    self.extensions = ['wma', 'shn']
    self.check()
    self.__qualities = [
    ['-', _('(Based on original file)')]
                       ]

  def check(self):
    """ Check if the required program(s) exist """
    if which('mplayer'):
      self.__decode = True
    else:
      self.__decode = False
    self.__tags = False

  def get(self):
    """ Return all information on the format """
    return [self.__encode, self.__decode, self.__tags, self.__qualities]

  def getTags(self, filename):
    """ Retrieves the metadata from filename """
    return None
    
  def setTags(self, filename, tags):
    """ Sets the metadata on filename """
    if MSWINDOWS:
      return
    return
  
  # FIXME: Finish this
  def decode(self, filename, newname):
    """ Decodes a mplayer-playable file """
    if MSWINDOWS:
      command = 'mplayer.exe -quiet -vo null -vc dummy -ao pcm:waveheader:file="%(b)s" "%(a)s" 2>&1 | awk.exe -vRS="\\r" "($2~/^[-+]?[0-9]/ && $5~/^[-+]?[0-9]/){print $2/$5*100;fflush();}"' % {'a': filename, 'b': newname}
    else:
      command = "mplayer -quiet -vo null -vc dummy -ao pcm:waveheader:file='%(b)s' '%(a)s' 2>&1 | awk -vRS='\\r' '($2~/^[-+]?[0-9]/ && $5~/^[-+]?[0-9]/){print $2/$5*100;fflush();}'" % {'a': filename, 'b': newname}
    sub = subprocess.Popen(command, shell=True, env=environ, stderr=subprocess.PIPE, stdout=subprocess.PIPE, stdin=subprocess.PIPE)
    return sub, command

# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------

class ac3:
  """ a52dec >> AC3 """
  def __init__(self):
    """ Initialize """
    self.__encode = False
    self.__decode = False
    self.__tags = False
    self.extensions = ['ac3']
    self.check()
    self.__qualities = [
    ['56', '56 kbps'],
    ['96', '96 kbps'],
    ['128', '128 kbps'],
    ['160', '160 kbps'],
    ['192', '192 kbps'],
    ['256', '256 kbps'],
    ['320', '320 kbps'],
                       ]

  def check(self):
    """ Check if the required program(s) exist """
    if which('a52dec'):
      self.__decode = True
    else:
      self.__decode = False
    if which('ffmpeg'):
      self.__encode = True
    else:
      self.__encode = False
    self.__tags = False

  def get(self):
    """ Return all information on the format """
    return [self.__encode, self.__decode, self.__tags, self.__qualities]

  def getTags(self, filename):
    """ Retrieves the metadata from filename """
    return None
    
  def setTags(self, filename, tags):
    """ Sets the metadata on filename """
    if MSWINDOWS:
      return
    return

  def decode(self, filename, newname):
    """ Decodes a AC3 file """
    if MSWINDOWS:
      command = 'echo 0;a52dec.exe -o wav "%(a)s" > "%(b)s"' % {'a': filename, 'b': newname}
    else:
      command = "echo 0;a52dec -o wav '%(a)s' > '%(b)s'" % {'a': filename, 'b': newname}
    sub = subprocess.Popen(command, shell=True, env=environ, stderr=subprocess.PIPE, stdout=subprocess.PIPE, stdin=subprocess.PIPE)
    return sub, command

  def encode(self, filename, newname, quality):
    """ Encodes a new AC3 file """
    if MSWINDOWS:
      command = 'echo 0;ffmpeg.exe -i "%(b)s" -y -ab %(a)ik -f ac3 "%(c)s" 2>&1 | awk.exe -vRS="\10\10\10\10\10\10" "(NR>1){gsub(/%%/,\\" \\");if($1 != \\"\\") print $1;fflush();}"' % {'a': quality, 'b': filename, 'c': newname}
    else:
      command = "echo 0;ffmpeg -i '%(b)s' -y -ab %(a)ik -f ac3 '%(c)s' 2>&1 | awk -vRS='\10\10\10\10\10\10' '(NR>1){gsub(/%%/,\" \");if($1 != \"\") print $1;fflush();}'" % {'a': quality, 'b': filename, 'c': newname}
    sub = subprocess.Popen(command, shell=True, env=environ, stderr=subprocess.PIPE, stdout=subprocess.PIPE, stdin=subprocess.PIPE)
    return sub, command


# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------

class wv:
  """ wavpack >> WVPK """
  def __init__(self):
    """ Initialize """
    self.__encode = False
    self.__decode = False
    self.__tags = False
    self.extensions = ['wv', 'wvc']
    self.check()
    self.__qualities = [
    ['0', _('Low compression')],
    ['1', _('High compression')],
    ['2', _('Very high compression')],
                       ]

  def check(self):
    """ Check if the required program(s) exist """
    if which('wvunpack'):
      self.__decode = True
    else:
      self.__decode = False
    if which('wavpack'):
      self.__encode = True
    else:
      self.__encode = False
    self.__tags = False

  def get(self):
    """ Return all information on the format """
    return [self.__encode, self.__decode, self.__tags, self.__qualities]

  def getTags(self, filename):
    """ Retrieves the metadata from filename """
    return None
    
  def setTags(self, filename, tags):
    """ Sets the metadata on filename """
    if MSWINDOWS:
      return
    return

  # -c || -i for lossless||lossy.... I smell workarounds :/
  def decode(self, filename, newname):
    """ Decodes a WVPk file """
    if MSWINDOWS:
      command = 'wvunpack.exe -y "%(a)s" -o "%(b)s" 2>&1 | awk.exe -vRS="\10\10\10\10\10\10" "(NR>1){gsub(/%%/,\\" \\");if($1 != \\"\\") print $1/100;fflush();}"' % {'a': filename, 'b': newname}
    else:
      command = "wvunpack -y '%(a)s' -o '%(b)s' 2>&1 | awk -vRS='\10\10\10\10\10\10' '(NR>1){gsub(/%%/,\" \");if($1 != \"\") print $1/100;fflush();}'" % {'a': filename, 'b': newname}
    sub = subprocess.Popen(command, shell=True, env=environ, stderr=subprocess.PIPE, stdout=subprocess.PIPE, stdin=subprocess.PIPE)
    return sub, command

  def encode(self, filename, newname, quality):
    """ Encodes a new WVPK file """
    if quality == 0:
      quality = '-f'
    elif quality == 1:
      quality = '-h'
    elif quality == 2:
      quality = '-hh'
    if MSWINDOWS:
      command = 'wavpack.exe -y %(a)s "%(b)s" -o "%(c)s" 2>&1 | awk.exe -vRS="\10\10\10\10\10\10" "(NR>1){gsub(/%%/,\\" \\");if($1 != \\"\\") print $1/100;fflush();}"' % {'a': quality, 'b': filename, 'c': newname}
    else:
      command = "wavpack -y %(a)s '%(b)s' -o '%(c)s' 2>&1 | awk -vRS='\10\10\10\10\10\10' '(NR>1){gsub(/%%/,\" \");if($1 != \"\") print $1/100;fflush();}'" % {'a': quality, 'b': filename, 'c': newname}
    sub = subprocess.Popen(command, shell=True, env=environ, stderr=subprocess.PIPE, stdout=subprocess.PIPE, stdin=subprocess.PIPE)
    return sub, command

# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------

FORMATS = {}
for format in [mp3(), ogg(), mpc(), ape(), aac(), ac3(), wv(), wav(), flac()]:
  FORMATS[format.__class__.__name__.lower()] = format

def recheck():
  """ Recheck all formats """
  for format in FORMATS.values():
    format.check()

def getFileType(path):
  """ Return the file type based on extension """
  fileExtension = path.split('.')[-1].lower()
  for format in FORMATS.values():
    for extension in format.extensions:
      if fileExtension == extension:
        return format
  # unknown filetype!
  return False

def decodable(path):
  """ Checks if a given file is currently decodable """
  fileType = getFileType(path)
  if fileType == False:
    # unknown filetype!
    return False
  return fileType.get()[0]

