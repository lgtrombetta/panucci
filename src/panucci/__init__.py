# -*- coding: utf-8 -*-



import os.path

__version__ = '0.99.6.0'

HOME = os.path.expanduser('~/.config/panucci')

if not os.path.exists(HOME):
    import os
    os.makedirs(HOME)

SETTINGS_FILE = os.path.join(HOME, 'panucci.conf')
DATABASE_FILE = os.path.join(HOME, 'panucci.sqlite')
PLAYLIST_FILE = os.path.join(HOME, 'panucci.m3u')
LOGFILE = os.path.join(HOME, 'panucci.log')
THEME_FILE = os.path.join(HOME, 'theme.conf')

EXTENSIONS = ('mp2', 'mp3', 'mp4', 'ogg', 'm4a', 'wav', 'flac', 'opus', 'aac', 'alac')
PLAYLISTS = ('m3u')
IMAGES = ('png', 'jpg', 'jpeg')
