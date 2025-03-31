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
os.makedirs(PICTURES_DIR, exist_ok=True)import os
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
                self.songs_list.append({"name": song_name, "path": filepath})
        
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
            self.songs_list.append({"name": song_name, "path": file})
        
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

# Main application
if __name__ == "__main__":
    root = tk.Tk()
    app = MusicPlayer(root)
    root.mainloop()

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
