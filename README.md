audio-convert-mod
======
A simple audio file converter that supporting many formats. Convert music files
between WAV, MP3, AAC, Ogg and more.

***Note: development of audio-convert-mod stopped in 2009.** You may have better
luck with similar actively maintained software such as [SoundConverter](http://soundconverter.org/).*

## Features
* Simple interface with progress indicators (current file + total conversion
  operation)
* Convert all files within a directory (recursively or non-recursively) using
  the same settings
* Copy file metadata/tags
* Wide format support: WAV, MP3, AAC/M4A, Ogg Vorbis, FLAC, Musepack, Monkey's
  audio, AC3/Dolby Digital, and Wavpack
* GNOME2 integration: minimize to tray icon and convert in the background, and
  Nautilus file explorer integration for media conversion with right-click
* Skip mistakenly added files on-the-fly
* Advanced options to help you keep your media files organized such as moving
  the source files after conversion or placing the newly converted files in a
  different folder

## Platform compatibility
Linux only (macOS theoretically, but untested).

## Dependencies
audio-convert-mod expects the following software to be available:
* `python` version 2.x, min. version 2.4
* `pygtk` python package >= 2.10 (with Glade support)
* `mutagen` python package

Developers and/or users wanting to build from source will also require `autotools`, `intltool` and `gettext`.

audio-convert-mod does not contain any media transcoding tools itself. Once
audio-convert-mod is running, you may select *File > Show Format Conversion
Capabilities* to see which additional tools are required to convert audio into
your preferred format(s). 

### Supported decoders
* `lame` for MP3
* `vorbis-tools` for OGG
* `musepack-tools` for Musepack (MPC)
* `flac` for FLAC
* `mac` for Monkey's Audio (APE)
* `faac` for AAC / M4A / MP4
* `wavpack` for Wavpack (WV)
* `a52dec` for Dolby Digital (AC3)

### Supported encoders
* `lame` for MP3
* `vorbis-tools` for OGG
* `musepack-tools` for Musepack (MPC)
* `flac` for FLAC
* `mac` for Monkey's Audio (APE)
* `faad` for AAC / M4A / MP4
* `wavpack` for Wavpack (WV)
* `ffmpeg` for Dolby Digital (AC3)

## Building from source
If you are **not** using a release download, you will need to generate the `configure` script by running `./autogen.sh` before running the steps below.

Configure and build audio-convert-mod:
```
./configure --prefix=/usr
make
```
Then run `make install` as root (or use sudo) to permanently install it on your system.

## Usage
audio-convert-mod installs a menu entry, or simply run `audio-convert-mod` from
the CLI.

If you would like to specify files to convert, add each as an argument:
```
audio-convert-mod /path/to/File1.mp3 /path/to/File2.ogg [...]
```

## Debugging
If you think you've found a bug in audio-convert-mod, run the application with
verbose output enabled:
```
audio-convert-mod --verbose
```
