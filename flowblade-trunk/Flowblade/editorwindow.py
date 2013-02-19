"""
    Flowblade Movie Editor is a nonlinear video editor.
    Copyright 2012 Janne Liljeblad.

    This file is part of Flowblade Movie Editor <http://code.google.com/p/flowblade>.

    Flowblade Movie Editor is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    Flowblade Movie Editor is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with Flowblade Movie Editor.  If not, see <http://www.gnu.org/licenses/>.
"""

"""
Module contains main editor window object.
"""
import cairo
import gtk
import pango
import pygtk

import app
import appconsts
import audiomonitoring
import batchrendering
import buttonevent
from cairoarea import CairoDrawableArea
from cairoarea import CairoEventBox
import clipeffectseditor
import compositeeditor
import dnd
import editevent
import editorpersistance
import editorstate
import exporting
import glassbuttons
import gui
import guicomponents
import guiutils
import menuactions
import mltplayer
import monitorevent
import movemodes
import respaths
import panels
import patternproducer
from positionbar import PositionBar
import syncsplitevent
import test
import titler
import tlinewidgets
import useraction
import updater
import utils
import vieweditor
import windowviewmenu

# GUI size params
"""
TOP_ROW_HEIGHT = 500 # defines app min height with tlinewidgets.HEIGHT
NOTEBOOK_WIDTH = appconsts.NOTEBOOK_WIDTH # defines app min width with MONITOR_AREA_WIDTH
NOTEBOOK_WIDTH_SMALL = appconsts.NOTEBOOK_WIDTH_SMALL
"""
MEDIA_MANAGER_WIDTH = 250

MONITOR_AREA_WIDTH = 600 # defines app min width with NOTEBOOK_WIDTH 400 for small

MODE_BUTTON_ACTIVE_COLOR = "#9d9d9d"
MODE_BUTTON_PRELIGHT_COLOR = "#bdbdbd"

BINS_HEIGHT = 250
EFFECT_STACK_VIEW_HEIGHT = 160
EFFECT_VALUE_EDITOR_HEIGHT = 200
EFFECT_SELECT_EDITOR_HEIGHT = 140

IMG_PATH = None


def _b(button, icon, remove_relief=False):
    button.set_image(icon)
    button.set_property("can-focus",  False)
    if remove_relief:
        button.set_relief(gtk.RELIEF_NONE)

def _toggle_image_switch(widget, icons):
    not_pressed, pressed = icons
    if widget.get_active() == True:
        widget.set_image(pressed)
    else:
        widget.set_image(not_pressed)


class EditorWindow:

    def __init__(self):
        global IMG_PATH
        IMG_PATH = respaths.IMAGE_PATH 

        # Window
        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.window.set_icon_from_file(respaths.IMAGE_PATH + "flowbladeappicon.png")
        self.window.set_border_width(5)

        # To ask confirmation for shutdown 
        self.window.connect("delete-event", lambda w, e:app.shutdown())

        # Player consumer has to be stopped and started when window resized
        self.window.connect("window-state-event", lambda w, e:updater.refresh_player())

        # Build menubar
        # Menubar build resources
        menu_actions = [
            ('FileMenu', None, _('_File')),
            ('New', None, _('_New...'), '<control>N', None, lambda a:useraction.new_project()),
            ('Open', None, _('_Open...'), '<control>O', None, lambda a:useraction.load_project()),
            ('OpenRecent', None, _('Open Recent')),
            ('Save', None, _('_Save'), '<control>S', None, lambda a:useraction.save_project()),
            ('Save As', None, _('_Save As...'), None, None, lambda a:useraction.save_project_as()),
            ('ExportMenu', None, _('Export')),
            ('ExportMeltXML', None, _('Export melt XML'), None, None, lambda a:exporting.MELT_XML_export()),
            ('ExportDvdAuthorXML', None, _('Export DVDAuthor files'), None, None, lambda a:exporting.DVD_AUTHOR_export()),
            ('Close', None, _('_Close'), None, None, lambda a:useraction.close_project()),
            ('Quit', None, _('_Quit'), '<control>Q', None, lambda a:app.shutdown()),
            ('EditMenu', None, _('_Edit')),
            ('Undo', None, _('_Undo'), '<control>Z', None, editevent.do_undo),
            ('Redo', None, _('_Redo'), '<control>Y', None, editevent.do_redo),
            ('ClearFilters', None, _('Clear Filters From Selected'), None, None, lambda a:editevent.clear_filters()),
            ('ConsolidateSelectedBlanks', None, _('Consolidate Selected Blanks'), None, None, lambda a:editevent.consolidate_selected_blanks()),
            ('ConsolidateAllBlanks', None, _('Consolidate All Blanks'), None, None, lambda a:editevent.consolidate_all_blanks()),
            ('ChangeSequenceTracks', None, _('Change Sequence Tracks Count...'), None, None, lambda a:useraction.change_sequence_track_count()),
            ('ProfilesManager', None, _('Profiles Manager'), None, None, lambda a:menuactions.profiles_manager()),
            ('Preferences', None, _('Preferences'), None, None, lambda a:menuactions.display_preferences()),
            ('ViewMenu', None, _('View')),
            ('Layout', None, _('Add Media Clip...'), None, None, lambda a: useraction.add_media_files()),
            ('ProjectMenu', None, _('Project')),
            ('AddMediaClip', None, _('Add Media Clip...'), None, None, lambda a: useraction.add_media_files()),
            ('AddImageSequence', None, _('Add Image Sequence...'), None, None, lambda a:useraction.add_image_sequence()),
            ('CreateColorClip', None, _('Create Color Clip...'), None, None, lambda a:patternproducer.create_color_clip()),
            ('PatternProducersMenu', None, _('Create Pattern Producer')),
            ('CreateNoiseClip', None, _('Noise'), None, None, lambda a:patternproducer.create_noise_clip()),
            ('CreateBarsClip', None, _('EBU Bars'), None, None, lambda a:patternproducer.create_bars_clip()),
            ('RecreateMediaIcons', None, _('Recreate Media Icons...'), None, None, lambda a:menuactions.recreate_media_file_icons()),
            ('ToolsMenu', None, _('Tools')),
            ('Titler', None, _('Titler'), None, None, lambda a:titler.show_titler()),
            ('AudioMix', None, _('Audio Mixer'), None, None, lambda a:audiomonitoring.show_audio_monitor()),
            ('RenderQueue', None, _('Render Queue'), None, None, lambda a:batchrendering.lauch_batch_rendering()),
            ('HelpMenu', None, _('_Help')),
            ('QuickReference', None, _('Contents'), None, None, lambda a:menuactions.quick_reference()),
            ('Environment', None, _('Environment'), None, None, lambda a:menuactions.environment()),
            ('About', None, _('About'), None, None, lambda a:menuactions.about())
            ]

        menu_string = """<ui>
            <menubar name='MenuBar'>
                <menu action='FileMenu'>
                    <menuitem action='New'/>
                    <menuitem action='Open'/>
                    <menu action='OpenRecent'/>
                    <menuitem action='Save'/>
                    <menuitem action='Save As'/>
                    <separator/>
                    <menu action='ExportMenu'>
                        <menuitem action='ExportMeltXML'/>
                        <menuitem action='ExportDvdAuthorXML'/>
                    </menu>
                    <separator/>
                    <menuitem action='Close'/>
                    <menuitem action='Quit'/>
                </menu>
                <menu action='EditMenu'>
                    <menuitem action='Undo'/>
                    <menuitem action='Redo'/>
                    <separator/>
                    <menuitem action='ClearFilters'/>     
                    <separator/>
                    <menuitem action='ConsolidateSelectedBlanks'/>
                    <menuitem action='ConsolidateAllBlanks'/>
                    <separator/>
                    <menuitem action='ChangeSequenceTracks'/>
                    <separator/>
                    <menuitem action='ProfilesManager'/>
                    <menuitem action='Preferences'/>
                </menu>
                <menu action='ViewMenu'>
                </menu>
                <menu action='ProjectMenu'>
                    <menuitem action='AddMediaClip'/>
                    <menuitem action='AddImageSequence'/>
                    <separator/>
                    <menuitem action='CreateColorClip'/>
                    <menu action='PatternProducersMenu'>
                        <menuitem action='CreateNoiseClip'/>
                        <menuitem action='CreateBarsClip'/>    
                    </menu>
                    <separator/>
                    <menuitem action='RecreateMediaIcons'/>
                </menu>
                <menu action='ToolsMenu'>
                    <menuitem action='Titler'/>
                    <menuitem action='AudioMix'/>
                </menu>
                <menu action='HelpMenu'>
                    <menuitem action='QuickReference'/>
                    <menuitem action='Environment'/>
                    <separator/>
                    <menuitem action='About'/>
                </menu>
          </menubar>
        </ui>"""
                    
        action_group = gtk.ActionGroup('WindowActions')
        action_group.add_actions(menu_actions, user_data=None)
        ui = gtk.UIManager()
        ui.insert_action_group(action_group, 0)
        ui.add_ui_from_string(menu_string)
        accel_group = ui.get_accel_group()
        self.window.add_accel_group(accel_group)
        self.menubar = ui.get_widget('/MenuBar')
        self.uimanager = ui

        # Add recent projects to menu
        editorpersistance.fill_recents_menu_widget(ui.get_widget('/MenuBar/FileMenu/OpenRecent'), useraction.open_recent_project)

        windowviewmenu.init_view_menu(ui.get_widget('/MenuBar/ViewMenu'))

        # Menu box
        menu_vbox = gtk.VBox(False, 0)
        menu_vbox.pack_start(self.menubar, False, True, 0)

        # Media manager
        self.bin_list_view = guicomponents.BinListView(
                                        useraction.bin_selection_changed, 
                                        useraction.bin_name_edited)
        dnd.connect_bin_tree_view(self.bin_list_view.treeview, useraction.move_files_to_bin)
        self.bin_list_view.set_property("can-focus",  True)
        bins_panel = panels.get_bins_panel(self.bin_list_view,
                                           lambda w,e: useraction.add_new_bin(),
                                           lambda w,e: useraction.delete_selected_bin())
        bins_panel.set_size_request(MEDIA_MANAGER_WIDTH, BINS_HEIGHT)


        self.media_list_view = guicomponents.MediaPanel(useraction.media_file_menu_item_selected,
                                                        updater.set_and_display_monitor_media_file)
        media_scroll_window = gtk.ScrolledWindow()
        media_scroll_window.add_with_viewport(self.media_list_view.widget)
        media_scroll_window.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        media_scroll_window.set_size_request(guicomponents.MEDIA_OBJECT_WIDGET_WIDTH * self.media_list_view.columns + 70, guicomponents.MEDIA_OBJECT_WIDGET_HEIGHT)
        media_scroll_window.show_all()

        media_panel = panels.get_media_files_panel(
                                media_scroll_window,
                                #self.media_list_view,
                                lambda w,e: useraction.add_media_files(), 
                                lambda w,e: useraction.delete_media_files(),
                                lambda a: self.media_list_view.columns_changed(a))

    
        mm_paned = gtk.HPaned()
        mm_paned.pack1(bins_panel, resize=True, shrink=True)
        mm_paned.pack2(media_panel, resize=True, shrink=False)
        
        mm_panel = gtk.Alignment(0.5, 0.5, 1.0, 1.0)
        mm_panel.set_padding(0, 0, 4, 0)
        mm_panel.add(mm_paned)

        # Effects
        self.effect_select_list_view = guicomponents.FilterListView()
        self.effect_select_combo_box = gtk.combo_box_new_text()
        self.effect_select_list_view.treeview.connect("row-activated", clipeffectseditor.effect_select_row_double_clicked)
        dnd.connect_effects_select_tree_view(self.effect_select_list_view.treeview)

        clip_editor_panel = panels.get_clip_effects_editor_panel(
                                    self.effect_select_combo_box,
                                    self.effect_select_list_view)

        clipeffectseditor.widgets.effect_stack_view.treeview.connect("button-press-event",
                                              clipeffectseditor.filter_stack_button_press)
                                              
        effects_editor_panel = gtk.Alignment(0.5, 0.5, 1.0, 1.0)
        effects_editor_panel.set_padding(0, 0, 4, 0)
        effects_editor_panel.add(clipeffectseditor.widgets.value_edit_frame)
        
        effects_hbox = gtk.HBox()
        effects_hbox.set_border_width(5)
        effects_hbox.pack_start(clip_editor_panel, False, False, 0)
        effects_hbox.pack_start(effects_editor_panel, True, True, 0)

        self.effects_panel = gtk.Alignment(0.5, 0.5, 1.0, 1.0)
        self.effects_panel.set_padding(0, 0, 0, 0)
        self.effects_panel.add(effects_hbox)
        
        # Compositors
        compositor_clip_panel = panels.get_compositor_clip_panel()

        compositor_editor_panel = gtk.Alignment(0.5, 0.5, 1.0, 1.0)
        compositor_editor_panel.set_padding(0, 0, 4, 0)
        compositor_editor_panel.add(compositeeditor.widgets.value_edit_frame)

        compositors_hbox = gtk.HBox()
        compositors_hbox.set_border_width(5)
        compositors_hbox.pack_start(compositor_clip_panel, False, False, 0)
        compositors_hbox.pack_start(compositor_editor_panel, True, True, 0)

        self.compositors_panel = gtk.Alignment(0.5, 0.5, 1.0, 1.0)
        self.compositors_panel.set_padding(0, 0, 0, 0)
        self.compositors_panel.add(compositors_hbox)

        # Project buttons
        self.open_project_b = gtk.Button(_("Open"))
        self.new_project_b = gtk.Button(_("New"))
    
        self.open_project_b.connect("clicked", lambda e: useraction.load_project())
        self.new_project_b.connect("clicked", lambda e: useraction.new_project())

        project_buttons_box = gtk.HBox(True,1)
        project_buttons_box.pack_start(self.open_project_b)
        project_buttons_box.pack_start(self.new_project_b)

        # Project
        name_panel = panels.get_project_name_panel(editorstate.project.name)

        profile_info = panels.get_profile_info_panel(editorstate.project.profile)
        
        self.project_info_vbox = gtk.VBox()
        self.project_info_vbox.pack_start(name_panel, False, True, 0)
        self.project_info_vbox.pack_start(profile_info, False, True, 0)
        
        # Sequence list
        self.sequence_list_view = guicomponents.SequenceListView(
                                        useraction.sequence_name_edited)
        seq_panel = panels.get_sequences_panel(
                             self.sequence_list_view,
                             lambda w,e: useraction.change_edit_sequence(),
                             lambda w,e: useraction.add_new_sequence(), 
                             lambda w,e: useraction.delete_selected_sequence())

        # Project vbox and panel
        project_vbox = gtk.VBox()
        project_vbox.pack_start(project_buttons_box, False, True, 0)
        project_vbox.pack_start(self.project_info_vbox, False, True, 0)
        project_vbox.pack_start(seq_panel, True, True, 0)
    
        project_panel = gtk.Alignment(0.5, 0.5, 1.0, 1.0)
        project_panel.set_padding(6, 0, 6, 6)
        project_panel.add(project_vbox)

        # Render
        normal_height = True
        if appconsts.TOP_ROW_HEIGHT < 500: # small screens have no space to display this
            normal_height = False

        add_audio_desc = True
        if editorstate.SCREEN_HEIGHT < 863:
            add_audio_desc = False
        render_panel_left = panels.get_render_panel_left(
                                self,
                                add_audio_desc)

        # 'None' here means that no possible rendering options were available
        # and creating panel failed. Inform user of this and hide render GUI 
        if render_panel_left == None:
            render_hbox = gtk.VBox(False, 5)
            render_hbox.pack_start(gtk.Label("Rendering disabled."), False, False, 0)
            render_hbox.pack_start(gtk.Label("No available rendering options found."), False, False, 0)
            render_hbox.pack_start(gtk.Label("See Help->Environment->Render Options for details."), False, False, 0)
            render_hbox.pack_start(gtk.Label("Install codecs to make rendering available."), False, False, 0)
            render_hbox.pack_start(gtk.Label(" "), True, True, 0)
        else: # all is good
            render_panel_right = panels.get_render_panel_right(lambda w,e: useraction.do_rendering(), normal_height)

            render_hbox = gtk.HBox(True, 5)
            render_hbox.pack_start(render_panel_left, True, True, 0)
            render_hbox.pack_start(render_panel_right, True, True, 0)

        render_panel = gtk.Alignment(0.5, 0.5, 1.0, 1.0)
        render_panel.set_padding(2, 6, 8, 6)
        render_panel.add(render_hbox)

        # Notebook
        self.notebook = gtk.Notebook()
        self.notebook.set_size_request(appconsts.NOTEBOOK_WIDTH, appconsts.TOP_ROW_HEIGHT)
        self.notebook.append_page(mm_panel, gtk.Label(_("Media")))
        self.notebook.append_page(self.effects_panel, gtk.Label(_("Filters")))
        self.notebook.append_page(self.compositors_panel, gtk.Label(_("Compositors")))
        self.notebook.append_page(project_panel, gtk.Label(_("Project")))
        self.notebook.append_page(render_panel, gtk.Label(_("Render")))
        self.notebook.set_tab_pos(gtk.POS_BOTTOM)

        # Right notebook, used for Widescreen and Two row layouts
        self.right_notebook = gtk.Notebook()
        self.right_notebook.set_tab_pos(gtk.POS_BOTTOM)

        # Timecode panel
        tc_panel = panels.get_timecode_panel(self)
   
        # Video display
        self.tline_display = gtk.DrawingArea() 
        dnd.connect_video_monitor(self.tline_display)
        
        # Position bar and decorative frame  for it
        self.pos_bar = PositionBar()
        pos_bar_frame = gtk.Frame()
        pos_bar_frame.add(self.pos_bar.widget)
        pos_bar_frame.set_shadow_type(gtk.SHADOW_ETCHED_IN)
        
        # Positionbar vbox
        pos_bar_vbox = gtk.VBox(False, 1)
        pos_bar_vbox.pack_start(guiutils.get_pad_label(5, 2), False, True, 0)
        pos_bar_vbox.pack_start(pos_bar_frame, False, True, 0)

        #player_buttons = self._get_player_buttons()
        self.player_buttons = glassbuttons.PlayerButtons()
        #playback_buttons = self.player_buttons.widget

        # Creates monitor switch buttons
        self._create_monitor_buttons()

        # Switch button box
        switch_hbox = gtk.HBox(True, 1)
        switch_hbox.pack_start(self.sequence_editor_b, False, False, 0)
        switch_hbox.pack_start(self.clip_editor_b, False, False, 0)

        # Switch button box V, for centered buttons
        switch_vbox = gtk.VBox(False, 1)
        switch_vbox.pack_start(guiutils.get_pad_label(5, 2), False, True, 0)
        switch_vbox.pack_start(switch_hbox, False, True, 0)

        # Switch / pos bar row
        self.view_mode_select = guicomponents.get_monitor_view_select_combo(lambda w, e: buttonevent.view_mode_menu_lauched(w, e))
        sw_pos_hbox = gtk.HBox(False, 1)
        sw_pos_hbox.pack_start(switch_vbox, False, True, 0)
        sw_pos_hbox.pack_start(pos_bar_vbox, True, True, 0)
        sw_pos_hbox.pack_start(self.view_mode_select.widget, False, False, 0)
        
        # Monitor
        monitor_vbox = gtk.VBox(False, 1)
        #monitor_vbox.pack_start(tc_panel, False, True, 0)
        monitor_vbox.pack_start(self.tline_display, True, True, 0)
        monitor_vbox.pack_start(sw_pos_hbox, False, True, 0)
        monitor_vbox.pack_start(self.player_buttons.widget, False, True, 0)
        
        monitor_align = gtk.Alignment(xalign=0.0, yalign=0.0, xscale=1.0, yscale=1.0) 
        monitor_align.add(monitor_vbox)
        monitor_align.set_padding(3, 0, 3, 3)
        
        monitor_frame = gtk.Frame()
        monitor_frame.add(monitor_align)
        monitor_frame.set_shadow_type(gtk.SHADOW_ETCHED_OUT)
        monitor_frame.set_size_request(MONITOR_AREA_WIDTH, appconsts.TOP_ROW_HEIGHT)

        # Notebook panel
        notebook_vbox = gtk.VBox(False, 1)
        notebook_vbox.pack_start(self.notebook, True, True)

        # Top row paned
        top_paned = gtk.HPaned()
        top_paned.pack1(notebook_vbox, resize=True, shrink=False)
        top_paned.pack2(monitor_frame, resize=False, shrink=False)

        # top row
        self.top_row_hbox = gtk.HBox(False, 0)
        self.top_row_hbox.pack_start(top_paned, True, True, 0)

        # Edit buttons rows
        self.edit_buttons_row = self._get_edit_buttons_row()
        self.edit_buttons_frame = gtk.Frame()
        self.edit_buttons_frame.add(self.edit_buttons_row)
        self.edit_buttons_frame.set_shadow_type(gtk.SHADOW_ETCHED_IN)
        # gtk.SHADOW_IN, gtk.SHADOW_OUT, gtk.SHADOW_ETCHED_IN, gtk.SHADOW_ETCHED_OUT
        #self.edit_buttons_event_box.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse(appconsts.MIDBAR_COLOR))
                
        # Timeline scale
        self.tline_scale = tlinewidgets.TimeLineFrameScale(editevent.insert_move_mode_pressed,  
                                                           updater.mouse_scroll_zoom)

        # Timecode display
        self.tline_info = gtk.HBox()
        info_contents = gtk.Label()
        self.tline_info.add(info_contents)
        self.tline_info.info_contents = info_contents # this switched and sacved as member of its container
        info_h = gtk.HBox()
        info_h.pack_start(self.tline_info, False, False, 0)
        info_h.pack_start(gtk.Label(), True, True, 0)
        info_h.set_size_request(tlinewidgets.COLUMN_WIDTH  - 22 - 22,# - 22, # room for 2 menu launch buttons 
                                      tlinewidgets.SCALE_HEIGHT)

        marker_pixbuf = gtk.gdk.pixbuf_new_from_file(respaths.IMAGE_PATH + "marker.png")
        markers_launcher = guicomponents.get_markers_menu_launcher(editevent.marker_menu_lauch_pressed, marker_pixbuf)
        tracks_launcher_pixbuf = gtk.gdk.pixbuf_new_from_file(respaths.IMAGE_PATH + "track_menu_launch.png")
        tracks_launcher = guicomponents.PressLaunch(editevent.all_tracks_menu_launch_pressed, tracks_launcher_pixbuf)

        # Timeline top row
        tline_hbox_1 = gtk.HBox()
        tline_hbox_1.pack_start(info_h, False, False, 0)
        tline_hbox_1.pack_start(tracks_launcher.widget, False, False, 0)
        tline_hbox_1.pack_start(markers_launcher.widget, False, False, 0)
        tline_hbox_1.pack_start(self.tline_scale.widget, True, True, 0)

        # Timeline column
        self.tline_column = tlinewidgets.TimeLineColumn(
                            editevent.track_active_switch_pressed,
                            editevent.track_mute_switch_pressed,
                            editevent.track_center_pressed)

        # Timeline editpanel
        self.tline_canvas = tlinewidgets.TimeLineCanvas(
            editevent.tline_canvas_mouse_pressed,
            editevent.tline_canvas_mouse_moved,
            editevent.tline_canvas_mouse_released,
            editevent.tline_canvas_double_click,
            updater.mouse_scroll_zoom)
            
        dnd.connect_tline(self.tline_canvas.widget, editevent.tline_effect_drop,  
                          editevent.tline_media_drop)

        # Timeline middle row
        tline_hbox_2 = gtk.HBox()
        tline_hbox_2.pack_start(self.tline_column.widget, False, False, 0)
        tline_hbox_2.pack_start(self.tline_canvas.widget, True, True, 0)
        
        # Bottom row filler
        left_corner = gtk.Label()
        left_corner.set_size_request(tlinewidgets.COLUMN_WIDTH, 20)
        # Timeline scroller
        self.tline_scroller = tlinewidgets.TimeLineScroller(updater.tline_scrolled)
        
        # Timeline bottom row
        tline_hbox_3 = gtk.HBox()
        tline_hbox_3.pack_start(left_corner, False, False, 0)
        tline_hbox_3.pack_start(self.tline_scroller, True, True, 0)
        
        # Timeline hbox 
        tline_vbox = gtk.VBox()
        tline_vbox.pack_start(tline_hbox_1, False, False, 0)
        tline_vbox.pack_start(tline_hbox_2, True, True, 0)
        tline_vbox.pack_start(tline_hbox_3, False, False, 0)
        
        # Timeline box 
        self.tline_box = gtk.HBox()
        self.tline_box.pack_start(tline_vbox, True, True, 0)

        # Timeline pane
        tline_pane = gtk.VBox(False, 1)
        tline_pane.pack_start(self.edit_buttons_frame, False, True, 0)
        #tline_pane.pack_start(guiutils.get_pad_label(5, 4), False, True, 0)
        tline_pane.pack_start(self.tline_box, True, True, 0)

        # VPaned top row / timeline
        app_v_paned = gtk.VPaned()
        app_v_paned.pack1(self.top_row_hbox, resize=False, shrink=False)
        app_v_paned.pack2(tline_pane, resize=True, shrink=False)

        # Pane
        pane = gtk.VBox(False, 1)
        pane.pack_start(menu_vbox, False, True, 0)
        pane.pack_start(app_v_paned, True, True, 0)
        
        # Tooltips
        self._add_tool_tips()

        windowviewmenu.init_gui_to_prefs(self)

        # Set pane and show window
        self.window.add(pane)
        self.window.set_title("Flowblade")
        self.window.set_position(gtk.WIN_POS_CENTER)  
        self.window.show_all()
        
        # Maximize if it seems that we exited maximized
        w, h = editorpersistance.prefs.exit_allocation
        if (float(w) / editorstate.SCREEN_WIDTH > 0.95) and (float(h) / editorstate.SCREEN_HEIGHT > 0.95):
            self.window.maximize() 

    def _create_monitor_buttons(self):
        # Monitor switch buttons
        self.sequence_editor_b = gtk.RadioButton(None, _("Timeline"))
        self.sequence_editor_b.set_mode(False)
        self.sequence_editor_b.connect("clicked", 
                        lambda w,e: self._monitor_switch_handler(w), 
                        None)
        self.sequence_editor_b.set_size_request(100, 25)

        self.clip_editor_b = gtk.RadioButton(self.sequence_editor_b,_("Clip"))
        self.clip_editor_b.set_mode(False)
        self.clip_editor_b.connect("clicked",
                        lambda w,e: self._monitor_switch_handler(w),
                        None)
        self.clip_editor_b.set_size_request(100, 25)
    
    def _monitor_switch_handler(self, widget):
        # We get two "clicked" events per toggle, send through only the one
        # from activated button
        if ((self.sequence_editor_b.get_active() == True) 
            and (widget == self.sequence_editor_b)):
            updater.display_sequence_in_monitor() 

        if ((self.clip_editor_b.get_active() == True) 
            and (widget == self.clip_editor_b)):
            updater.display_clip_in_monitor()
    
    def _get_player_buttons(self):
        pass
        """
        # Icons
        rew_icon = gtk.image_new_from_file(IMG_PATH + "backward_s.png")
        ff_icon = gtk.image_new_from_file(IMG_PATH + "forward_s.png")
        play_icon = gtk.image_new_from_file(IMG_PATH + "play_2_s.png")
        stop_icon = gtk.image_new_from_file(IMG_PATH + "stop_s.png")
        next_icon = gtk.image_new_from_file(IMG_PATH + "next_frame_s.png")
        prev_icon = gtk.image_new_from_file(IMG_PATH + "prev_frame_s.png")
        mark_in_icon = gtk.image_new_from_file(IMG_PATH + "mark_in_s.png")
        mark_out_icon = gtk.image_new_from_file(IMG_PATH + "mark_out_s.png")
        marks_clear_icon = gtk.image_new_from_file(IMG_PATH + "marks_clear_s.png") 
        to_mark_in_icon = gtk.image_new_from_file(IMG_PATH + "to_mark_in_s.png")        
        to_mark_out_icon = gtk.image_new_from_file(IMG_PATH + "to_mark_out_s.png") 
        
        # Create buttons
        self.rew_b = gtk.Button()
        self.rew_b.set_relief(gtk.RELIEF_NONE)
        _b(self.rew_b, rew_icon)

        self.ff_b = gtk.Button()
        self.ff_b.set_relief(gtk.RELIEF_NONE)
        _b(self.ff_b, ff_icon)
        
        self.next_b = gtk.Button()
        self.next_b.set_relief(gtk.RELIEF_NONE)
        _b(self.next_b, next_icon)
        
        self.prev_b = gtk.Button()
        self.prev_b.set_relief(gtk.RELIEF_NONE)
        _b(self.prev_b, prev_icon)
        
        self.play_b = gtk.Button()
        self.play_b.set_relief(gtk.RELIEF_NONE)
        _b(self.play_b, play_icon)
        
        self.stop_b = gtk.Button()
        self.stop_b.set_relief(gtk.RELIEF_NONE)
        _b(self.stop_b, stop_icon)

        self.mark_in_b = gtk.Button()
        self.mark_in_b.set_relief(gtk.RELIEF_NONE)
        _b(self.mark_in_b, mark_in_icon)

        self.mark_out_b = gtk.Button()
        self.mark_out_b.set_relief(gtk.RELIEF_NONE)
        _b(self.mark_out_b, mark_out_icon)

        self.marks_clear_b = gtk.Button()
        self.marks_clear_b.set_relief(gtk.RELIEF_NONE)
        _b(self.marks_clear_b, marks_clear_icon)

        self.to_mark_in_b = gtk.Button()
        self.to_mark_in_b.set_relief(gtk.RELIEF_NONE)
        _b(self.to_mark_in_b, to_mark_in_icon)

        self.to_mark_out_b = gtk.Button()
        self.to_mark_out_b.set_relief(gtk.RELIEF_NONE)
        _b(self.to_mark_out_b, to_mark_out_icon)

        # Button groups
        rewind_group = gtk.HBox(True, 1)
        rewind_group.set_size_request(50, 23)
        one_frame_group = gtk.HBox(True, 1)
        one_frame_group.set_size_request(50, 23)
        play_group = gtk.HBox(True, 1)
        play_group.set_size_request(30, 23)
        in_out_group = gtk.HBox(True, 1)
        in_out_group.set_size_request(50, 23)
        to_marks_group = gtk.HBox(True, 1)
        to_marks_group.set_size_request(50, 23)

        # Create and return buttons panel
        player_buttons = gtk.HBox(False, 1)
        player_buttons.pack_start(guiutils.get_pad_label(65, 23), False, True, 0)
        player_buttons.pack_start(gtk.Label(), True, True, 0)
        rewind_group.pack_start(self.rew_b, False, True, 0)
        rewind_group.pack_start(self.ff_b, False, True, 0)
        player_buttons.pack_start(rewind_group, False, True, 0)
        player_buttons.pack_start(gtk.Label(), True, True, 0)
        one_frame_group.pack_start(self.prev_b, False, True, 0)
        one_frame_group.pack_start(self.next_b, False, True, 0)
        player_buttons.pack_start(one_frame_group, False, True, 0)
        player_buttons.pack_start(gtk.Label(), True, True, 0)
        play_group.pack_start(self.play_b, False, True, 0)
        play_group.pack_start(self.stop_b, False, True, 0)
        player_buttons.pack_start(play_group, False, True, 0)
        player_buttons.pack_start(gtk.Label(), True, True, 0)
        in_out_group.pack_start(self.mark_in_b, False, True, 0)
        in_out_group.pack_start(self.mark_out_b, False, True, 0)
        player_buttons.pack_start(in_out_group, False, True, 0)
        player_buttons.pack_start(gtk.Label(), True, True, 0)
        to_marks_group.pack_start(self.to_mark_in_b, False, True, 0)
        to_marks_group.pack_start(self.to_mark_out_b, False, True, 0)
        player_buttons.pack_start(to_marks_group, False, True, 0)
        player_buttons.pack_start(gtk.Label(), True, True, 0)
        player_buttons.pack_start(self.marks_clear_b, False, True, 0)
        player_buttons.pack_start(gtk.Label(), True, True, 0)
        #player_buttons.pack_start(self.view_mode_select,  False, True, 0)
        player_buttons.pack_start(guiutils.get_pad_label(65, 23), False, True, 0)

        return player_buttons
        """
    
    def connect_player(self, mltplayer):
        # Buttons
        """
        self.play_b.connect("clicked", lambda w,e: monitorevent.play_pressed(), None)
        self.stop_b.connect("clicked", lambda w,e: monitorevent.stop_pressed(), None)
        self.prev_b.connect("clicked", lambda w,e: monitorevent.prev_pressed(), None)
        self.next_b.connect("clicked", lambda w,e: monitorevent.next_pressed(), None)

        self.ff_b.connect("pressed", lambda w,e: monitorevent.ff_pressed(), None)
        self.ff_b.connect("released", lambda w,e: monitorevent.ff_released(), None)
        self.rew_b.connect("pressed", lambda w,e: monitorevent.rew_pressed(), None)
        self.rew_b.connect("released", lambda w,e: monitorevent.rew_released(), None)

        self.mark_in_b.connect("clicked", lambda w,e: monitorevent.mark_in_pressed(), None)
        self.mark_out_b.connect("clicked", lambda w,e: monitorevent.mark_out_pressed(), None)
        self.marks_clear_b.connect("clicked", lambda w,e: monitorevent.marks_clear_pressed(), None)
        self.to_mark_in_b.connect("clicked", lambda w,e: monitorevent.to_mark_in_pressed(), None)
        self.to_mark_out_b.connect("clicked", lambda w,e: monitorevent.to_mark_out_pressed(), None)
        """
        # NOTE: ORDER OF CALLBACKS IS THE SAME AS ORDER OF BUTTONS FROM LEFT TO RIGHT
        pressed_callback_funcs = [monitorevent.rew_pressed,
                                  monitorevent.ff_pressed,
                                  monitorevent.prev_pressed,
                                  monitorevent.next_pressed,
                                  monitorevent.play_pressed,
                                  monitorevent.stop_pressed,
                                  monitorevent.mark_in_pressed,
                                  monitorevent.mark_out_pressed,
                                  monitorevent.marks_clear_pressed,
                                  monitorevent.to_mark_in_pressed,
                                  monitorevent.to_mark_out_pressed]
        released_callback_funcs = [monitorevent.rew_released,
                                   monitorevent.ff_released]
        self.player_buttons.set_callbacks(pressed_callback_funcs, released_callback_funcs)
        #self.view_mode_select.connect("changed", lambda w, e: buttonevent.view_mode_changed(w), None)

        # Monitor position bar
        self.pos_bar.set_listener(mltplayer.seek_position_normalized)

    def _get_edit_buttons_row(self):
        windowviewmenu.create_edit_buttons_row_buttons(self)
    
        buttons_row = gtk.HBox(False, 1)
        if editorpersistance.prefs.midbar_tc_left == True:
            windowviewmenu.fill_with_TC_LEFT_pattern(buttons_row, self)
        else:
            windowviewmenu.fill_with_TC_MIDDLE_pattern(buttons_row, self)

        return buttons_row

    def _set_mode_button_colors(self, mode_button):
        mode_button.modify_bg(gtk.STATE_ACTIVE, gtk.gdk.color_parse(MODE_BUTTON_ACTIVE_COLOR))
        mode_button.modify_bg(gtk.STATE_PRELIGHT, gtk.gdk.color_parse(MODE_BUTTON_PRELIGHT_COLOR))

    """
    def _get_middle_buttons_row(self):
        show_media_icon = gtk.image_new_from_file(IMG_PATH + "show_media.png") 
        show_filters_icon = gtk.image_new_from_file(IMG_PATH + "show_filters.png") 
        show_compositors_icon = gtk.image_new_from_file(IMG_PATH + "show_compositors.png")
        show_sequences_icon = gtk.image_new_from_file(IMG_PATH + "show_sequences.png")
        show_render_icon = gtk.image_new_from_file(IMG_PATH + "show_render.png") 
        open_mixer_icon = gtk.image_new_from_file(IMG_PATH + "open_mixer.png") 
        open_titler_icon = gtk.image_new_from_file(IMG_PATH + "open_titler.png") 
        #save_icon = gtk.image_new_from_stock(gtk.STOCK_SAVE, gtk.ICON_SIZE_MENU)
        #load_icon = gtk.image_new_from_stock(gtk.STOCK_OPEN, gtk.ICON_SIZE_MENU)
        #quit_icon = gtk.image_new_from_stock(gtk.STOCK_QUIT, gtk.ICON_SIZE_MENU)
        #new_icon = gtk.image_new_from_stock(gtk.STOCK_NEW, gtk.ICON_SIZE_MENU)

        # Create buttons
        self.show_media_panel_b = gtk.RadioButton()
        self.show_media_panel_b.set_mode(False)
        _b(self.show_media_panel_b, show_media_icon)
        self._set_mode_button_colors(self.show_media_panel_b)
        
        self.show_filters_panel_b = gtk.RadioButton(self.show_media_panel_b)
        self.show_filters_panel_b.set_mode(False)
        _b(self.show_filters_panel_b, show_filters_icon)
        self._set_mode_button_colors(self.show_filters_panel_b)
        
        self.show_compositors_panel_b = gtk.RadioButton(self.show_media_panel_b)
        self.show_compositors_panel_b.set_mode(False)
        _b(self.show_compositors_panel_b, show_compositors_icon)
        self._set_mode_button_colors(self.show_compositors_panel_b)
                
        self.show_sequences_panel_b = gtk.RadioButton(self.show_media_panel_b)
        self.show_sequences_panel_b.set_mode(False)
        _b(self.show_sequences_panel_b, show_sequences_icon)
        self._set_mode_button_colors(self.show_sequences_panel_b)

        self.show_render_panel_b = gtk.RadioButton(self.show_media_panel_b)
        self.show_render_panel_b.set_mode(False)
        _b(self.show_render_panel_b, show_render_icon)
        self._set_mode_button_colors(self.show_render_panel_b)
        
        self.open_mixer_b = gtk.Button()
        _b(self.open_mixer_b, open_mixer_icon)
        
        self.open_titler_b = gtk.Button()
        _b(self.open_titler_b, open_titler_icon)
        #save_b = gtk.Button()
        #_b(save_b, save_icon)
        #load_b = gtk.Button()
        #_b(load_b, load_icon)
        #quit_b = gtk.Button()
        #_b(quit_b, quit_icon)
        #new_b = gtk.Button()
        #_b(new_b, new_icon)

        # Connect signals
        self.show_media_panel_b.connect("clicked", lambda w,e: updater.switch_notebook_panel(0), None)
        self.show_filters_panel_b.connect("clicked", lambda w,e: updater.switch_notebook_panel(1), None)
        self.show_compositors_panel_b.connect("clicked", lambda w,e: updater.switch_notebook_panel(2), None)
        self.show_sequences_panel_b.connect("clicked", lambda w,e: updater.switch_notebook_panel(3), None)
        self.show_render_panel_b.connect("clicked", lambda w,e: updater.switch_notebook_panel(4), None)
        self.open_mixer_b.connect("clicked", lambda w: audiomonitoring.show_audio_monitor())
        self.open_titler_b.connect("clicked", lambda w: titler.show_titler())
            
        # Row
        buttons_row = gtk.HBox(False, 1)
        buttons_row.pack_start(self.show_media_panel_b, False, True, 0)
        buttons_row.pack_start(self.show_filters_panel_b, False, True, 0)
        buttons_row.pack_start(self.show_compositors_panel_b, False, True, 0)
        buttons_row.pack_start(self.show_sequences_panel_b, False, True, 0)
        buttons_row.pack_start(self.show_render_panel_b, False, True, 0)
        #buttons_row.pack_start(gtk.Label(), True, True, 0)
        #buttons_row.pack_start(new_b, False, True, 0)
        #buttons_row.pack_start(save_b, False, True, 0)
        #buttons_row.pack_start(load_b, False, True, 0)
        #buttons_row.pack_start(quit_b, False, True, 0)
        buttons_row.pack_start(gtk.Label(), True, True, 0)
        buttons_row.pack_start(self.open_titler_b, False, True, 0)
        buttons_row.pack_start(self.open_mixer_b, False, True, 0)
        
        return buttons_row
    """

    def _add_tool_tips(self):
        self.big_TC.widget.set_tooltip_text(_("Timeline current frame timecode"))

        #self.zoom_in_b.set_tooltip_text(_("Zoom In"))
        #self.zoom_out_b.set_tooltip_text(_("Zoom Out"))
        #self.zoom_length_b.set_tooltip_text(_("Zoom to Sequence length"))

        #self.insert_move_b.set_tooltip_text(_("Insert Move"))      
        #self.one_roll_trim_b.set_tooltip_text(_("One Roll Trim"))           
        #self.tworoll_trim_b.set_tooltip_text(_("Two Roll Trim"))    
        #self.overwrite_move_b.set_tooltip_text(_("Overwrite Move"))    

        #self.cut_b.set_tooltip_text(_("Cut"))    
        #self.splice_out_b.set_tooltip_text(_("Splice Out Clip"))    
        #self.lift_b.set_tooltip_text(_("Lift Clip"))    
        #self.resync_b.set_tooltip_text(_("Resync Selected Clips"))    

        #self.insert_b.set_tooltip_text(_("Insert Monitor Clip Range"))    
        #self.overwrite_b.set_tooltip_text(_("Overwrite Selected Clips with Monitor Clip Range"))    
        #self.overwrite_range_b.set_tooltip_text(_("Overwrite Mark In/Mark Out Range with Monitor Clip Range"))    
        #self.append_b.set_tooltip_text(_("Append Monitor Clip Range"))    

        #self.undo_b.set_tooltip_text(_("Undo"))    
        #self.redo_b.set_tooltip_text(_("Redo"))

        #self.play_b.set_tooltip_text(_("Play"))
        #self.stop_b.set_tooltip_text(_("Stop"))
        #self.prev_b.set_tooltip_text(_("Previous frame"))
        #self.next_b.set_tooltip_text(_("Next frame"))

        #self.ff_b.set_tooltip_text(_("Fast Forward"))
        #self.rew_b.set_tooltip_text(_("Rewind"))

        #self.mark_in_b.set_tooltip_text(_("Set Mark In"))
        #self.mark_out_b.set_tooltip_text(_("Set Mark Out"))
        #self.marks_clear_b.set_tooltip_text(_("Clear Marks"))
        #self.to_mark_in_b.set_tooltip_text(_("Go to Mark In"))
        #self.to_mark_out_b.set_tooltip_text(_("Go to Mark Out"))

        self.view_mode_select.widget.set_tooltip_text(_("Select view mode: Program Video/Vectorscope/RGBParade"))
        
        self.tc.widget.set_tooltip_text(_("Monitor program current frame timecode"))
        self.monitor_source.set_tooltip_text(_("Current Monitor program name"))
        self.mark_in_entry.set_tooltip_text(_("Monitor program Mark In timecode"))
        self.mark_out_entry.set_tooltip_text(_("Monitor program Mark Out timecode"))
        self.length_entry.set_tooltip_text(_("Monitor program selected range length"))
    
        self.pos_bar.widget.set_tooltip_text(_("Monitor program current position"))
        
        self.sequence_editor_b.set_tooltip_text(_("Display Current Sequence on Timeline"))
        self.clip_editor_b.set_tooltip_text(_("Display Monitor Clip"))

        self.open_project_b.set_tooltip_text(_("Open Project File"))
        self.new_project_b.set_tooltip_text(_("Open New Project"))

    def handle_over_move_mode_button_press(self):
        editevent.overwrite_move_mode_pressed()

    def handle_insert_move_mode_button_press(self):
        editevent.insert_move_mode_pressed()

    def handle_one_roll_mode_button_press(self):
        editevent.oneroll_trim_mode_pressed()

    def handle_two_roll_mode_button_press(self):
        editevent.tworoll_trim_mode_pressed()

    def _handle_mode_button_press(self, widget):
        # We get two "clicked" events per mode toggle, send through only the one
        # from the activated button
        if ((self.insert_move_b.get_active() == True) 
            and (widget == self.insert_move_b)):
            editevent.insert_move_mode_pressed()

        if ((self.one_roll_trim_b.get_active() == True) 
            and (widget == self.one_roll_trim_b)):
            editevent.oneroll_trim_mode_pressed()
            
        if ((self.tworoll_trim_b.get_active() == True) 
            and (widget == self.tworoll_trim_b)):
            editevent.tworoll_trim_mode_pressed()

        if ((self.overwrite_move_b.get_active() == True) 
            and (widget == self.overwrite_move_b)):
            editevent.overwrite_move_mode_pressed()



