#!/usr/bin/env python
#
# Copyright (c) 2008 The Panucci Audiobook and Podcast Player Project
# 
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
# 
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
# CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
# 

import os.path
import pickle
import shutil
import time
import logging

from dbsqlite import db
from playlist import Bookmark

_ = lambda s: s
log = logging.getLogger('panucci.pickle_converter')

def load_pickle_file( pfile, create_backup=True ):
    try:
        f = open( pfile, 'r' )
    except Exception, e:
        log.exception('Can\'t open pickle file: %s', pfile)
        return False

    try:
        d = pickle.load(f)
    except:
        log.exception('Can\'t load data from pickle file: %s', pfile)
        return False

    f.close()

    for f, data in d.iteritems():
        if not data.has_key('bookmarks'):
            data['bookmarks'] = []

        if data.has_key('position'):
            data['bookmarks'].append(
                ( _('Auto Bookmark'), data.get('position', 0)) )

        playlist_id = db.get_playlist_id( f, create_new=True )

        for name, position in data['bookmarks']:
            b = Bookmark()
            b.playlist_id = playlist_id
            b.bookmark_filepath = f
            b.timestamp = time.time()
            b.bookmark_name = name
            b.seek_position = position
            b.is_resume_position = name == _('Auto Bookmark')
            db.save_bookmark(b)

    if create_backup:
        shutil.move( pfile, pfile + '.bak' )

    return True

