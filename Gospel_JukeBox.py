import flet as ft
import os
import base64
import json
import time
from datetime import datetime

# Define the application paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MP3_DIR = os.path.join(BASE_DIR, "mp3_files")
PICTURES_DIR = os.path.join(BASE_DIR, "pictures")

# Ensure directories exist
os.makedirs(MP3_DIR, exist_ok=True)
os.makedirs(PICTURES_DIR, exist_ok=True)

# Helper function to encode MP3 files to base64
def encode_audio_to_base64(file_path):
    """
    Read an audio file and encode it to base64 string
    """
    try:
        with open(file_path, "rb") as audio_file:
            audio_data = audio_file.read()
            base64_data = base64.b64encode(audio_data).decode('utf-8')
            return base64_data
    except Exception as e:
        print(f"Error encoding audio file {file_path}: {e}")
        return None

class GospelJukeBox:
    def __init__(self, page: ft.Page):
        self.page = page
        self.page.title = "Gospel JukeBox"
        self.page.theme_mode = ft.ThemeMode.LIGHT
        self.page.padding = 20
        self.page.window_width = 1000
        self.page.window_height = 800
        
        # App state variables
        self.current_view = "music"  # Default view: music or pictures
        self.current_song = None
        self.current_picture = None
        self.is_playing = False
        self.autoplay = False
        self.loop_queue = False
        self.songs_list = []
        self.pictures_list = []
        self.current_song_index = 0
        self.queue = []  # List of song indices in the queue
        self.history = []  # List of previously played songs
        self.current_audio = None  # Reference to current audio element
        
        # Initialize UI components
        self.init_ui()
        
        # Load initial content
        self.load_content()
        
    def init_ui(self):
        # App bar with title and theme toggle
        self.app_bar = ft.AppBar(
            title=ft.Text("Gospel JukeBox", size=32, weight=ft.FontWeight.BOLD, color=ft.colors.BLACK),
            bgcolor=ft.colors.BLUE_100,
            actions=[
                ft.IconButton(
                    icon=ft.icons.DARK_MODE if self.page.theme_mode == ft.ThemeMode.LIGHT else ft.icons.LIGHT_MODE,
                    tooltip="Toggle Theme",
                    on_click=self.toggle_theme
                )
            ]
        )
        
        # Navigation tabs
        self.tabs = ft.Tabs(
            selected_index=0,
            on_change=self.tab_changed,
            tabs=[
                ft.Tab(text="Music", icon=ft.icons.MUSIC_NOTE),
                ft.Tab(text="Pictures", icon=ft.icons.IMAGE)
            ]
        )
        
        # Sidebar for queue and history
        self.sidebar = ft.NavigationRail(
            selected_index=0,
            label_type=ft.NavigationRailLabelType.ALL,
            min_width=100,
            min_extended_width=200,
            destinations=[
                ft.NavigationRailDestination(
                    icon=ft.icons.LIBRARY_MUSIC_OUTLINED,
                    selected_icon=ft.icons.LIBRARY_MUSIC,
                    label="Library"
                ),
                ft.NavigationRailDestination(
                    icon=ft.icons.QUEUE_MUSIC_OUTLINED,
                    selected_icon=ft.icons.QUEUE_MUSIC,
                    label="Queue"
                ),
                ft.NavigationRailDestination(
                    icon=ft.icons.HISTORY_OUTLINED,
                    selected_icon=ft.icons.HISTORY,
                    label="History"
                ),
            ],
            on_change=self.sidebar_changed
        )
        
        # Content area
        self.content_area = ft.Container(
            content=ft.Column([], scroll=ft.ScrollMode.AUTO),
            expand=True
        )
        
        # Player controls
        self.player_controls = ft.Column(
            visible=False,
            controls=[
                ft.Row(
                    controls=[
                        ft.IconButton(
                            icon=ft.icons.SKIP_PREVIOUS,
                            tooltip="Previous",
                            on_click=self.play_previous
                        ),
                        ft.IconButton(
                            icon=ft.icons.PLAY_ARROW,
                            tooltip="Play",
                            on_click=self.toggle_play,
                            data="play"
                        ),
                        ft.IconButton(
                            icon=ft.icons.SKIP_NEXT,
                            tooltip="Next",
                            on_click=self.play_next
                        ),
                        ft.IconButton(
                            icon=ft.icons.STOP,
                            tooltip="Stop Current Song",
                            on_click=self.stop_current_song
                        ),
                        ft.IconButton(
                            icon=ft.icons.LIST,
                            tooltip="Back to List",
                            on_click=self.reset_view
                        ),
                        ft.Checkbox(
                            label="Autoplay",
                            value=False,
                            on_change=self.toggle_autoplay
                        ),
                        ft.Checkbox(
                            label="Loop Queue",
                            value=False,
                            on_change=self.toggle_loop
                        ),
                        ft.IconButton(
                            icon=ft.icons.SHUFFLE,
                            tooltip="Toggle Shuffle",
                            on_click=self.toggle_shuffle
                        ),
                        ft.IconButton(
                            icon=ft.icons.REPEAT,
                            tooltip="Toggle Repeat",
                            on_click=self.toggle_repeat,
                            data="no_repeat"  # Options: no_repeat, repeat_one, repeat_all
                        )
                    ],
                    alignment=ft.MainAxisAlignment.CENTER
                ),
                ft.Row(
                    controls=[
                        ft.Text("0:00 / 0:00", size=12),
                        ft.Slider(
                            min=0,
                            max=100,
                            value=0,
                            on_change=self.seek_position,
                            expand=True,
                            disabled=True
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER
                ),
                ft.Row(
                    controls=[
                        ft.IconButton(
                            icon=ft.icons.VOLUME_DOWN,
                            tooltip="Volume Down",
                            on_click=self.volume_down
                        ),
                        ft.Slider(
                            min=0,
                            max=1,
                            value=0.5,
                            on_change=self.set_volume,
                            width=100,
                            divisions=10
                        ),
                        ft.IconButton(
                            icon=ft.icons.VOLUME_UP,
                            tooltip="Volume Up",
                            on_click=self.volume_up
                        )
                    ],
                    alignment=ft.MainAxisAlignment.CENTER
                )
            ]
        )
        
        # Donation button
        self.donation_button = ft.ElevatedButton(
            "Donate with CashApp",
            icon=ft.icons.ATTACH_MONEY,
            on_click=self.open_donation_link,
            style=ft.ButtonStyle(
                color=ft.colors.WHITE,
                bgcolor="#00D632"  # CashApp green color
            )
        )
        
        # Main layout with sidebar and content
        self.main_layout = ft.Row(
            controls=[
                self.sidebar,
                ft.VerticalDivider(width=1),
                self.content_area,
            ],
            expand=True
        )
        
        # Assemble the main layout
        # Add search bar after the tabs
        self.search_bar = ft.TextField(
            label="Search songs",
            prefix_icon=ft.icons.SEARCH,
            on_change=self.filter_songs,
            expand=True,
            height=40,
            border_radius=20,
        )
        
        self.search_row = ft.Row(
            controls=[self.search_bar],
            alignment=ft.MainAxisAlignment.CENTER,
            visible=True
        )
        
        self.page.add(
            self.app_bar,
            self.tabs,
            self.search_row,  # Add search bar here
            self.main_layout,
            self.player_controls,
            ft.Row([self.donation_button], alignment=ft.MainAxisAlignment.CENTER)
        )
    
    def load_content(self):
        # Load songs and pictures from directories
        self.songs_list = self.get_media_list(MP3_DIR, ".mp3")
        self.pictures_list = self.get_media_list(PICTURES_DIR, ".jpg", ".png", ".jpeg")
        
        # Display the appropriate content based on current view
        if self.current_view == "music":
            self.display_music_list()
        else:
            self.display_pictures_list()
    
    def get_media_list(self, directory, *extensions):
        media_list = []
        if os.path.exists(directory):
            # First, check for media files directly in the directory
            direct_media_files = []
            for ext in extensions:
                direct_media_files.extend([f for f in os.listdir(directory) if f.lower().endswith(ext)])
            
            # Add direct media files to the list
            for media_file in direct_media_files:
                file_name = os.path.splitext(media_file)[0]  # Get name without extension
                media_path = os.path.join(directory, media_file)
                
                # Create a default text file path (may not exist)
                text_file_path = os.path.join(directory, f"{file_name}.txt")
                
                # If text file doesn't exist, create a placeholder
                if not os.path.exists(text_file_path):
                    with open(text_file_path, 'w') as f:
                        f.write(f"Lyrics for {file_name}")
                
                # For MP3 files, encode to base64
                base64_data = None
                if any(media_file.lower().endswith(ext) for ext in [".mp3"]):
                    base64_data = encode_audio_to_base64(media_path)
                
                media_list.append({
                    "name": file_name,
                    "media_file": media_path,
                    "text_file": text_file_path,
                    "base64_data": base64_data
                })
            
            # Then check subdirectories
            for folder_name in os.listdir(directory):
                folder_path = os.path.join(directory, folder_name)
                if os.path.isdir(folder_path):
                    # Look for media files with the specified extensions
                    media_files = []
                    for ext in extensions:
                        media_files.extend([f for f in os.listdir(folder_path) if f.lower().endswith(ext)])
                    
                    # Look for text files (lyrics or descriptions)
                    text_files = [f for f in os.listdir(folder_path) if f.lower().endswith(".txt")]
                    
                    if media_files and text_files:
                        media_path = os.path.join(folder_path, media_files[0])
                        
                        # For MP3 files, encode to base64
                        base64_data = None
                        if any(media_files[0].lower().endswith(ext) for ext in [".mp3"]):
                            base64_data = encode_audio_to_base64(media_path)
                        
                        media_list.append({
                            "name": folder_name,
                            "media_file": media_path,
                            "text_file": os.path.join(folder_path, text_files[0]),
                            "base64_data": base64_data
                        })
        return media_list
    
    def display_music_list(self):
        # Clear current content
        content_column = ft.Column(scroll=ft.ScrollMode.AUTO)
        
        if not self.songs_list:
            content_column.controls.append(ft.Text("No songs available"))
        else:
            for i, song in enumerate(self.songs_list):
                # Check if this song is in the queue
                in_queue = i in self.queue
                
                content_column.controls.append(
                    ft.ListTile(
                        leading=ft.Icon(ft.icons.MUSIC_NOTE),
                        title=ft.Text(song["name"]),
                        subtitle=ft.Text("In Queue" if in_queue else ""),
                        trailing=ft.PopupMenuButton(
                            icon=ft.icons.MORE_VERT,
                            items=[
                                ft.PopupMenuItem(text="Play", on_click=lambda e, idx=i: self.select_song(idx)),
                                ft.PopupMenuItem(text="Add to Queue", on_click=lambda e, idx=i: self.add_to_queue(idx)),
                                ft.PopupMenuItem(text="View Lyrics", on_click=lambda e, idx=i: self.view_lyrics(idx))
                            ]
                        ),
                        on_click=lambda e, idx=i: self.select_song(idx)
                    )
                )
        
        self.content_area.content = content_column
        self.player_controls.visible = bool(self.songs_list)
        self.page.update()
    
    def display_queue(self):
        # Display the queue
        content_column = ft.Column(scroll=ft.ScrollMode.AUTO)
        content_column.controls.append(ft.Text("Queue", size=20, weight=ft.FontWeight.BOLD))
        
        if not self.queue:
            content_column.controls.append(ft.Text("Queue is empty"))
        else:
            for i, song_index in enumerate(self.queue):
                song = self.songs_list[song_index]
                content_column.controls.append(
                    ft.ListTile(
                        leading=ft.Icon(ft.icons.QUEUE_MUSIC),
                        title=ft.Text(song["name"]),
                        trailing=ft.IconButton(
                            icon=ft.icons.DELETE,
                            tooltip="Remove from Queue",
                            on_click=lambda e, idx=i: self.remove_from_queue(idx)
                        ),
                        on_click=lambda e, idx=song_index: self.select_song(idx)
                    )
                )
            
            # Add clear queue button
            content_column.controls.append(
                ft.ElevatedButton(
                    "Clear Queue",
                    icon=ft.icons.CLEAR_ALL,
                    on_click=self.clear_queue
                )
            )
        
        self.content_area.content = content_column
        self.page.update()
    
    def display_history(self):
        # Display playback history
        content_column = ft.Column(scroll=ft.ScrollMode.AUTO)
        content_column.controls.append(ft.Text("History", size=20, weight=ft.FontWeight.BOLD))
        
        if not self.history:
            content_column.controls.append(ft.Text("No playback history"))
        else:
            # Display most recent first
            for i, song_index in enumerate(reversed(self.history)):
                song = self.songs_list[song_index]
                content_column.controls.append(
                    ft.ListTile(
                        leading=ft.Icon(ft.icons.HISTORY),
                        title=ft.Text(song["name"]),
                        trailing=ft.IconButton(
                            icon=ft.icons.PLAYLIST_ADD,
                            tooltip="Add to Queue",
                            on_click=lambda e, idx=song_index: self.add_to_queue(idx)
                        ),
                        on_click=lambda e, idx=song_index: self.select_song(idx)
                    )
                )
            
            # Add clear history button
            content_column.controls.append(
                ft.ElevatedButton(
                    "Clear History",
                    icon=ft.icons.CLEAR_ALL,
                    on_click=self.clear_history
                )
            )
        
        self.content_area.content = content_column
        self.page.update()
    
    def display_pictures_list(self):
        # Clear current content
        content_column = ft.Column(scroll=ft.ScrollMode.AUTO)
        
        if not self.pictures_list:
            content_column.controls.append(ft.Text("No pictures available"))
        else:
            # Create a grid for pictures
            grid = ft.GridView(
                expand=1,
                max_extent=200,
                child_aspect_ratio=1.0,
                spacing=10,
                run_spacing=10
            )
            
            for i, picture in enumerate(self.pictures_list):
                grid.controls.append(
                    ft.Card(
                        content=ft.Container(
                            content=ft.Column([
                                ft.Image(
                                    src=picture["media_file"],
                                    width=180,
                                    height=150,
                                    fit=ft.ImageFit.COVER
                                ),
                                ft.Text(picture["name"], size=14)
                            ]),
                            padding=10,
                            on_click=lambda e, idx=i: self.select_picture(idx)
                        )
                    )
                )
            
            content_column.controls.append(grid)
        
        self.content_area.content = content_column
        self.player_controls.visible = False
        self.page.update()
    
    def _stop_audio_in_control(self, control):
        """Recursively search for and stop audio controls"""
        try:
            # Check if this is an audio control
            if isinstance(control, ft.Audio):
                try:
                    if hasattr(control, 'pause'):
                        control.pause()
                    if hasattr(control, 'release'):
                        control.release()
                    print(f"Stopped audio control: {id(control)}")
                except Exception as ex:
                    print(f"Error stopping audio control: {ex}")
            
            # Check if it has controls attribute (like Column, Row, etc.)
            if hasattr(control, 'controls') and control.controls:
                for child in control.controls:
                    self._stop_audio_in_control(child)
                    
            # Check if it has content attribute (like Container)
            if hasattr(control, 'content') and control.content:
                self._stop_audio_in_control(control.content)
        except Exception as e:
            print(f"Error in _stop_audio_in_control: {e}")
    
    def stop_all_audio(self):
        """Stop all audio playback on the page"""
        try:
            # Stop the current audio control if it exists
            if hasattr(self, 'current_audio') and self.current_audio:
                try:
                    if hasattr(self.current_audio, 'pause'):
                        self.current_audio.pause()
                    if hasattr(self.current_audio, 'release'):
                        self.current_audio.release()
                except Exception as e:
                    print(f"Error stopping current audio: {e}")
                self.current_audio = None
            
            # Check the content area which contains the audio control
            if self.content_area and hasattr(self.content_area, 'content'):
                self._stop_audio_in_control(self.content_area.content)
                
            # Then check all page controls as a fallback
            for control in self.page.controls:
                self._stop_audio_in_control(control)
        except Exception as e:
            print(f"Error in stop_all_audio: {e}")
    
    def select_song(self, index):
        # Stop current playback if any
        self.stop_all_audio()
        
        self.current_song_index = index
        self.current_song = self.songs_list[index]
        
        # Add to history if not already the last item
        if not self.history or self.history[-1] != index:
            self.history.append(index)
            # Keep history at a reasonable size
            if len(self.history) > 50:
                self.history.pop(0)
        
        # Read lyrics
        lyrics = "No lyrics available"
        if os.path.exists(self.current_song["text_file"]):
            try:
                with open(self.current_song["text_file"], "r") as f:
                    lyrics = f.read()
            except Exception as e:
                print(f"Error reading lyrics file: {e}")
        
        # Create audio control with base64 data if available
        audio_control = None
        if self.current_song.get("base64_data"):
            # Use base64 encoded data for audio playback
            audio_control = ft.Audio(
                src_base64=self.current_song["base64_data"],
                autoplay=True,  # Start playing immediately
                volume=1.0,
                on_loaded=lambda _: print(f"Audio loaded: {self.current_song['name']}")
            )
            print(f"Created audio control with base64 data")
        else:
            # Fallback to file path if base64 encoding failed
            audio_control = ft.Audio(
                src=self.current_song["media_file"],
                autoplay=True,  # Start playing immediately
                volume=1.0,
                on_loaded=lambda _: print(f"Audio loaded: {self.current_song['name']}")
            )
            print(f"Created audio control with file path (base64 not available)")
        
        # Store reference to the audio control
        self.current_audio = audio_control
        
        # Create content with song details and lyrics
        content_column = ft.Column([
            ft.Text(f"Now Playing: {self.current_song['name']}", size=20, weight=ft.FontWeight.BOLD),
            audio_control,
            ft.Divider(),
            ft.Text("Lyrics:", weight=ft.FontWeight.BOLD),
            ft.Container(
                content=ft.Text(lyrics, color=ft.colors.BLACK),
                padding=10,
                bgcolor=ft.colors.BLUE_50,
                border_radius=10,
                expand=True
            )
        ], scroll=ft.ScrollMode.AUTO)
        
        # Update play button icon
        play_button = self.player_controls.controls[0].controls[1]
        play_button.icon = ft.icons.PAUSE
        play_button.data = "pause"
        self.is_playing = True
        
        # Set the content and update the page
        self.content_area.content = content_column
        self.player_controls.visible = True
        self.page.update()
    
    def select_picture(self, index):
        self.current_picture = self.pictures_list[index]
        
        # Display picture and description
        description = "No description available"
        if os.path.exists(self.current_picture["text_file"]):
            with open(self.current_picture["text_file"], "r") as f:
                description = f.read()
        
        content_column = ft.Column([
            ft.Text(self.current_picture["name"], size=20, weight=ft.FontWeight.BOLD),
            ft.Container(
                content=ft.Image(
                    src=self.current_picture["media_file"],
                    fit=ft.ImageFit.CONTAIN,
                    width=600
                ),
                alignment=ft.alignment.center
            ),
            ft.Divider(),
            ft.Text("Description:", weight=ft.FontWeight.BOLD),
            ft.Container(
                content=ft.Text(description),
                padding=10,
                bgcolor=ft.colors.BLUE_50,
                border_radius=10
            )
        ], scroll=ft.ScrollMode.AUTO)
        
        self.content_area.content = content_column
        self.page.update()
    
    def add_to_queue(self, index):
        if index not in self.queue:
            self.queue.append(index)
            # If this is the first song in the queue and nothing is playing, play it
            if len(self.queue) == 1 and self.current_song is None and self.autoplay:
                self.select_song(index)
            else:
                # Just update the UI to show the song is in queue
                self.display_music_list()
    
    def remove_from_queue(self, queue_index):
        if 0 <= queue_index < len(self.queue):
            self.queue.pop(queue_index)
            self.display_queue()
    
    def clear_queue(self, e=None):
        self.queue = []
        self.display_queue()
    
    def clear_history(self, e=None):
        self.history = []
        self.display_history()
    
    def play_previous(self, e=None):
        # Play the previous song in history if available
        if len(self.history) > 1:
            # Remove current song from history
            self.history.pop()
            # Get previous song
            prev_song_index = self.history.pop()
            # Play it
            self.select_song(prev_song_index)
    
    def play_next(self, e=None):
        # Play the next song in queue if available
        if self.queue:
            next_song_index = self.queue.pop(0)
            self.select_song(next_song_index)
        elif self.loop_queue and self.history:
            # If loop is enabled and we have history, play the first song in history
            self.select_song(self.history[0])
    
    def toggle_play(self, e):
        # Toggle playing state
        self.is_playing = not self.is_playing
        
        # Update button icon
        if self.is_playing:
            e.control.icon = ft.icons.PAUSE
            e.control.data = "pause"
            # Resume playback
            if self.current_audio:
                if hasattr(self.current_audio, 'play'):
                    self.current_audio.play()
                    print(f"Playing audio: {self.current_song['name']}")
        else:
            e.control.icon = ft.icons.PLAY_ARROW
            e.control.data = "play"
            # Pause playback
            if self.current_audio:
                if hasattr(self.current_audio, 'pause'):
                    self.current_audio.pause()
                    print(f"Paused audio: {self.current_song['name']}")
        
        self.page.update()
    
    def stop_current_song(self, e=None):
        # Stop the current song
        if self.current_audio:
            if hasattr(self.current_audio, 'pause'):
                self.current_audio.pause()
            if hasattr(self.current_audio, 'release'):
                self.current_audio.release()
            self.current_audio = None
            self.is_playing = False
            
            # Update play button
            play_button = self.player_controls.controls[0].controls[1]
            play_button.icon = ft.icons.PLAY_ARROW
            play_button.data = "play"
            
            print(f"Stopped current song")
            self.page.update()
    
    def reset_view(self, e=None):
        # Stop all audio when returning to list view
        self.stop_all_audio()
        
        # Return to the song list view
        if self.current_view == "music":
            self.display_music_list()
        else:
            # If in pictures view, also reset to music view
            self.current_view = "music"
            self.tabs.selected_index = 0
            self.load_content()
    
    def toggle_theme(self, e):
        # Toggle between light and dark theme
        self.page.theme_mode = ft.ThemeMode.DARK if self.page.theme_mode == ft.ThemeMode.LIGHT else ft.ThemeMode.LIGHT
        e.control.icon = ft.icons.DARK_MODE if self.page.theme_mode == ft.ThemeMode.LIGHT else ft.icons.LIGHT_MODE
        self.page.update()
    
    def toggle_autoplay(self, e):
        self.autoplay = e.control.value
    
    def toggle_loop(self, e):
        self.loop_queue = e.control.value
    
    def toggle_shuffle(self, e=None):
        # Implement shuffle functionality
        import random
        if self.queue:
            random.shuffle(self.queue)
            self.display_queue()
    
    def toggle_repeat(self, e=None):
        # Cycle through repeat modes: no_repeat -> repeat_one -> repeat_all -> no_repeat
        current_mode = e.control.data
        if current_mode == "no_repeat":
            e.control.data = "repeat_one"
            e.control.icon = ft.icons.REPEAT_ONE
        elif current_mode == "repeat_one":
            e.control.data = "repeat_all"
            e.control.icon = ft.icons.REPEAT_ON
        else:  # repeat_all
            e.control.data = "no_repeat"
            e.control.icon = ft.icons.REPEAT
        
        self.page.update()
    
    def seek_position(self, e):
        # Implement seek functionality for Flet Audio control
        if self.current_audio and hasattr(self.current_audio, 'seek'):
            position = e.control.value
            self.current_audio.seek(position)
            print(f"Seeking to position: {position}")
    
    def set_volume(self, e):
        # Set volume for Flet Audio control
        if self.current_audio and hasattr(self.current_audio, 'volume'):
            volume = e.control.value
            self.current_audio.volume = volume
            print(f"Set volume to: {volume}")
            self.page.update()
    
    def volume_up(self, e=None):
        # Increase volume
        volume_slider = self.player_controls.controls[2].controls[1]
        new_volume = min(1.0, volume_slider.value + 0.1)
        volume_slider.value = new_volume
        self.set_volume(ft.ControlEvent(control=volume_slider, data=str(new_volume)))
        self.page.update()
    
    def volume_down(self, e=None):
        # Decrease volume
        volume_slider = self.player_controls.controls[2].controls[1]
        new_volume = max(0.0, volume_slider.value - 0.1)
        volume_slider.value = new_volume
        self.set_volume(ft.ControlEvent(control=volume_slider, data=str(new_volume)))
        self.page.update()
    
    # Add after the init_ui method
    def filter_songs(self, e):
        search_term = self.search_bar.value.lower()
        content_column = ft.Column(scroll=ft.ScrollMode.AUTO)
        
        if not self.songs_list:
            content_column.controls.append(ft.Text("No songs available"))
        else:
            filtered_songs = [
                (i, song) for i, song in enumerate(self.songs_list)
                if search_term in song["name"].lower()
            ]
            
            if not filtered_songs:
                content_column.controls.append(ft.Text("No matching songs found"))
            else:
                for i, (original_index, song) in enumerate(filtered_songs):
                    in_queue = original_index in self.queue
                    content_column.controls.append(
                        ft.ListTile(
                            leading=ft.Icon(ft.icons.MUSIC_NOTE),
                            title=ft.Text(song["name"]),
                            subtitle=ft.Text("In Queue" if in_queue else ""),
                            trailing=ft.PopupMenuButton(
                                icon=ft.icons.MORE_VERT,
                                items=[
                                    ft.PopupMenuItem(text="Play", on_click=lambda e, idx=original_index: self.select_song(idx)),
                                    ft.PopupMenuItem(text="Add to Queue", on_click=lambda e, idx=original_index: self.add_to_queue(idx)),
                                    ft.PopupMenuItem(text="View Lyrics", on_click=lambda e, idx=original_index: self.view_lyrics(idx))
                                ]
                            ),
                            on_click=lambda e, idx=original_index: self.select_song(idx)
                        )
                    )
        
        self.content_area.content = content_column
        self.page.update()
    
    # Update tab_changed method to handle search bar visibility
    def tab_changed(self, e):
        self.current_view = "music" if e.control.selected_index == 0 else "pictures"
        self.search_row.visible = (self.current_view == "music")
        self.load_content()
    
    def sidebar_changed(self, e):
        selected_index = e.control.selected_index
        if selected_index == 0:  # Library
            self.display_music_list()
        elif selected_index == 1:  # Queue
            self.display_queue()
        elif selected_index == 2:  # History
            self.display_history()
    
    def view_lyrics(self, index):
        song = self.songs_list[index]
        lyrics = "No lyrics available"
        if os.path.exists(song["text_file"]):
            try:
                with open(song["text_file"], "r") as f:
                    lyrics = f.read()
            except Exception as e:
                print(f"Error reading lyrics file: {e}")
        
        # Show lyrics in a dialog
        self.page.dialog = ft.AlertDialog(
            title=ft.Text(f"Lyrics: {song['name']}"),
            content=ft.Container(
                content=ft.Text(lyrics),
                padding=20,
                width=400,
                height=300,
                scroll=ft.ScrollMode.AUTO
            ),
            actions=[
                ft.TextButton("Close", on_click=lambda e: self.close_dialog())
            ]
        )
        self.page.dialog.open = True
        self.page.update()
    
    def close_dialog(self):
        self.page.dialog.open = False
        self.page.update()
    
    def open_donation_link(self, e):
        # Open CashApp link
        cashapp_url = "https://cash.app/$SolidBuildersInc/"
        self.page.launch_url(cashapp_url)


def main(page: ft.Page):
    # Create the app instance
    app = GospelJukeBox(page)


# Run the app
ft.app(target=main)
