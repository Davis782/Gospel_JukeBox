import streamlit as st
import os
import base64
import time
from datetime import datetime

# Set page configuration
st.set_page_config(
    page_title="Gospel JukeBox",
    page_icon="🎵",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Define the application paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MP3_DIR = os.path.join(BASE_DIR, "mp3_files")
PICTURES_DIR = os.path.join(BASE_DIR, "pictures")

# Ensure directories exist
os.makedirs(MP3_DIR, exist_ok=True)
os.makedirs(PICTURES_DIR, exist_ok=True)

# Initialize session state for persistent data across reruns
if 'queue' not in st.session_state:
    st.session_state.queue = []
if 'history' not in st.session_state:
    st.session_state.history = []
if 'current_song' not in st.session_state:
    st.session_state.current_song = None
if 'current_lyrics' not in st.session_state:
    st.session_state.current_lyrics = None
if 'play_time' not in st.session_state:
    st.session_state.play_time = None

# Helper function to encode MP3 files to base64
def encode_audio_to_base64(file_path):
    """Read an audio file and encode it to base64 string."""
    try:
        with open(file_path, "rb") as audio_file:
            audio_data = audio_file.read()
            base64_data = base64.b64encode(audio_data).decode('utf-8')
            return base64_data
    except Exception as e:
        st.error(f"Error encoding audio file {file_path}: {e}")
        return None

def play_audio(file_path, song_name):
    """Updates the current song in session state without interrupting playback."""
    try:
        # Update session state without recreating the audio player
        # This allows the persistent player to handle the actual playback
        st.session_state.current_song = song_name
        st.session_state.play_time = datetime.now().strftime("%H:%M:%S")
        
        # Load and store lyrics
        lyrics = load_lyrics(file_path)
        st.session_state.current_lyrics = lyrics
        
        # Add to history if not already the last item
        if not st.session_state.history or st.session_state.history[-1] != song_name:
            st.session_state.history.append(song_name)
            # Keep history to last 10 items
            if len(st.session_state.history) > 10:
                st.session_state.history = st.session_state.history[-10:]
                
        # Force a rerun to update the persistent player
        st.rerun()
    except FileNotFoundError:
        st.error(f"File not found: {file_path}")
    except Exception as e:
        st.error(f"An error occurred: {e}")

def load_content():
    """Load songs and pictures from directories."""
    mp3_files = sorted([f for f in os.listdir(MP3_DIR) if f.endswith('.mp3')])
    picture_files = sorted([f for f in os.listdir(PICTURES_DIR) if f.lower().endswith(('.jpg', '.png', '.jpeg'))])
    return mp3_files, picture_files

def load_lyrics(file_path):
    """Load lyrics from a corresponding text file."""
    text_file_path = os.path.splitext(file_path)[0] + '.txt'
    if os.path.exists(text_file_path):
        with open(text_file_path, 'r') as f:
            return f.read()
    return "No lyrics available."

def add_to_queue(song_name):
    """Add a song to the queue."""
    st.session_state.queue.append(song_name)

def remove_from_queue(index):
    """Remove a song from the queue."""
    if 0 <= index < len(st.session_state.queue):
        st.session_state.queue.pop(index)

def play_from_queue(index):
    """Play a song from the queue and remove it."""
    if 0 <= index < len(st.session_state.queue):
        song_name = st.session_state.queue[index]
        file_path = os.path.join(MP3_DIR, song_name)
        
        # Play the audio and update session state
        play_audio(file_path, song_name)
        
        # Ensure lyrics are loaded and stored in session state
        lyrics = load_lyrics(file_path)
        st.session_state.current_lyrics = lyrics
        
        # Remove from queue after playing
        remove_from_queue(index)

def clear_queue():
    """Clear the entire queue."""
    st.session_state.queue = []

def display_persistent_player():
    """Display a persistent audio player at the top of the app."""
    if st.session_state.current_song:
        # Create a container with a fixed style for the persistent player
        with st.container():
            st.markdown(
                """<style>
                .persistent-player {
                    position: sticky;
                    top: 0;
                    z-index: 999;
                    background-color: #f0f2f6;
                    padding: 10px;
                    border-radius: 10px;
                    margin-bottom: 15px;
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                }
                </style>""", 
                unsafe_allow_html=True
            )
            
            # Display the persistent player
            file_path = os.path.join(MP3_DIR, st.session_state.current_song)
            try:
                with open(file_path, "rb") as audio_file:
                    audio_data = audio_file.read()
                    b64 = base64.b64encode(audio_data).decode()
                    audio_html = f"""
                        <div class="persistent-player">
                            <h4 style="color: #1e3a8a; margin-bottom: 5px;">Now Playing: {st.session_state.current_song.replace('.mp3', '')}</h4>
                            <audio controls style="width: 100%;" autoplay>
                                <source src="data:audio/mpeg;base64,{b64}" type="audio/mpeg">
                                Your browser does not support the audio element.
                            </audio>
                        </div>
                    """
                    st.markdown(audio_html, unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Error loading audio: {e}")

def display_mp3_player():
    # Sidebar for navigation and app info
    with st.sidebar:
        st.title("Gospel JukeBox 🎵")
        st.markdown("---")
        st.markdown("### Navigation")
        page = st.radio("Go to", ["Music Library", "Now Playing", "Queue & History", "Pictures", "About"])
        
        st.markdown("---")
        # Donation button
        st.markdown("### Support Us")
        cashapp_url = "https://cash.app/$SolidBuildersInc/"
        st.markdown(
            f'<a href="{cashapp_url}" target="_blank"><button style="background-color:#00D632; color:white; padding:8px 16px; border:none; border-radius:4px; cursor:pointer; width:100%;">Donate with Cash App</button></a>',
            unsafe_allow_html=True,
        )
    
    # Display the persistent player at the top of every page
    display_persistent_player()
    
    # Main content area
    if page == "Music Library":
        display_music_library()
    elif page == "Now Playing":
        display_now_playing()
    elif page == "Queue & History":
        display_queue_and_history()
    elif page == "Pictures":
        display_pictures()
    elif page == "About":
        display_about()

def display_music_library():
    """Display the music library page."""
    st.header("Music Library")
    
    # Load songs
    mp3_files, _ = load_content()
    
    if not mp3_files:
        st.warning("No MP3 files found in the directory.")
        return
    
    # Search functionality
    search_query = st.text_input("Search songs", "").lower()
    filtered_songs = [song for song in mp3_files if search_query in song.lower()]
    
    # Create a dropdown for song selection
    selected_song = st.selectbox(
        "Select a song to play",
        options=filtered_songs,
        format_func=lambda x: x.replace('.mp3', '')
    )
    
    # Create columns for action buttons
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("▶️ Play Selected Song"):
            if selected_song:
                file_path = os.path.join(MP3_DIR, selected_song)
                play_audio(file_path, selected_song)
    
    with col2:
        if st.button("➕ Add to Queue"):
            if selected_song:
                add_to_queue(selected_song)
                st.success(f"{selected_song} added to queue.")
    
    # Display lyrics of the selected song
    if selected_song:
        file_path = os.path.join(MP3_DIR, selected_song)
        lyrics = load_lyrics(file_path)
        
        # Store lyrics in session state for persistence
        st.session_state.current_lyrics = lyrics
        
        # Display lyrics in an expander
        with st.expander("Preview Lyrics", expanded=True):  # Set to expanded=True to show lyrics by default
            if lyrics != "No lyrics available.":
                st.markdown(
                    f"<div style='background-color: #000000; padding: 20px; border-radius: 10px; max-height: 300px; overflow-y: auto; color: white;'>{lyrics.replace('\n', '<br>')}</div>",
                    unsafe_allow_html=True
                )
            else:
                st.info("No lyrics available for this song.")
                
        # Also display a direct text area for better visibility
        st.text_area("Lyrics", lyrics, height=200, key="lyrics_text_area", label_visibility="collapsed")
    
    # Optional: Still show all songs in a list format
    with st.expander("All Songs", expanded=False):
        # Display songs in a grid layout
        col1, col2, col3 = st.columns(3)
        
        for i, song in enumerate(filtered_songs):
            col = [col1, col2, col3][i % 3]
            with col:
                st.markdown(f"### {song.replace('.mp3', '')}")
                file_path = os.path.join(MP3_DIR, song)
                
                # Create two columns for buttons
                btn_col1, btn_col2 = st.columns(2)
                
                with btn_col1:
                    if st.button(f"▶️ Play", key=f"play_{i}"):
                        play_audio(file_path, song)
                
                with btn_col2:
                    if st.button(f"➕ Queue", key=f"queue_{i}"):
                        add_to_queue(song)
                        st.success(f"{song} added to queue.")
                
                st.markdown("---")

def display_now_playing():
    """Display the now playing page."""
    st.header("Now Playing")
    
    if st.session_state.current_song:
        # Display current song info
        st.subheader(f"🎵 {st.session_state.current_song.replace('.mp3', '')}")
        st.write(f"Started playing at: {st.session_state.play_time}")
        
        # Play the current song again
        file_path = os.path.join(MP3_DIR, st.session_state.current_song)
        play_audio(file_path, st.session_state.current_song)
        
        # Display lyrics in a nice format
        st.markdown("### Lyrics")
        if st.session_state.current_lyrics and st.session_state.current_lyrics != "No lyrics available.":
            st.markdown(
                f"<div style='background-color: #000000; padding: 20px; border-radius: 10px; max-height: 400px; overflow-y: auto; color: white;'>{st.session_state.current_lyrics.replace('\n', '<br>')}</div>",
                unsafe_allow_html=True
            )
        else:
            st.info("No lyrics available for this song.")
    else:
        st.info("No song is currently playing. Select a song from the Music Library.")

def display_queue_and_history():
    """Display the queue and history page."""
    st.header("Queue & History")
    
    # Create tabs for Queue and History
    queue_tab, history_tab = st.tabs(["Queue", "History"])
    
    with queue_tab:
        st.subheader("Queue")
        if st.session_state.queue:
            # Add a clear queue button
            if st.button("Clear Queue"):
                clear_queue()
                st.success("Queue cleared.")
            
            # Display queue items with play and remove buttons
            for i, song in enumerate(st.session_state.queue):
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    st.write(f"{i+1}. {song.replace('.mp3', '')}")
                with col2:
                    if st.button("▶️", key=f"play_queue_{i}"):
                        play_from_queue(i)
                with col3:
                    if st.button("❌", key=f"remove_queue_{i}"):
                        remove_from_queue(i)
                        st.rerun()
        else:
            st.write("Queue is empty. Add songs from the Music Library.")
    
    with history_tab:
        st.subheader("Recently Played")
        if st.session_state.history:
            # Display history in reverse order (most recent first)
            for i, song in enumerate(reversed(st.session_state.history)):
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.write(f"{song.replace('.mp3', '')}")
                with col2:
                    file_path = os.path.join(MP3_DIR, song)
                    if st.button("▶️", key=f"play_history_{i}"):
                        play_audio(file_path, song)
        else:
            st.write("No playback history yet.")

def display_pictures():
    """Display the pictures page."""
    st.header("Pictures")
    
    # Load pictures
    _, picture_files = load_content()
    
    if not picture_files:
        st.warning("No pictures found in the directory.")
        return
    
    # Display pictures in a grid
    cols = st.columns(3)
    for i, picture_file in enumerate(picture_files):
        with cols[i % 3]:
            st.image(
                os.path.join(PICTURES_DIR, picture_file),
                caption=picture_file,
                use_column_width=True
            )

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
    - View pictures related to the ministry
    
    #### How to use:
    1. Navigate to the Music Library to browse available songs
    2. Play songs directly or add them to your queue
    3. View the current playing song and lyrics in the Now Playing section
    4. Manage your queue and view history in the Queue & History section
    
    Thank you for using Gospel JukeBox!
    """)

def main():
    display_mp3_player()  # Display the MP3 player section

if __name__ == "__main__":
