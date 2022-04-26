# bottle_installers.py
#
# Copyright 2020 brombinmirko <send@mirko.pm>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os
from gettext import gettext as _
from gi.repository import Gtk

from bottles.utils.threading import RunAsync  # pyright: reportMissingImports=false
from bottles.utils.common import open_doc_url
from bottles.widgets.dependency import DependencyEntry


@Gtk.Template(resource_path='/com/usebottles/bottles/details-dependencies.ui')
class DependenciesView(Gtk.ScrolledWindow):
    __gtype_name__ = 'DetailsDependencies'

    # region Widgets
    list_dependencies = Gtk.Template.Child()
    btn_report = Gtk.Template.Child()
    btn_help = Gtk.Template.Child()
    btn_install = Gtk.Template.Child()
    btn_toggle_selection = Gtk.Template.Child()
    btn_toggle_search = Gtk.Template.Child()
    entry_search = Gtk.Template.Child()
    actions = Gtk.Template.Child()
    search_bar = Gtk.Template.Child()

    # endregion

    def __init__(self, window, config, **kwargs):
        super().__init__(**kwargs)

        # common variables and references
        self.window = window
        self.manager = window.manager
        self.config = config
        self.selected_dependencies = []

        entry_search_ev = Gtk.EventControllerKey.new()
        entry_search_ev.connect("key-pressed", self.__search_dependencies)
        self.entry_search.add_controller(entry_search_ev)

        self.btn_report.connect("clicked", open_doc_url, "contribute/missing-dependencies")
        self.btn_help.connect("clicked", open_doc_url, "bottles/dependencies")
        self.btn_toggle_selection.connect('toggled', self.__toggle_selection)
        self.btn_toggle_search.connect('toggled', self.__toggle_search)
        self.btn_install.connect('clicked', self.__install_dependencies)
        self.list_dependencies.connect('row-selected', self.__select_dependency)

    def __select_dependency(self, widget, row, data=None):
        if row is not None:
            self.selected_dependencies.append(row.dependency)

    def __install_dependencies(self, widget):
        def callback(result, error=False):
            nonlocal self
            self.selected_dependencies = []
            self.update(config=self.config)

        def process_queue():
            nonlocal self
            for d in self.selected_dependencies:
                self.manager.dependency_manager.install(self.config, d)

        self.btn_toggle_selection.set_active(False)
        self.list_dependencies.set_sensitive(False)

        RunAsync(process_queue, callback=callback)

    def __search_dependencies(self, widget, event=None, data=None):
        """
        This function search in the list of dependencies the
        text written in the search entry.
        """
        terms = self.entry_search.get_text()
        self.list_dependencies.set_filter_func(
            self.__filter_dependencies,
            terms
        )

    def __toggle_selection(self, widget):
        """
        This function toggle the selection of the dependencies
        in the list.
        """
        widgets = [self.btn_help, self.btn_report, self.btn_install]
        list_statues = {
            True: Gtk.SelectionMode.MULTIPLE,
            False: Gtk.SelectionMode.NONE
        }
        status = widget.get_active()
        self.update(config=self.config, selection=status)
        self.window.toggle_selection_mode(status)

        for w in widgets:
            _status = w.get_visible()
            w.set_visible(not _status)

        self.list_dependencies.set_selection_mode(list_statues[status])

    @staticmethod
    def __filter_dependencies(row, terms=None):
        text = row.get_title().lower() + row.get_subtitle().lower()
        if terms.lower() in text:
            return True
        return False

    def update(self, widget=False, config=None, selection=False):
        """
        This function update the dependencies list with the
        supported by the manager.
        """
        if config is None:
            config = {}
        self.config = config

        while self.list_dependencies.get_first_child():
            self.list_dependencies.remove(self.list_dependencies.get_first_child())

        supported_dependencies = self.manager.supported_dependencies
        if len(supported_dependencies.keys()) > 0:
            for dep in supported_dependencies.items():
                if dep[0] in self.config.get("Installed_Dependencies"):
                    '''Do not list already installed dependencies'''
                    continue
                self.list_dependencies.append(
                    DependencyEntry(
                        window=self.window,
                        config=self.config,
                        dependency=dep,
                        selection=selection
                    )
                )

        if not selection and len(self.config.get("Installed_Dependencies")) > 0:
            for dep in self.config.get("Installed_Dependencies"):
                plain = True
                if dep in supported_dependencies:
                    dep = (
                        dep,
                        supported_dependencies[dep]
                    )
                    plain = False

                self.list_dependencies.append(
                    DependencyEntry(
                        window=self.window,
                        config=self.config,
                        dependency=dep,
                        plain=plain
                    )
                )

        self.list_dependencies.set_sensitive(True)

    def __toggle_search(self, widget):
        """
        This function toggle the search mode.
        """
        status = not self.search_bar.get_search_mode()
        self.search_bar.set_search_mode(status)
        if not status:
            self.entry_search.set_text("")
