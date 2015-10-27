#!/usr/bin/env python3
# -*- coding: utf-8 -*-#
#
#  Copyright 2012 Unknown <diogo@arch>
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#
#  Author: Diogo N. Silva
#  Version:
#  Last update:

from kivy.uix.togglebutton import ToggleButton
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.core.window import Window
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.tabbedpanel import TabbedPanel
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.textinput import TextInput
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.spinner import Spinner
from kivy.uix.slider import Slider
from kivy.uix.filechooser import FileChooserListView, FileChooserIconView
from kivy.core.text.markup import MarkupLabel as CoreMarkupLabel
from kivy.utils import get_hex_from_color
from kivy.properties import NumericProperty, StringProperty, BooleanProperty,\
    ObjectProperty
from kivy.uix.screenmanager import Screen
from kivy.graphics import Color, Rectangle

import re
from os.path import join, sep, abspath, pardir


class ShowcaseScreen(Screen):
    fullscreen = BooleanProperty(False)

    def add_widget(self, *args):
        if 'content' in self.ids:
            return self.ids.content.add_widget(*args)
        return super(ShowcaseScreen, self).add_widget(*args)


class StringInput(TextInput):
    """
    Modification of TextInput that only accepts integers
    """

    def insert_text(self, substring, from_undo=False):

        s = re.sub(r"\D", "", substring)

        return super(StringInput, self).insert_text(s, from_undo=from_undo)


class LinkedLabel(Label):
    """
    Modification of label to reformat label for path linking
    """

    def __init__(self, **kwargs):
        super(LinkedLabel, self).__init__(**kwargs)

    @staticmethod
    def create_ref_label(text):
        """
        Modifies the original label by adding references to each directory in
        the path
        """

        s = p = sep
        path_list = text.split(sep)

        for d in path_list:
            p = join(p, d)
            if p != sep:
                s = join(s, "[ref={}]{}[/ref]".format(p, d))

        return s

    def texture_update(self, *largs):
        """Force texture recreation with the current Label properties.

        After this function call, the :attr:`texture` and :attr:`texture_size`
        will be updated in this order.
        """
        mrkup = self._label.__class__ is CoreMarkupLabel
        self.texture = None

        if (not self._label.text or (self.halign[-1] == 'y' or self.strip) and
                not self._label.text.strip()):
            self.texture_size = (0, 0)
            if mrkup:
                self.refs, self._label._refs = {}, {}
                self.anchors, self._label._anchors = {}, {}
        else:
            if mrkup:
                text = self.text
                text = self.create_ref_label(text)
                # we must strip here, otherwise, if the last line is empty,
                # markup will retain the last empty line since it only strips
                # line by line within markup
                if self.halign[-1] == 'y' or self.strip:
                    text = text.strip()
                self._label.text = ''.join(('[color=',
                                            get_hex_from_color(self.color),
                                            ']', text, '[/color]'))
                self._label.refresh()
                # force the rendering to get the references
                if self._label.texture:
                    self._label.texture.bind()
                self.refs = self._label.refs
                self.anchors = self._label.anchors
            else:
                self._label.refresh()
            texture = self._label.texture
            if texture is not None:
                self.texture = self._label.texture
                self.texture_size = list(self.texture.size)


class FileChooserL(FileChooserListView):
    """
    Modification of the FileChooserListView widget that fixes an issue of path
    update when clicking in the parent directory
    """

    def __init__(self, **kwargs):
        super(FileChooserL, self).__init__(**kwargs)

    def open_entry(self, entry):
        """
        Modification of the open entry method so that when the entry.path is
        "../", the path is updated to the parent directory, instead of
        appending the entry.path
        """
        try:
            # Just check if we can list the directory. This is also what
            # _add_file does, so if it fails here, it would also fail later
            # on. Do the check here to prevent setting path to an invalid
            # directory that we cannot list.
            self.file_system.listdir(entry.path)
        except OSError:
            entry.locked = True
        else:
            # If entry.path is to jump to previous directory, update path with
            # parent directory
            if entry.path == "../" or entry.path == "..\\":
                self.path = abspath(join(self.path, pardir))
                self.selection = []
            else:
                self.path = join(self.path, entry.path)
                self.selection = []


class FileChooserM(FileChooserIconView):
    """
    Modification of the FileChooserIconView widget that fixes n issue of path
    update when clicking in the parent directory and provides support for
    multiple file selection using Shift+Click. To achieve this, a few methods
    were added that listen to keyboard input in order to capture when the
    shift key is being pressed. These methods change the new shift attribute of
    the class, which is used when an entry is touched.

    The current Shift+Click implementation supports forward and backward
    selection from the last entry touched.
    """

    shift = False

    def __init__(self, **kwargs):
        super(FileChooserM, self).__init__(**kwargs)
        # Register new event that is triggered when entering a directory
        self.register_event_type("on_dir_entry")
        Window.bind(on_key_down=self.keyboard_listen)
        Window.bind(on_key_up=self.release_shift)

    def on_dir_entry(self):
        """
        Event triggered when entering a directory
        """
        pass

    def keyboard_listen(self, *vals):
        """
        Listens to keyboard when a key is pressed. It is used to set the shift
        attribute to True when Shift is being pressed
        :param vals: keyboard input
        """

        key_code = vals[1]

        if key_code == 304:
            self.shift = True

    def release_shift(self, *vals):
        """
        Listens to keyboard when a key is released. It is used to set the
        shift attribute to False when the Shift key is released.
        :param vals:
        :return:
        """

        key_code = vals[1]

        if key_code == 304:
            self.shift = False

    def open_entry(self, entry):
        """
        Modification of the open entry method so that when the entry.path is
        "../", the path is updated to the parent directory, instead of
        appending the entry.path
        """
        self.dispatch("on_dir_entry")
        try:
            # Just check if we can list the directory. This is also what
            # _add_file does, so if it fails here, it would also fail later
            # on. Do the check here to prevent setting path to an invalid
            # directory that we cannot list.
            self.file_system.listdir(entry.path)
        except OSError:
            entry.locked = True
        else:
            # If entry.path is to jump to previous directory, update path with
            # parent directory
            if entry.path == "../" or entry.path == "..\\":
                self.path = abspath(join(self.path, pardir))
                self.selection = []
            else:
                self.path = join(self.path, entry.path)
                self.selection = []

    def entry_touched(self, entry, touch):
        """
        (internal) This method must be called by the template when an entry
        is touched by the user. Supports Shift+Clicking for multiple selection
        """
        if (
            'button' in touch.profile and touch.button in (
                'scrollup', 'scrolldown', 'scrollleft', 'scrollright')):
            return False

        _dir = self.file_system.is_dir(entry.path)
        dirselect = self.dirselect

        if _dir and dirselect and touch.is_double_tap:
            self.open_entry(entry)
            return

        if self.shift and self.selection:
            # Get index of last selection entry and current entry
            idx_selection = self.files.index(self.selection[-1])
            idx_current = self.files.index(entry.path)

            # If current entry is ahead of last selection, select files
            # going forward
            if idx_selection < idx_current:
                idx_s = idx_selection
                idx_f = idx_current
            else:
                idx_s = idx_current
                idx_f = idx_selection

        if self.multiselect:
            if entry.path in self.selection:
                # This will deselect multiple files when the shift key is down
                # while clicking
                if self.shift and self.selection:
                    for i in range(idx_s + 1, idx_f + 1):
                        f = self.files[i]
                        if f in self.selection:
                            self.selection.remove(f)
                else:
                    self.selection.remove(entry.path)
            else:
                if _dir and not self.dirselect:
                    self.open_entry(entry)
                    return
                # This will select multiple files when the shift key is down
                # while clicking
                if self.shift and self.selection:
                    for i in range(idx_s, idx_f + 1):
                        f = self.files[i]
                        if f not in self.selection:
                            self.selection.append(f)
                else:
                    self.selection.append(entry.path)
        else:
            if _dir and not self.dirselect:
                self.open_entry(entry)
                return
            self.selection = [entry.path, ]


class CustomPopup(Popup):
    """
    Modification of Popup class with a few additional feature.

    .: The title does not wrap, but instead is shortened
    .: A custom background may be provided using the custom_background attribute
    """

    def __init__(self, **kwargs):
        super(CustomPopup, self).__init__(**kwargs)
        label = self.children[0].children[-1]
        label.shorten = True
        label.shorten_from = "right"
        label.markup = True

        # New attributes
        try:
            self.custom_background = kwargs["custom_background"]
        except KeyError:
            self.custom_background = None

        # Set custom background
        if self.custom_background:
            gl = self.children[0]
            with gl.canvas.before:
                Color(.7, .7, .7, 1)
                self.rect = Rectangle(
                    source=self.custom_background,
                    pos=self.pos,
                    size=self.size)

                # This will update the background position when the popup is
                # set to the final position
                self.bind(size=self._update_rect, pos=self._update_rect)

    def _update_rect(self, instance, value):
        self.rect.pos = instance.pos
        self.rect.size = instance.size


class AutoCompTextInput(TextInput):
    """
    Modified widget of text input in which the tab key does not introduce a
    tabular space. This is meant to use with _auto_completion, in which the
    tab key serves as a keybinding
    """

    def insert_text(self, substring, from_undo=False):
        if substring == "\t":
            s = ""
        else:
            s = substring
        return super(AutoCompTextInput, self).insert_text(s,
                                                          from_undo=from_undo)


class SP_MoreOpts_Dialog(BoxLayout):
    def __init__(self, **kwargs):
        super(SP_MoreOpts_Dialog, self).__init__(**kwargs)

        self.ds_type = kwargs["ds_type"]


class PartitionsDialog(BoxLayout):
    """
    Custom layout for partition box when editing partitions
    """
    pass


class ModelSpinner(Spinner):
    """
    Custom Spinner that takes a background_normal argument to set the
    background
    """

    def __init__(self, **kwargs):
        super(ModelSpinner, self).__init__(**kwargs)

        try:
            self.background_normal = kwargs["background_normal"]
        except KeyError:
            pass


class MySlider(Slider):

    def __init__(self, **kwargs):
        super(MySlider, self).__init__(**kwargs)
        self.register_event_type("on_release")

    def on_release(self):
        pass

    def on_touch_up(self, touch):
        super(MySlider, self).on_touch_up(touch)
        if touch.grab_current == self:
            self.dispatch("on_release")
            return True


class CrunchData(BoxLayout):
    pass


class TFButton(Button):

    def __init__(self, **kwargs):
        super(TFButton, self).__init__(**kwargs)


class TFButtonOff(Button):

    def __init__(self, **kwargs):
        super(TFButtonOff, self).__init__(**kwargs)


class TGToggleButton(ToggleButton):

    def __init__(self, **kwargs):
        super(TGToggleButton, self).__init__(**kwargs)


class ExportGraphics(BoxLayout):
    cancel = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(ExportGraphics, self).__init__(**kwargs)

        kwargs["bookmark_init"](self.ids.bookmark_gl, self.ids.sv_mycomp,
                                self.ids.sd_filechooser)


class ExportGroupDialog(BoxLayout):
    cancel = ObjectProperty(None)


class InputTextDialog(BoxLayout):
    cancel = ObjectProperty(None)
    action = ObjectProperty(None)


class BackButton(Button):
    pass


class ProjectOrtoBt(Button):
    pass


class ProjectProcBt(Button):
    pass


class SelectGeneDialog(BoxLayout):
    cancel = ObjectProperty()


class StatsToggleWgt(BoxLayout):
    avg_func = ObjectProperty(None)
    sp_func = ObjectProperty(None)


class StatsPlotToolbar(BoxLayout):
    pass


class PlotTriageDialog(BoxLayout):
    cancel = ObjectProperty(None)


class OrtoPlotToolbar(BoxLayout):
    pass


class OrthologySearchGrid(TabbedPanel):
    pass


class DescriptionBox(BoxLayout):
    # Attribute for number of proteins
    prot_txt = StringProperty()
    # Attribute for number of taxa
    taxa_txt = StringProperty()
    # Attribute for total number of orthologs
    ortholog_txt = StringProperty()


class GaugePlot(BoxLayout):
    # Attribute for Gauge plot top label
    txt = StringProperty()
    # Attribute for proportion for gauge plot. This proportion should range
    # between 0 and 1. It will be automatically adapted in the gauge plot
    proportion = NumericProperty()
    # Attribute for number of orthologs
    ortholog_num = StringProperty()


class OrtoSetFiltersDialog(BoxLayout):
    cancel = ObjectProperty(None)


class OrthoReportDialog(BoxLayout):
    cancel = ObjectProperty(None)


class OrthoGraphicReport(BoxLayout):
    pass


class OrtoFilterDialog(BoxLayout):
    cancel = ObjectProperty(None)


class OrtoExecutionDialog(BoxLayout):
    cancel = ObjectProperty(None)


class OrtoProgressDialog(BoxLayout):
    pass


class ProteinFilterDialog(BoxLayout):
    cancel = ObjectProperty(None)


class MySQLDialog(BoxLayout):
    cancel = ObjectProperty(None)


class InflationDialog(BoxLayout):
    cancel = ObjectProperty(None)


class SidepanelToggle(ToggleButton):
    pass


class SequenceSimilarity(TFButtonOff):
    pass


class SegregatingSites(TFButtonOff):
    pass


class OptsGrid(GridLayout):
    pass


class SizeDistribution(TFButtonOff):
    pass


class NucAAProportions(TFButtonOff):
    pass


class GeneOccupancy(TFButtonOff):
    pass


class MissingData(TFButtonOff):
    pass


class MissingOrto(TFButtonOff):
    pass


class LoadMultipleDialog(BoxLayout):
    """
    A Filechooser widget in Icon view that allows multpiple file choosing
    """
    cancel = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(LoadMultipleDialog, self).__init__(**kwargs)

        kwargs["bookmark_init"](self.ids.bookmark_gl, self.ids.sv_mycomp,
                                self.ids.sd_filechooser)


class CloseBox(BoxLayout):
    """
    This is part of the taxa information popup. It contains the closing button
    """
    cancel = ObjectProperty(None)


class RemoveFloat(Button):
    """
    Simple (X) float button that can be associated with several root_window
    widgets for closing buttons
    """
    pass


class DataSetTriageDialog(BoxLayout):
    cancel = ObjectProperty(None)


class WarningFloat(Label):
    """
    The general purpose unintruside warning float for errors and informations.
    This dialog is added to the root_window with fade in and fade out animations
    """
    pass


class InfoPopup(BoxLayout):
    """
    Dialog for help texts that can be accessed for several options using the
    "?" button
    """
    cancel = ObjectProperty(None)


class FancyButton(Button):
    pass


class FancyMarker(Button):
    pass


class FancyMarkerPersist(Button):
    pass


class MouseOverLabel(Button):
    """
    General use mouse over label for diverse buttons
    """
    pass


class HseparatorFooter(BoxLayout):
    pass


class RevConcDialog(BoxLayout):
    """
    Reverse concatenation dialog
    """
    cancel = ObjectProperty(None)


class BtList(BoxLayout):
    cancel = ObjectProperty(None)


class InputList(BoxLayout):
    """
    Dialog with list of input files to select file for reverse concatenation
    """
    cancel = ObjectProperty(None)


class SideLabel(Label):
    """
    Mouseover label for side option buttons in the sidepanel
    """
    pass


class LoadMoreBt(AnchorLayout):
    """
    Custom button widget for for the "load more button" in the side panel
    """
    pass


class StatsMoreBt(AnchorLayout):
    pass


class PathLabel(LinkedLabel):
    """
    Dialog for the Label with the path for the main file chooser
    """
    pass


class PathText(AutoCompTextInput):
    """
    Dialog for the TextInput for the main file chooser that controls the path
     and inherits from the custom AutoCompTextInput for auto completion
    """

    def __init__(self, **kwargs):
        super(PathText, self).__init__(**kwargs)


class ExecutionDialog(BoxLayout):
    """
    The Execution dialog for Process operations
    """
    cancel = ObjectProperty(None)


class ProteomePopup(BoxLayout):
    """
    Informative popup for proteome files when clicking the "i" button in the
    side panel
    """
    cancel = ObjectProperty(None)


class LoadProgressDialog(BoxLayout):
    """
    Dialog for the progression dialog when loading files into the program
    """
    pass


class FilePopup(BoxLayout):
    """
    Class with a custom BoxLayout controlling the informative popup for the
     file buttons in the File tab of the side panel
    """
    cancel = ObjectProperty(None)


class TaxaEdit(BoxLayout):
    pass


class TaxaPopup(BoxLayout):
    """
    Class with a custom BoxLayout controlling the informative popup for the
     taxa buttons in the Taxa tab of the side panel
    """
    pass


class CheckDialog(BoxLayout):
    """
    Class controlling the layout of a general purpose dialog to check if the
    user wants of perform a certain action
    """
    cancel = ObjectProperty(None)


class WarningDialog(BoxLayout):
    """
    Class controlling the layout of a general purpose dialog to warn the user
    of certain events
    """
    cancel = ObjectProperty(None)


class PartitionActiveDialog(BoxLayout):
    cancel = ObjectProperty(None)


class LoadDialog(BoxLayout):
    """
    Class controlling a general purpose layout for loading additional files
    """
    cancel = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(LoadDialog, self).__init__(**kwargs)

        kwargs["bookmark_init"](self.ids.bookmark_gl, self.ids.sv_mycomp,
                                self.ids.ld_filechooser)


class SaveDialog(FloatLayout):
    """
    Class controlling the layout of the save file dialog in the Process screen
    """
    save = ObjectProperty(None)
    text_input = ObjectProperty(None)
    cancel = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(SaveDialog, self).__init__(**kwargs)

        kwargs["bookmark_init"](self.ids.bookmark_gl, self.ids.sv_mycomp,
                                self.ids.sd_filechooser)


class SplitPartitions(BoxLayout):
    cancel = ObjectProperty(None)


class FormatDialog(BoxLayout):
    """
    Class controlling the layout of the output format dialog in the Process
    screen
    """
    cancel = ObjectProperty(None)


class TaxaFilterDialog(BoxLayout):
    cancel = ObjectProperty(None)


class CodonFilterDialog(BoxLayout):
    cancel = ObjectProperty(None)


class FilterDialog(BoxLayout):
    """
    Class controlling the layout of the gap/missing filtering options in the
    Process screen
    """
    cancel = ObjectProperty(None)


class TextDialog(BoxLayout):
    """
    Class controlling a simple text input popup
    """
    cancel = ObjectProperty(None)


class NexusExtra(BoxLayout):
    cancel = ObjectProperty(None)


class PhylipExtra(BoxLayout):
    """
    Class controlling the dialog with extra options for phylip output format
    """
    cancel = ObjectProperty(None)


class ProcessGeneral(GridLayout):
    """
    Class controlling the layout of the general options of the Process screen
    """
    pass


class AdditionalProcessContents(TabbedPanel):
    """
    Class controlling the layout of the additional options of the Process screen
    """
    pass


class TaxaGroupDialog(BoxLayout):
    """
    Class controlling the layout of the taxa group creation dialogue in the
    side panel
    """
    cancel = ObjectProperty(None)


class ZorroDialog(BoxLayout):
    """
    Class controlling the layout of the ZORRO operation dialog
    """
    cancel = ObjectProperty(None)




__author__ = 'diogo'