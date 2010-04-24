#!/usr/bin/env python
#
# This file is part of Panucci.
# Copyright (c) 2008-2010 The Panucci Audiobook and Podcast Player Project
#
# Panucci is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Panucci is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Panucci.  If not, see <http://www.gnu.org/licenses/>.
#

from __future__ import absolute_import

import gtk
import os
import os.path
import sys
import traceback
import webbrowser
import logging

__log = logging.getLogger('panucci.util')


def string_in_file( filepath, string ):
    try:
        f = open( filepath, 'r' )
        found = f.read().find( string ) != -1
        f.close()
    except:
        found = False

    return found


class Platform(object):
    """ A platform detection class """
    
    PLATFORM_ENV_VAR = "PANUCCIPLATFORM"
    
    def __init__(self):
        self.MAEMO, self.MAEMO5, self.DESKTOP = (False,)*3
        
        if os.getenv(self.PLATFORM_ENV_VAR) is not None:
            self.MAEMO   = os.getenv(self.PLATFORM_ENV_VAR) == "MAEMO"
            self.MAEMO5  = os.getenv(self.PLATFORM_ENV_VAR) == "MAEMO5"
            self.DESKTOP = os.getenv(self.PLATFORM_ENV_VAR) == "DESKTOP"
        
        # If no platform is forced by an environment variable, try to
        # detect what platform we're running on
        if not ( self.MAEMO or self.MAEMO5 or self.DESKTOP ):
        
            # Checks for older versions of Maemo (diablo, chinook, etc)
            if ( os.path.exists('/etc/osso_software_version') or
                 os.path.exists('/proc/component_version') or
                 string_in_file('/etc/issue', 'maemo') ):
                self.MAEMO = True
            
            # Otherwise we're just using regular desktop-linux
            else:
                self.DESKTOP = True
            
            # Check for Maemo 5 (fremantle)
            if string_in_file('/etc/issue', 'Maemo 5'):
                self.MAEMO5 = True
                
        # For now MAEMO5 implies MAEMO
        self.MAEMO = self.MAEMO or self.MAEMO5


platform = Platform()

if platform.DESKTOP:
    try:
        import pynotify
        pynotify.init('Panucci')
        have_pynotify = True
    except:
        have_pynotify = False
elif platform.MAEMO:
    import hildon

try:
    import osso
    have_osso = True
except:
    have_osso = False


def convert_ns(time_int):
    time_int = max( 0, int(time_int) )
    time_int = time_int / 10**9
    time_str = ""
    if time_int >= 3600:
        _hours = time_int / 3600
        time_int = time_int - (_hours * 3600)
        time_str = str(_hours) + ":"
    if time_int >= 600:
        _mins = time_int / 60
        time_int = time_int - (_mins * 60)
        time_str = time_str + str(_mins) + ":"
    elif time_int >= 60:
        _mins = time_int / 60
        time_int = time_int - (_mins * 60)
        time_str = time_str + "0" + str(_mins) + ":"
    else:
        time_str = time_str + "00:"
    if time_int > 9:
        time_str = time_str + str(time_int)
    else:
        time_str = time_str + "0" + str(time_int)

    return time_str

def detect_filetype( filepath ):
    if len(filepath.split('.')) > 1:
        filename, extension = filepath.rsplit( '.', 1 )
        return extension.lower()

def pretty_filename( filename ):
    filename, extension = os.path.basename(filename).rsplit('.',1)
    return filename.replace('_', ' ')

def build_full_path( path ):
    if path is not None:
        if path.startswith('/'):
            return os.path.abspath(path)
        else:
            return os.path.abspath( os.path.join(os.getcwdu(), path) )

def open_link(d, url, data):
    webbrowser.open_new(url)

def find_image(filename):
    locations = ['./icons/', '../icons/', '/usr/share/panucci/',
        os.path.dirname(sys.argv[0])+'/../icons/']

    for location in locations:
        if os.path.exists(location+filename):
            return os.path.abspath(location+filename)

def notify( msg, title='Panucci' ):
    """ Sends a notification using pynotify, returns msg """

    if platform.DESKTOP and have_pynotify:
        icon = find_image('panucci_64x64.png')
        args = ( title, msg ) if icon is None else ( title, msg, icon )
        notification = pynotify.Notification(*args)
        notification.show()
    elif platform.MAEMO:
        # Note: This won't work if we're not in the gtk main loop
        markup = '<b>%s</b>\n<small>%s</small>' % (title, msg)
        hildon.hildon_banner_show_information_with_markup(
            gtk.Label(''), None, markup )

    return msg

def poke_backlight():
    """ Prevents the backlight from turning off (screen blanking).
        Note: this needs to be called once a minute to be effective """

    if have_osso:
        dev = osso.DeviceState(osso.Context('ScreenManager', '0.0.1', False))
        dev.display_blanking_pause()
    elif platform.MAEMO:
        __log.info('Please install python2.5-osso for backlight ctl support.')
        return False

    return True

def get_logfile():
    if platform.MAEMO:
        f = '~/MyDocs/panucci.log'
    else:
        f = '~/.panucci.log'
    
    return os.path.expanduser( f )
