# -*- coding: utf-8 -*-
#
# This file is part of Panucci.
# Copyright (c) 2008-2011 The Panucci Project
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

from __future__ import absolute_import

import logging
import time
import re
import dbus
import os.path
from hashlib import md5
from xml.sax.saxutils import escape

from panucci import util
from panucci.dbsqlite import db

class PlaylistFile(object):
    """ The base class for playlist file parsers/exporters,
        this should not be used directly but instead subclassed. """

    def __init__(self, filepath, queue):
        self.__log = logging.getLogger('panucci.playlist.PlaylistFile')
        self._filepath = filepath
        self._file = None
        self._items = queue

    def __open_file(self, filepath, mode):
        if self._file is not None:
            self.close_file()

        try:
            self._file = open( filepath, mode )
            self._filepath = filepath
        except Exception, e:
            self._filepath = None
            self._file = None

            self.__log.exception( 'Error opening file: %s', filepath)
            return False

        return True

    def __close_file(self):
        error = False

        if self._file is not None:
            try:
                self._file.close()
            except Exception, e:
                self.__log.exception( 'Error closing file: %s', self.filepath )
                error = True

        self._filepath = None
        self._file = None

        return not error

    def get_absolute_filepath(self, item_filepath):
        if item_filepath is None: return

        if item_filepath.startswith('/'):
            path = item_filepath
        else:
            path = os.path.join(os.path.dirname(self._filepath), item_filepath)

        if os.path.exists( path ):
            return path

    def get_filelist(self):
        return [ item.filepath for item in self._items ]

    def get_filedicts(self):
        dict_list = []
        for item in self._items:
            d = { 'title': item.title,
                  'length': item.length,
                  'filepath': item.filepath }

            dict_list.append(d)
        return dict_list

    def get_queue(self):
        return self._items

    def export_items(self, filepath=None):
        if filepath is not None:
            self._filepath = filepath

        if self.__open_file(filepath, 'w'):
            self.export_hook(self._items)
            self.__close_file()
            return True
        else:
            return False

    def export_hook(self, playlist_items):
        pass

    def parse(self, filepath):
        if self.__open_file( filepath, mode='r' ):
            current_line = self._file.readline()
            while current_line:
                self.parse_line_hook( current_line.strip() )
                current_line = self._file.readline()
            self.__close_file()
            self.parse_eof_hook()
        else:
            return False
        return True

    def parse_line_hook(self, line):
        pass

    def parse_eof_hook(self):
        pass

    def _add_playlist_item(self, item):
        path = self.get_absolute_filepath(item.playlist_reported_filepath)
        if path is not None and os.path.isfile(path):
            item.filepath = path
            self._items.append(item)

class M3U_Playlist(PlaylistFile):
    """ An (extended) m3u parser/writer """

    def __init__(self, *args):
        self.__log = logging.getLogger('panucci.playlist.M3U_Playlist')
        PlaylistFile.__init__( self, *args )
        self.extended_m3u = False
        self.current_item = PlaylistItem()

    def parse_line_hook(self, line):
        if line.startswith('#EXTM3U'):
            self.extended_m3u = True
        elif self.extended_m3u and line.startswith('#EXTINF'):
            match = re.match('#EXTINF:([^,]+),(.*)', line)
            if match is not None:
                length, title = match.groups()
                try: length = int(length)
                except: length = -1
                self.current_item.playlist_length = length
                self.current_item.playlist_title = title
        elif line.startswith('#'):
            pass # skip comments
        elif line:
            path = self.get_absolute_filepath( line )
            if path is not None:
                if os.path.isfile( path ):
                    self.current_item.playlist_reported_filepath = line
                    self._add_playlist_item(self.current_item)
                    self.current_item = PlaylistItem()
                elif os.path.isdir( path ):
                    files = os.listdir( path )
                    files.sort()
                    for file in files:
                        item = PlaylistItem()
                        item.playlist_reported_filepath=os.path.join(line,file)
                        self._add_playlist_item(item)

    def export_hook(self, playlist_items):
        self._file.write('#EXTM3U\n\n')

        for item in playlist_items:
            string = ''
            if not ( item.length is None and item.title is None ):
                length = -1 if item.length is None else int(item.length)
                title = '' if item.title is None else item.title
                string += '#EXTINF:%d,%s\n' % ( length, title )

            string += '%s\n' % item.filepath
            self._file.write(string)

class PLS_Playlist(PlaylistFile):
    """ A somewhat simple pls parser/writer """

    def __init__(self, *args):
        self.__log = logging.getLogger('panucci.playlist.PLS_Playlist')
        PlaylistFile.__init__( self, *args )
        self.current_item = PlaylistItem()
        self.in_playlist_section = False
        self.current_item_number = None

    def __add_current_item(self):
        self._add_playlist_item(self.current_item)

    def parse_line_hook(self, line):
        sect_regex = '\[([^\]]+)\]'
        item_regex = '[^\d]+([\d]+)=(.*)'

        if re.search(item_regex, line) is not None:
            current = re.search(item_regex, line).group(1)
            if self.current_item_number is None:
                self.current_item_number = current
            elif self.current_item_number != current:
                self.__add_current_item()

                self.current_item = PlaylistItem()
                self.current_item_number = current

        if re.search(sect_regex, line) is not None:
            section = re.match(sect_regex, line).group(1).lower()
            self.in_playlist_section = section == 'playlist'
        elif not self.in_playlist_section:
            pass # don't do anything if we're not in [playlist]
        elif line.lower().startswith('file'):
            self.current_item.playlist_reported_filepath = re.search(
                item_regex, line).group(2)
        elif line.lower().startswith('title'):
            self.current_item.playlist_title = re.search(
                                                    item_regex, line).group(2)
        elif line.lower().startswith('length'):
            try: length = int(re.search(item_regex, line).group(2))
            except: length = -1
            self.current_item.playlist_length = length

    def parse_eof_hook(self):
        self.__add_current_item()

    def export_hook(self, playlist_items):
        self._file.write('[playlist]\n')
        self._file.write('NumberOfEntries=%d\n\n' % len(playlist_items))

        for i,item in enumerate(playlist_items):
            title = '' if item.title is None else item.title
            length = -1 if item.length is None else item.length
            self._file.write('File%d=%s\n' % (i+1, item.filepath))
            self._file.write('Title%d=%s\n' % (i+1, title))
            self._file.write('Length%d=%s\n\n' % (i+1, length))

        self._file.write('Version=2\n')

class PlaylistItem(object):
    """ A (hopefully) lightweight object to hold the bare minimum amount of
        data about a single item in a playlist and it's bookmark objects. """

    def __init__(self):
        self.__log = logging.getLogger('panucci.playlist.PlaylistItem')

        self.__filepath = None
        self.__metadata = None
        self.playlist_id = None
        self.duplicate_id = 0
        self.seek_to = 0

        # metadata that's pulled from the playlist file (pls/extm3u)
        self.playlist_reported_filepath = None
        self.playlist_title = None
        self.playlist_length = None

        # a flag to determine whether the item's bookmarks need updating
        # ( used for example, if the duplicate_id is changed )
        self.is_modified = False
        self.bookmarks = []

    def __set_filepath(self, fp):
        if fp != self.__filepath:
            self.__filepath = fp
            self.__metadata = FileMetadata(self.filepath)
            # Don't extract Metadata right away, this makes opening large
            #   playlists _very_ slow. TODO: do this intelligently AND
            #   perhaps del the Metadata object if the file is no longer
            #   being used.
            #self.__metadata.extract_metadata()

    def __get_filepath(self):
        return self.__filepath

    filepath = property( __get_filepath, __set_filepath )

    @staticmethod
    def create_by_filepath(reported_filepath, filepath):
        item = PlaylistItem()
        item.playlist_reported_filepath = reported_filepath
        item.filepath = filepath
        return item

    def __eq__(self, b):
        if isinstance( b, PlaylistItem ):
            return ( self.filepath == b.filepath and
                     self.duplicate_id == b.duplicate_id )
        elif isinstance( b, str ):
            return str(self) == b
        else:
            self.__log.warning('Unsupported comparison: %s', type(b))
            return False

    def __str__(self):
        uid = self.filepath + str(self.duplicate_id)
        return md5(uid).hexdigest()

    @property
    def metadata(self):
        """ Returns a dict of metadata, wooo. """

        metadata = self.__metadata.get_metadata()
        metadata['title'] = self.title
        return metadata

    @property
    def filetype(self):
        return util.detect_filetype(self.filepath)

    def __get_title(self):
        """ Get the title of item, priority is (most important first):
            1. the title in the file's metadata (ex. ID3)
            2. the title given in playlist metadata
            3. a "pretty" version of the filename """

        if self.__metadata.title:
            return self.__metadata.title
        elif self.playlist_title is not None:
            return self.playlist_title
        else:
            return util.pretty_filename(self.filepath)

    # For now set the "playlist_title" because it has highest priority in the
    # __get_title method. We might evenually want to create a separate
    # __custom_title to preserve the playlist_title.
    title = property(__get_title, lambda s,v: setattr(s, 'playlist_title', v))

    @property
    def length(self):
        """ Get the lenght of the item priority is (most important first):
            1. length as reported by mutagen
            2. length found in playlist metadata
            3. otherwise -1 when unknown """

        if self.__metadata.length:
            return self.__metadata.length
        elif self.playlist_length:
            return self.playlist_length
        else:
            return -1

    def load_bookmarks(self):
        self.bookmarks = db.load_bookmarks(
            factory                 = Bookmark().load_from_dict,
            playlist_id             = self.playlist_id,
            bookmark_filepath       = self.filepath,
            playlist_duplicate_id   = self.duplicate_id,
            request_resume_bookmark = None  )

    def save_bookmark(self, name, position, resume_pos=False):
        b = Bookmark()
        b.playlist_id = self.playlist_id
        b.bookmark_name = name
        b.bookmark_filepath = self.filepath
        b.seek_position = position
        b.timestamp = time.time()
        b.is_resume_position = resume_pos
        b.playlist_duplicate_id = self.duplicate_id
        b.save()
        self.bookmarks.append(b)

    def get_bookmark(self, bkmk_id):
        for i in self.bookmarks:
            if str(i) == bkmk_id:
                return i

    def delete_bookmark(self, bookmark_id):
        """ WARNING: if bookmark_id is None, ALL bookmarks will be deleted """
        if bookmark_id is None:
            self.__log.debug( 'Deleting all bookmarks for %s',
                              self.playlist_reported_filepath )

            for bkmk in self.bookmarks:
                bkmk.delete()
            self.bookmarks = []
        else:
            bookmark = self.get_bookmark(bookmark_id)
            pos = self.bookmarks.index(bookmark)
            if pos >= 0:
                self.bookmarks[pos].delete()
                self.bookmarks.remove(bookmark)
            else:
                self.__log.info('Cannot find bookmark with id: %s',bookmark_id)
                return False
        return True

    def update_bookmarks(self):
        for bookmark in self.bookmarks:
            bookmark.playlist_duplicate_id = self.duplicate_id
            bookmark.bookmark_filepath = self.filepath
            db.update_bookmark(bookmark)

class Bookmark(object):
    """ A single bookmark, nothing more, nothing less. """

    def __init__(self):
        self.__log = logging.getLogger('panucci.playlist.Bookmark')

        self.id = 0
        self.playlist_id = None
        self.bookmark_name = ''
        self.bookmark_filepath = ''
        self.seek_position = 0
        self.timestamp = 0
        self.is_resume_position = False
        self.playlist_duplicate_id = 0

    @staticmethod
    def load_from_dict(bkmk_dict):
        bkmkobj = Bookmark()

        for key,value in bkmk_dict.iteritems():
            if hasattr( bkmkobj, key ):
                setattr( bkmkobj, key, value )
            else:
                self.__log.info("Attr: %s doesn't exist...", key)

        return bkmkobj

    def save(self):
        self.id = db.save_bookmark(self)
        return self.id

    def delete(self):
        return db.remove_bookmark(self.id)

    def __eq__(self, b):
        if isinstance(b, str):
            return str(self) == b
        elif b is None:
            return False
        else:
            self.__log.warning('Unsupported comparison: %s', type(b))
            return False

    def __str__(self):
        uid =  self.bookmark_filepath
        uid += str(self.playlist_duplicate_id)
        uid += str(self.seek_position)
        return md5(uid).hexdigest()

    def __cmp__(self, b):
        if self.bookmark_filepath == b.bookmark_filepath:
            if self.seek_position == b.seek_position:
                return 0
            else:
                return -1 if self.seek_position < b.seek_position else 1
        else:
            self.__log.info(
                "Can't compare bookmarks from different files:\n\tself: %s"
                "\n\tb: %s", self.bookmark_filepath, b.bookmark_filepath )
            return 0

class FileMetadata(object):
    """ A class to hold all information about the file that's currently being
        played. Basically it takes care of metadata extraction... """

    coverart_names = ['cover', 'front', 'albumart', 'back']
    coverart_extensions = ['.png', '.jpg', '.jpeg']
    tag_mappings = {
        'mp4': { '\xa9nam': 'title',
                 '\xa9ART': 'artist',
                 '\xa9alb': 'album',
                 'covr':    'coverart' },
        'mp3': { 'TIT2': 'title',
                 'TPE1': 'artist',
                 'TALB': 'album',
                 'APIC': 'coverart' },
        'ogg': { 'title':  'title',
                 'artist': 'artist',
                 'album':  'album' ,
                 'METADATA_BLOCK_PICTURE': 'coverart' },
        'flac':{ 'TITLE': 'title',
                 'ARTIST': 'artist',
                 'ALBUM': 'album' }
    }
    tag_mappings['m4a']  = tag_mappings['mp4']
    tag_mappings['opus'] = tag_mappings['ogg']

    def __init__(self, filepath):
        self.__log = logging.getLogger('panucci.playlist.FileMetadata')
        self.__filepath = filepath

        self.title = ''
        self.artist = ''
        self.album = ''
        self.length = 0
        self.coverart = None

        self.__metadata_extracted = False

    def _ask_gpodder_for_metadata(self):
        GPO_NAME = 'org.gpodder'
        GPO_PATH = '/podcasts'
        GPO_INTF = 'org.gpodder.podcasts'

        bus = dbus.SessionBus()
        try:
            if bus.name_has_owner(GPO_NAME):
                o = bus.get_object(GPO_NAME, GPO_PATH)
                i = dbus.Interface(o, GPO_INTF)
                episode, podcast = i.get_episode_title(self.__filepath)
                if episode and podcast:
                    self.title = episode
                    self.artist = podcast
                    self.__metadata_extracted = True
                    return True
        except Exception, e:
            self.__log.debug('Cannot get metadata from gPodder: %s', str(e))

        return False

    def extract_metadata(self):
        self.__log.debug('Extracting metadata for %s', self.__filepath)

        if self._ask_gpodder_for_metadata():
            if self.coverart is None:
                self.coverart = self.__find_coverart()
            return

        filetype = util.detect_filetype(self.__filepath)

        if filetype == 'mp3':
            import mutagen.mp3 as meta_parser
        elif filetype == 'ogg':
            import mutagen.oggvorbis as meta_parser
        elif filetype == 'opus':
            import mutagen.oggopus as meta_parser
        elif filetype == 'flac':
            import mutagen.flac as meta_parser
        elif filetype in ['mp4', 'm4a']:
            import mutagen.mp4 as meta_parser
        else:
            self.__log.info(
                'Extracting metadata not supported for %s files.', filetype )
            return False

        try:
            metadata = meta_parser.Open(self.__filepath)
            self.__metadata_extracted = True
        except Exception, e:
            self.title = util.pretty_filename(self.__filepath)
            self.__log.exception('Error running metadata parser...')
            self.__metadata_extracted = False
            return False

        self.length = metadata.info.length * 10**9
        for tag in self.tag_mappings[filetype].keys():
            value = None
            if filetype in ["ogg", "flac", "opus"]:
                for _tup in metadata.tags:
                    if tag == _tup[0]:
                        value = _tup[1]
            else:
                for _key in metadata.tags.keys():
                    if tag == _key:
                        value = metadata.tags[_key]
                        if isinstance(value, list):
                            value = value[0]
            if value:
                if self.tag_mappings[filetype][tag] != 'coverart':
                    try:
                        value = escape(unicode(value).strip().encode("utf-8"))
                    except Exception, e:
                        self.__log.exception(
                          'Could not convert tag (%s) to escaped string', tag )
                else:
                    # some coverart classes store the image in the data
                    # attribute whereas others do not :S
                    if hasattr( value, 'data' ):
                        value = value.data
                    elif filetype in ["ogg", "opus"]:
                        import mutagen.flac
                        import base64
                        _pic = mutagen.flac.Picture(base64.b64decode(value))
                        value = _pic.data

                setattr( self, self.tag_mappings[filetype][tag], value )

        if filetype == 'flac' and metadata.pictures:
            self.coverart = metadata.pictures[0].data
        if self.coverart is None:
            self.coverart = self.__find_coverart()

    def __find_coverart(self):
        """ Find coverart in the same directory as the filepath """

        if '://' in self.__filepath and \
                not self.__filepath.startswith('file://'):
            # No cover art for streaming at the moment
            return None

        directory = os.path.dirname(self.__filepath)
        for cover in self.__find_coverart_filepath(directory):
            self.__log.debug('Trying to load coverart from %s', cover)
            try:
                f = open(cover,'r')
            except:
                self.__log.exception('Could not open coverart file %s', cover )
                continue

            binary_coverart = f.read()
            f.close()

            if self.__test_coverart(binary_coverart):
                return binary_coverart

        return None

    def __test_coverart(self, data):
        """ tests to see if the file is a proper image file that can be loaded
            into a gtk.gdk.Pixbuf """

        return True

    def __find_coverart_filepath(self, directory):
        """ finds the path of potential coverart files """
        dir_filelist = []
        possible_matches = []

        # build the filelist
        for f in os.listdir(directory):
            if os.path.isfile(os.path.join(directory,f)):
                dir_filelist.append(os.path.splitext(f))

        # first pass, check for known filenames
        for f,ext in dir_filelist[:]:
            if f.lower() in self.coverart_names and \
                ext.lower() in self.coverart_extensions:
                possible_matches.append((f,ext))
                dir_filelist.remove((f,ext))

        # second pass, check for known filenames without extensions
        for f,ext in dir_filelist[:]:
            if f.lower() in self.coverart_names and ext == '':
                possible_matches.append((f,ext))
                dir_filelist.remove((f,ext))

        # third pass, check for any image file
        for f,ext in dir_filelist[:]:
            if ext.lower() in self.coverart_extensions:
                possible_matches.append((f,ext))
                dir_filelist.remove((f,ext))

        # yield the results
        for f,ext in possible_matches:
            yield os.path.join( directory, f+ext )

    def get_metadata(self):
        """ Returns a dict of metadata """

        if not self.__metadata_extracted:
            self.extract_metadata()

        metadata = {
            'title':    self.title,
            'artist':   self.artist,
            'album':    self.album,
            'image':    self.coverart,
            'length':   self.length
        }

        return metadata
