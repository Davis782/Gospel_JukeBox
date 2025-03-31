import os
import shutil
import bcrypt
import base64
from datetime import datetime
import flet as ft

# Define the application paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MP3_DIR = os.path.join(BASE_DIR, "mp3_files")
PICTURES_DIR = os.path.join(BASE_DIR, "pictures")

# Ensure directories exist
os.makedirs(MP3_DIR, exist_ok=True)
os.makedirs(PICTURES_DIR, exist_ok=True)

# Admin credentials (in a real app, these would be stored securely)
ADMIN_USERNAME = "admin"
# Hashed password for "admin123"
ADMIN_PASSWORD_HASH = bcrypt.hashpw("admin123".encode(), bcrypt.gensalt())

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
        self.current_view = "music"  # Default view: music or pictures
        self.current_song = None
        self.current_picture = None
        self.is_playing = False
        self.is_admin = False
        self.autoplay = False
        self.loop_queue = False
        self.songs_list = []
        self.pictures_list = []
        self.current_song_index = 0
        self.current_audio_control = None  # Store reference to the current audio control
        self.current_position = 0  # Current position in seconds
        self.song_duration = 0  # Total duration in seconds
        self.progress_timer = None  # Timer for updating progress
        self.queue = []  # List of song indices in the queue for autoplay
        self.active_audio_controls = []  # Global list to track all active audio controls
        
        # Initialize UI components
        self.init_ui()
        
        # Load initial content
        self.load_content()
        
    def init_ui(self):
        # App bar with title and login button
        self.app_bar = ft.AppBar(
            title=ft.Text("Gospel JukeBox", size=32, weight=ft.FontWeight.BOLD, color=ft.colors.BLACK),
            bgcolor=ft.colors.BLUE_100,
            actions=[
                ft.IconButton(
                    icon=ft.icons.DARK_MODE if self.page.theme_mode == ft.ThemeMode.LIGHT else ft.icons.LIGHT_MODE,
                    tooltip="Toggle Theme",
                    on_click=self.toggle_theme
                ),
                ft.IconButton(
                    icon=ft.icons.PERSON,
                    tooltip="Admin Login",
                    on_click=self.show_login_dialog
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
        
        # Content area
        self.content_area = ft.Container(
            content=ft.Column([], scroll=ft.ScrollMode.AUTO),
            expand=True
        )
        
        # Music player controls
        self.progress_slider = ft.Slider(
            min=0,
            max=100,
            value=0,
            on_change=self.seek_position,
            expand=True,
            disabled=True
        )
        
        self.time_display = ft.Text("0:00 / 0:00", size=12)
        
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
                        )
                    ],
                    alignment=ft.MainAxisAlignment.CENTER
                ),
                ft.Row(
                    controls=[
                        self.time_display,
                        self.progress_slider,
                    ],
                    alignment=ft.MainAxisAlignment.CENTER
                )
            ]
        )
        
        # Donation button
        self.donation_button = ft.ElevatedButton(
            "Donate with CashApp - Work in Progress",
            icon=ft.icons.ATTACH_MONEY,
            on_click=self.open_donation_link,
            style=ft.ButtonStyle(
                color=ft.colors.WHITE,
                bgcolor=ft.colors.GREEN
            )
        )
        
        # Admin panel (initially hidden)
        self.admin_panel = ft.Container(
            visible=False,
            content=ft.Column([
                ft.Text("Admin Panel", size=24, weight=ft.FontWeight.BOLD),
                ft.Divider(),
                self.build_upload_section()
            ])
        )
        
        # Assemble the main layout
        self.page.add(
            self.app_bar,
            self.tabs,
            self.content_area,
            self.player_controls,
            ft.Row([self.donation_button], alignment=ft.MainAxisAlignment.CENTER),
            self.admin_panel
        )
    
    def build_upload_section(self):
        # File upload section for admin
        self.upload_type_dropdown = ft.Dropdown(
            label="Content Type",
            options=[
                ft.dropdown.Option("mp3", "Music (MP3)"),
                ft.dropdown.Option("picture", "Picture")
            ],
            width=200,
            on_change=self.upload_type_changed
        )
        
        self.folder_name_field = ft.TextField(
            label="Folder Name (Song/Picture Name)",
            width=300
        )
        
        self.media_file_picker = ft.FilePicker(
            on_result=self.media_file_picked
        )
        self.page.overlay.append(self.media_file_picker)
        
        self.lyrics_file_picker = ft.FilePicker(
            on_result=self.lyrics_file_picked
        )
        self.page.overlay.append(self.lyrics_file_picker)
        
        self.media_file_path = ft.Text("No file selected")
        self.lyrics_file_path = ft.Text("No file selected")
        
        return ft.Column([
            self.upload_type_dropdown,
            self.folder_name_field,
            ft.Row([
                ft.ElevatedButton(
                    "Select Media File",
                    icon=ft.icons.UPLOAD_FILE,
                    on_click=lambda _: self.media_file_picker.pick_files()
                ),
                self.media_file_path
            ]),
            ft.Row([
                ft.ElevatedButton(
                    "Select Lyrics/Description File",
                    icon=ft.icons.UPLOAD_FILE,
                    on_click=lambda _: self.lyrics_file_picker.pick_files()
                ),
                self.lyrics_file_path
            ]),
            ft.ElevatedButton(
                "Upload Files",
                icon=ft.icons.CLOUD_UPLOAD,
                on_click=self.upload_files
            )
        ])
    
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
            
            # Then check subdirectories as before
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
                        trailing=ft.Checkbox(
                            value=in_queue,
                            on_change=lambda e, idx=i: self.toggle_queue(e, idx)
                        ),
                        on_click=lambda e, idx=i: self.select_song(idx)
                    )
                )
        
        self.content_area.content = content_column
        self.player_controls.visible = bool(self.songs_list)
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
    
    def select_song(self, index):
        # First, stop all audio playback on the page
        try:
            # Stop and release the current audio control if it exists
            if self.current_audio_control:
                try:
                    if hasattr(self.current_audio_control, 'pause'):
                        self.current_audio_control.pause()
                    if hasattr(self.current_audio_control, 'release'):
                        self.current_audio_control.release()
                    print(f"Stopped current audio control: {id(self.current_audio_control)}")
                except Exception as ex:
                    print(f"Error stopping current audio: {ex}")
            
            # Master stop: check all page controls to find and stop any audio elements
            print("Performing master audio stop...")
            # First check the content area which contains the audio control
            if self.content_area and hasattr(self.content_area, 'content'):
                self._stop_audio_in_control(self.content_area.content)
                
            # Then check all page controls as a fallback
            for control in self.page.controls:
                self._stop_audio_in_control(control)
                
            # Force a small delay to ensure audio has stopped
            self.page.update()
        except Exception as e:
            print(f"Error in master audio stop: {e}")
        
        self.current_song_index = index
        self.current_song = self.songs_list[index]
        
        # Ensure the current song is in the queue if autoplay is enabled
        if self.autoplay and index not in self.queue:
            self.queue.append(index)
            self.queue.sort()  # Keep queue in order
        
        # Reset progress tracking
        self.current_position = 0
        self.song_duration = 0
        self.progress_slider.value = 0
        self.progress_slider.disabled = True
        self.update_time_display()
        
        # Display song details and lyrics
        lyrics = "No lyrics available"
        if os.path.exists(self.current_song["text_file"]):
            with open(self.current_song["text_file"], "r") as f:
                lyrics = f.read()
        
        # Create audio control with base64 data if available
        audio_control = None
        if self.current_song.get("base64_data"):
            # Use base64 encoded data for audio playback
            audio_control = ft.Audio(
                src_base64=self.current_song["base64_data"],
                autoplay=False,  # Important: don't autoplay yet
                volume=1.0,
                on_state_changed=self.audio_state_changed
            )
            print(f"Created audio control with base64 data")
        else:
            # Fallback to file path if base64 encoding failed
            audio_control = ft.Audio(
                src=self.current_song["media_file"],
                autoplay=False,  # Important: don't autoplay yet
                volume=1.0,
                on_state_changed=self.audio_state_changed
            )
            print(f"Created audio control with file path (base64 not available)")
        
        # Store reference to the audio control
        self.current_audio_control = audio_control
        
        # Add to the global tracking list
        if audio_control not in self.active_audio_controls:
            self.active_audio_controls.append(audio_control)
            print(f"Added audio control to tracking list: {id(audio_control)}")
        
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
        play_button.icon = ft.icons.PAUSE if self.is_playing else ft.icons.PLAY_ARROW
        play_button.data = "pause"
        
        # Set the content and update the page
        self.content_area.content = content_column
        self.player_controls.visible = True
        self.page.update()
        
        # Now that the audio control is added to the page and we've ensured all other
        # audio is stopped, we can play it if needed
        if self.is_playing and self.current_audio_control:
            try:
                print(f"Starting playback of new audio: {id(self.current_audio_control)}")
                if hasattr(self.current_audio_control, 'play'):
                    self.current_audio_control.play()
            except Exception as e:
                print(f"Error playing audio: {e}")
        
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
    
    def tab_changed(self, e):
        self.current_view = "music" if e.control.selected_index == 0 else "pictures"
        self.load_content()
    
    def reset_view(self, e):
        # Stop all audio when returning to list view
        self.stop_all_audio()
        
        # Reset to the song list view
        if self.current_view == "music":
            self.display_music_list()
        else:
            # If in pictures view, also reset to music view
            self.current_view = "music"
            self.tabs.selected_index = 0
            self.load_content()
    
    def toggle_play(self, e):
        # Toggle playing state
        self.is_playing = not self.is_playing
        
        # Update button icon
        if self.is_playing:
            e.control.icon = ft.icons.PAUSE
            e.control.data = "pause"
        else:
            e.control.icon = ft.icons.PLAY_ARROW
            e.control.data = "play"
        
        # If we're starting playback, ensure all other audio is stopped first
        if self.is_playing:
            try:
                # Stop all other audio controls except the current one
                print("Stopping all other audio controls before starting playback...")
                
                # Use our global tracking list to stop all audio except current one
                for audio in list(self.active_audio_controls):
                    if audio != self.current_audio_control:
                        try:
                            if hasattr(audio, 'pause'):
                                audio.pause()
                            if hasattr(audio, 'release'):
                                audio.release()
                            print(f"Stopped other audio control: {id(audio)}")
                            
                            # Remove from tracking list
                            if audio in self.active_audio_controls:
                                self.active_audio_controls.remove(audio)
                        except Exception as ex:
                            print(f"Error stopping other audio: {ex}")
                
                # Force a small delay to ensure audio has stopped
                self.page.update()
            except Exception as ex:
                print(f"Error in stopping other audio during toggle_play: {ex}")
        
        # Control the audio element directly
        if self.current_audio_control:
            try:
                if self.is_playing:
                    if hasattr(self.current_audio_control, 'play'):
                        self.current_audio_control.play()
                        # Enable the slider when playback starts
                        self.progress_slider.disabled = False
                        
                        # Get the current position from the audio control to ensure slider is in sync
                        try:
                            current_ms = self.current_audio_control.get_current_position()
                            self.current_position = current_ms / 1000  # Convert from ms to seconds
                            self.progress_slider.value = self.current_position
                            self.update_time_display()
                            print(f"Updated slider position on play: {self.current_position} seconds")
                        except Exception as pos_ex:
                            print(f"Error getting current position on play: {pos_ex}")
                else:
                    if hasattr(self.current_audio_control, 'pause'):
                        self.current_audio_control.pause()
                        
                        # Get the current position from the audio control to ensure slider is in sync
                        try:
                            current_ms = self.current_audio_control.get_current_position()
                            self.current_position = current_ms / 1000  # Convert from ms to seconds
                            self.progress_slider.value = self.current_position
                            self.update_time_display()
                            print(f"Updated slider position on pause: {self.current_position} seconds")
                        except Exception as pos_ex:
                            print(f"Error getting current position on pause: {pos_ex}")
            except Exception as e:
                print(f"Error controlling audio: {e}")
        elif self.current_song:
            # If no audio control exists yet, create one by selecting the song
            self.select_song(self.current_song_index)
        
        self.page.update()
    
    def _play_audio_after_update(self, audio_control):
        # This method is called after the page update to ensure the audio control is properly initialized
        try:
            if hasattr(audio_control, 'play'):
                audio_control.play()
        except Exception as e:
            print(f"Error in _play_audio_after_update: {e}")
    
    def _stop_audio_in_control(self, control):
        # Recursively search for and stop audio controls
        try:
            if isinstance(control, ft.Audio):
                try:
                    if hasattr(control, 'pause'):
                        control.pause()
                    if hasattr(control, 'release'):
                        control.release()
                    print(f"Stopped audio control in recursive search: {id(control)}")
                except Exception as ex:
                    print(f"Error stopping audio in recursive search: {ex}")
                return
            
            # Check if the control has controls attribute (like Column, Row, etc.)
            if hasattr(control, 'controls') and control.controls:
                for child in control.controls:
                    self._stop_audio_in_control(child)
            
            # Check if the control has content attribute (like Container)
            if hasattr(control, 'content') and control.content:
                self._stop_audio_in_control(control.content)
        except Exception as e:
            print(f"Error in _stop_audio_in_control: {e}")
    
    def stop_all_audio(self):
        # Stop all audio playback on the page
        try:
            # First, stop the current audio control if it exists
            if self.current_audio_control:
                try:
                    if hasattr(self.current_audio_control, 'pause'):
                        self.current_audio_control.pause()
                    if hasattr(self.current_audio_control, 'release'):
                        self.current_audio_control.release()
                    print(f"Stopped current audio control: {id(self.current_audio_control)}")
                except Exception as ex:
                    print(f"Error stopping current audio: {ex}")
            
            # Then check all page controls to find and stop any audio elements
            for control in self.page.controls:
                self._stop_audio_in_control(control)
            
            # Also check the content area specifically
            if self.content_area and hasattr(self.content_area, 'content'):
                self._stop_audio_in_control(self.content_area.content)
            
            # Clear the global tracking list
            self.active_audio_controls = []
            
            # Update playing state and button
            self.is_playing = False
            play_button = self.player_controls.controls[0].controls[1]
            play_button.icon = ft.icons.PLAY_ARROW
            play_button.data = "play"
            
            # Force a page update to ensure UI is consistent
            self.page.update()
        except Exception as e:
            print(f"Error in stop_all_audio: {e}")
    
    def stop_current_song(self, e):
        # Stop the current song and reset the player
        self.stop_all_audio()
        
        # Reset progress tracking
        self.current_position = 0
        self.song_duration = 0
        self.progress_slider.value = 0
        self.progress_slider.disabled = True
        self.update_time_display()
        
        self.page.update()
    
    def play_previous(self, e):
        # Play the previous song in the list or queue
        if not self.songs_list:
            return
        
        if self.queue:
