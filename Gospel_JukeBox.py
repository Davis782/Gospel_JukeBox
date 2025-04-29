import os
import base64
import sqlite3
import streamlit as st
from datetime import datetime
import matplotlib.pyplot as plt
from streamlit import components
from supabase import create_client, Client


# Load environment variables and initialize Supabase client
load_dotenv('.env')  # explicitly load from .env file
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Set page configuration
st.set_page_config(
    page_title="Gospel JukeBox",
    page_icon="🎵",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Define application paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MP3_DIR = os.path.join(BASE_DIR, "mp3_files")
PICTURES_DIR = os.path.join(BASE_DIR, "pictures")
os.makedirs(MP3_DIR, exist_ok=True)
os.makedirs(PICTURES_DIR, exist_ok=True)
os.makedirs(os.path.join(PICTURES_DIR, "sheet_music"), exist_ok=True)

# Initialize SQLite database for votes, sheet music, and users
def init_db():
    conn = sqlite3.connect('Gospel_Jukebox.db')
    cursor = conn.cursor()
    
    # Create votes table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS votes (
            song_name TEXT,
            vote INTEGER
        )
    ''')
    
    # Create instrument sheet music table
    cursor.execute('''
        -- Updated schema: added 'label' column for multi-type sheet music support (2025-04-21)
        -- Updated schema: added 'creator_username' column for permission management (2025-04-22)
        CREATE TABLE IF NOT EXISTS instrument_sheet_music (
            song_name TEXT,
            instrument TEXT,
            label TEXT,
            file_path TEXT,
            creator_username TEXT,
            PRIMARY KEY (song_name, instrument, label)
        )
    ''')
    
    # Create song notes table to store user/admin notes
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS song_notes (
            song_name TEXT,
            username TEXT,
            label TEXT,
            notes TEXT,
            last_updated TEXT,
            PRIMARY KEY (song_name, username, label)
        )
    ''')
    
    # Create users table for authentication
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT,
            is_admin INTEGER DEFAULT 0
        )
    ''')
    
    # --- MIGRATION: Add 'is_admin' column if missing for legacy DBs ---
    cursor.execute("PRAGMA table_info(users)")
    columns = [col[1] for col in cursor.fetchall()]
    if 'is_admin' not in columns:
        cursor.execute("ALTER TABLE users ADD COLUMN is_admin INTEGER DEFAULT 0")
    
    # Add default admin user if not exists
    cursor.execute("SELECT * FROM users WHERE username = 'admin'")
    if not cursor.fetchone():
        # Simple password storage for demo purposes
        # In production, use password hashing
        cursor.execute("PRAGMA table_info(users)")
        cols = [col[1] for col in cursor.fetchall()]
        if 'role' in cols:
            cursor.execute("INSERT INTO users (username, password, is_admin, role) VALUES (?, ?, ?, ?)", ('admin', 'admin123', 1, 'admin'))
        else:
            cursor.execute("INSERT INTO users (username, password, is_admin) VALUES (?, ?, ?)", ('admin', 'admin123', 1))
    
    # --- MIGRATION: Add 'label' and 'creator_username' columns if missing (for legacy DBs) ---
    try:
        cursor.execute("PRAGMA table_info(instrument_sheet_music)")
        columns = [row[1] for row in cursor.fetchall()]
        if 'label' not in columns:
            cursor.execute("ALTER TABLE instrument_sheet_music ADD COLUMN label TEXT DEFAULT ''")
            # Rebuild primary key if needed (requires manual intervention if not empty)
            # For now, just add the column for compatibility.
        if 'creator_username' not in columns:
            cursor.execute("ALTER TABLE instrument_sheet_music ADD COLUMN creator_username TEXT DEFAULT ''")
    except Exception as e:
        print(f"Migration warning: {e}")
    conn.commit()
    conn.close()

# Initialize the database
init_db()

# Define available instruments
AVAILABLE_INSTRUMENTS = [
    "Lead_Guitar", 
    "Bass", 
    "Piano", 
    "Drums", 
    "Trumpet", 
    "Saxophone"
]

# --- Label Management Helper Functions ---
def get_labels_for_song_instrument(song_name, instrument):
    """Return a list of (label, creator_username) for a given song/instrument."""
    conn = sqlite3.connect('Gospel_Jukebox.db')
    cursor = conn.cursor()
    cursor.execute("SELECT label, creator_username FROM instrument_sheet_music WHERE song_name = ? AND instrument = ?", (song_name, instrument))
    labels = [(row[0], row[1] if row[1] else 'Unknown') for row in cursor.fetchall() if row[0]]
    conn.close()
    return labels

def add_label(song_name, instrument, label, creator_username):
    """Add a new label for a song/instrument."""
    conn = sqlite3.connect('Gospel_Jukebox.db')
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR IGNORE INTO instrument_sheet_music (song_name, instrument, label, file_path, creator_username) VALUES (?, ?, ?, ?, ?)",
        (song_name, instrument, label, '', creator_username)
    )
    conn.commit()
    conn.close()

def delete_label(song_name, instrument, label):
    """Delete a label for a song/instrument."""
    conn = sqlite3.connect('Gospel_Jukebox.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM instrument_sheet_music WHERE song_name = ? AND instrument = ? AND label = ?", (song_name, instrument, label))
    conn.commit()
    conn.close()

def get_label_notes(song_name, instrument, label):
    """Return all notes for a song/instrument/label as a list of (username, notes, last_updated)."""
    conn = sqlite3.connect('Gospel_Jukebox.db')
    cursor = conn.cursor()
    cursor.execute("SELECT username, notes, last_updated FROM song_notes WHERE song_name = ? AND label = ?", (song_name, label))
    notes = cursor.fetchall()
    conn.close()
    return notes
# --- End Label Management Helpers ---

# Initialize Supabase connection if environment variables are available
SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY')
USE_SUPABASE = SUPABASE_URL and SUPABASE_KEY

# If using Supabase, import the library
if USE_SUPABASE:
    try:
        import supabase
        from supabase import create_client, Client
        supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("Supabase client initialized successfully")
    except ImportError:
        print("Supabase library not installed. Run: pip install supabase")
        USE_SUPABASE = False
    except Exception as e:
        print(f"Error initializing Supabase client: {e}")
        USE_SUPABASE = False

# Initialize session state
defaults = {
    'queue': [],
    'history': [],
    'current_song': None,
    'current_lyrics': None,
    'play_time': None,
    'song_notes': {},
    'audio_playing': False,
    'audio_data': None,
    'current_playback_time': 0,
    'autoplay': False,
    'replay': False,
    'song_ended': False,
    'view_notes': True,  # Toggle between Notes and Sheet Music
    'queue_updated': False,  # Flag for UI refresh
    'selected_instrument': AVAILABLE_INSTRUMENTS[0],  # Default to first instrument
    'selected_label': None,  # Currently selected sheet music label
    'last_check_time': datetime.now(),  # For the 20-second timer loop
    'check_interval': 10,  # Check interval in seconds (reduced for more responsive autoplay)
    'song_start_timestamp': None,  # Full timestamp when song started
    'estimated_song_duration': 180,  # Default estimated song duration in seconds (3 minutes)
    'force_next_song': False,  # Flag to force playing the next song
    'logged_in': False,  # User login status
    'username': None,  # Current logged in username
    'is_admin': False,  # Admin privileges flag
    'use_supabase': USE_SUPABASE  # Flag to indicate if Supabase is being used
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value

def encode_audio_to_base64(file_path):
    """Encode audio to base64."""
    with open(file_path, "rb") as audio_file:
        return base64.b64encode(audio_file.read()).decode('utf-8')

def play_audio(file_path, song_name):
    """Play an audio file. Ensures play button is always responsive."""
    # Always reset audio state for new playback
    st.session_state.audio_playing = False
    st.session_state.current_song = None
    st.session_state.audio_data = None
    # DO NOT reset or modify st.session_state.queue here!
    # Now set new state
    st.session_state.audio_data = encode_audio_to_base64(file_path)
    st.session_state.audio_playing = True
    st.session_state.current_song = song_name
    st.session_state.play_time = datetime.now().strftime("%H:%M:%S")
    st.session_state.song_start_timestamp = datetime.now()  # Store full timestamp
    st.session_state.current_playback_time = 0
    st.session_state.current_lyrics = load_lyrics(file_path)
    st.session_state.song_ended = False  # Reset song ended flag when starting a new song
    st.session_state.force_next_song = False  # Reset force next flag when starting a new song
    # Debug information for song playback
    print(f"Started playing: {song_name} at {st.session_state.play_time}")
    print(f"Estimated duration: {st.session_state.estimated_song_duration} seconds")
    if song_name not in st.session_state.history:
        st.session_state.history.append(song_name)
        st.session_state.history = st.session_state.history[-10:]

def load_content():
    """Load songs from directories."""
    return sorted(f for f in os.listdir(MP3_DIR) if f.endswith('.mp3'))

def load_lyrics(file_path):
    """Load lyrics from a corresponding text file."""
    text_file_path = os.path.splitext(file_path)[0] + '.txt'
    return open(text_file_path).read() if os.path.exists(text_file_path) else "No lyrics available."

def add_to_queue(song_name):
    """Add a song to the queue dynamically without full page refresh, preserving order and uniqueness."""
    # Only add if not already present to preserve order and uniqueness
    if song_name not in st.session_state.queue:
        st.session_state.queue.append(song_name)
        st.session_state.queue_updated = True
        st.session_state['autoplay_queue_empty_warned'] = False
        try:
            st.rerun()
        except AttributeError:
            st.warning("st.rerun() is not available in this Streamlit version. Please upgrade Streamlit.")
        return True
    return False

def play_from_queue(index, remove_after_playing=True):
    """Play a song from the queue. Removes it unless told not to (for replay mode or Next Song button)."""
    if 0 <= index < len(st.session_state.queue):
        song_name = st.session_state.queue[index]
        play_audio(os.path.join(MP3_DIR, song_name), song_name)
        # If force_next_song_active is True, do NOT remove from queue (manual next song)
        # If force_next_song_active is False (autoplay), DO remove from queue
        if remove_after_playing:
            if not st.session_state.get('force_next_song_active', False):
                st.session_state.queue.pop(index)
                print(f"[DEBUG] Removed {song_name} from queue.")
            else:
                print(f"[DEBUG] Did NOT remove {song_name} from queue due to manual next song.")
        print(f"[DEBUG] Queue after play_from_queue: {st.session_state.queue}")

def display_mp3_player():
    """Display the MP3 player in the sidebar."""
    
    # Get current time
    current_time = datetime.now()
    
    # Check if song has ended on every Streamlit refresh
    # This makes the autoplay more responsive than the 20-second interval
    if st.session_state.audio_playing and st.session_state.current_song and st.session_state.song_start_timestamp:
        # Calculate how long the song has been playing
        song_play_duration = (current_time - st.session_state.song_start_timestamp).total_seconds()
        
        # If song has been playing longer than the estimated duration, mark it as ended
        if song_play_duration >= st.session_state.estimated_song_duration:
            st.session_state.song_ended = True
            print(f"Song ended detection: {st.session_state.current_song} played for {song_play_duration} seconds")


        
        # Also keep the duration-based detection as a fallback
        elif song_play_duration >= st.session_state.estimated_song_duration:
            st.session_state.song_ended = True
            # Log that we detected song end
            print(f"Song ended detection: {st.session_state.current_song} played for {song_play_duration} seconds")
    
    # Also keep the interval check as a backup method
    time_diff = (current_time - st.session_state.last_check_time).total_seconds()
    if time_diff >= st.session_state.check_interval:
        # Update last check time
        st.session_state.last_check_time = current_time
        print(f"{st.session_state.check_interval}-second interval check: Last check time updated")
        
        # Force song end check on interval as a backup method
        if st.session_state.audio_playing and st.session_state.current_song and st.session_state.song_start_timestamp:
            song_play_duration = (current_time - st.session_state.song_start_timestamp).total_seconds()
            print(f"Interval check: Song {st.session_state.current_song} has been playing for {song_play_duration:.1f} seconds")
            
            # If song has been playing for a while, consider forcing next song
            if song_play_duration >= st.session_state.estimated_song_duration - 10:  # 10 seconds before estimated end
                st.session_state.force_next_song = True
                print("Forcing next song flag set to True")
    
    # If song ended or force_next_song flag is set, handle next steps
    if st.session_state.song_ended or st.session_state.force_next_song:
        print(f"Song ended or force next detected, checking for autoplay. Song ended: {st.session_state.song_ended}, Force next: {st.session_state.force_next_song}")
        # Always reset flags after use
        st.session_state.song_ended = False
        st.session_state.force_next_song = False

        if st.session_state.autoplay:
            if st.session_state.queue:
                print(f"Autoplay enabled, playing next song from queue: {st.session_state.queue[0]}")
                # Only set force_next_song_active for manual next, not autoplay
                st.session_state['force_next_song_active'] = False
                play_from_queue(0, remove_after_playing=not st.session_state.replay)
                st.session_state['force_next_song_active'] = False  # Always reset after playing
                st.success("Autoplay: Started next song in queue")
                try:
                    st.rerun()
                except AttributeError:
                    st.warning("st.rerun() is not available in this Streamlit version. Please upgrade Streamlit.")
            else:
                # Only warn and log if not already warned
                if not st.session_state.get('autoplay_queue_empty_warned', False):
                    print("Autoplay enabled but queue is empty")
                    st.warning("Autoplay is on, but there are no songs in the queue")
                    st.session_state['autoplay_queue_empty_warned'] = True
                # Stop playback to break infinite loop
                st.session_state.audio_playing = False
        else:
            print("Autoplay is disabled")
            st.info("Song ended. Enable autoplay to automatically play the next song.")


    with st.sidebar:
        st.title("Gospel JukeBox ")

        # Display Currently Playing Song
        if st.session_state.audio_playing and st.session_state.current_song:
            st.markdown("### Now Playing")
            # Show the current song name clearly above the audio player
            col_song, col_btn = st.columns([4, 1])
            with col_song:
                st.markdown(f"#### {st.session_state.current_song.replace('.mp3','')}")
            with col_btn:
                if st.session_state.get('current_lyrics'):
                    show_lyrics = st.session_state.get('show_lyrics_in_sidebar', False)
                    if st.button("Hide Lyrics" if show_lyrics else "Show Lyrics", key="show_lyrics_btn"):
                        st.session_state['show_lyrics_in_sidebar'] = not show_lyrics

            # Use HTML5 audio element with autoplay, controls, and ended event listener
            audio_html = """
            <audio id="audio-player" autoplay controls>
                <source src="data:audio/mpeg;base64,{0}" type="audio/mpeg">
                Your browser does not support the audio element.
            </audio>
            <script>
                // Ensure autoplay works
                const audioPlayer = document.getElementById('audio-player');
                audioPlayer.play();
                
                // Add ended event listener to detect when song actually ends
                audioPlayer.addEventListener('ended', function() {{
                    // Set a flag in the DOM that Streamlit can check
                    const songEndedFlag = document.createElement('div');
                    songEndedFlag.id = 'song-ended-flag';
                    songEndedFlag.style.display = 'none';
                    songEndedFlag.innerText = 'true';
                    document.body.appendChild(songEndedFlag);
                    
                    // Force a page refresh to trigger the next song
                    window.parent.postMessage({{type: 'streamlit:forceRerun'}}, '*');
                }});
            </script>
            """.format(st.session_state.audio_data)
            st.components.v1.html(audio_html, height=80)

            # Display lyrics in sidebar if requested
            if st.session_state.get('show_lyrics_in_sidebar') and st.session_state.get('current_lyrics'):
                st.markdown(f"**Lyrics for {st.session_state.current_song.replace('.mp3','')}**")
                st.markdown(st.session_state.current_lyrics)


        # Navigation Buttons
        if st.button("Previous"):
            current_index = st.session_state.queue.index(st.session_state.current_song) if st.session_state.current_song in st.session_state.queue else -1
            if current_index > 0:
                play_from_queue(current_index - 1)
        if st.button("Next"):
            current_index = st.session_state.queue.index(st.session_state.current_song) if st.session_state.current_song in st.session_state.queue else -1
            if current_index >= 0 and current_index < len(st.session_state.queue) - 1:
                play_from_queue(current_index + 1)

        # Manual trigger for next song (Force Next Song)
        if st.button("Force Next Song"):
            print(f"[DEBUG] Force Next Song pressed. Queue before: {st.session_state.queue}")
            if st.session_state.queue:
                st.session_state['force_next_song_active'] = True  # Only set here!
                st.session_state.force_next_song = True
                try:
                    st.rerun()
                except AttributeError:
                    st.warning("st.rerun() is not available in this Streamlit version. Please upgrade Streamlit.")
            else:
                print("[DEBUG] Force Next Song pressed but queue is empty.")

        # Display Queue
        st.markdown("### Current Queue")
        if st.session_state.queue:
            for i, song in enumerate(st.session_state.queue):
                # Display only the play button with the song name as the label
                if st.button(song.replace('.mp3', ''), key=f"sidebar_play_queue_{i}"): # Added sidebar prefix to key for uniqueness
                    play_from_queue(i, remove_after_playing=not st.session_state.replay)
        else:
            st.write("Queue is empty.")

        # Replay and Autoplay Toggles
        st.session_state.replay = st.checkbox("Replay", value=st.session_state.replay)
        st.session_state.autoplay = st.checkbox("Autoplay Next Song", value=st.session_state.autoplay)
        
        # Display countdown timer for next song with enhanced information
        if st.session_state.audio_playing and st.session_state.current_song and st.session_state.song_start_timestamp:
            # Calculate initial values for display
            current_time = datetime.now()
            song_play_duration = (current_time - st.session_state.song_start_timestamp).total_seconds()
            remaining_time = max(0, st.session_state.estimated_song_duration - song_play_duration)
            
            # Format times as MM:SS for initial display
            minutes_elapsed = int(song_play_duration // 60)
            seconds_elapsed = int(song_play_duration % 60)
            elapsed_display = f"{minutes_elapsed:02d}:{seconds_elapsed:02d}"
            
            minutes_remaining = int(remaining_time // 60)
            seconds_remaining = int(remaining_time % 60)
            remaining_display = f"{minutes_remaining:02d}:{seconds_remaining:02d}"
            
            minutes_total = int(st.session_state.estimated_song_duration // 60)
            seconds_total = int(st.session_state.estimated_song_duration % 60)
            total_display = f"{minutes_total:02d}:{seconds_total:02d}"
            
            # Create a progress bar for visual feedback
            progress = min(1.0, song_play_duration / st.session_state.estimated_song_duration)
            progress_bar = st.progress(progress)
            
            # Create a container for the countdown display
            countdown_container = st.empty()
            message_container = st.empty()
            caption_container = st.empty()
            
            # Create JavaScript-based auto-updating timer
            # This will update the countdown without requiring user interaction
            start_time_ms = int(st.session_state.song_start_timestamp.timestamp() * 1000)
            estimated_duration_ms = st.session_state.estimated_song_duration * 1000
            
            # Determine the message to display based on autoplay setting and queue status
            autoplay_enabled = "true" if st.session_state.autoplay else "false"
            has_queue = "true" if st.session_state.queue else "false"
            
            # Create HTML component with JavaScript for auto-updating timer
            timer_html = """
            <div id="timer-display" style="font-family: sans-serif; margin-bottom: 10px;"></div>
            <div id="message-display" style="font-family: sans-serif; font-weight: bold;"></div>
            <div id="caption-display" style="font-family: sans-serif; font-size: 0.8em; color: #666;"></div>
            <div id="progress-container" style="display: none;">0</div>
            
            <script>
                // Timer configuration
                const startTimeMs = {0};
                const estimatedDurationMs = {1};
                const autoplayEnabled = {2};
                const hasQueue = {3};
                
                // Function to format time as MM:SS
                function formatTime(seconds) {{
                    const mins = Math.floor(seconds / 60);
                    const secs = Math.floor(seconds % 60);
                    return `${{mins.toString().padStart(2, '0')}}:${{secs.toString().padStart(2, '0')}}`;
                }}
                
                // Function to update the timer display
                function updateTimer() {{
                    const currentTimeMs = new Date().getTime();
                    const elapsedTimeMs = currentTimeMs - startTimeMs;
                    const elapsedTimeSec = elapsedTimeMs / 1000;
                    const remainingTimeSec = Math.max(0, {4} - elapsedTimeSec);
                    const totalTimeSec = {4};
                    
                    // Update progress
                    const progress = Math.min(1.0, elapsedTimeSec / totalTimeSec);
                    document.getElementById('progress-container').innerText = progress.toFixed(4);
                    
                    // Update elapsed/total time display
                    document.getElementById('timer-display').innerHTML = 
                        `<strong>Current Song Time</strong>: ${{formatTime(elapsedTimeSec)}} / ${{formatTime(totalTimeSec)}}`;
                    
                    // Update message based on remaining time and settings
                    let messageHTML = '';
                    let captionText = '';
                    
                    if (remainingTimeSec <= 0) {{
                        // Song has reached its estimated end time
                        if (autoplayEnabled && hasQueue) {{
                            messageHTML = `<span style='color:green'>Next song should be playing now!</span>`;
                            captionText = `If music hasn't changed, click 'Force Next Song' above`;
                        }} else if (autoplayEnabled && !hasQueue) {{
                            messageHTML = `<span style='color:orange'>Song has ended!</span>`;
                            captionText = `No songs in queue for autoplay`;
                        }} else {{
                            messageHTML = `<span style='color:orange'>Song has ended!</span>`;
                            captionText = `Autoplay is disabled. Please select the next song manually.`;
                        }}
                    }} else {{
                        // Song is still playing
                        if (autoplayEnabled && hasQueue) {{
                            messageHTML = `Next song in: ${{formatTime(remainingTimeSec)}}`;
                            captionText = `Autoplay will start the next song automatically`;
                        }} else if (autoplayEnabled && !hasQueue) {{
                            messageHTML = `Song ends in: ${{formatTime(remainingTimeSec)}}`;
                            captionText = `No songs in queue for autoplay`;
                        }} else {{
                            messageHTML = `Song ends in: ${{formatTime(remainingTimeSec)}}`;
                            captionText = `Autoplay is disabled`;
                        }}
                    }}
                    
                    document.getElementById('message-display').innerHTML = messageHTML;
                    document.getElementById('caption-display').innerText = captionText;
                }}
                
                // Update immediately and then every 1 second
                updateTimer();
                setInterval(updateTimer, 1000);
            </script>
            """.format(start_time_ms, estimated_duration_ms, autoplay_enabled, has_queue, st.session_state.estimated_song_duration)
            
            # Display the auto-updating timer
            st.components.v1.html(timer_html, height=100)
            
            # JavaScript to Python communication for progress bar updates
            # This is a workaround since we can't directly update Streamlit elements from JavaScript
            # We'll use a periodic check to update the progress bar based on the JavaScript calculation
            js_progress_html = """
            <script>
                // Function to periodically update the progress value in the DOM
                function updateProgressValue() {
                    const progressContainer = document.getElementById('progress-container');
                    if (progressContainer) {
                        const currentTimeMs = new Date().getTime();
                        const elapsedTimeMs = currentTimeMs - %s;
                        const elapsedTimeSec = elapsedTimeMs / 1000;
                        const progress = Math.min(1.0, elapsedTimeSec / %s);
                        progressContainer.innerText = progress.toFixed(4);
                    }
                    setTimeout(updateProgressValue, 500); // Update twice per second
                }
                updateProgressValue();
            </script>
            """ % (start_time_ms, st.session_state.estimated_song_duration)
            
            st.components.v1.html(js_progress_html, height=0)
            # Add a small spacer
            st.write("")
    
    # Manual trigger for next song (useful if autoplay doesn't trigger automatically)
    if st.button("Force Next Song", key="force_next_song_btn"):
        print(f"[DEBUG] Force Next Song pressed. Queue before: {st.session_state.queue}")
        if st.session_state.queue:
            st.session_state['force_next_song_active'] = True  # Only set here!
            st.session_state.force_next_song = True
            try:
                st.rerun()
            except AttributeError:
                st.warning("st.rerun() is not available in this Streamlit version. Please upgrade Streamlit.")
        else:
            print("[DEBUG] Force Next Song pressed but queue is empty.")

    # Display Queue
    st.markdown("### Current Queue")
    if st.session_state.queue:
        for i, song in enumerate(st.session_state.queue):
            if st.button(song.replace('.mp3', ''), key=f"play_queue_{i}_{song}"):
                play_from_queue(i, remove_after_playing=not st.session_state.replay)
    else:
        st.write("Queue is empty.")

def display_music_library():
    """Display the music library page."""
    st.header("Music Library")
    mp3_files = load_content()

    # Add search functionality
    search_query = st.text_input("Search songs by title, sheet music label, or note label", "")
    
    # Filter songs based on search query
    if search_query:
        # First search by song title
        filtered_songs = [song for song in mp3_files if search_query.lower() in song.lower()]
        
        # Always search by label in the database, regardless of whether we found matches by title
        conn = sqlite3.connect('Gospel_Jukebox.db')
        cursor = conn.cursor()
        cursor.execute(
            "SELECT DISTINCT song_name FROM instrument_sheet_music WHERE label LIKE ?", 
            (f'%{search_query}%',)
        )
        label_matches = [f"{row[0]}" for row in cursor.fetchall() if f"{row[0]}" in mp3_files]
        conn.close()
        
        # Also search by note labels in song_notes
        conn = sqlite3.connect('Gospel_Jukebox.db')
        cursor = conn.cursor()
        cursor.execute(
            "SELECT DISTINCT song_name FROM song_notes WHERE label LIKE ?", (f'%{search_query}%',)
        )
        note_matches = [row[0] for row in cursor.fetchall() if row[0] in mp3_files]
        conn.close()
        
        # Combine results from both searches and remove duplicates
        filtered_songs = list(set(filtered_songs + label_matches + note_matches))
        
        # Display which songs were found by label if any were found this way
        if label_matches and not any(search_query.lower() in song.lower() for song in label_matches):
            st.info(f"Found {len(label_matches)} song(s) with label matching '{search_query}' click dropdown below to view")
        # Inform user about note label matches
        if note_matches and not any(search_query.lower() in song.lower() for song in note_matches):
            st.info(f"Found {len(note_matches)} song(s) with note label matching '{search_query}', click dropdown to view")
    else:
        filtered_songs = mp3_files
    
    if not filtered_songs and search_query:
        st.warning(f"No songs found matching '{search_query}' in titles or labels")
        # Keep filtered_songs empty to show the warning, but still allow selection from all songs
        filtered_songs = mp3_files  # Show all songs if no matches
    
    selected_song = st.selectbox("Select a song to play", options=filtered_songs)

    # Create a row with three columns for the buttons
    col1, col2, col3 = st.columns([1, 1, 1])

    with col1:
        # Button state logic
        if 'song_btn_state' not in st.session_state:
            st.session_state.song_btn_state = 'idle'
        if 'last_selected_song' not in st.session_state:
            st.session_state.last_selected_song = None

        # Reset button state if playback started or song changed
        if st.session_state.audio_playing and st.session_state.current_song == selected_song:
            st.session_state.song_btn_state = 'idle'
        elif st.session_state.last_selected_song != selected_song:
            st.session_state.song_btn_state = 'idle'
            st.session_state.last_selected_song = selected_song

        # Button text and style
        if st.session_state.song_btn_state == 'lyrics_loaded':
            play_btn_label = 'Lyrics loaded, press again to play'
            play_btn_tooltip = 'Lyrics loaded. Press again to play music.'
            play_btn_style = "background-color: white; color: green; border: 2px solid green; border-radius: 5px; font-weight: bold; width: 100%;"
        else:
            play_btn_label = 'Play Selected Song'
            play_btn_tooltip = 'Select a song and press to load lyrics.'
            play_btn_style = ""

        # Button text and style
        # Multi-step button flow: idle -> show_lyrics -> play_song
        if 'song_btn_state' not in st.session_state:
            st.session_state.song_btn_state = 'idle'
        if 'last_selected_song' not in st.session_state:
            st.session_state.last_selected_song = None

        # Reset if playback started or song changed
        if st.session_state.audio_playing and st.session_state.current_song == selected_song:
            st.session_state.song_btn_state = 'idle'
        elif st.session_state.last_selected_song != selected_song:
            st.session_state.song_btn_state = 'idle'
            st.session_state.last_selected_song = selected_song

        # Button label and style for each step
        if st.session_state.song_btn_state == 'idle':
            play_btn_label = 'Play Selected Song'
            play_btn_style = ""
        elif st.session_state.song_btn_state == 'show_lyrics':
            play_btn_label = 'Lyrics Loaded, Press Again to Show Lyrics'
            play_btn_style = "background-color: white; color: green; border: 2px solid green; border-radius: 5px; font-weight: bold; width: 100%;"
        elif st.session_state.song_btn_state == 'play_song':
            play_btn_label = 'Lyrics Loaded, Press Again to Play Song'
            play_btn_style = "background-color: white; color: green; border: 2px solid green; border-radius: 5px; font-weight: bold; width: 100%;"
        else:
            play_btn_label = 'Play Selected Song'
            play_btn_style = ""

        play_btn_kwargs = {"key": "play_selected_song_btn"}

        if st.button(play_btn_label, **play_btn_kwargs) and selected_song:
            if st.session_state.song_btn_state == 'idle':
                # First press: move to show_lyrics
                st.session_state.song_btn_state = 'show_lyrics'
                st.session_state.last_selected_song = selected_song
                try:
                    st.rerun()
                except AttributeError:
                    st.warning("st.rerun() is not available in this Streamlit version. Please upgrade Streamlit or interact with the UI to refresh.")
            elif st.session_state.song_btn_state == 'show_lyrics':
                # Second press: update lyrics and move to play_song
                file_path = os.path.join(MP3_DIR, selected_song)
                st.session_state.current_lyrics = load_lyrics(file_path)
                st.session_state.song_btn_state = 'play_song'
                st.session_state.last_selected_song = selected_song
                try:
                    st.rerun()
                except AttributeError:
                    st.warning("st.rerun() is not available in this Streamlit version. Please upgrade Streamlit or interact with the UI to refresh.")
            elif st.session_state.song_btn_state == 'play_song':
                # Third press: play song
                if selected_song in st.session_state.queue:
                    idx = st.session_state.queue.index(selected_song)
                    play_from_queue(idx, remove_after_playing=not st.session_state.replay)
                else:
                    play_audio(os.path.join(MP3_DIR, selected_song), selected_song)
                st.session_state.song_btn_state = 'idle'

            if st.session_state.song_btn_state == 'lyrics_loaded':
                # Play the song now
                if selected_song in st.session_state.queue:
                    idx = st.session_state.queue.index(selected_song)
                    play_from_queue(idx, remove_after_playing=not st.session_state.replay)
                else:
                    play_audio(os.path.join(MP3_DIR, selected_song), selected_song)
                st.session_state.song_btn_state = 'idle'
            else:
                # First press: load lyrics
                st.session_state.song_btn_state = 'lyrics_loaded'
                st.session_state.last_selected_song = selected_song
                try:
                    st.rerun()
                except AttributeError:
                    st.warning("st.rerun() is not available in this Streamlit version. Please upgrade Streamlit or interact with the UI to refresh.")

    
    with col2:
        if st.button(" Add to Queue") and selected_song:
            if add_to_queue(selected_song):
                st.success(f"{selected_song} added to queue.")
            else:
                st.info(f"{selected_song} is already in queue.")
    
    with col3:
        # CashApp button
        cash_app_link = "https://cash.app/$SolidBuildersInc"
        st.button("Donate via CashApp", on_click=lambda: webbrowser.open(cash_app_link))

    show_lyrics_state = st.session_state.get('song_btn_state') in ['show_lyrics', 'play_song']
    if st.session_state.current_song or show_lyrics_state:
        st.session_state.current_song = selected_song  # ensure current song is set for DB queries
        st.subheader(f" {selected_song.replace('.mp3', '')}")
        if st.session_state.audio_playing and st.session_state.current_song:
            st.write(f"Started playing at: {st.session_state.play_time}")

        # The audio player is now only shown in the sidebar to avoid playback conflicts.
        # (Removed audio player from main area to prevent stopping music when interacting with main screen.)

        # Toggle between Notes and Sheet Music
        st.session_state.view_notes = st.checkbox("View Notes Instead of Sheet Music", value=st.session_state.view_notes)

        # Split view
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### Lyrics")
            st.write(f'<div style="height:250px;overflow-y:scroll;">{st.session_state.current_lyrics}</div>', unsafe_allow_html=True)

        with col2:
            if st.session_state.view_notes:
                st.markdown("### Notes")
                current_song_name = st.session_state.current_song
                is_logged_in = st.session_state.get('logged_in', False)
                current_username = st.session_state.get('username', None)
                is_admin = st.session_state.get('is_admin', False)

                # --- Display All Existing Notes --- 
                conn = sqlite3.connect('Gospel_Jukebox.db')
                cursor = conn.cursor()
                # Fetch username, label, and notes content
                cursor.execute("SELECT username, label, notes FROM song_notes WHERE song_name = ? ORDER BY username, label", (current_song_name,))
                all_notes = cursor.fetchall()
                conn.close()

                if all_notes:
                    # Prepare filtered notes by label
                    unique_labels = sorted({lbl for _, lbl, _ in all_notes if lbl})
                    note_view_mode = st.radio(
                        "Existing Notes View", ["All notes", "Labels only", "Filter by label"], index=0, key="note_view_mode_radio"
                    )
                    if note_view_mode == "Labels only":
                        st.markdown("**Note Labels:**")
                        if unique_labels:
                            for lbl in unique_labels:
                                st.write(f"- {lbl}")
                        else:
                            st.info("No labels to display.")
                    else:
                        # Determine which notes to show
                        if note_view_mode == "Filter by label" and unique_labels:
                            selected_note_label = st.selectbox(
                                "Select label to filter notes", unique_labels, key="note_label_filter_select"
                            )
                            filtered_notes = [item for item in all_notes if item[1] == selected_note_label]
                        else:
                            filtered_notes = all_notes

                        st.markdown("**Existing Notes:**")
                        notes_container = st.container()  # Use a container for better layout control
                        with notes_container:
                            for user, label, note_content in filtered_notes:
                                display_label = label if label else '[No Label]'
                                # Display each note in a read-only text area within the container
                                st.text_area(
                                    f"Note by {user} ({display_label})", 
                                    value=note_content if note_content else "", 
                                    height=100, 
                                    key=f"note_display_{user}_{label}", 
                                    disabled=True # Make it read-only for now
                                )
                                st.markdown("--- *end of note* ---") # Separator
                else:
                    st.info("No notes found for this song yet.")

                # --- Add New Note Section (Logged-in Users Only) ---

                # --- Add New Note Section (Logged-in Users Only) ---
                if is_logged_in:
                    st.markdown("---")
                    st.markdown("#### Add Your Note")
                    with st.form(key='add_note_form'):
                        new_note_label = st.text_input("Note Label (e.g., 'Verse 1 Chords', 'Performance Idea')", key="new_note_label")
                        new_note_content = st.text_area("Note Content", height=100, key="new_note_content")
                        submit_new_note = st.form_submit_button("Save New Note")

                        if submit_new_note:
                            if not new_note_label.strip() or not new_note_content.strip():
                                st.warning("Both Label and Content are required to save a new note.")
                            else:
                                conn = sqlite3.connect('Gospel_Jukebox.db')
                                cursor = conn.cursor()
                                # Check if a note with the same user and label already exists for this song
                                cursor.execute("SELECT 1 FROM song_notes WHERE song_name = ? AND username = ? AND label = ?", 
                                               (current_song_name, current_username, new_note_label))
                                exists = cursor.fetchone()
                                if exists:
                                    st.error(f"You already have a note with the label '{new_note_label}' for this song. Please choose a different label or edit the existing one.")
                                else:
                                    cursor.execute("INSERT INTO song_notes (song_name, username, label, notes, last_updated) VALUES (?, ?, ?, ?, ?)",
                                        (current_song_name, current_username, new_note_label, new_note_content, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                                    )
                                    conn.commit()
                                    st.success(f"New note with label '{new_note_label}' saved!")
                                    # Clear form fields after successful submission is tricky with st.form, 
                                    # usually requires rerun or session state management.
                                    # For simplicity, we just show success and let rerun handle refresh.
                                    try: st.rerun() # Refresh to show the new note in the dropdown
                                    except: pass 
                                conn.close()
                elif not all_notes: # Only show if not logged in AND no notes exist
                     st.info("Log in to add notes for this song.")

                # --- Notes Management Section (Admins Only) ---
                if is_admin:
                    st.markdown("---")
                    st.markdown("#### All Notes for this Song (Admin Management)")
                    conn = sqlite3.connect('Gospel_Jukebox.db')
                    cursor = conn.cursor()
                    cursor.execute("SELECT username, label, notes, last_updated FROM song_notes WHERE song_name = ?", (current_song_name,))
                    note_entries = cursor.fetchall()
                    conn.close()
                    if note_entries:
                        for note_user, note_label, note_text, note_time in note_entries:
                            # Use unique keys for delete buttons within the loop
                            delete_key = f"delete_note_{note_user}_{note_label}_{current_song_name}"
                            col_n1, col_n2, col_n3, col_n4 = st.columns([2, 2, 6, 2])
                            with col_n1:
                                st.write(f"User: {note_user}")
                            with col_n2:
                                st.write(f"Label: {note_label if note_label else '[No Label]'}")
                            with col_n3:
                                st.write(f"{note_text}")
                            with col_n4:
                                if st.button(f"Delete", key=delete_key):
                                    conn = sqlite3.connect('Gospel_Jukebox.db')
                                    cursor = conn.cursor()
                                    cursor.execute("DELETE FROM song_notes WHERE song_name = ? AND username = ? AND label = ?", (current_song_name, note_user, note_label))
                                    conn.commit()
                                    conn.close()
                                    st.success(f"Note for user '{note_user}', label '{note_label}' deleted!")
                                    try: 
                                        st.rerun() # Refresh the page to reflect deletion
                                    except AttributeError:
                                        st.warning("Note deleted! Please manually refresh the page to see the update (st.rerun() is not available).")
                                    except Exception as e:
                                        st.error(f"Error deleting note: {e}")
                    else:
                        st.info("No notes found for admin management.")
            else:
                # Sheet Music Display with Instrument Selection
                st.markdown("### Sheet Music")
                
                # Instrument and label selection dropdowns side by side
                col1, col2 = st.columns(2)
                with col1:
                    selected_instrument = st.selectbox(
                        "Select Instrument", 
                        AVAILABLE_INSTRUMENTS,
                        index=AVAILABLE_INSTRUMENTS.index(st.session_state.selected_instrument)
                    )
                with col2:
                    # Fetch sheet music entries with creator information
                    conn = sqlite3.connect('Gospel_Jukebox.db')
                    cursor = conn.cursor()
                    cursor.execute(
                        "SELECT label, creator_username FROM instrument_sheet_music WHERE song_name = ? AND instrument = ?",
                        (st.session_state.current_song, st.session_state.selected_instrument)
                    )
                    sheet_music_entries = cursor.fetchall()
                    conn.close()
                    
                    # Initialize unique_labels and label_to_creator
                    unique_labels = []
                    label_to_creator = {}
                    
                    for label, creator in sheet_music_entries:
                        if label and label.strip() and label not in unique_labels:
                            unique_labels.append(label)
                            label_to_creator[label] = creator if creator else 'Unknown'
                    
                    # Use session state to remember selected label
                    if st.session_state.selected_label is None or st.session_state.selected_label not in unique_labels:
                        st.session_state.selected_label = unique_labels[0] if unique_labels else None
                    
                    # Display the label selector
                    selected_label = st.selectbox(
                        "Select Sheet Music Type", 
                        unique_labels, 
                        index=unique_labels.index(st.session_state.selected_label) if st.session_state.selected_label in unique_labels else 0,
                        key="sheet_music_label_select"
                    )
                    st.session_state.selected_label = selected_label
                    
                    # Display label creator information
                    if selected_label:
                        st.write(f"Created by: {label_to_creator[selected_label]}")
                    
                # Update session state with selected instrument
                if selected_instrument != st.session_state.selected_instrument:
                    st.session_state.selected_instrument = selected_instrument
                    st.session_state.selected_label = None  # Reset label when instrument changes
                    try:
                        st.rerun()  # Refresh to apply the instrument change
                    except AttributeError:
                        st.warning("st.rerun() is not available in this Streamlit version. Please upgrade Streamlit.")
                
                # Display sheet music if available
                if selected_label:
                    conn = sqlite3.connect('Gospel_Jukebox.db')
                    cursor = conn.cursor()
                    cursor.execute(
                        "SELECT file_path FROM instrument_sheet_music WHERE song_name = ? AND instrument = ? AND label = ?",
                        (st.session_state.current_song, st.session_state.selected_instrument, selected_label)
                    )
                    file_path = cursor.fetchone()[0] if cursor.fetchone() else None
                    conn.close()
                    
                    if file_path and os.path.exists(file_path):
                        st.image(file_path, caption=f"{st.session_state.selected_instrument} - {selected_label}", use_column_width=True)
                    else:
                        st.info(f"No sheet music file uploaded for '{selected_label}'.")
                
                # Admin controls for label management
                if st.session_state.get('logged_in', False) and st.session_state.get('is_admin', False):
                    st.markdown("---")
                    st.subheader("Manage Sheet Music Labels")
                    
                    # Add new sheet music type/label
                    new_label = st.text_input("Add New Sheet Music Type (Label)", key="add_sheet_music_label")
                    if st.button("Add Type", key="add_sheet_music_label_btn"):
                        if new_label.strip():
                            # Prevent duplicate label for this song/instrument
                            if new_label.strip() in unique_labels:
                                st.warning(f"Label '{new_label.strip()}' already exists for this song/instrument. Please use a unique label.")
                            else:
                                st.write("(No permission)")

            # --- Notes Management Section (admins) ---
            if st.session_state.get('logged_in', False) and st.session_state.get('is_admin', False):
                st.markdown("---")
                st.markdown("#### Notes for this Song (Admin Management)")
                # Add new sheet music type/label
                new_label = st.text_input("Add New Sheet Music Type (Label)", key="add_sheet_music_label")
                if st.button("Add Type", key="add_sheet_music_label_btn"):
                    if new_label.strip():
                        # Make sure unique_labels is defined in this code path
                        if 'unique_labels' not in locals():
                            # Fetch labels if not already done
                            conn = sqlite3.connect('Gospel_Jukebox.db')
                            cursor = conn.cursor()
                            cursor.execute(
                                "SELECT label FROM instrument_sheet_music WHERE song_name = ? AND instrument = ?",
                                (st.session_state.current_song, st.session_state.selected_instrument)
                            )
                            unique_labels = [row[0] for row in cursor.fetchall() if row[0]]
                            conn.close()
                        
                        # Prevent duplicate label for this song/instrument
                        if new_label.strip() in unique_labels:
                            st.warning(f"Label '{new_label.strip()}' already exists for this song/instrument.")
                        else:
                            # Get current username for creator attribution
                            creator = st.session_state.get('username', '')
                            
                            if st.session_state.get('use_supabase', False):
                                try:
                                    # Insert into Supabase
                                    data = {
                                        'song_name': st.session_state.current_song,
                                        'instrument': st.session_state.selected_instrument,
                                        'label': new_label.strip(),
                                        'file_path': "",
                                        'creator_username': creator
                                    }
                                    supabase_client.table('instrument_sheet_music').insert(data).execute()
                                    st.success(f"Sheet music type '{new_label.strip()}' added to Supabase!")
                                except Exception as e:
                                    st.error(f"Supabase error: {e}")
                                    # Fall back to SQLite if Supabase fails
                                    st.warning("Falling back to local database...")
                                    conn = sqlite3.connect('Gospel_Jukebox.db')
                                    cursor = conn.cursor()
                                    cursor.execute(
                                        "INSERT OR IGNORE INTO instrument_sheet_music (song_name, instrument, label, file_path, creator_username) VALUES (?, ?, ?, ?, ?)",
                                        (st.session_state.current_song, st.session_state.selected_instrument, new_label.strip(), "", creator)
                                    )
                                    conn.commit()
                                    conn.close()
                            else:
                                # Use SQLite
                                conn = sqlite3.connect('Gospel_Jukebox.db')
                                cursor = conn.cursor()
                                cursor.execute(
                                    "INSERT OR IGNORE INTO instrument_sheet_music (song_name, instrument, label, file_path, creator_username) VALUES (?, ?, ?, ?, ?)",
                                    (st.session_state.current_song, st.session_state.selected_instrument, new_label.strip(), "", creator)
                                )
                                conn.commit()
                                conn.close()
                                st.success(f"Sheet music type '{new_label.strip()}' added!")
                            
                            # Try to rerun, otherwise notify and ask user to refresh manually
                            try:
                                st.rerun()
                            except AttributeError:
                                st.warning("Sheet music type added! Please manually refresh the page to see the update (st.rerun() is not available in this Streamlit version).")
                    else:
                        st.warning("Please enter a label name.")
                
                # Remove selected sheet music - moved outside the Add Type button logic
                if 'selected_label' in locals() and st.button(f"🗑️ Remove '{selected_label}' Sheet Music", key="remove_sheet_music_btn"):
                    conn = sqlite3.connect('Gospel_Jukebox.db')
                    cursor = conn.cursor()
                    cursor.execute(
                        "DELETE FROM instrument_sheet_music WHERE song_name = ? AND instrument = ? AND label = ?",
                        (st.session_state.current_song, st.session_state.selected_instrument, selected_label)
                    )
                    conn.commit()
                    conn.close()
                    # Delete file from disk
                    if 'label_to_path' in locals() and selected_label in label_to_path:
                        try:
                            os.remove(label_to_path[selected_label])
                            st.success(f"Sheet music '{selected_label}' removed!")
                        except Exception as e:
                            st.warning(f"File delete error: {e}")
                    # Try to rerun, otherwise notify and ask user to refresh manually
                    try:
                        st.experimental_rerun()
                    except AttributeError:
                        st.warning("Sheet music removed! Please manually refresh the page to see the update (st.experimental_rerun() is not available in this Streamlit version).")
                    else:
                        st.info("Log in to manage sheet music.")
                        if st.button("Go to Login", key="login_from_sheet_music"):
                            st.session_state['login_checkbox'] = True
                            try:
                                st.rerun()
                            except AttributeError:
                                st.warning("st.rerun() is not available in this Streamlit version. Please upgrade Streamlit.")
                else:
                    st.warning(f"No sheet music available for {st.session_state.selected_instrument} on this song.")
                    # Check if user is logged in before showing upload option
                    if not st.session_state.logged_in:
                        st.info("Please log in to upload sheet music.")
                        if st.button("Go to Login"):
                            # Set the sidebar checkbox to trigger login page
                            st.session_state['login_checkbox'] = True
                            try:
                                st.rerun()
                            except AttributeError:
                                st.warning("st.rerun() is not available in this Streamlit version. Please upgrade Streamlit.")
                    else:
                        label_input = st.text_input("Label for this sheet music (e.g., Chord Progression, Arpeggios)", key="sheet_music_label_input")
                        uploaded_file = st.file_uploader(
                            f"Upload {st.session_state.selected_instrument} Sheet Music (JPG, PNG, PDF)", 
                            type=["jpg", "png", "pdf"],
                            key=f"upload_{st.session_state.selected_instrument}"
                        )
                        upload_btn = st.button("Upload Sheet Music", key="upload_sheet_music_btn")
                        if upload_btn:
                            if uploaded_file is not None and label_input.strip():
                                # Prevent duplicate label for this song/instrument
                                if label_input.strip() in unique_labels:
                                    st.warning(f"Label '{label_input.strip()}' already exists for this song/instrument. Please use a unique label.")
                                else:
                                    ext = uploaded_file.name.split('.')[-1]
                                    save_path = os.path.join(
                                        os.path.join(PICTURES_DIR, "sheet_music"), 
                                        f"{os.path.splitext(st.session_state.current_song)[0]}_{st.session_state.selected_instrument}_{label_input.strip().replace(' ', '_')}.{ext}"
                                    )
                                    with open(save_path, "wb") as f:
                                        f.write(uploaded_file.getbuffer())
                                    # Get current username for creator attribution
                                    creator = st.session_state.get('username', '')
                                    
                                    if st.session_state.get('use_supabase', False):
                                        try:
                                            # Store in Supabase
                                            data = {
                                                'song_name': st.session_state.current_song,
                                                'instrument': st.session_state.selected_instrument,
                                                'label': label_input.strip(),
                                                'file_path': save_path,
                                                'creator_username': creator
                                            }
                                            supabase_client.table('instrument_sheet_music').upsert(data).execute()
                                            st.success("Sheet music uploaded and saved to Supabase!")
                                        except Exception as e:
                                            st.error(f"Supabase error: {e}")
                                            # Fall back to SQLite
                                            conn = sqlite3.connect('Gospel_Jukebox.db')
                                            cursor = conn.cursor()
                                            cursor.execute(
                                                "INSERT OR REPLACE INTO instrument_sheet_music (song_name, instrument, label, file_path, creator_username) VALUES (?, ?, ?, ?, ?)",
                                                (st.session_state.current_song, st.session_state.selected_instrument, label_input.strip(), save_path, creator)
                                            )
                                            conn.commit()
                                            conn.close()
                                            st.success("Sheet music uploaded and saved to local database!")
                                    else:
                                        # Use SQLite
                                        conn = sqlite3.connect('Gospel_Jukebox.db')
                                        cursor = conn.cursor()
                                        cursor.execute(
                                            "INSERT OR REPLACE INTO instrument_sheet_music (song_name, instrument, label, file_path, creator_username) VALUES (?, ?, ?, ?, ?)",
                                            (st.session_state.current_song, st.session_state.selected_instrument, label_input.strip(), save_path, creator)
                                        )
                                        conn.commit()
                                        conn.close()
                                        st.success("Sheet music uploaded and saved to database!")
                                    
                                    # Try to rerun, otherwise notify and ask user to refresh manually
                                    try:
                                        st.rerun()
                                    except AttributeError:
                                        st.warning("Sheet music uploaded! Please manually refresh the page to see the update (st.rerun() is not available in this Streamlit version).")
                            elif uploaded_file is not None and not label_input.strip():
                                st.warning("Please enter a label for this sheet music.")
                            elif uploaded_file is None:
                                st.warning("Please select a file to upload.")

def display_voting_page():
    """Display the voting page."""
    st.header("Vote for Your Favorite Song!")
    st.markdown("""
        To vote for your favorite song, please send your vote in pennies to Cash App: **$SolidBuildersInc**.
        Then, enter the song name and the amount you sent below.
    """)

    # Ensure the queue is populated
    if not st.session_state.queue:
        st.warning("No songs available for voting. Please add songs to the queue.")
        return

    song_to_vote = st.selectbox("Select a song to vote for:", st.session_state.queue)

    if song_to_vote:
        vote_amount = st.slider("Rate this song (1-100 pennies):", min_value=1, max_value=100)
        if st.button("Submit Vote"):
            # Store the vote in the database
            conn = sqlite3.connect('Gospel_Jukebox.db')
            cursor = conn.cursor()
            cursor.execute("INSERT INTO votes (song_name, vote) VALUES (?, ?)", (song_to_vote, vote_amount))
            conn.commit()
            conn.close()

            # Open Cash App link in a new tab
            cash_app_link = f"https://cash.app/$SolidBuildersInc?amount={vote_amount}"
            st.markdown(f"[Click here to pay in Cash App]({cash_app_link})", unsafe_allow_html=True)

            st.success(f"Thank you for your vote! Please confirm your payment of {vote_amount} cents via Cash App.")

def display_results_page():
    """Display the voting results as a pie chart."""
    st.header("Vote Results")

    # Fetch votes from the database
    conn = sqlite3.connect('Gospel_Jukebox.db')
    cursor = conn.cursor()
    cursor.execute("SELECT song_name, SUM(vote) FROM votes GROUP BY song_name")
    results = cursor.fetchall()
    conn.close()

    if results:
        song_names = [row[0] for row in results]
        votes = [row[1] for row in results]

        # Create a pie chart
        plt.figure(figsize=(10, 6))
        plt.pie(votes, labels=song_names, autopct='%1.1f%%', startangle=140)
        plt.title("Song Voting Results")
        st.pyplot(plt)
    else:
        st.write("No votes have been cast yet.")

def display_about():
    """Display the about page."""
    st.header("About Gospel JukeBox")
    st.markdown("""
    ### Welcome to Gospel JukeBox!

    This application allows you to listen to gospel music, view lyrics, and organize your listening experience.

    #### Features:
    - Browse and search the music library
    - Queue management for continuous playback
    - View song lyrics while listening
    - Track your listening history
    - Add notes to songs for future reference
    - Upload and view sheet music for songs
    - Vote for your favorite songs using CashApp
    - View voting results in a pie chart
    """)

def login_page():
    """Display the login page and handle authentication."""
    st.header("Login to Gospel JukeBox")
    st.markdown("Please log in to access sheet music management features.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        
        if st.button("Login"):
            if username and password:
                # Check credentials against database
                conn = sqlite3.connect('Gospel_Jukebox.db')
                cursor = conn.cursor()
                cursor.execute("SELECT username, is_admin FROM users WHERE username = ? AND password = ?", 
                              (username, password))
                user = cursor.fetchone()
                conn.close()
                
                if user:
                    st.session_state.logged_in = True
                    st.session_state.username = user[0]
                    st.session_state.is_admin = bool(user[1])
                    st.success(f"Welcome, {username}!")
                    try:
                        st.rerun()
                    except AttributeError:
                        st.error("st.rerun() is not available in this Streamlit version. Please upgrade Streamlit.")
                        if st.button("Back to Main"):
                            st.session_state['login_checkbox'] = False
                            st.session_state['show_login'] = False
                            st.query_params.update({'page': 'main'})
                else:
                    st.error("Invalid username or password.")
            else:
                st.warning("Please enter both username and password.")
        # Add Back to Main button
        if st.button("Back to Main"):
            st.session_state['login_checkbox'] = False
            st.session_state['show_login'] = False
            st.query_params.update({'page': 'main'})
    
    with col2:
        st.markdown("### New User?")
        st.markdown("Contact the administrator to create an account.")
        # st.markdown("Default admin credentials:")
        # st.markdown("- Username: admin")
        # st.markdown("- Password: admin123")
        # st.markdown("*Note: For demonstration purposes only.*")

def logout():
    """Log out the current user."""
    st.session_state.logged_in = False
    st.session_state.username = None
    st.session_state.is_admin = False
    st.success("You have been logged out.")
    try:
        st.rerun()
    except AttributeError:
        st.warning("Note deleted! Please manually refresh the page to see the update (st.rerun() is not available in this Streamlit version).")

def main():
    # Display login status and logout button in sidebar if logged in
    if st.session_state.logged_in:
        with st.sidebar:
            st.markdown(f"**Logged in as: {st.session_state.username}**")
            if st.session_state.is_admin:
                st.markdown("*Administrator*")
            if st.button("Logout"):
                logout()
    
    # Initialize login_checkbox in session state if not present
    if 'login_checkbox' not in st.session_state:
        st.session_state['login_checkbox'] = False
        
    # Navigation
    if not st.session_state.logged_in and (st.sidebar.checkbox("Login to manage sheet music", value=st.session_state['login_checkbox']) or st.session_state['login_checkbox']):
        page = "Login"
        # Keep the checkbox state in sync
        st.session_state['login_checkbox'] = True
    else:
        pages = ["Music Library", "Vote", "Results", "About"]
        if st.session_state.get('is_admin'):
            pages.append("User Management")
        page = st.sidebar.selectbox("Select a Page", pages)
        # Admin: Add User section in sidebar
        if st.session_state.get('is_admin'):
            st.sidebar.markdown("---")
            st.sidebar.markdown("### Admin: Add User")
            new_user = st.sidebar.text_input('New Username', key='admin_add_user_input_sidebar')
            new_pass = st.sidebar.text_input('New Password', type='password', key='admin_add_pass_input_sidebar')
            new_label = st.sidebar.text_input('User Label (optional)', key='admin_add_label_input_sidebar')
            if st.sidebar.button('Create User', key='admin_create_user_btn_sidebar'):
                if new_user and new_pass:
                    conn = sqlite3.connect('Gospel_Jukebox.db')
                    cursor = conn.cursor()
                    cursor.execute("SELECT username FROM users WHERE username = ?", (new_user,))
                    if cursor.fetchone():
                        st.sidebar.error('Username already exists.')
                    else:
                        cursor.execute("INSERT INTO users (username, password, is_admin) VALUES (?, ?, 0)", (new_user, new_pass))
                        conn.commit()
                        st.sidebar.success('User created!')
                    conn.close()
                else:
                    st.sidebar.warning('Please enter both username and password.')
        # Reset login checkbox when navigating to other pages
        st.session_state['login_checkbox'] = False

    # Always display the MP3 player in the sidebar, regardless of selected page
    display_mp3_player()

    if page == "Login":
        login_page()
    elif page == "Music Library":
        display_music_library()
    elif page == "Vote":
        display_voting_page()
    elif page == "Results":
        display_results_page()
    elif page == "About":
        display_about()

if __name__ == "__main__":
    main()
