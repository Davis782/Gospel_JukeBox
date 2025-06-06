import flet as ft
import os
import shutil
import bcrypt
from datetime import datetime

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

class GospelJukeBox:
    def __init__(self, page: ft.Page):
        self.page = page
        self.page.title = "Gospel JukeBox"
        self.page.theme_mode = ft.ThemeMode.LIGHT
        self.page.padding = 20
        self.page.window_width = 1000
        self.page.window_height = 800
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
                
                media_list.append({
                    "name": file_name,
                    "media_file": media_path,
                    "text_file": text_file_path
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
                        media_list.append({
                            "name": folder_name,
                            "media_file": os.path.join(folder_path, media_files[0]),
                            "text_file": os.path.join(folder_path, text_files[0])
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
        
        # Create audio control with a unique ID for tracking
        audio_control = ft.Audio(
            src=self.current_song["media_file"],
            autoplay=False,  # Important: don't autoplay yet
            volume=1.0,
            on_state_changed=self.audio_state_changed
        )
        
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
            print(f"Error playing audio: {e}")
    
    def audio_state_changed(self, e):
        # Handle audio state changes (for autoplay functionality and progress tracking)
        print(f"Audio state changed: {e.data}")
        
        if e.data == "durationchange" and self.current_audio_control:
            # Update duration when it becomes available
            try:
                self.song_duration = self.current_audio_control.get_duration() / 1000  # Convert from ms to seconds
                # Ensure the slider's max value matches the song duration
                self.progress_slider.max = self.song_duration
                self.progress_slider.disabled = False
                self.update_time_display()
                self.page.update()
                print(f"Updated song duration: {self.song_duration} seconds")
            except Exception as ex:
                print(f"Error getting duration: {ex}")
        
        elif e.data == "timeupdate" and self.current_audio_control:
            # Update current position
            try:
                # Get the current position from the audio control
                current_ms = self.current_audio_control.get_current_position()
                self.current_position = current_ms / 1000  # Convert from ms to seconds
                
                # Ensure position is within valid range
                if self.current_position < 0:
                    self.current_position = 0
                elif self.current_position > self.song_duration and self.song_duration > 0:
                    self.current_position = self.song_duration
                
                # Update the slider to match the current position
                self.progress_slider.value = self.current_position
                # Update the time display with the current position
                self.update_time_display()
                
                # Check if we're near the end of the song (within 0.5 seconds) to ensure smooth transition
                if self.autoplay and self.current_position >= self.song_duration - 0.5 and self.song_duration > 0:
                    print("Near end of song, preparing for next song")
                    # This will ensure we don't trigger this multiple times
                    self.current_position = self.song_duration
                    self.progress_slider.value = self.song_duration
                    self.update_time_display()
                    # Force the "ended" event by seeking to the end
                    if hasattr(self.current_audio_control, 'seek'):
                        self.current_audio_control.seek(int(self.song_duration * 1000))
                
                # Force a page update to reflect changes in UI
                self.page.update()
            except Exception as ex:
                print(f"Error getting current time: {ex}")
        
        elif e.data == "play" or e.data == "playing":
            # When playback starts or resumes, ensure the slider position is in sync
            try:
                if self.current_audio_control:
                    current_ms = self.current_audio_control.get_current_position()
                    self.current_position = current_ms / 1000  # Convert from ms to seconds
                    self.progress_slider.value = self.current_position
                    self.update_time_display()
                    print(f"Updated position on play event: {self.current_position} seconds")
                    self.page.update()
            except Exception as ex:
                print(f"Error updating position on play event: {ex}")
        
        elif e.data == "pause":
            # When playback is paused, ensure the slider position is in sync
            try:
                if self.current_audio_control:
                    current_ms = self.current_audio_control.get_current_position()
                    self.current_position = current_ms / 1000  # Convert from ms to seconds
                    self.progress_slider.value = self.current_position
                    self.update_time_display()
                    print(f"Updated position on pause event: {self.current_position} seconds")
                    self.page.update()
            except Exception as ex:
                print(f"Error updating position on pause event: {ex}")
        
        elif e.data == "ended":
            # Reset position when song ends
            self.current_position = 0
            self.progress_slider.value = 0
            self.update_time_display()
            
            if self.autoplay and self.current_song:
                print("Song ended, autoplay is enabled. Playing next song.")
                # Ensure playing state is set to True for autoplay
                self.is_playing = True
                
                # Find the next song in the queue
                next_song_index = None
                
                # If queue is empty, use all songs
                if not self.queue:
                    self.queue = list(range(len(self.songs_list)))
                
                # Find the current song's position in the queue
                if self.current_song_index in self.queue:
                    current_queue_position = self.queue.index(self.current_song_index)
                    # Get the next song in the queue (wrap around if needed)
                    if current_queue_position < len(self.queue) - 1:
                        next_song_index = self.queue[current_queue_position + 1]
                    else:
                        # Loop back to the beginning of the queue if loop_queue is enabled
                        if self.loop_queue:
                            next_song_index = self.queue[0]
                            print("Looping back to first song in queue")
                        else:
                            # Stop playback if we reached the end of the queue and loop is disabled
                            self.is_playing = False
                            play_button = self.player_controls.controls[0].controls[1]
                            play_button.icon = ft.icons.PLAY_ARROW
                            play_button.data = "play"
                            self.page.update()
                            return
                else:
                    # Current song not in queue, start from the beginning of the queue
                    if self.queue:
                        next_song_index = self.queue[0]
                    else:
                        # Fallback: move to the next song in the list
                        next_song_index = (self.current_song_index + 1) % len(self.songs_list)
                
                # Play the next song
                if next_song_index is not None:
                    # First stop all audio playback to prevent multiple songs playing
                    try:
                        # Stop and release the current audio control if it exists
                        if self.current_audio_control:
                            try:
                                if hasattr(self.current_audio_control, 'pause'):
                                    self.current_audio_control.pause()
                                if hasattr(self.current_audio_control, 'release'):
                                    self.current_audio_control.release()
                                print(f"Stopped current audio control before autoplay: {id(self.current_audio_control)}")
                            except Exception as ex:
                                print(f"Error stopping current audio before autoplay: {ex}")
                        
                        # Master stop: check all page controls to find and stop any audio elements
                        print("Performing master audio stop before autoplay...")
                        # First check the content area which contains the audio control
                        if self.content_area and hasattr(self.content_area, 'content'):
                            self._stop_audio_in_control(self.content_area.content)
                            
                        # Then check all page controls as a fallback
                        for control in self.page.controls:
                            self._stop_audio_in_control(control)
                            
                        # Force a small delay to ensure audio has stopped
                        self.page.update()
                    except Exception as e:
                        print(f"Error in master audio stop before autoplay: {e}")
                    
                    # Now play the next song
                    self.current_song_index = next_song_index
                    self.select_song(self.current_song_index)
            else:
                print(f"Song ended but autoplay is {self.autoplay}")
                self.page.update()
    
    def play_previous(self, e):
        if not self.songs_list:
            return
        
        # Set playing state to true when previous button is pressed
        self.is_playing = True
        
        # Perform a complete audio stop to prevent multiple songs playing
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
            print("Performing master audio stop in play_previous...")
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
        
        # Find the previous song in the queue if autoplay is enabled
        if self.autoplay and self.queue:
            # Find the current song's position in the queue
            if self.current_song_index in self.queue:
                current_queue_position = self.queue.index(self.current_song_index)
                # Get the previous song in the queue (wrap around if needed)
                if current_queue_position > 0:
                    self.current_song_index = self.queue[current_queue_position - 1]
                else:
                    # Loop back to the end of the queue if loop_queue is enabled
                    if self.loop_queue:
                        self.current_song_index = self.queue[-1]
                    else:
                        # Stay on the first song if loop is disabled
                        pass
            else:
                # Current song not in queue, start from the end of the queue
                self.current_song_index = self.queue[-1]
        else:
            # Regular previous song behavior
            self.current_song_index = (self.current_song_index - 1) % len(self.songs_list)
            
        # Enable the slider for the new song
        self.progress_slider.disabled = False
        self.select_song(self.current_song_index)
        
        # Update play button to show pause icon since we're now playing
        play_button = self.player_controls.controls[0].controls[1]
        play_button.icon = ft.icons.PAUSE
        play_button.data = "pause"
        self.page.update()
    
    def play_next(self, e):
        if not self.songs_list:
            return
            
        # Set playing state to true when next button is pressed
        if e is not None:  # Only set if user clicked next (not from autoplay)
            self.is_playing = True
        # If this was triggered by autoplay (e is None), ensure playing state is maintained
        elif e is None and self.autoplay:
            self.is_playing = True
        
        # Perform a complete audio stop to prevent multiple songs playing
        try:
            # Stop and release the current audio control if it exists
            if self.current_audio_control:
                try:
                    if hasattr(self.current_audio_control, 'pause'):
                        self.current_audio_control.pause()
                    if hasattr(self.current_audio_control, 'release'):
                        self.current_audio_control.release()
                    print(f"Stopped current audio control in play_next: {id(self.current_audio_control)}")
                except Exception as ex:
                    print(f"Error stopping current audio in play_next: {ex}")
            
            # Master stop: check all page controls to find and stop any audio elements
            print("Performing master audio stop in play_next...")
            # First check the content area which contains the audio control
            if self.content_area and hasattr(self.content_area, 'content'):
                self._stop_audio_in_control(self.content_area.content)
                
            # Then check all page controls as a fallback
            for control in self.page.controls:
                self._stop_audio_in_control(control)
                
            # Force a small delay to ensure audio has stopped
            self.page.update()
        except Exception as e:
            print(f"Error in master audio stop in play_next: {e}")
        
        # Find the next song in the queue if autoplay is enabled
        if self.autoplay and self.queue:
            # Find the current song's position in the queue
            if self.current_song_index in self.queue:
                current_queue_position = self.queue.index(self.current_song_index)
                # Get the next song in the queue (wrap around if needed)
                if current_queue_position < len(self.queue) - 1:
                    self.current_song_index = self.queue[current_queue_position + 1]
                else:
                    # Loop back to the beginning of the queue if loop_queue is enabled
                    if self.loop_queue:
                        self.current_song_index = self.queue[0]
                    else:
                        # Stay on the last song if loop is disabled and we're at the end
                        if e is not None:  # Only advance if user clicked next
                            self.current_song_index = (self.current_song_index + 1) % len(self.songs_list)
            else:
                # Current song not in queue, start from the beginning of the queue
                self.current_song_index = self.queue[0]
        else:
            # Regular next song behavior
            self.current_song_index = (self.current_song_index + 1) % len(self.songs_list)
        
        # Enable the slider for the new song
        self.progress_slider.disabled = False
        self.select_song(self.current_song_index)
        
        # Update play button to show pause icon since we're now playing
        play_button = self.player_controls.controls[0].controls[1]
        play_button.icon = ft.icons.PAUSE
        play_button.data = "pause"
        self.page.update()
    
    def toggle_autoplay(self, e):
        self.autoplay = e.control.value
        
        # If autoplay is enabled but queue is empty, add all songs to queue
        if self.autoplay and not self.queue:
            self.queue = list(range(len(self.songs_list)))
            # Refresh the display to show queue status
            self.display_music_list()
    
    def toggle_queue(self, e, index):
        # Add or remove the song from the queue
        if e.control.value:
            if index not in self.queue:
                self.queue.append(index)
        else:
            if index in self.queue:
                self.queue.remove(index)
        
        # Sort the queue to maintain the original song order
        self.queue.sort()
        
    def seek_position(self, e):
        # Update the position when user drags the slider
        if self.current_audio_control and hasattr(self.current_audio_control, 'seek'):
            try:
                position = e.control.value
                # Ensure position is within valid range
                if position < 0:
                    position = 0
                elif position > self.song_duration:
                    position = self.song_duration
                    
                # Convert position from seconds to milliseconds for the seek method
                self.current_audio_control.seek(int(position * 1000))
                # Update current position to match slider position
                self.current_position = position
                # Update the time display with the new position
                self.update_time_display()
                
                print(f"Seeking to position: {position} seconds of {self.song_duration} seconds")
                
                # Check if user dragged to the end of the song (within 0.5 seconds of the end)
                if position >= self.song_duration - 0.5 and self.song_duration > 0:
                    print("Slider dragged to end of song, triggering end of song")
                    # Force the "ended" event by seeking to the end
                    if hasattr(self.current_audio_control, 'seek'):
                        self.current_audio_control.seek(int(self.song_duration * 1000))
                    
                    # If autoplay is enabled, play the next song
                    if self.autoplay:
                        # Reset position
                        self.current_position = 0
                        self.progress_slider.value = 0
                        # Play the next song
                        self.play_next(None)
                    else:
                        # If autoplay is not enabled, just stop at the end
                        self.current_position = self.song_duration
                        self.progress_slider.value = self.song_duration
                        self.update_time_display()
                        self.page.update()
                else:
                    # Update the page to reflect the time display change
                    self.page.update()
            except Exception as ex:
                print(f"Error seeking position: {ex}")
    
    def update_time_display(self):
        # Format time as minutes:seconds for current position
        current_min = int(self.current_position // 60)
        current_sec = int(self.current_position % 60)
        
        # Calculate remaining time
        remaining_time = max(0, self.song_duration - self.current_position)
        remaining_min = int(remaining_time // 60)
        remaining_sec = int(remaining_time % 60)
        
        # Update the time display text with current time and remaining time
        self.time_display.value = f"{current_min}:{current_sec:02d} / -{remaining_min}:{remaining_sec:02d}"
        # Print for debugging
        print(f"Time display updated: {current_min}:{current_sec:02d} / -{remaining_min}:{remaining_sec:02d}")
    
    def open_donation_link(self, e):
        # Open CashApp donation link
        self.page.launch_url("https://cash.app/$SolidBuildersInc")
    
    def show_login_dialog(self, e):
        # Show admin login dialog
        if self.is_admin:
            # If already logged in, log out
            self.is_admin = False
            self.admin_panel.visible = False
            self.page.update()
            return
            
        def close_dlg(e):
            dialog.open = False
            self.page.update()
        
        def try_login(e):
            username = username_field.value
            password = password_field.value
            
            if username == ADMIN_USERNAME and bcrypt.checkpw(password.encode(), ADMIN_PASSWORD_HASH):
                self.is_admin = True
                self.admin_panel.visible = True
                dialog.open = False
                self.page.update()
            else:
                error_text.value = "Invalid username or password"
                self.page.update()
        
        username_field = ft.TextField(label="Username")
        password_field = ft.TextField(label="Password", password=True)
        error_text = ft.Text("", color=ft.colors.RED)
        
        dialog = ft.AlertDialog(
            title=ft.Text("Admin Login"),
            content=ft.Column([
                username_field,
                password_field,
                error_text
            ], width=300, height=150),
            actions=[
                ft.TextButton("Cancel", on_click=close_dlg),
                ft.TextButton("Login", on_click=try_login)
            ],
            actions_alignment=ft.MainAxisAlignment.END
        )
        
        self.page.dialog = dialog
        dialog.open = True
        self.page.update()
    
    def toggle_theme(self, e):
        # Toggle between light and dark theme
        self.page.theme_mode = ft.ThemeMode.DARK if self.page.theme_mode == ft.ThemeMode.LIGHT else ft.ThemeMode.LIGHT
        
        # Update the theme toggle icon
        e.control.icon = ft.icons.DARK_MODE if self.page.theme_mode == ft.ThemeMode.LIGHT else ft.icons.LIGHT_MODE
        
        # Update the page to apply the theme change
        self.page.update()
    
    def toggle_loop(self, e):
        # Update loop_queue state
        self.loop_queue = e.control.value
        
        # If loop is enabled and autoplay is enabled, make sure we have a queue
        if self.loop_queue and self.autoplay and not self.queue:
            # Add all songs to queue if it's empty
            self.queue = list(range(len(self.songs_list)))
            # Refresh the display to show queue status
            self.display_music_list()
        
        print(f"Loop queue set to: {self.loop_queue}")
        self.page.update()
    
    def stop_current_song(self, e):
        # Stop the current song and reset player
        try:
            # Stop all tracked audio controls using our global list
            self.stop_all_audio()
            
            # Reset UI state
            self.is_playing = False
            self.current_position = 0
            self.progress_slider.value = 0
            self.progress_slider.disabled = True
            self.update_time_display()
            
            # Update play button icon
            play_button = self.player_controls.controls[0].controls[1]
            play_button.icon = ft.icons.PLAY_ARROW
            play_button.data = "play"
            
            # Set current_audio_control to None so toggle_play will create a new one
            self.current_audio_control = None
            
            self.page.update()
        except Exception as e:
            print(f"Error in master stop: {e}")
            
    def stop_all_audio(self):
        """Stop all tracked audio controls"""
        print(f"Stopping all {len(self.active_audio_controls)} tracked audio controls")
        
        # First, stop all tracked audio controls
        for audio in list(self.active_audio_controls):
            try:
                if hasattr(audio, 'pause'):
                    audio.pause()
                if hasattr(audio, 'release'):
                    audio.release()
                print(f"Stopped tracked audio control: {id(audio)}")
            except Exception as ex:
                print(f"Error stopping tracked audio: {ex}")
            
            # Remove from tracking list
            if audio in self.active_audio_controls:
                self.active_audio_controls.remove(audio)
        
        # As a fallback, also use the recursive method to find any untracked audio controls
        if self.content_area and hasattr(self.content_area, 'content'):
            self._stop_audio_in_control(self.content_area.content)
            
        for control in self.page.controls:
            self._stop_audio_in_control(control)
    
    def _stop_audio_in_control(self, control, exclude_control=None):
        # Recursively search for and stop all audio controls
        # exclude_control parameter allows skipping a specific control (useful when toggling play/pause)
        try:
            # Check if this control is an Audio control by checking its type name
            if control.__class__.__name__ == 'Audio':
                # Skip this control if it's the one we want to exclude
                if exclude_control is not None and id(control) == id(exclude_control):
                    print(f"Skipping excluded audio control: {id(control)}")
                    return
                    
                try:
                    if hasattr(control, 'pause'):
                        control.pause()
                    if hasattr(control, 'release'):
                        control.release()
                    print(f"Stopped an audio control: {id(control)}")
                    
                    # Add to tracking list if not already there
                    if control not in self.active_audio_controls:
                        self.active_audio_controls.append(control)
                        print(f"Added found audio control to tracking list: {id(control)}")
                    # Remove from tracking list if it's being stopped
                    elif control in self.active_audio_controls and exclude_control is None:
                        self.active_audio_controls.remove(control)
                        print(f"Removed audio control from tracking list: {id(control)}")
                except Exception as inner_ex:
                    print(f"Error stopping specific audio control: {inner_ex}")
            
            # Check if this control has controls property (like Container, Column, etc.)
            if hasattr(control, 'controls') and control.controls:
                for child in control.controls:
                    self._stop_audio_in_control(child, exclude_control)
                    
            # Check if this control has content property (like Container)
            if hasattr(control, 'content') and control.content:
                self._stop_audio_in_control(control.content, exclude_control)
                
            # Check for tabs and their content
            if hasattr(control, 'tabs') and control.tabs:
                for tab in control.tabs:
                    if hasattr(tab, 'content') and tab.content:
                        self._stop_audio_in_control(tab.content, exclude_control)
        except Exception as ex:
            print(f"Error in recursive audio stop: {ex}")
    
    def upload_type_changed(self, e):
        # Update UI based on selected upload type
        upload_type = self.upload_type_dropdown.value
        if upload_type == "mp3":
            self.media_file_picker.allowed_extensions = ["mp3"]
        else:  # picture
            self.media_file_picker.allowed_extensions = ["jpg", "jpeg", "png"]
    
    def media_file_picked(self, e):
        if e.files and len(e.files) > 0:
            self.media_file_path.value = e.files[0].name
            self.page.update()
    
    def lyrics_file_picked(self, e):
        if e.files and len(e.files) > 0:
            self.lyrics_file_path.value = e.files[0].name
            self.page.update()
    
    def upload_files(self, e):
        # Get values from form
        upload_type = self.upload_type_dropdown.value
        folder_name = self.folder_name_field.value
        
        # Validate inputs
        if not upload_type or not folder_name:
            self.page.snack_bar = ft.SnackBar(content=ft.Text("Please select content type and folder name"))
            self.page.snack_bar.open = True
            self.page.update()
            return
        
        # Check if files were selected
        if not hasattr(self.media_file_picker, "result") or not self.media_file_picker.result or not self.media_file_picker.result.files:
            self.page.snack_bar = ft.SnackBar(content=ft.Text("Please select a media file"))
            self.page.snack_bar.open = True
            self.page.update()
            return
            
        if not hasattr(self.lyrics_file_picker, "result") or not self.lyrics_file_picker.result or not self.lyrics_file_picker.result.files:
            self.page.snack_bar = ft.SnackBar(content=ft.Text("Please select a lyrics/description file"))
            self.page.snack_bar.open = True
            self.page.update()
            return
        
        # Create destination folder
        if upload_type == "mp3":
            dest_folder = os.path.join(MP3_DIR, folder_name)
        else:  # picture
            dest_folder = os.path.join(PICTURES_DIR, folder_name)
        
        os.makedirs(dest_folder, exist_ok=True)
        
        # Copy files to destination
        try:
            # Copy media file
            media_file = self.media_file_picker.result.files[0]
            media_ext = os.path.splitext(media_file.name)[1]
            media_dest = os.path.join(dest_folder, f"{folder_name}{media_ext}")
            shutil.copy(media_file.path, media_dest)
            
            # Copy lyrics/description file
            lyrics_file = self.lyrics_file_picker.result.files[0]
            lyrics_dest = os.path.join(dest_folder, "lyrics.txt" if upload_type == "mp3" else "description.txt")
            shutil.copy(lyrics_file.path, lyrics_dest)
            
            # Show success message
            self.page.snack_bar = ft.SnackBar(content=ft.Text(f"Files uploaded successfully to {folder_name}"))
            self.page.snack_bar.open = True
            
            # Reset form
            self.folder_name_field.value = ""
            self.media_file_path.value = "No file selected"
            self.lyrics_file_path.value = "No file selected"
            self.media_file_picker.result = None
            self.lyrics_file_picker.result = None
            
            # Reload content
            self.load_content()
            
        except Exception as e:
            self.page.snack_bar = ft.SnackBar(content=ft.Text(f"Error uploading files: {str(e)}"))
            self.page.snack_bar.open = True
            
        self.page.update()

# Main entry point
def main(page: ft.Page):
    
    app = GospelJukeBox(page)

ft.app(target=main)