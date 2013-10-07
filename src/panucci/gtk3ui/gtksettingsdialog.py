# -*- coding: utf-8 -*-
#
# gPodder - A media aggregator and podcast client
# Copyright (c) 2005-2010 Thomas Perl and the gPodder Team
#
# gPodder is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# gPodder is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from gi.repository import Gtk as gtk

from panucci import platform

_ = lambda x: x

class SettingsDialog():
    def __init__(self, main):
        self.main = main
        dialog = gtk.Dialog(_("Settings"),
                   self.main.main_window,
                   gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT)

        # GNOME's UI has instant-apply semantics -> add only Close button
        dialog.add_button(gtk.STOCK_CLOSE, gtk.RESPONSE_CLOSE)

        # List of (action, checkbutton) pairs to update when "Save" is clicked
        actions_to_update = []

        # Group for radio buttons
        radio_button_group = []

        # GNOME/Desktop: Instant-apply by connecting check buttons
        def check_button_factory(action):
                b = gtk.CheckButton()
                action.connect_proxy(b)
                return b
        def radio_button_factory(action):
                #global radio_button_group
                b = gtk.RadioButton()
                if not radio_button_group:
                    radio_button_group.append(b)
                else:
                    b.set_group(radio_button_group[0])
                action.connect_proxy(b)
                b.set_active(action.get_active())
                return b

        vb = gtk.VBox()

        dialog.vbox.add(vb)

        vb.pack_start(gtk.Frame(_('Main window')))
        vb.pack_start(check_button_factory(self.main.action_scrolling_labels))
        vb.pack_start(check_button_factory(self.main.action_lock_progress))
        vb.pack_start(check_button_factory(self.main.action_dual_action_button))
        vb.pack_start(check_button_factory(self.main.action_resume_all))
        vb.pack_start(check_button_factory(self.main.action_play_on_headset))

        vb.pack_start(gtk.Label('')) # Used as a spacer

        vb.pack_start(gtk.Frame(_('Playback')))
        vb.pack_start(check_button_factory(self.main.action_stay_at_end))
        vb.pack_start(check_button_factory(self.main.action_seek_back))

        vb.pack_start(gtk.Label('')) # Used as a spacer

        vb.pack_start(gtk.Frame(_('Play mode')))
        hb = gtk.HBox(homogeneous=True)
        vb.pack_start(hb)

        for action in (self.main.action_play_mode_all,
                self.main.action_play_mode_single,
                self.main.action_play_mode_random,
                self.main.action_play_mode_repeat):
            hb.pack_start(radio_button_factory(action))

        dialog.show_all()
        response = dialog.run()

        if response == gtk.RESPONSE_APPLY:
            # On Maemo 5, if the user picked "Save" we need
            # to copy the state of the buttons into our actions
            for action, button in actions_to_update:
                action.set_active(button.get_active())

        dialog.destroy()
