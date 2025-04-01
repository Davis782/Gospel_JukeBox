import os
import sys
import subprocess
import pygame
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import time
import json
import random
from PIL import Image, ImageTk
import requests
from io import BytesIO
import re
import base64
import tempfile
# from pyvirtualdisplay import Display
# display = Display(visible=0, size=(800, 600))
# display.start()

# Your Tkinter code here

class MusicPlayer:
    def __init__(self, root):
        self.root = root
        self.root.title("Gospel JukeBox")
        self.root.geometry("800x600")
        self.root.configure(bg="#f0f0f0")
        
        # Initialize pygame mixer
        pygame.mixer.init()
        
        # Variables
        self.current_song = ""
        self.paused = False
        self.songs_list = []
        self.current_song_index = 0
        self.queue = []
        self.history = []
        self.repeat_mode = "no_repeat"  # Options: no_repeat, repeat_one, repeat_all
        self.shuffle_mode = False
        self.volume = 0.5
        self.current_temp_file = None
        pygame.mixer.music.set_volume(self.volume)
        
        # Create main frames
        self.sidebar_frame = tk.Frame(self.root, bg="#2c3e50", width=200)
        self.sidebar_frame.pack(side=tk.LEFT, fill=tk.Y)
        
        self.content_frame = tk.Frame(self.root, bg="#f0f0f0")
        self.content_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Create sidebar elements
        self.logo_label = tk.Label(self.sidebar_frame, text="Gospel JukeBox", font=("Helvetica", 16, "bold"), bg="#2c3e50", fg="white")
        self.logo_label.pack(pady=20)
        
        # Navigation buttons
        self.nav_buttons_frame = tk.Frame(self.sidebar_frame, bg="#2c3e50")
        self.nav_buttons_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.library_btn = tk.Button(self.nav_buttons_frame, text="Library", bg="#34495e", fg="white", bd=0, padx=10, pady=5, width=15, command=self.show_library)
        self.library_btn.pack(pady=5)
        
        self.queue_btn = tk.Button(self.nav_buttons_frame, text="Queue", bg="#34495e", fg="white", bd=0, padx=10, pady=5, width=15, command=self.show_queue)
        self.queue_btn.pack(pady=5)
        
        self.history_btn = tk.Button(self.nav_buttons_frame, text="History", bg="#34495e", fg="white", bd=0, padx=10, pady=5, width=15, command=self.show_history)
        self.history_btn.pack(pady=5)
        
        self.settings_btn = tk.Button(self.nav_buttons_frame, text="Settings", bg="#34495e", fg="white", bd=0, padx=10, pady=5, width=15, command=self.show_settings)
        self.settings_btn.pack(pady=5)
        
        # Now playing section in sidebar
        self.now_playing_frame = tk.Frame(self.sidebar_frame, bg="#2c3e50")
        self.now_playing_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=10)
        
        self.now_playing_label = tk.Label(self.now_playing_frame, text="Now Playing", font=("Helvetica", 10, "bold"), bg="#2c3e50", fg="white")
        self.now_playing_label.pack(pady=5)
        
        self.current_song_label = tk.Label(self.now_playing_frame, text="No song playing", font=("Helvetica", 8), bg="#2c3e50", fg="white", wraplength=180)
        self.current_song_label.pack(pady=5)
        
        # Content area - initially show library
        self.current_view = None
        
        # Player controls at the bottom
        self.controls_frame = tk.Frame(self.content_frame, bg="#ecf0f1", height=100)
        self.controls_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Progress bar
        self.progress_frame = tk.Frame(self.controls_frame, bg="#ecf0f1")
        self.progress_frame.pack(fill=tk.X, padx=20, pady=5)
        
        self.current_time_label = tk.Label(self.progress_frame, text="0:00", bg="#ecf0f1")
        self.current_time_label.pack(side=tk.LEFT, padx=5)
        
        self.progress_bar = ttk.Scale(self.progress_frame, from_=0, to=100, orient=tk.HORIZONTAL, command=self.seek, length=500)
        self.progress_bar.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)
        
        self.song_length_label = tk.Label(self.progress_frame, text="0:00", bg="#ecf0f1")
        self.song_length_label.pack(side=tk.LEFT, padx=5)
        
        # Control buttons
        self.buttons_frame = tk.Frame(self.controls_frame, bg="#ecf0f1")
        self.buttons_frame.pack(pady=10)
        
        self.shuffle_btn = tk.Button(self.buttons_frame, text="🔀", font=("Helvetica", 12), bg="#ecf0f1", bd=0, command=self.toggle_shuffle)
        self.shuffle_btn.grid(row=0, column=0, padx=10)
        
        self.prev_btn = tk.Button(self.buttons_frame, text="⏮", font=("Helvetica", 16), bg="#ecf0f1", bd=0, command=self.play_prev)
        self.prev_btn.grid(row=0, column=1, padx=10)
        
        self.play_pause_btn = tk.Button(self.buttons_frame, text="▶", font=("Helvetica", 16), bg="#ecf0f1", bd=0, command=self.play_pause)
        self.play_pause_btn.grid(row=0, column=2, padx=10)
        
        self.next_btn = tk.Button(self.buttons_frame, text="⏭", font=("Helvetica", 16), bg="#ecf0f1", bd=0, command=self.play_next)
        self.next_btn.grid(row=0, column=3, padx=10)
        
        self.repeat_btn = tk.Button(self.buttons_frame, text="🔁", font=("Helvetica", 12), bg="#ecf0f1", bd=0, command=self.toggle_repeat)
        self.repeat_btn.grid(row=0, column=4, padx=10)
        
        # Volume control
        self.volume_frame = tk.Frame(self.controls_frame, bg="#ecf0f1")
        self.volume_frame.pack(pady=5)
        
        self.volume_down_btn = tk.Button(self.volume_frame, text="🔉", font=("Helvetica", 12), bg="#ecf0f1", bd=0, command=self.volume_down)
        self.volume_down_btn.pack(side=tk.LEFT, padx=5)
        
        self.volume_scale = ttk.Scale(self.volume_frame, from_=0, to=1, orient=tk.HORIZONTAL, command=self.set_volume, value=self.volume, length=100)
        self.volume_scale.pack(side=tk.LEFT, padx=5)
        
        self.volume_up_btn = tk.Button(self.volume_frame, text="🔊", font=("Helvetica", 12), bg="#ecf0f1", bd=0, command=self.volume_up)
        self.volume_up_btn.pack(side=tk.LEFT, padx=5)
        
        # Initialize the library view
        self.show_library()
        
        # Start the progress update thread
        self.update_thread = threading.Thread(target=self.update_progress)
        self.update_thread.daemon = True
        self.update_thread.start()
        
        # Load songs from the default directory
        self.load_default_songs()
        
        # Load settings
        self.load_settings()
    
    def load_default_songs(self):
        # Default directory for songs
        default_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mp3_files")
        if os.path.exists(default_dir):
            self.load_songs_from_directory(default_dir)
    
    def load_songs_from_directory(self, directory):
        self.songs_list = []
        for filename in os.listdir(directory):
            if filename.endswith(".mp3"):
                filepath = os.path.join(directory, filename)
                song_name = os.path.splitext(filename)[0]
                
                # Read the MP3 file as binary data and encode it as base64
                try:
                    with open(filepath, 'rb') as f:
                        audio_data = f.read()
                        audio_base64 = base64.b64encode(audio_data).decode('utf-8')
                        self.songs_list.append({
                            "name": song_name, 
                            "path": filepath,  # Keep the path for reference
                            "audio_data": audio_base64  # Store the base64 encoded audio data
                        })
                except Exception as e:
                    print(f"Error loading {filepath}: {str(e)}")
        
        self.update_library_view()
    
    def show_library(self):
        if self.current_view == "library":
            return
        
        # Clear the content area
        for widget in self.content_frame.winfo_children():
            if widget != self.controls_frame:
                widget.destroy()
        
        # Create library view
        self.library_frame = tk.Frame(self.content_frame, bg="#f0f0f0")
        self.library_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Header
        header_frame = tk.Frame(self.library_frame, bg="#f0f0f0")
        header_frame.pack(fill=tk.X, pady=10)
        
        title_label = tk.Label(header_frame, text="Music Library", font=("Helvetica", 18, "bold"), bg="#f0f0f0")
        title_label.pack(side=tk.LEFT)
        
        add_btn = tk.Button(header_frame, text="Add Songs", bg="#3498db", fg="white", bd=0, padx=10, pady=5, command=self.add_songs)
        add_btn.pack(side=tk.RIGHT)
        
        # Search bar
        search_frame = tk.Frame(self.library_frame, bg="#f0f0f0")
        search_frame.pack(fill=tk.X, pady=10)
        
        search_label = tk.Label(search_frame, text="Search:", bg="#f0f0f0")
        search_label.pack(side=tk.LEFT, padx=5)
        
        self.search_var = tk.StringVar()
        self.search_var.trace("w", lambda name, index, mode, sv=self.search_var: self.search_songs(sv))
        search_entry = tk.Entry(search_frame, textvariable=self.search_var, width=30)
        search_entry.pack(side=tk.LEFT, padx=5)
        
        # Songs list
        songs_frame = tk.Frame(self.library_frame, bg="white")
        songs_frame.pack(fill=tk.BOTH, expand=True)
        
        # Scrollbar
        scrollbar = tk.Scrollbar(songs_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Songs listbox
        self.songs_listbox = tk.Listbox(songs_frame, bg="white", selectbackground="#3498db", selectforeground="white", font=("Helvetica", 10), height=20, yscrollcommand=scrollbar.set)
        self.songs_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.songs_listbox.yview)
        
        # Bind double-click event
        self.songs_listbox.bind("<Double-1>", self.play_selected_song)
        
        # Right-click menu
        self.song_menu = tk.Menu(self.songs_listbox, tearoff=0)
        self.song_menu.add_command(label="Play", command=self.play_selected_song)
        self.song_menu.add_command(label="Add to Queue", command=self.add_to_queue)
        self.song_menu.add_separator()
        self.song_menu.add_command(label="Remove from Library", command=self.remove_from_library)
        
        self.songs_listbox.bind("<Button-3>", self.show_song_menu)
        
        # Update the library view
        self.update_library_view()
        
        self.current_view = "library"
    
    def update_library_view(self):
        if hasattr(self, 'songs_listbox'):
            self.songs_listbox.delete(0, tk.END)
            for song in self.songs_list:
                self.songs_listbox.insert(tk.END, song["name"])
    
    def show_song_menu(self, event):
        try:
            index = self.songs_listbox.nearest(event.y)
            self.songs_listbox.selection_clear(0, tk.END)
            self.songs_listbox.selection_set(index)
            self.songs_listbox.activate(index)
            self.song_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.song_menu.grab_release()
    
    def add_songs(self):
        files = filedialog.askopenfilenames(filetypes=[("MP3 Files", "*.mp3")])
        for file in files:
            song_name = os.path.splitext(os.path.basename(file))[0]
            
            # Read the MP3 file as binary data and encode it as base64
            try:
                with open(file, 'rb') as f:
                    audio_data = f.read()
                    audio_base64 = base64.b64encode(audio_data).decode('utf-8')
                    self.songs_list.append({
                        "name": song_name, 
                        "path": file,  # Keep the path for reference
                        "audio_data": audio_base64  # Store the base64 encoded audio data
                    })
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load {song_name}: {str(e)}")
        
        self.update_library_view()
    
    def search_songs(self, search_var):
        search_term = search_var.get().lower()
        self.songs_listbox.delete(0, tk.END)
        
        for song in self.songs_list:
            if search_term in song["name"].lower():
                self.songs_listbox.insert(tk.END, song["name"])
    
    def play_selected_song(self, event=None):
        try:
            index = self.songs_listbox.curselection()[0]
            song = self.songs_list[index]
            self.play_song(song)
        except IndexError:
            pass
    
    def add_to_queue(self):
        try:
            index = self.songs_listbox.curselection()[0]
            song = self.songs_list[index]
            self.queue.append(song)
            messagebox.showinfo("Queue", f"Added '{song['name']}' to the queue")
        except IndexError:
            pass
    
    def remove_from_library(self):
        try:
            index = self.songs_listbox.curselection()[0]
            song = self.songs_list[index]
            self.songs_list.pop(index)
            self.update_library_view()
            messagebox.showinfo("Library", f"Removed '{song['name']}' from the library")
        except IndexError:
            pass
    
    def show_queue(self):
        if self.current_view == "queue":
            return
        
        # Clear the content area
        for widget in self.content_frame.winfo_children():
            if widget != self.controls_frame:
                widget.destroy()
        
        # Create queue view
        self.queue_frame = tk.Frame(self.content_frame, bg="#f0f0f0")
        self.queue_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Header
        header_frame = tk.Frame(self.queue_frame, bg="#f0f0f0")
        header_frame.pack(fill=tk.X, pady=10)
        
        title_label = tk.Label(header_frame, text="Queue", font=("Helvetica", 18, "bold"), bg="#f0f0f0")
        title_label.pack(side=tk.LEFT)
        
        clear_btn = tk.Button(header_frame, text="Clear Queue", bg="#e74c3c", fg="white", bd=0, padx=10, pady=5, command=self.clear_queue)
        clear_btn.pack(side=tk.RIGHT)
        
        # Queue list
        queue_list_frame = tk.Frame(self.queue_frame, bg="white")
        queue_list_frame.pack(fill=tk.BOTH, expand=True)
        
        # Scrollbar
        scrollbar = tk.Scrollbar(queue_list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Queue listbox
        self.queue_listbox = tk.Listbox(queue_list_frame, bg="white", selectbackground="#3498db", selectforeground="white", font=("Helvetica", 10), height=20, yscrollcommand=scrollbar.set)
        self.queue_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.queue_listbox.yview)
        
        # Bind double-click event
        self.queue_listbox.bind("<Double-1>", self.play_from_queue)
        
        # Right-click menu
        self.queue_menu = tk.Menu(self.queue_listbox, tearoff=0)
        self.queue_menu.add_command(label="Play", command=self.play_from_queue)
        self.queue_menu.add_command(label="Remove from Queue", command=self.remove_from_queue)
        
        self.queue_listbox.bind("<Button-3>", self.show_queue_menu)
        
        # Update the queue view
        self.update_queue_view()
        
        self.current_view = "queue"
    
    def update_queue_view(self):
        if hasattr(self, 'queue_listbox'):
            self.queue_listbox.delete(0, tk.END)
            for song in self.queue:
                self.queue_listbox.insert(tk.END, song["name"])
    
    def show_queue_menu(self, event):
        try:
            index = self.queue_listbox.nearest(event.y)
            self.queue_listbox.selection_clear(0, tk.END)
            self.queue_listbox.selection_set(index)
            self.queue_listbox.activate(index)
            self.queue_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.queue_menu.grab_release()
    
    def play_from_queue(self, event=None):
        try:
            index = self.queue_listbox.curselection()[0]
            song = self.queue.pop(index)
            self.play_song(song)
            self.update_queue_view()
        except IndexError:
            pass
    
    def remove_from_queue(self):
        try:
            index = self.queue_listbox.curselection()[0]
            song = self.queue.pop(index)
            self.update_queue_view()
            messagebox.showinfo("Queue", f"Removed '{song['name']}' from the queue")
        except IndexError:
            pass
    
    def clear_queue(self):
        self.queue = []
        self.update_queue_view()
        messagebox.showinfo("Queue", "Queue cleared")
    
    def show_history(self):
        if self.current_view == "history":
            return
        
        # Clear the content area
        for widget in self.content_frame.winfo_children():
            if widget != self.controls_frame:
                widget.destroy()
        
        # Create history view
        self.history_frame = tk.Frame(self.content_frame, bg="#f0f0f0")
        self.history_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Header
        header_frame = tk.Frame(self.history_frame, bg="#f0f0f0")
        header_frame.pack(fill=tk.X, pady=10)
        
        title_label = tk.Label(header_frame, text="History", font=("Helvetica", 18, "bold"), bg="#f0f0f0")
        title_label.pack(side=tk.LEFT)
        
        clear_btn = tk.Button(header_frame, text="Clear History", bg="#e74c3c", fg="white", bd=0, padx=10, pady=5, command=self.clear_history)
        clear_btn.pack(side=tk.RIGHT)
        
        # History list
        history_list_frame = tk.Frame(self.history_frame, bg="white")
        history_list_frame.pack(fill=tk.BOTH, expand=True)
        
        # Scrollbar
        scrollbar = tk.Scrollbar(history_list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # History listbox
        self.history_listbox = tk.Listbox(history_list_frame, bg="white", selectbackground="#3498db", selectforeground="white", font=("Helvetica", 10), height=20, yscrollcommand=scrollbar.set)
        self.history_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.history_listbox.yview)
        
        # Bind double-click event
        self.history_listbox.bind("<Double-1>", self.play_from_history)
        
        # Right-click menu
        self.history_menu = tk.Menu(self.history_listbox, tearoff=0)
        self.history_menu.add_command(label="Play", command=self.play_from_history)
        self.history_menu.add_command(label="Add to Queue", command=self.add_from_history_to_queue)
        
        self.history_listbox.bind("<Button-3>", self.show_history_menu)
        
        # Update the history view
        self.update_history_view()
        
        self.current_view = "history"
    
    def update_history_view(self):
        if hasattr(self, 'history_listbox'):
            self.history_listbox.delete(0, tk.END)
            for song in reversed(self.history):  # Show most recent first
                self.history_listbox.insert(tk.END, song["name"])
    
    def show_history_menu(self, event):
        try:
            index = self.history_listbox.nearest(event.y)
            self.history_listbox.selection_clear(0, tk.END)
            self.history_listbox.selection_set(index)
            self.history_listbox.activate(index)
            self.history_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.history_menu.grab_release()
    
    def play_from_history(self, event=None):
        try:
            index = self.history_listbox.curselection()[0]
            # Get song from reversed history (most recent first)
            song = list(reversed(self.history))[index]
            self.play_song(song)
        except IndexError:
            pass
    
    def add_from_history_to_queue(self):
        try:
            index = self.history_listbox.curselection()[0]
            # Get song from reversed history (most recent first)
            song = list(reversed(self.history))[index]
            self.queue.append(song)
            messagebox.showinfo("Queue", f"Added '{song['name']}' to the queue")
        except IndexError:
            pass
    
    def clear_history(self):
        self.history = []
        self.update_history_view()
        messagebox.showinfo("History", "History cleared")
    
    def show_settings(self):
        if self.current_view == "settings":
            return
        
        # Clear the content area
        for widget in self.content_frame.winfo_children():
            if widget != self.controls_frame:
                widget.destroy()
        
        # Create settings view
        self.settings_frame = tk.Frame(self.content_frame, bg="#f0f0f0")
        self.settings_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Header
        header_frame = tk.Frame(self.settings_frame, bg="#f0f0f0")
        header_frame.pack(fill=tk.X, pady=10)
        
        title_label = tk.Label(header_frame, text="Settings", font=("Helvetica", 18, "bold"), bg="#f0f0f0")
        title_label.pack(side=tk.LEFT)
        
        # Settings options
        options_frame = tk.Frame(self.settings_frame, bg="white", padx=20, pady=20)
        options_frame.pack(fill=tk.BOTH, expand=True)
        
        # Theme selection
        theme_frame = tk.Frame(options_frame, bg="white")
        theme_frame.pack(fill=tk.X, pady=10)
        
        theme_label = tk.Label(theme_frame, text="Theme:", bg="white", font=("Helvetica", 10, "bold"))
        theme_label.grid(row=0, column=0, sticky="w", padx=5, pady=5)
        
        
        self.theme_var = tk.StringVar(value="light")
        light_radio = tk.Radiobutton(theme_frame, text="Light", variable=self.theme_var, value="light", bg="white", command=self.apply_theme)
        light_radio.grid(row=0, column=1, sticky="w", padx=5, pady=5)
        
        dark_radio = tk.Radiobutton(theme_frame, text="Dark", variable=self.theme_var, value="dark", bg="white", command=self.apply_theme)
        dark_radio.grid(row=0, column=2, sticky="w", padx=5, pady=5)
        
        # Default directory
        dir_frame = tk.Frame(options_frame, bg="white")
        dir_frame.pack(fill=tk.X, pady=10)
        
        dir_label = tk.Label(dir_frame, text="Default Music Directory:", bg="white", font=("Helvetica", 10, "bold"))
        dir_label.grid(row=0, column=0, sticky="w", padx=5, pady=5)
        
        self.dir_var = tk.StringVar()
        dir_entry = tk.Entry(dir_frame, textvariable=self.dir_var, width=30)
        dir_entry.grid(row=0, column=1, sticky="w", padx=5, pady=5)
        
        browse_btn = tk.Button(dir_frame, text="Browse", command=self.browse_directory)
        browse_btn.grid(row=0, column=2, sticky="w", padx=5, pady=5)
        
        # Save settings button
        save_btn = tk.Button(options_frame, text="Save Settings", bg="#3498db", fg="white", bd=0, padx=10, pady=5, command=self.save_settings)
        save_btn.pack(pady=20)
        
        # Load current settings
        self.load_settings_to_view()
        
        self.current_view = "settings"
    
    def browse_directory(self):
        directory = filedialog.askdirectory()
        if directory:
            self.dir_var.set(directory)
    
    def apply_theme(self):
        theme = self.theme_var.get()
        if theme == "dark":
            # Apply dark theme
            self.root.configure(bg="#2c3e50")
            self.content_frame.configure(bg="#34495e")
            # Add more theme changes here
        else:
            # Apply light theme
            self.root.configure(bg="#f0f0f0")
            self.content_frame.configure(bg="#f0f0f0")
            # Add more theme changes here
    
    def save_settings(self):
        settings = {
            "theme": self.theme_var.get(),
            "default_dir": self.dir_var.get(),
            "volume": self.volume,
            "repeat_mode": self.repeat_mode,
            "shuffle_mode": self.shuffle_mode
        }
        
        try:
            with open("settings.json", "w") as f:
                json.dump(settings, f)
            messagebox.showinfo("Settings", "Settings saved successfully")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save settings: {str(e)}")
    
    def load_settings(self):
        try:
            with open("settings.json", "r") as f:
                settings = json.load(f)
                
                # Apply settings
                self.theme_var.set(settings.get("theme", "light"))
                self.dir_var.set(settings.get("default_dir", ""))
                self.volume = settings.get("volume", 0.5)
                self.repeat_mode = settings.get("repeat_mode", "no_repeat")
                self.shuffle_mode = settings.get("shuffle_mode", False)
                
                # Apply theme
                self.apply_theme()
                
                # Apply volume
                pygame.mixer.music.set_volume(self.volume)
                self.volume_scale.set(self.volume)
                
                # Load songs from default directory
                default_dir = settings.get("default_dir", "")
                if default_dir and os.path.exists(default_dir):
                    self.load_songs_from_directory(default_dir)
        except FileNotFoundError:
            # No settings file found, use defaults
            pass
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load settings: {str(e)}")
    
    def load_settings_to_view(self):
        if hasattr(self, 'dir_var'):
            self.dir_var.set(os.path.join(os.path.dirname(os.path.abspath(__file__)), "mp3_files"))
    
    def play_song(self, song):
        try:
            # Clean up previous temporary file if it exists
            self.cleanup_temp_file()
            
            if "audio_data" in song:
                # Decode the base64 audio data
                audio_bytes = base64.b64decode(song["audio_data"])
                
                # Create a temporary file to store the decoded audio data
                # Use a unique filename based on song name to avoid conflicts
                temp_dir = tempfile.gettempdir()
                temp_path = os.path.join(temp_dir, f"temp_audio_{hash(song['name'])}.mp3")
                
                with open(temp_path, 'wb') as temp_file:
                    temp_file.write(audio_bytes)
                
                # Load the audio file using pygame
                pygame.mixer.music.load(temp_path)
                pygame.mixer.music.play()
                
                # Store the temp path for later cleanup
                self.current_temp_file = temp_path
            else:
                # Fallback to traditional path-based loading if audio_data is not available
                pygame.mixer.music.load(song["path"])
                pygame.mixer.music.play()
            
            self.current_song = song["name"]
            self.current_song_label.config(text=song["name"])
            self.play_pause_btn.config(text="⏸")
            self.paused = False
            
            # Add to history
            self.history.append(song)
            if self.current_view == "history":
                self.update_history_view()
            
            # Update current song index
            for i, s in enumerate(self.songs_list):
                if s["path"] == song["path"]:
                    self.current_song_index = i
                    break
        except Exception as e:
            messagebox.showerror("Error", f"Failed to play song: {str(e)}")
    
    def play_pause(self):
        if self.current_song:
            if self.paused:
                pygame.mixer.music.unpause()
                self.play_pause_btn.config(text="⏸")
                self.paused = False
            else:
                pygame.mixer.music.pause()
                self.play_pause_btn.config(text="▶")
                self.paused = True
        elif self.songs_list:
            self.play_song(self.songs_list[0])
    
    def play_next(self):
        if self.shuffle_mode:
            if self.songs_list:
                next_index = random.randint(0, len(self.songs_list) - 1)
                self.play_song(self.songs_list[next_index])
        elif self.queue:
            # Play next song from queue
            next_song = self.queue.pop(0)
            self.play_song(next_song)
            if self.current_view == "queue":
                self.update_queue_view()
        elif self.repeat_mode == "repeat_one" and self.current_song:
            # Replay current song
            current_song = self.songs_list[self.current_song_index]
            self.play_song(current_song)
        elif self.songs_list:
            # Play next song in playlist
            next_index = (self.current_song_index + 1) % len(self.songs_list)
            self.play_song(self.songs_list[next_index])
    
    def play_prev(self):
        if self.songs_list:
            prev_index = (self.current_song_index - 1) % len(self.songs_list)
            self.play_song(self.songs_list[prev_index])
    
    def toggle_repeat(self):
        if self.repeat_mode == "no_repeat":
            self.repeat_mode = "repeat_all"
            self.repeat_btn.config(text="🔁")
        elif self.repeat_mode == "repeat_all":
            self.repeat_mode = "repeat_one"
            self.repeat_btn.config(text="🔂")
        else:
            self.repeat_mode = "no_repeat"
            self.repeat_btn.config(text="🔁")
    
    def toggle_shuffle(self):
        self.shuffle_mode = not self.shuffle_mode
        if self.shuffle_mode:
            self.shuffle_btn.config(bg="#3498db")
        else:
            self.shuffle_btn.config(bg="#ecf0f1")
    
    def set_volume(self, val):
        self.volume = float(val)
        pygame.mixer.music.set_volume(self.volume)
    
    def volume_up(self):
        self.volume = min(1.0, self.volume + 0.1)
        self.volume_scale.set(self.volume)
        pygame.mixer.music.set_volume(self.volume)
    
    def volume_down(self):
        self.volume = max(0.0, self.volume - 0.1)
        self.volume_scale.set(self.volume)
        pygame.mixer.music.set_volume(self.volume)
    
    def seek(self, val):
        pass  # Implement seeking functionality
    
    def update_progress(self):
        while True:
            if self.current_song and not self.paused and pygame.mixer.music.get_busy():
                # Update progress bar
                pass
            elif self.current_song and not self.paused and not pygame.mixer.music.get_busy():
                # Song ended, play next
                self.play_next()
            time.sleep(0.1)

    def cleanup_temp_file(self):
        """Clean up temporary audio file"""
        if hasattr(self, 'current_temp_file') and self.current_temp_file and os.path.exists(self.current_temp_file):
            try:
                os.remove(self.current_temp_file)
                self.current_temp_file = None
            except Exception as e:
                print(f"Error removing temp file: {e}")

# Main application
def is_headless():
    """Check if the script is running in a headless environment"""
    return os.environ.get('DISPLAY', '') == ''

if __name__ == "__main__":
    # Check if we need a virtual display
    display = None
    
    # Check for command line arguments
    if '--headless' in sys.argv:
        print("Running in headless mode...")
        try:
            from pyvirtualdisplay import Display
            
            # Start virtual display
            display = Display(visible=0, size=(800, 600))
            display.start()
            print(f"Virtual display started with ID: {display.display}")
            
        except ImportError:
            print("PyVirtualDisplay not installed. Installing...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", "pyvirtualdisplay"])
            from pyvirtualdisplay import Display
            display = Display(visible=0, size=(800, 600))
            display.start()
        except Exception as e:
            print(f"Error starting virtual display: {e}")
            print("Xvfb might not be installed on this system.")
            print("On Linux systems, install with: sudo apt-get install xvfb")
            print("On Windows, this approach may not work as Xvfb is not natively supported.")
            sys.exit(1)
    
    try:
        # Tkinter application
        root = tk.Tk()
        app = MusicPlayer(root)
        
        # Add cleanup on window close
        def on_closing():
            app.cleanup_temp_file()
            root.destroy()
            
        root.protocol("WM_DELETE_WINDOW", on_closing)
        root.mainloop()
    finally:
        # Clean up any temporary files
        if 'app' in locals():
            app.cleanup_temp_file()
            
        # Stop virtual display
        if display:
            print("Stopping virtual display...")
            display.stop()
