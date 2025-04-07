import streamlit as st
import os
import base64
import time
from datetime import datetime
from icecream import ic

# Configure icecream for better debugging
ic.configureOutput(prefix='🍦 Debug | ', includeContext=True)

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
if 'song_notes' not in st.session_state:
    st.session_state.song_notes = {}
if 'audio_playing' not in st.session_state:
    st.session_state.audio_playing = False
if 'audio_data' not in st.session_state:
    st.session_state.audio_data = None
if 'sheet_music' not in st.session_state:
    st.session_state.sheet_music = {}
if 'current_playback_time' not in st.session_state:
    st.session_state.current_playback_time = 0
if 'autoplay' not in st.session_state:
    st.session_state.autoplay = False
if 'replay' not in st.session_state:
    st.session_state.replay = False
if 'song_ended' not in st.session_state:
    st.session_state.song_ended = False

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

def play_audio(file_path, song_name, display_player=False):
    """Plays an audio file in Streamlit using the audio component.
    
    Args:
        file_path: Path to the MP3 file
        song_name: Name of the song to display
        display_player: Whether to display the audio player in the main content area (default: False)
                       This parameter is kept for backward compatibility but is no longer used
                       as all audio players are now displayed only in the sidebar.
    """
    ic(f"play_audio called with song: {song_name}")
    ic(f"Current song: {st.session_state.current_song}, Audio playing: {st.session_state.audio_playing}")
    try:
        # If we're starting a new song or no song is currently playing
        if st.session_state.current_song != song_name or not st.session_state.audio_playing:
            with open(file_path, "rb") as audio_file:
                audio_data = audio_file.read()
                b64 = base64.b64encode(audio_data).decode()
                
                # Store the audio data in session state for persistent playback
                st.session_state.audio_data = b64
                st.session_state.audio_playing = True
                
                # Update session state for the new song
                st.session_state.current_song = song_name
                st.session_state.play_time = datetime.now().strftime("%H:%M:%S")
                st.session_state.current_playback_time = 0  # Reset playback time for new song
                
                # Load and store lyrics
                lyrics = load_lyrics(file_path)
                st.session_state.current_lyrics = lyrics
                
                # Add to history if not already the last item
                if not st.session_state.history or st.session_state.history[-1] != song_name:
                    st.session_state.history.append(song_name)
                    # Keep history to last 10 items
                    if len(st.session_state.history) > 10:
                        st.session_state.history = st.session_state.history[-10:]
                
                # We no longer force a rerun here to prevent disrupting the queue
                # The UI will update on the next natural rerun
        else:
            # Use the existing audio data from session state
            b64 = st.session_state.audio_data
            
        # We no longer display the audio player here regardless of display_player parameter
        # The audio player is now only displayed in the sidebar (in display_mp3_player function)
        # This ensures consistency across all pages
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
    """Add a song to the queue without interrupting current playback.
    
    Args:
        song_name: Name of the song to add to the queue
        
    Returns:
        bool: True if the song was added, False if it was already in the queue
    """
    # Check if the song is already in the queue to prevent duplicates
    if song_name not in st.session_state.queue:
        st.session_state.queue.append(song_name)
        # Return True to indicate success (can be used for displaying success messages)
        return True
    return False
    # No rerun is needed here - this prevents interrupting current playback
    # and allows the UI to update naturally on the next rerun

def remove_from_queue(index):
    """Remove a song from the queue."""
    if 0 <= index < len(st.session_state.queue):
        st.session_state.queue.pop(index)

def play_from_queue(index, remove_after_playing=True):
    """Play a song from the queue and optionally remove it.
    
    Args:
        index: The index of the song in the queue
        remove_after_playing: Whether to remove the song from the queue after playing (default: True)
                             Set to False for autoplay functionality to preserve the queue
    """
    ic(f"play_from_queue called with index={index}, remove_after_playing={remove_after_playing}")
    ic("Current queue before playing:", st.session_state.queue)
    
    if 0 <= index < len(st.session_state.queue):
        song_name = st.session_state.queue[index]
        ic("Playing song from queue:", song_name)
        file_path = os.path.join(MP3_DIR, song_name)
        
        # Play the audio and update session state
        play_audio(file_path, song_name, display_player=False)
        
        # Ensure lyrics are loaded and stored in session state
        lyrics = load_lyrics(file_path)
        st.session_state.current_lyrics = lyrics
        
        # Set the current page to Now Playing to show lyrics
        st.session_state.current_page = "Now Playing"
        
        # Improved queue management based on replay mode
        if st.session_state.replay:
            ic("Replay mode is enabled")
            # In replay mode, we want to keep songs in the queue for continuous playback
            if st.session_state.autoplay and index == 0 and remove_after_playing:
                ic("Moving song to end of queue for replay")
                # Move the song to the end of the queue for continuous playback
                song = st.session_state.queue.pop(index)
                st.session_state.queue.append(song)
                ic("Queue after moving song to end:", st.session_state.queue)
        elif remove_after_playing:
            ic("Replay mode is disabled, removing song from queue")
            # If replay is disabled and removal is requested, remove the song from the queue
            remove_from_queue(index)
            ic("Queue after removing song:", st.session_state.queue)
        
        # We don't force a rerun here to prevent disrupting the queue
        # The UI will update on the next natural rerun
    else:
        ic("Error: Invalid queue index", index, "Queue length:", len(st.session_state.queue))
        ic("Current queue:", st.session_state.queue)

def clear_queue():
    """Clear the entire queue."""
    st.session_state.queue = []

# Custom component to receive playback time updates from JavaScript
def time_position_component():
    # Create a placeholder for the component
    component_value = st.empty()
    
    # Debug the component creation
    ic("Creating time position component")
    
    # Create a custom component that will receive messages from JavaScript
    component_html = """
    <div id="time-position-component" style="display:none;"></div>
    <script>
        // Function to handle component value changes
        function handleComponentValueChange(event) {
            console.log('Message received:', event.data);
            
            if (event.data.current_playback_time !== undefined) {
                // Update the session state with the current playback time
                const args = {
                    current_playback_time: event.data.currentTime
                };
                console.log('Sending playback time to Streamlit:', args);
                window.parent.Streamlit.setComponentValue(args);
            }
            
            if (event.data.type === 'audio_ended' || event.data.song_ended === true) {
                // Update the session state when song ends
                console.log('Song ended event detected in component');
                const args = {
                    song_ended: true
                };
                console.log('Sending song_ended to Streamlit:', args);
                window.parent.Streamlit.setComponentValue(args);
            }
        }
        
        // Listen for messages from audio elements
        window.addEventListener('message', handleComponentValueChange);
        console.log('Event listener for messages registered');
    </script>
    """
    
    # Render the component
    component_value.markdown(component_html, unsafe_allow_html=True)
    
    # Return the component value
    return component_value

def display_mp3_player():
    # Add the time position component to receive updates from JavaScript
    time_component = time_position_component()
    
    # Debug the time_component object
    ic("Time component object:", time_component)
    ic("Time component has attributes:", dir(time_component) if time_component else "None")
    
    # If we received a time update from JavaScript, store it in session state
    if time_component and hasattr(time_component, 'current_playback_time'):
        ic("Received playback time update:", time_component.current_playback_time)
        st.session_state.current_playback_time = time_component.current_playback_time
    
    # Debug song_ended attribute
    if time_component:
        ic("Has song_ended attribute:", hasattr(time_component, 'song_ended'))
        if hasattr(time_component, 'song_ended'):
            ic("song_ended value:", time_component.song_ended)
    
    # Check if song has ended and autoplay is enabled
    # We now check both the time_component and the session_state for song_ended
    song_ended_detected = (time_component and hasattr(time_component, 'song_ended') and time_component.song_ended) or st.session_state.song_ended
    
    if song_ended_detected:
        ic("Song ended event detected - processing autoplay logic")
        # Reset the flags immediately to prevent duplicate processing
        if hasattr(time_component, 'song_ended'):
            time_component.song_ended = False
        st.session_state.song_ended = False
        
        ic("Current queue:", st.session_state.queue)
        ic("Autoplay enabled:", st.session_state.autoplay)
        ic("Replay mode:", st.session_state.replay)
        
        # If autoplay is enabled and there are songs in the queue, play the next song
        if st.session_state.autoplay and st.session_state.queue:
            ic("Autoplay condition met - playing next song from queue")
            ic("Next song:", st.session_state.queue[0])
            # When autoplay is enabled, we should play the next song
            # The play_from_queue function will handle queue management based on replay setting
            # This allows for continuous playback while maintaining proper queue state
            play_from_queue(0, remove_after_playing=not st.session_state.replay)
            ic("After play_from_queue - Queue state:", st.session_state.queue)
            # Force a rerun to ensure the UI updates with the new song
            st.rerun()
        elif st.session_state.autoplay and not st.session_state.queue and st.session_state.replay and st.session_state.history:
            ic("Autoplay with empty queue, replay enabled, using history")
            ic("History:", st.session_state.history)
            # If autoplay is enabled, queue is empty, replay is enabled, and there's history
            # Add the last played song from history back to the queue and play it
            if st.session_state.history:
                last_song = st.session_state.history[-1]
                ic("Adding last song from history to queue:", last_song)
                add_to_queue(last_song)
                play_from_queue(0, remove_after_playing=False)
                ic("After play_from_queue with history - Queue state:", st.session_state.queue)
                # Force a rerun to ensure the UI updates with the new song
                st.rerun()
        else:
            ic("No autoplay conditions met - song ended but no action taken")
            ic("Autoplay:", st.session_state.autoplay)
            ic("Queue empty:", len(st.session_state.queue) == 0)
            ic("Replay mode:", st.session_state.replay)
            ic("History available:", len(st.session_state.history) > 0)
    
    # Store the current page in session state if not already there
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "Music Library"
    
    # Sidebar for navigation and app info
    with st.sidebar:
        st.title("Gospel JukeBox 🎵")
        st.markdown("---")
        
        # Add persistent audio player in sidebar if a song is playing
        if st.session_state.audio_playing and st.session_state.current_song and st.session_state.audio_data:
            st.markdown("### Now Playing")
            audio_html = f"""
                <div style="background-color: #f0f2f6; padding: 10px; border-radius: 10px; margin-bottom: 10px;">
                    <h4 style="color: #1e3a8a; margin-bottom: 5px;">{st.session_state.current_song.replace('.mp3', '')}</h4>
                    <audio id="audio-player" controls autoplay style="width: 100%;" 
                        onpause="window.parent.postMessage({{'type': 'audio_paused'}}, '*')" 
                        ontimeupdate="window.parent.postMessage({{'type': 'audio_timeupdate', 'currentTime': this.currentTime}}, '*')"
                        onloadedmetadata="this.currentTime = {st.session_state.current_playback_time}"
                        onended="handleAudioEnded()">
                        <source src="data:audio/mpeg;base64,{st.session_state.audio_data}" type="audio/mpeg">
                        Your browser does not support the audio element.
                    </audio>
                </div>
                <script>
                    // Function to handle audio ended event
                    function handleAudioEnded() {{
                        console.log('Audio ended event triggered directly from audio element');
                        // Send the song ended event to Streamlit via postMessage
                        window.parent.postMessage({{
                            type: 'audio_ended',
                            song_ended: true
                        }}, '*');
                        
                        // Also try to send directly to Streamlit component
                        if (window.parent.Streamlit) {{
                            console.log('Sending song_ended directly to Streamlit component');
                            window.parent.Streamlit.setComponentValue({{ song_ended: true }});
                        }}
                    }}
                    
                    // Listen for messages from the audio element
                    window.addEventListener('message', function(event) {{
                        console.log('Message received in audio player:', event.data);
                        
                        if (event.data.type === 'audio_timeupdate') {{
                            // Store the current time in a variable that will be accessible to Streamlit
                            window.current_playback_time = event.data.currentTime;
                            // Send the current time to Streamlit via session state
                            const data = {{
                                current_playback_time: event.data.currentTime
                            }};
                            // Use Streamlit's setComponentValue to update session state
                            if (window.parent.Streamlit) {{
                                window.parent.Streamlit.setComponentValue(data);
                            }}
                        }} else if (event.data.type === 'audio_ended') {{
                            // Send the song ended event to Streamlit
                            console.log('Audio ended event detected in message handler');
                            const data = {{
                                song_ended: true
                            }};
                            // Use Streamlit's setComponentValue to update session state
                            if (window.parent.Streamlit) {{
                                console.log('Sending song_ended to Streamlit from message handler');
                                window.parent.Streamlit.setComponentValue(data);
                            }}
                        }}
                    }});
                    
                    // Add an additional event listener directly to the audio element
                    document.addEventListener('DOMContentLoaded', function() {{
                        const audioPlayer = document.getElementById('audio-player');
                        if (audioPlayer) {{
                            console.log('Adding direct event listener to audio player');
                            audioPlayer.addEventListener('ended', handleAudioEnded);
                        }}
                    }});
                </script>
            """
            st.markdown(audio_html, unsafe_allow_html=True)
            
            # Add stop button
            if st.button("⏹️ Stop Playback", key="sidebar_stop_audio"):
                st.session_state.audio_playing = False
                st.session_state.audio_data = None
                # We don't force a rerun here to prevent disrupting the queue
                # The UI will update naturally on the next rerun
            
            # Add button to go to Now Playing page if not already there
            if st.session_state.current_page != "Now Playing":
                if st.button("🎵 Go to Now Playing"):
                    st.session_state.current_page = "Now Playing"
                    # We don't force a rerun here to prevent disrupting the queue
                    # The UI will update naturally on the next rerun
            
            st.markdown("---")
        
        # Add autoplay and replay toggles in sidebar
        st.markdown("### Playback Settings")
        autoplay = st.toggle("Autoplay Next Song in Queue", value=st.session_state.autoplay)
        if autoplay != st.session_state.autoplay:
            # Update autoplay setting without forcing a page change
            ic("Autoplay setting changed:", f"{st.session_state.autoplay} -> {autoplay}")
            st.session_state.autoplay = autoplay
            ic("Current queue state after autoplay change:", st.session_state.queue)
            # Don't rerun here - this prevents the queue from being cleared
            # The autoplay setting will be used next time a song ends
            
        # Add replay toggle directly under autoplay toggle
        replay = st.toggle("Keep Songs in Queue (Replay Mode)", value=st.session_state.replay)
        if replay != st.session_state.replay:
            # Update replay setting without forcing a page change
            st.session_state.replay = replay
            # Don't rerun here - this prevents the queue from being cleared
            # The replay setting will be used next time a song ends
            
        st.markdown("---")
        st.markdown("### Navigation")
        # Use session state to remember the selected page
        page = st.radio("Go to", ["Music Library", "Now Playing", "Queue & History", "Pictures", "About"], 
                       index=["Music Library", "Now Playing", "Queue & History", "Pictures", "About"].index(st.session_state.current_page))
        
        # Update the current page in session state when changed
        if page != st.session_state.current_page:
            # Store the current page in session state without clearing the queue
            st.session_state.current_page = page
            # Don't rerun here to prevent the queue from being cleared
        
        st.markdown("---")
        # Donation button
        st.markdown("### Support Us")
        cashapp_url = "https://cash.app/$SolidBuildersInc/"
        st.markdown(
            f'<a href="{cashapp_url}" target="_blank"><button style="background-color:#00D632; color:white; padding:8px 16px; border:none; border-radius:4px; cursor:pointer; width:100%;">Donate with Cash App</button></a>',
            unsafe_allow_html=True,
        )
    
    # We've moved the persistent audio player to the sidebar, so we don't need it here anymore
    
    # Check if we should redirect to Now Playing
    if 'go_to_now_playing' in st.session_state and st.session_state.go_to_now_playing:
        page = "Now Playing"
        st.session_state.current_page = "Now Playing"
        st.session_state.go_to_now_playing = False
    
    # Main content area
    ic("Displaying page:", page)
    ic("Current song:", st.session_state.current_song)
    ic("Queue state:", st.session_state.queue)
    ic("Autoplay enabled:", st.session_state.autoplay)
    
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
    
    # If a song is currently playing, just show the song info (player is in sidebar)
    if st.session_state.audio_playing and st.session_state.current_song:
        # Display a compact version of the current song info
        st.markdown(f"**Currently Playing:** {st.session_state.current_song.replace('.mp3', '')}")
        
        # Add a stop button that matches the one in the sidebar
        if st.button("⏹️ Stop Playback", key="music_library_stop_audio"):
            st.session_state.audio_playing = False
            st.session_state.audio_data = None
            # We don't force a rerun here to prevent disrupting the queue
            # The UI will update naturally on the next rerun
    
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
                play_audio(file_path, selected_song, display_player=False)
    
    with col2:
        if st.button("➕ Add to Queue"):
            if selected_song:
                if add_to_queue(selected_song):
                    # Use a container to show success message without triggering rerun
                    success_container = st.empty()
                    success_container.success(f"{selected_song} added to queue.")
                else:
                    # Show message if song is already in queue
                    info_container = st.empty()
                    info_container.info(f"{selected_song} is already in queue.")
                # Don't rerun here to prevent interrupting current playback
    
    # Display lyrics and notes for the selected song
    if selected_song:
        file_path = os.path.join(MP3_DIR, selected_song)
        lyrics = load_lyrics(file_path)
        
        # Store lyrics in session state for persistence
        st.session_state.current_lyrics = lyrics
        
        # Create tabs for lyrics and notes
        lyrics_tab, notes_tab, sheet_music_tab = st.tabs(["Lyrics", "Notes", "Sheet Music"])
        
        with lyrics_tab:
            # Display lyrics in an expander
            if lyrics != "No lyrics available.":
                lyrics_html = lyrics.replace('\n', '<br>')  # Perform replacement before inserting into f-string
                st.markdown(
                    f"<div style='background-color: #000000; padding: 20px; border-radius: 10px; max-height: 300px; overflow-y: auto; color: white;'>{lyrics_html}</div>",
                    unsafe_allow_html=True
                )
            else:
                st.info("No lyrics available for this song.")
        
        with notes_tab:
            # Initialize notes for this song if not already in session state
            if selected_song not in st.session_state.song_notes:
                st.session_state.song_notes[selected_song] = ""
            
            # Display a text area for notes
            notes = st.text_area(
                "Song Notes (chord progressions, performance notes, etc.)",
                value=st.session_state.song_notes[selected_song],
                height=300,
                key=f"notes_{selected_song}"
            )
            
            # Save notes when changed
            if notes != st.session_state.song_notes[selected_song]:
                st.session_state.song_notes[selected_song] = notes
                st.success("Notes saved!")
        
        with sheet_music_tab:
            # Upload sheet music image
            uploaded_file = st.file_uploader("Upload sheet music image", type=["jpg", "jpeg", "png", "pdf"], key=f"sheet_music_upload_{selected_song}")
            
            if uploaded_file is not None:
                # Save the uploaded file to the sheet music directory
                sheet_music_dir = os.path.join(PICTURES_DIR, "sheet_music")
                os.makedirs(sheet_music_dir, exist_ok=True)
                
                # Create a filename based on the song name
                sheet_music_filename = f"{os.path.splitext(selected_song)[0]}_sheet.{uploaded_file.name.split('.')[-1]}"
                sheet_music_path = os.path.join(sheet_music_dir, sheet_music_filename)
                
                # Save the file
                with open(sheet_music_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                # Store in session state
                st.session_state.sheet_music[selected_song] = sheet_music_path
                st.success(f"Sheet music saved for {selected_song.replace('.mp3', '')}")
            
            # Display existing sheet music if available
            if selected_song in st.session_state.sheet_music and os.path.exists(st.session_state.sheet_music[selected_song]):
                st.image(st.session_state.sheet_music[selected_song], caption=f"Sheet Music for {selected_song.replace('.mp3', '')}", use_column_width=True)
            else:
                # Check if there's a sheet music file with the song name in the sheet_music directory
                sheet_music_dir = os.path.join(PICTURES_DIR, "sheet_music")
                os.makedirs(sheet_music_dir, exist_ok=True)
                
                possible_extensions = [".jpg", ".jpeg", ".png", ".pdf"]
                found_sheet_music = False
                
                for ext in possible_extensions:
                    sheet_music_path = os.path.join(sheet_music_dir, f"{os.path.splitext(selected_song)[0]}_sheet{ext}")
                    if os.path.exists(sheet_music_path):
                        st.session_state.sheet_music[selected_song] = sheet_music_path
                        st.image(sheet_music_path, caption=f"Sheet Music for {selected_song.replace('.mp3', '')}", use_column_width=True)
                        found_sheet_music = True
                        break
                
                if not found_sheet_music:
                    st.info("No sheet music available for this song. Upload using the file uploader above.")
    
    # Optional: Still show all songs in a list format
    with st.expander("All Songs that Can Go into Queue", expanded=False):
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
                        play_audio(file_path, song, display_player=False)
                
                with btn_col2:
                    if st.button(f"➕ Queue", key=f"queue_{i}"):
                        if add_to_queue(song):
                            # Use a container to show success message without triggering rerun
                            success_container = st.empty()
                            success_container.success(f"{song} added to queue.")
                        else:
                            # Show message if song is already in queue
                            info_container = st.empty()
                            info_container.info(f"{song} is already in queue.")
                        # Don't rerun here to prevent interrupting current playback
                
                st.markdown("---")

def display_now_playing():
    """Display the now playing page."""
    st.header("Now Playing")
    
    if st.session_state.current_song:
        # Display current song info
        st.subheader(f"🎵 {st.session_state.current_song.replace('.mp3', '')}")
        st.write(f"Started playing at: {st.session_state.play_time}")
        
        # Only start playing if no song is currently playing
        # The audio player will only appear in the sidebar
        if not st.session_state.audio_playing:
            file_path = os.path.join(MP3_DIR, st.session_state.current_song)
            play_audio(file_path, st.session_state.current_song, display_player=False)
        
        # Add a stop button that matches the one in the sidebar
        if st.button("⏹️ Stop Playback", key="now_playing_stop_audio"):
            st.session_state.audio_playing = False
            st.session_state.audio_data = None
            # We don't force a rerun here to prevent disrupting the queue
            # The UI will update naturally on the next rerun
        
        # Create tabs for lyrics, notes, and sheet music
        lyrics_tab, notes_tab, sheet_music_tab = st.tabs(["Lyrics", "Notes", "Sheet Music"])
        
        with lyrics_tab:
            # Display lyrics in a nice format
            if st.session_state.current_lyrics and st.session_state.current_lyrics != "No lyrics available.":
                lyrics_html = st.session_state.current_lyrics.replace('\n', '<br>')  # Perform replacement before inserting into f-string
                st.markdown(
                    f"<div style='background-color: #000000; padding: 20px; border-radius: 10px; max-height: 400px; overflow-y: auto; color: white;'>{lyrics_html}</div>",
                    unsafe_allow_html=True
                )
            else:
                st.info("No lyrics available for this song.")
        
        with notes_tab:
            # Initialize notes for this song if not already in session state
            if st.session_state.current_song not in st.session_state.song_notes:
                st.session_state.song_notes[st.session_state.current_song] = ""
            
            # Display a text area for notes
            notes = st.text_area(
                "Song Notes (chord progressions, performance notes, etc.)",
                value=st.session_state.song_notes[st.session_state.current_song],
                height=300,
                key=f"now_playing_notes"
            )
            
            # Save notes when changed
            if notes != st.session_state.song_notes[st.session_state.current_song]:
                st.session_state.song_notes[st.session_state.current_song] = notes
                st.success("Notes saved!")
        
        with sheet_music_tab:
            # Upload sheet music image
            uploaded_file = st.file_uploader("Upload sheet music image", type=["jpg", "jpeg", "png", "pdf"], key=f"now_playing_sheet_music_upload")
            
            if uploaded_file is not None:
                # Save the uploaded file to the sheet music directory
                sheet_music_dir = os.path.join(PICTURES_DIR, "sheet_music")
                os.makedirs(sheet_music_dir, exist_ok=True)
                
                # Create a filename based on the song name
                sheet_music_filename = f"{os.path.splitext(st.session_state.current_song)[0]}_sheet.{uploaded_file.name.split('.')[-1]}"
                sheet_music_path = os.path.join(sheet_music_dir, sheet_music_filename)
                
                # Save the file
                with open(sheet_music_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                # Store in session state
                st.session_state.sheet_music[st.session_state.current_song] = sheet_music_path
                st.success(f"Sheet music saved for {st.session_state.current_song.replace('.mp3', '')}")
            
            # Display existing sheet music if available
            if st.session_state.current_song in st.session_state.sheet_music and os.path.exists(st.session_state.sheet_music[st.session_state.current_song]):
                st.image(st.session_state.sheet_music[st.session_state.current_song], caption=f"Sheet Music for {st.session_state.current_song.replace('.mp3', '')}", use_column_width=True)
            else:
                # Check if there's a sheet music file with the song name in the sheet_music directory
                sheet_music_dir = os.path.join(PICTURES_DIR, "sheet_music")
                os.makedirs(sheet_music_dir, exist_ok=True)
                
                possible_extensions = [".jpg", ".jpeg", ".png", ".pdf"]
                found_sheet_music = False
                
                for ext in possible_extensions:
                    sheet_music_path = os.path.join(sheet_music_dir, f"{os.path.splitext(st.session_state.current_song)[0]}_sheet{ext}")
                    if os.path.exists(sheet_music_path):
                        st.session_state.sheet_music[st.session_state.current_song] = sheet_music_path
                        st.image(sheet_music_path, caption=f"Sheet Music for {st.session_state.current_song.replace('.mp3', '')}", use_column_width=True)
                        found_sheet_music = True
                        break
                
                if not found_sheet_music:
                    st.info("No sheet music available for this song. Upload using the file uploader above.")
    else:
        st.info("No song is currently playing. Select a song from the Music Library.")

def display_queue_and_history():
    """Display the queue and history page."""
    st.header("Queue & History")
    
    # If a song is currently playing, just show the song info (player is in sidebar)
    if st.session_state.audio_playing and st.session_state.current_song:
        # Display a compact version of the current song info
        st.markdown(f"**Currently Playing:** {st.session_state.current_song.replace('.mp3', '')}")
        
        # Add a stop button that matches the one in the sidebar
        if st.button("⏹️ Stop Playback", key="queue_history_stop_audio"):
            st.session_state.audio_playing = False
            st.session_state.audio_data = None
            # We don't force a rerun here to prevent disrupting the queue
            # The UI will update naturally on the next rerun
    
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
                        # When playing from queue manually, check if replay is enabled
                        # If replay is enabled, we want to preserve the queue regardless of autoplay setting
                        # This ensures songs remain in the queue for continuous playback when replay is enabled
                        play_from_queue(i, remove_after_playing=not st.session_state.replay)
                with col3:
                    if st.button("❌", key=f"remove_queue_{i}"):
                        remove_from_queue(i)
                        # We don't force a rerun here to prevent disrupting the queue
                        # The UI will update naturally on the next rerun
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
    
    # If a song is currently playing, just show the song info (player is in sidebar)
    if st.session_state.audio_playing and st.session_state.current_song:
        # Display a compact version of the current song info
        st.markdown(f"**Currently Playing:** {st.session_state.current_song.replace('.mp3', '')}")
        
        # Add a stop button that matches the one in the sidebar
        if st.button("⏹️ Stop Playback", key="pictures_stop_audio"):
            st.session_state.audio_playing = False
            st.session_state.audio_data = None
            # We don't force a rerun here to prevent disrupting the queue
            # The UI will update naturally on the next rerun
    
    # Create tabs for general pictures and sheet music
    general_tab, sheet_music_tab = st.tabs(["General Pictures", "Sheet Music"])
    
    with general_tab:
        # Load pictures
        _, picture_files = load_content()
        
        if not picture_files:
            st.warning("No pictures found in the directory.")
        else:
            # Display pictures in a grid
            cols = st.columns(3)
            for i, picture_file in enumerate(picture_files):
                with cols[i % 3]:
                    st.image(
                        os.path.join(PICTURES_DIR, picture_file),
                        caption=picture_file,
                        use_column_width=True
                    )
    
    with sheet_music_tab:
        # Check for sheet music directory
        sheet_music_dir = os.path.join(PICTURES_DIR, "sheet_music")
        os.makedirs(sheet_music_dir, exist_ok=True)
        
        # Get all sheet music files
        sheet_music_files = [f for f in os.listdir(sheet_music_dir) 
                            if os.path.isfile(os.path.join(sheet_music_dir, f)) and 
                            f.lower().endswith(('.jpg', '.jpeg', '.png', '.pdf'))]
        
        if not sheet_music_files:
            st.warning("No sheet music images found. Upload sheet music from the Music Library or Now Playing pages.")
        else:
            # Group sheet music by song name (remove _sheet and extension)
            sheet_music_by_song = {}
            for file in sheet_music_files:
                song_name = file.replace('_sheet', '').split('.')[0]
                if song_name not in sheet_music_by_song:
                    sheet_music_by_song[song_name] = []
                sheet_music_by_song[song_name].append(file)
            
            # Display sheet music grouped by song
            for song_name, files in sheet_music_by_song.items():
                st.subheader(f"{song_name}")
                cols = st.columns(min(len(files), 3))
                for i, file in enumerate(files):
                    with cols[i % 3]:
                        st.image(
                            os.path.join(sheet_music_dir, file),
                            caption=file,
                            use_column_width=True
                        )
                st.markdown("---")

def display_about():
    """Display the about page."""
    st.header("About Gospel JukeBox")
    
    # If a song is currently playing, just show the song info (player is in sidebar)
    if st.session_state.audio_playing and st.session_state.current_song:
        # Display a compact version of the current song info
        st.markdown(f"**Currently Playing:** {st.session_state.current_song.replace('.mp3', '')}")
        
        # Add a stop button that matches the one in the sidebar
        if st.button("⏹️ Stop Playback", key="about_stop_audio"):
            st.session_state.audio_playing = False
            st.session_state.audio_data = None
            # We don't force a rerun here to prevent disrupting the queue
            # The UI will update naturally on the next rerun
    
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
    main()
