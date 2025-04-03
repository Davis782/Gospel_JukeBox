import flet as ft
import os
from playsound import playsound

class AudioPlayerApp:
    def __init__(self, page: ft.Page):
        self.page = page
        self.page.title = "Audio Player"
        self.page.padding = 20
        self.mp3_directory = "mp3_files"

        # Ensure the directory exists
        if not os.path.exists(self.mp3_directory):
            os.makedirs(self.mp3_directory)

        self.display_audio_files()

    def display_audio_files(self):
        """Display the list of MP3 files and create buttons for playback."""
        mp3_files = sorted([f for f in os.listdir(self.mp3_directory) if f.endswith('.mp3')])

        if not mp3_files:
            self.page.add(ft.Text(f"No MP3 files found in the directory '{self.mp3_directory}'."))
            return

        for mp3_file in mp3_files:
            file_path = os.path.join(self.mp3_directory, mp3_file)

            # Create a button for each MP3 file
            play_button = ft.ElevatedButton(
                text=f"Play {mp3_file}",
                on_click=lambda e, path=file_path: self.play_audio(path)
            )
            self.page.add(play_button)

    def play_audio(self, file_path):
        """Play the selected audio file."""
        try:
            playsound(file_path)
        except Exception as e:
            self.page.add(ft.Text(f"Error playing audio: {e}"))

def main(page: ft.Page):
    AudioPlayerApp(page)

# Run the app
ft.app(target=main)
