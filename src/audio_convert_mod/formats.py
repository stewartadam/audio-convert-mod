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

import mutagen
from mutagen.easyid3 import EasyID3
from mutagen.mp3 import MP3
from mutagen.flac import FLAC
from mutagen.oggvorbis import OggVorbis
from mutagen.musepack import Musepack
from mutagen.apev2 import APEv2
from mutagen.mp4 import MP4
from mutagen.wavpack import WavPack

environ = {'PATH': str(os.getenv('PATH'))}

def getNewExt(ext, filename):
    return '%s.%s' % ('.'.join(filename.split('.')[:-1]), ext)

def getTrackInfo(audiotags):
  """Gets track information from the generic "tags" mutagen object"""
  tags = []
  for item in ["title", "artist", "album", "date", "tracknumber", "genre", "comment"]:
    try:
      if not audiotags.has_key(item):
        tags.append("")
      else:
        if type(audiotags[item]) == list: # dealing with a list - use first value
          tags.append(str(audiotags[item][0]))
        else: # strings
          tags.append(str(audiotags[item]))
    except Exception, error:
      tags.append("")
  return tags

def saveTrackInfo(audiotags, tags):
  """Save the track information defined in tags to mutagen object audiotags"""
  audiotags["title"] = tags[0]
  audiotags["artist"] = tags[1]
  audiotags["album"] = tags[2]
  audiotags["date"] = tags[3]
  audiotags["tracknumber"] = tags[4]
  audiotags["genre"] = tags[5]
  audiotags["comment"] = tags[6]
  audiotags.save()

class wav:
  """The WAV format class."""
  def __init__(self):
    """Initialize"""
    self.__encode = True
    self.__decode = True
    self.__tags = False
    self.extensions = ['wav']
    self.check()
    self.__qualities = [
    ['0', _('(Based on original file)')]
                       ]

  def check(self):
    """Check if the required program(s) exist"""
    return True

  def decode(self, filename, newname):
    command = "echo .5"
    sub = subprocess.Popen(command, shell=True, env=environ, stderr=subprocess.PIPE, stdout=subprocess.PIPE, stdin=subprocess.PIPE)
    return sub, command

  def encode(self, filename, newname, quality):
    command = "echo 1"
    sub = subprocess.Popen(command, shell=True, env=environ, stderr=subprocess.PIPE, stdout=subprocess.PIPE, stdin=subprocess.PIPE)
    return sub, command

  def get(self):
    """Return all information on the format"""
    return [self.__encode, self.__decode, self.__tags, self.__qualities]

# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------

class mp3:
  """The MP3 format class. Requires lame."""
  def __init__(self):
    """Initialize"""
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
    """Check if the required program(s) exist"""
    if which('lame'):
      self.__encode, self.__decode = True, True
    else:
      self.__encode, self.__decode = False, False
    # mutagen supports ID3 tags
    self.__tags = True

  def get(self):
    """Return all information on the format"""
    return [self.__encode, self.__decode, self.__tags, self.__qualities]

  def decode(self, filename, newname):
    """Decodes a MP3 file"""
    if MSWINDOWS:
      command = 'lame.exe --decode --mp3input "%(a)s" "%(b)s" 2>&1 | awk.exe -vRS="\\r" -F"[ /]+" "(NR>2){print $2/$3;fflush();}"' % {'a': filename, 'b': newname}
    else:
      command = "lame --decode --mp3input '%(a)s' '%(b)s' 2>&1 | awk -vRS='\\r' -F'[ /]+' '(NR>2){print $2/$3;fflush();}'" % {'a': filename, 'b': newname}
    sub = subprocess.Popen(command, shell=True, env=environ, stderr=subprocess.PIPE, stdout=subprocess.PIPE, stdin=subprocess.PIPE)
    return sub, command

  def encode(self, filename, newname, quality):
    """Encodes a new MP3 file"""
    if MSWINDOWS:
      command = 'lame.exe -m auto --preset cbr %(a)i "%(b)s" "%(c)s" 2>&1 | awk.exe -vRS="\\r" "(NR>3){gsub(/[()%%|]/,\\" \\");if($1 != \\"\\") print $2/100;fflush();}"' % {'a': quality, 'b': filename, 'c': newname}
    else:
      command = "lame -m auto --preset cbr %(a)i '%(b)s' '%(c)s' 2>&1 | awk -vRS='\\r' '(NR>3){gsub(/[()%%|]/,\" \");if($1 != \"\") print $2/100;fflush();}'" % {'a': quality, 'b': filename, 'c': newname}
    sub = subprocess.Popen(command, shell=True, env=environ, stderr=subprocess.PIPE, stdout=subprocess.PIPE, stdin=subprocess.PIPE)
    return sub, command

  def getTags(self, filename):
    """Retrieves the metadata from filename"""
    # FIXME: Comments in MP3 are not supported by EasyID3
    audiotags = MP3(filename, ID3=EasyID3)
    try: # try to add a tag header
      audiotags.add_tags(ID3=EasyID3)
      audiotags['title'] = '' # save one empty tag to create a header
      audiotags.save()
    except mutagen.id3.error: # header exists
      pass
    return getTrackInfo(audiotags)

  def setTags(self, filename, tags):
    """Sets the metadata on filename"""
    audiotags = MP3(filename, ID3=EasyID3)
    try: # try to add a tag header
      audiotags.add_tags(ID3=EasyID3)
      audiotags['title'] = '' # save one empty tag to create a header
      audiotags.save()
    except mutagen.id3.error: # header exists
      pass
    audiotags["title"] = tags[0]
    audiotags["artist"] = tags[1]
    audiotags["album"] = tags[2]
    audiotags["date"] = tags[3]
    audiotags["tracknumber"] = tags[4]
    audiotags["genre"] = tags[5]
    audiotags.save(v1=2) # save both id3v1 and 2 tags

# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------

class flac:
  """The FLAC format class. Requires flac."""
  def __init__(self):
    """Initialize"""
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
    """Check if the required program(s) exist"""
    if which('flac'):
      self.__encode, self.__decode = True, True
    else:
      self.__encode, self.__decode = False, False
    # mutagen supports vorbis/flac tags
    self.__tags = True

  def get(self):
    """Return all information on the format"""
    return [self.__encode, self.__decode, self.__tags, self.__qualities]
    
  def getTags(self, filename):
    """Retrieves the metadata from filename"""
    audiotags = FLAC(filename)
    return getTrackInfo(audiotags)

  def setTags(self, filename, tags):
    """Sets the metadata on filename"""
    audiotags = FLAC(filename)
    saveTrackInfo(audiotags, tags)
    
  def decode(self, filename, newname):
    """Decodes a FLAC file"""
    if MSWINDOWS:
      command = 'flac.exe -d -f "%(a)s" -o "%(b)s" 2>&1 | awk.exe -vRS="\\r" -F":" "!/done/{gsub(/ /,\\"\\");gsub(/%% complete/,\\"\\");;gsub(/%%complete/,\\"\\");if(NR>1) print $2/100;fflush();}"' % {'a': filename, 'b': newname}
    else:
      command = "flac -d -f '%(a)s' -o '%(b)s' 2>&1 | awk -vRS='\\r' -F':' '!/done/{gsub(/ /,\"\");gsub(/%% complete/,\"\");;gsub(/%%complete/,\"\");if(NR>1) print $2/100;fflush();}'" % {'a': filename, 'b': newname}
    sub = subprocess.Popen(command, shell=True, env=environ, stderr=subprocess.PIPE, stdout=subprocess.PIPE, stdin=subprocess.PIPE)
    return sub, command

  def encode(self, filename, newname, quality):
    """Encodes a new FLAC file"""
    if MSWINDOWS:
      command = 'flac.exe -f --compression-level-%(a)i "%(b)s" -o "%(c)s" 2>&1 | awk.exe -vRS="\\r" -F":" "!/wrote/{gsub(/ /,\\"\\");if(NR>1)print $2/100;fflush();}" | awk.exe -F"%%" "{printf $1\\"\\n\\";fflush();}"' % {'a': quality, 'b': filename, 'c': newname}
    else:
      command = "flac -f --compression-level-%(a)i '%(b)s' -o '%(c)s' 2>&1 | awk -vRS='\\r' -F':' '!/wrote/{gsub(/ /,\"\");if(NR>1)print $2/100;fflush();}' | awk -F'%%' '{printf $1\"\\n\";fflush();}'" % {'a': quality, 'b': filename, 'c': newname}
    sub = subprocess.Popen(command, shell=True, env=environ, stderr=subprocess.PIPE, stdout=subprocess.PIPE, stdin=subprocess.PIPE)
    return sub, command

# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------

class ogg:
  """The OGG format class. Requires ogg{enc,dec,info} (vorbis-tools)"""
  def __init__(self):
    """Initialize"""
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
    """Check if the required program(s) exist"""
    if which('oggdec'):
      self.__decode = True
    else:
      self.__decode = False
    if which('oggenc'):
      self.__encode = True
    else:
      self.__encode = False
    # mutagen supports vorbis/flac tags
    self.__tags = True

  def get(self):
    """Return all information on the format"""
    return [self.__encode, self.__decode, self.__tags, self.__qualities]

  def getTags(self, filename):
    """Retrieves the metadata from filename"""
    audiotags = OggVorbis(filename)
    return getTrackInfo(audiotags)
    
  def setTags(self, filename, tags):
    """Sets the metadata on filename"""
    audiotags = OggVorbis(filename)
    saveTrackInfo(audiotags, tags)
    
  def decode(self, filename, newname):
    """Decodes a OGG file"""
    if MSWINDOWS:
      command = 'oggdec.exe "%(a)s" -o "%(b)s" 2>&1 | awk.exe -vRS="\\r" "(NR>1){gsub(/%%/,\\" \\");print $2/100;fflush();}"' % {'a': filename, 'b': newname}
    else:
      command = "oggdec '%(a)s' -o '%(b)s' 2>&1 | awk -vRS='\\r' '(NR>1){gsub(/%%/,\" \");print $2/100;fflush();}'" % {'a': filename, 'b': newname}
    sub = subprocess.Popen(command, shell=True, env=environ, stderr=subprocess.PIPE, stdout=subprocess.PIPE, stdin=subprocess.PIPE)
    return sub, command

  def encode(self, filename, newname, quality):
    """Encodes a new OGG file"""
    if MSWINDOWS:
      command = 'oggenc.exe -b %(a)i "%(b)s" -o "%(c)s" 2>&1 | awk.exe -vRS="\\r" "(NR>1){gsub(/%%/,\\" \\");print $2/100;fflush();}"' % {'a': quality, 'b': filename, 'c': newname}
    else:
      command = "oggenc -b %(a)i '%(b)s' -o '%(c)s' 2>&1 | awk -vRS='\\r' '(NR>1){gsub(/%%/,\" \");print $2/100;fflush();}'" % {'a': quality, 'b': filename, 'c': newname}
    sub = subprocess.Popen(command, shell=True, env=environ, stderr=subprocess.PIPE, stdout=subprocess.PIPE, stdin=subprocess.PIPE)
    return sub, command

# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------

class mpc:
  """The MPC format class. Requires mpp{dec,enc} (musepack-tools)"""
  def __init__(self):
    """Initialize"""
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
    """Check if the required program(s) exist"""
    if which('mppdec'):
      self.__decode = True
    else:
      self.__decode = False
    if which('mppenc'):
      self.__encode = True
    else:
      self.__encode = False
    # mutagen supports Musepack tags
    self.__tags = True

  def get(self):
    """Return all information on the format"""
    return [self.__encode, self.__decode, self.__tags, self.__qualities]

  def getTags(self, filename):
    """Retrieves the metadata from filename"""
    audiotags = Musepack(filename)
    return getTrackInfo(audiotags)
    
  def setTags(self, filename, tags):
    """Sets the metadata on filename"""
    audiotags = Musepack(filename)
    saveTrackInfo(audiotags, tags)

  def decode(self, filename, newname):
    """Decodes a MPC file"""
    if MSWINDOWS:
      command = 'mppdec.exe "%(a)s" "%(b)s" 2>&1 | awk.exe -vRS="\\r" -F"[ (]+" "!/s/{gsub(/(%%)/,\\" \\");if(NR>5)print $5/100;fflush();}"' % {'a': filename, 'b': newname}
    else:
      command = "mppdec '%(a)s' '%(b)s' 2>&1 | awk -vRS='\\r' -F'[ (]+' '!/s/{gsub(/(%%)/,\" \");if(NR>5)print $5/100;fflush();}'" % {'a': filename, 'b': newname}
    sub = subprocess.Popen(command, shell=True, env=environ, stderr=subprocess.PIPE, stdout=subprocess.PIPE, stdin=subprocess.PIPE)
    return sub, command

  def encode(self, filename, newname, quality):
    """Encodes a new MPC file"""
    if MSWINDOWS:
      command = 'mppenc.exe --quality %(a)i --overwrite "%(b)s" "%(c)s" 2>&1 | awk.exe -vRS="\\r" "!/^$/{if (NR>5) print $1/100;fflush();}"' % {'a': quality, 'b': filename, 'c': newname}
    else:
      command = "mppenc --quality %(a)i --overwrite '%(b)s' '%(c)s' 2>&1 | awk -vRS='\\r' '!/^$/{if (NR>5) print $1/100;fflush();}'" % {'a': quality, 'b': filename, 'c': newname}
    sub = subprocess.Popen(command, shell=True, env=environ, stderr=subprocess.PIPE, stdout=subprocess.PIPE, stdin=subprocess.PIPE)
    return sub, command


# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------

class ape:
  """The Monkey's Audio format class. Requires mac."""
  def __init__(self):
    """Initialize"""
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
    """Check if the required program(s) exist"""
    if which('mac'):
      self.__decode, self.__encode = True, True
    else:
      self.__decode, self.__encode = False, False
    # mutagen supports apev2 tags
    self.__tags = True

  def get(self):
    """Return all information on the format"""
    return [self.__encode, self.__decode, self.__tags, self.__qualities]

  def getTags(self, filename):
    """Retrieves the metadata from filename"""
    audiotags = APEv2(filename)
    return getTrackInfo(audiotags)
    
  def setTags(self, filename, tags):
    """Sets the metadata on filename"""
    audiotags = APEv2(filename)
    saveTrackInfo(audiotags, tags)

  def decode(self, filename, newname):
    """Decodes a MAC file"""
    if MSWINDOWS:
      command = 'mac.exe "%(a)s" "%(b)s" -d 2>&1 | awk.exe -vRS="\\r" "(NR>1){gsub(/%%/,\\" \\");print $2/100;fflush();}"' % {'a': filename, 'b': newname}
    else:
      command = "mac '%(a)s' '%(b)s' -d 2>&1 | awk -vRS='\\r' '(NR>1){gsub(/%%/,\" \");print $2/100;fflush();}'" % {'a': filename, 'b': newname}
    sub = subprocess.Popen(command, shell=True, env=environ, stderr=subprocess.PIPE, stdout=subprocess.PIPE, stdin=subprocess.PIPE)
    return sub, command

  def encode(self, filename, newname, quality):
    """Encodes a new MAC file"""
    if MSWINDOWS:
      command = 'mac.exe "%(b)s" "%(c)s" -c%(a)i 2>&1 | awk.exe -vRS="\\r" "(NR>1){gsub(/%%/,\\" \\");print $2/100;fflush();}"' % {'a': quality, 'b': filename, 'c': newname}
    else:
      command = "mac '%(b)s' '%(c)s' -c%(a)i 2>&1 | awk -vRS='\\r' '(NR>1){gsub(/%%/,\" \");print $2/100;fflush();}'" % {'a': quality, 'b': filename, 'c': newname}
    sub = subprocess.Popen(command, shell=True, env=environ, stderr=subprocess.PIPE, stdout=subprocess.PIPE, stdin=subprocess.PIPE)
    return sub, command

# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------

class aac:
  """The AAC format class. Requires faad, faac."""
  def __init__(self):
    """Initialize"""
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
    """Check if the required program(s) exist"""
    if which('faad'):
      self.__decode = True
    else:
      self.__decode = False
    if which('faac'):
      self.__encode = True
    else:
      self.__encode = False
    # mutagen supports aac/m4a tags
    self.__tags = True

  def get(self):
    """Return all information on the format"""
    return [self.__encode, self.__decode, self.__tags, self.__qualities]

  def getTags(self, filename):
    """Retrieves the metadata from filename"""
    audiotags = MP4(filename)
    # Map our the iTunes MP4 atom names to our regular tag data.
    tags = []
    for item in ["\xa9nam", "\xa9ART", "\xa9alb", "\xa9day", "trkn", "\xa9gen", "\xa9cmt"]:
      if not audiotags.has_key(item):
        tags.append("")
      else:
        if type(audiotags[item]) == list: # dealing with a list - use first value
          tags.append(str(audiotags[item][0]))
        else: # strings
          tags.append(str(audiotags[item]))
    return tags
    
  def setTags(self, filename, tags):
    """Sets the metadata on filename"""
    audiotags = MP4(filename)
    # Map our regular tag data to the iTunes MP4 atom names.
    audiotags["\xa9nam"] = tags[0]
    audiotags["\xa9ART"] = tags[1]
    audiotags["\xa9alb"] = tags[2]
    audiotags["\xa9day"] = tags[3]
    # MP4 requires a tuple here - (track#,#tracks)
    if type(tags[4]) == list and len(tags[4]) == 2:
      audiotags["trkn"] = [tags[4]]
    else:
      audiotags["trkn"] = [(int(tags[4]), 0)]
    audiotags["\xa9gen"] = tags[5]
    audiotags["\xa9cmt"] = tags[6]
    audiotags.save()

  def decode(self, filename, newname):
    """Decodes a AAC file"""
    if MSWINDOWS:
      command = 'faad.exe "%(a)s" -o "%(b)s" 2>&1 | awk.exe -vRS="\\r" "(NR>1){gsub(/%%/,\\" \\");print $1/100;fflush();}"' % {'a': filename, 'b': newname}
    else:
      command = "faad '%(a)s' -o '%(b)s' 2>&1 | awk -vRS='\\r' '(NR>1){gsub(/%%/,\" \");print $1/100;fflush();}'" % {'a': filename, 'b': newname}
    sub = subprocess.Popen(command, shell=True, env=environ, stderr=subprocess.PIPE, stdout=subprocess.PIPE, stdin=subprocess.PIPE)
    return sub, command

  def encode(self, filename, newname, quality):
    """Encodes a new AAC file"""
    if MSWINDOWS:
      command = 'faac.exe -w -q %(a)i "%(b)s" -o "%(c)s" 2>&1 | awk.exe -vRS="\\r" "(NR>1){gsub(/%%/,\\" \\");print $3/100;fflush();}"' % {'a': quality, 'b': filename, 'c': newname}
    else:
      command = "faac -w -q %(a)i '%(b)s' -o '%(c)s' 2>&1 | awk -vRS='\\r' '(NR>1){gsub(/%%/,\" \");print $3/100;fflush();}'" % {'a': quality, 'b': filename, 'c': newname}
    sub = subprocess.Popen(command, shell=True, env=environ, stderr=subprocess.PIPE, stdout=subprocess.PIPE, stdin=subprocess.PIPE)
    return sub, command

# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------

class mplayer:
  """MPlayer format class for some misc. mplayer-compatible filetypes"""
  def __init__(self):
    """Initialize"""
    self.__encode = False
    self.__decode = False
    self.__tags = False
    self.extensions = ['wma', 'shn']
    self.check()
    self.__qualities = [
    ['-', _('(Based on original file)')]
                       ]

  def check(self):
    """Check if the required program(s) exist"""
    if which('mplayer'):
      self.__decode = True
    else:
      self.__decode = False
    self.__tags = False

  def get(self):
    """Return all information on the format"""
    return [self.__encode, self.__decode, self.__tags, self.__qualities]

  def getTags(self, filename):
    """Retrieves the metadata from filename"""
    return None
    
  def setTags(self, filename, tags):
    """Sets the metadata on filename"""
    return
  
  # FIXME: Finish this
  def decode(self, filename, newname):
    """Decodes a mplayer-playable file"""
    if MSWINDOWS:
      command = 'mplayer.exe -quiet -vo null -vc dummy -ao pcm:waveheader:file="%(b)s" "%(a)s" 2>&1 | awk.exe -vRS="\\r" "($2~/^[-+]?[0-9]/ && $5~/^[-+]?[0-9]/){print $2/$5*100;fflush();}"' % {'a': filename, 'b': newname}
    else:
      command = "mplayer -quiet -vo null -vc dummy -ao pcm:waveheader:file='%(b)s' '%(a)s' 2>&1 | awk -vRS='\\r' '($2~/^[-+]?[0-9]/ && $5~/^[-+]?[0-9]/){print $2/$5*100;fflush();}'" % {'a': filename, 'b': newname}
    sub = subprocess.Popen(command, shell=True, env=environ, stderr=subprocess.PIPE, stdout=subprocess.PIPE, stdin=subprocess.PIPE)
    return sub, command

# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------

class ac3:
  """a52dec >> AC3"""
  def __init__(self):
    """Initialize"""
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
    """Check if the required program(s) exist"""
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
    """Return all information on the format"""
    return [self.__encode, self.__decode, self.__tags, self.__qualities]

  def getTags(self, filename):
    """Retrieves the metadata from filename"""
    return None
    
  def setTags(self, filename, tags):
    """Sets the metadata on filename"""
    if MSWINDOWS:
      return
    return

  def decode(self, filename, newname):
    """Decodes a AC3 file"""
    if MSWINDOWS:
      command = 'echo 0;a52dec.exe -o wav "%(a)s" > "%(b)s"' % {'a': filename, 'b': newname}
    else:
      command = "echo 0;a52dec -o wav '%(a)s' > '%(b)s'" % {'a': filename, 'b': newname}
    sub = subprocess.Popen(command, shell=True, env=environ, stderr=subprocess.PIPE, stdout=subprocess.PIPE, stdin=subprocess.PIPE)
    return sub, command

  def encode(self, filename, newname, quality):
    """Encodes a new AC3 file"""
    if MSWINDOWS:
      command = 'echo 0;ffmpeg.exe -i "%(b)s" -y -ab %(a)ik -f ac3 "%(c)s" 2>&1 | awk.exe -vRS="\10\10\10\10\10\10" "(NR>1){gsub(/%%/,\\" \\");if($1 != \\"\\") print $1;fflush();}"' % {'a': quality, 'b': filename, 'c': newname}
    else:
      command = "echo 0;ffmpeg -i '%(b)s' -y -ab %(a)ik -f ac3 '%(c)s' 2>&1 | awk -vRS='\10\10\10\10\10\10' '(NR>1){gsub(/%%/,\" \");if($1 != \"\") print $1;fflush();}'" % {'a': quality, 'b': filename, 'c': newname}
    sub = subprocess.Popen(command, shell=True, env=environ, stderr=subprocess.PIPE, stdout=subprocess.PIPE, stdin=subprocess.PIPE)
    return sub, command


# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------

class wv:
  """The wavpack format class. Requires wvunpack, wavpack (wavpack)"""
  def __init__(self):
    """Initialize"""
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
    """Check if the required program(s) exist"""
    if which('wvunpack'):
      self.__decode = True
    else:
      self.__decode = False
    if which('wavpack'):
      self.__encode = True
    else:
      self.__encode = False
    # mutagen supports wavpack tags
    self.__tags = True

  def get(self):
    """Return all information on the format"""
    return [self.__encode, self.__decode, self.__tags, self.__qualities]

  def getTags(self, filename):
    """Retrieves the metadata from filename"""
    audiotags = WavPack(filename)
    return getTrackInfo(audiotags)
    
  def setTags(self, filename, tags):
    """Sets the metadata on filename"""
    audiotags = WavPack(filename)
    saveTrackInfo(audiotags, tags)

  # -c || -i for lossless||lossy.... I smell workarounds :/
  def decode(self, filename, newname):
    """Decodes a WVPk file"""
    if MSWINDOWS:
      command = 'wvunpack.exe -y "%(a)s" -o "%(b)s" 2>&1 | awk.exe -vRS="\10\10\10\10\10\10" "(NR>1){gsub(/%%/,\\" \\");if($1 != \\"\\") print $1/100;fflush();}"' % {'a': filename, 'b': newname}
    else:
      command = "wvunpack -y '%(a)s' -o '%(b)s' 2>&1 | awk -vRS='\10\10\10\10\10\10' '(NR>1){gsub(/%%/,\" \");if($1 != \"\") print $1/100;fflush();}'" % {'a': filename, 'b': newname}
    sub = subprocess.Popen(command, shell=True, env=environ, stderr=subprocess.PIPE, stdout=subprocess.PIPE, stdin=subprocess.PIPE)
    return sub, command

  def encode(self, filename, newname, quality):
    """Encodes a new WVPK file"""
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
  """Recheck all formats"""
  for format in FORMATS.values():
    format.check()

def getFileType(path):
  """Return the file type based on extension"""
  fileExtension = path.split('.')[-1].lower()
  for format in FORMATS.values():
    for extension in format.extensions:
      if fileExtension == extension:
        return format
  # unknown filetype!
  return False

def decodable(path):
  """Checks if a given file is currently decodable"""
  fileType = getFileType(path)
  if fileType == False:
    # unknown filetype!
    return False
  return fileType.get()[1]

