import os
import base64
import sqlite3
import streamlit as st
from datetime import datetime
import matplotlib.pyplot as plt
from streamlit import components

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

# Initialize SQLite database for votes and sheet music
def init_db():
    conn = sqlite3.connect('votes.db')
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
        CREATE TABLE IF NOT EXISTS instrument_sheet_music (
            song_name TEXT,
            instrument TEXT,
            file_path TEXT,
            PRIMARY KEY (song_name, instrument)
        )
    ''')
    
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
    'last_check_time': datetime.now(),  # For the 20-second timer loop
    'check_interval': 10,  # Check interval in seconds (reduced for more responsive autoplay)
    'song_start_timestamp': None,  # Full timestamp when song started
    'estimated_song_duration': 180,  # Default estimated song duration in seconds (3 minutes)
    'force_next_song': False  # Flag to force playing the next song
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value

def encode_audio_to_base64(file_path):
    """Encode audio to base64."""
    with open(file_path, "rb") as audio_file:
        return base64.b64encode(audio_file.read()).decode('utf-8')

def play_audio(file_path, song_name):
    """Play an audio file."""
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
    """Add a song to the queue dynamically without full page refresh."""
    if song_name not in st.session_state.queue:
        st.session_state.queue.append(song_name)  # Add song to queue
        st.session_state.queue = list(set(st.session_state.queue))  # Ensure unique entries
        st.session_state.queue_updated = True  # Flag for UI refresh
        return True
    return False

def play_from_queue(index):
    """Play a song from the queue."""
    if 0 <= index < len(st.session_state.queue):
        song_name = st.session_state.queue[index]
        play_audio(os.path.join(MP3_DIR, song_name), song_name)
        if not st.session_state.replay:
            st.session_state.queue.pop(index)

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
    
    # If song ended or force_next_song flag is set and autoplay is enabled, play next song
    if st.session_state.song_ended or st.session_state.force_next_song:
        print(f"Song ended or force next detected, checking for autoplay. Song ended: {st.session_state.song_ended}, Force next: {st.session_state.force_next_song}")
        st.session_state.song_ended = False  # Reset flag
        st.session_state.force_next_song = False  # Reset force next flag

        if st.session_state.autoplay and st.session_state.queue:
            print(f"Autoplay enabled, playing next song from queue: {st.session_state.queue[0]}")
            play_from_queue(0)  # Automatically play next song
            st.success("Autoplay: Started next song in queue")
            st.rerun()  # Force UI refresh
        elif st.session_state.autoplay and not st.session_state.queue:
            print("Autoplay enabled but queue is empty")
            st.warning("Autoplay is on, but there are no songs in the queue")
        elif not st.session_state.autoplay:
            print("Autoplay is disabled")
            st.info("Song ended. Enable autoplay to automatically play the next song.")

    with st.sidebar:
        st.title("Gospel JukeBox 🎵")

        # Display Currently Playing Song
        if st.session_state.audio_playing and st.session_state.current_song:
            st.markdown("### Now Playing")
            # Use HTML5 audio element with autoplay and controls
            audio_html = f"""
            <audio id="audio-player" autoplay controls>
                <source src="data:audio/mpeg;base64,{st.session_state.audio_data}" type="audio/mpeg">
                Your browser does not support the audio element.
            </audio>
            <script>
                // Ensure autoplay works
                document.getElementById('audio-player').play();
            </script>
            """
            st.components.v1.html(audio_html, height=80)

        # Navigation Buttons
        if st.button("Previous"):
            current_index = st.session_state.queue.index(st.session_state.current_song) if st.session_state.current_song in st.session_state.queue else -1
            if current_index > 0:
                play_from_queue(current_index - 1)
        if st.button("Next"):
            current_index = st.session_state.queue.index(st.session_state.current_song) if st.session_state.current_song in st.session_state.queue else -1
            if current_index >= 0 and current_index < len(st.session_state.queue) - 1:
                play_from_queue(current_index + 1)

        # Replay and Autoplay Toggles
        st.session_state.replay = st.checkbox("Replay", value=st.session_state.replay)
        st.session_state.autoplay = st.checkbox("Autoplay Next Song", value=st.session_state.autoplay)
        
        # Display countdown timer for next song with enhanced information
        if st.session_state.audio_playing and st.session_state.current_song and st.session_state.song_start_timestamp:
            current_time = datetime.now()
            song_play_duration = (current_time - st.session_state.song_start_timestamp).total_seconds()
            remaining_time = max(0, st.session_state.estimated_song_duration - song_play_duration)
            
            # Format times as MM:SS
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
            st.progress(progress)
            
            # Show comprehensive timing information
            st.markdown(f"**Current Song Time**: {elapsed_display} / {total_display}")
            
            # Show countdown with appropriate message based on autoplay setting and remaining time
            if remaining_time <= 0:
                # Song has reached its estimated end time
                if st.session_state.autoplay and st.session_state.queue:
                    st.markdown(f"**<span style='color:green'>Next song should be playing now!</span>**", unsafe_allow_html=True)
                    st.caption(f"If music hasn't changed, click 'Force Next Song' below")
                elif st.session_state.autoplay and not st.session_state.queue:
                    st.markdown(f"**<span style='color:orange'>Song has ended!</span>**", unsafe_allow_html=True)
                    st.caption("No songs in queue for autoplay")
                else:
                    st.markdown(f"**<span style='color:orange'>Song has ended!</span>**", unsafe_allow_html=True)
                    st.caption("Autoplay is disabled. Please select the next song manually.")
            else:
                # Song is still playing
                if st.session_state.autoplay and st.session_state.queue:
                    st.markdown(f"**Next song in**: {remaining_display}")
                    st.caption(f"Autoplay will start the next song automatically")
                elif st.session_state.autoplay and not st.session_state.queue:
                    st.markdown(f"**Song ends in**: {remaining_display}")
                    st.caption("No songs in queue for autoplay")
                else:
                    st.markdown(f"**Song ends in**: {remaining_display}")
                    st.caption("Autoplay is disabled")
            
            # Add a small spacer
            st.write("")
        
        # Manual trigger for next song (useful if autoplay doesn't trigger automatically)
        if st.button("Force Next Song") and st.session_state.queue:
            st.session_state.force_next_song = True
            st.rerun()

        # Display Queue
        st.markdown("### Current Queue")
        if st.session_state.queue:
            for i, song in enumerate(st.session_state.queue):
                st.write(f"{i + 1}. {song.replace('.mp3', '')}")
                if st.button(f"▶️ Play {song}", key=f"play_queue_{i}"):
                    play_from_queue(i)
        else:
            st.write("Queue is empty.")

def display_music_library():
    """Display the music library page."""
    st.header("Music Library")
    mp3_files = load_content()
    selected_song = st.selectbox("Select a song to play", options=mp3_files)

    # Create a row with two columns for the buttons
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        if st.button("▶️ Play Selected Song") and selected_song:
            play_audio(os.path.join(MP3_DIR, selected_song), selected_song)
    
    with col2:
        if st.button("➕ Add to Queue") and selected_song:
            if add_to_queue(selected_song):
                st.success(f"{selected_song} added to queue.")
            else:
                st.info(f"{selected_song} is already in queue.")
    
    with col3:
        # CashApp button
        cash_app_link = "https://cash.app/$SolidBuildersInc"
        st.markdown(f"<a href='{cash_app_link}' target='_blank'><button style='background-color:#00D632; color:white; border:none; border-radius:5px; padding:10px 15px; font-weight:bold;'>💵 Donate via CashApp</button></a>", unsafe_allow_html=True)

    if st.session_state.current_song:
        st.subheader(f"🎶 {st.session_state.current_song.replace('.mp3', '')}")
        st.write(f"Started playing at: {st.session_state.play_time}")

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
                notes = st.session_state.song_notes.get(st.session_state.current_song, "")
                notes_input = st.text_area("Song Notes", value=notes, height=150)
                if notes_input != notes:
                    st.session_state.song_notes[st.session_state.current_song] = notes_input
                    st.success("Notes saved!")
            else:
                # Sheet Music Display with Instrument Selection
                st.markdown("### Sheet Music")
                
                # Instrument selection dropdown
                selected_instrument = st.selectbox(
                    "Select Instrument", 
                    AVAILABLE_INSTRUMENTS,
                    index=AVAILABLE_INSTRUMENTS.index(st.session_state.selected_instrument)
                )
                
                # Update session state with selected instrument
                if selected_instrument != st.session_state.selected_instrument:
                    st.session_state.selected_instrument = selected_instrument
                    st.rerun()  # Refresh to apply the instrument change
                
                # Construct the sheet music path with instrument suffix
                sheet_music_path = os.path.join(
                    PICTURES_DIR, 
                    "sheet_music", 
                    f"{os.path.splitext(st.session_state.current_song)[0]}_{st.session_state.selected_instrument}.jpg"
                )
                
                # Check if instrument-specific sheet music exists in the database
                conn = sqlite3.connect('votes.db')
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT file_path FROM instrument_sheet_music WHERE song_name = ? AND instrument = ?", 
                    (st.session_state.current_song, st.session_state.selected_instrument)
                )
                db_result = cursor.fetchone()
                conn.close()
                
                # If found in database, use that path
                if db_result:
                    sheet_music_path = db_result[0]
                
                # Display sheet music if it exists
                if os.path.exists(sheet_music_path):
                    st.image(sheet_music_path, caption=f"{st.session_state.selected_instrument} Sheet Music", use_column_width=True)
                else:
                    st.warning(f"No sheet music available for {st.session_state.selected_instrument} on this song.")
                    uploaded_file = st.file_uploader(
                        f"Upload {st.session_state.selected_instrument} Sheet Music (JPG, PNG, PDF)", 
                        type=["jpg", "png", "pdf"],
                        key=f"upload_{st.session_state.selected_instrument}"
                    )
                    
                    if uploaded_file:
                        # Create sheet_music directory if it doesn't exist
                        sheet_music_dir = os.path.join(PICTURES_DIR, "sheet_music")
                        os.makedirs(sheet_music_dir, exist_ok=True)
                        
                        # Save the uploaded file with the song name and instrument suffix
                        save_path = os.path.join(
                            sheet_music_dir, 
                            f"{os.path.splitext(st.session_state.current_song)[0]}_{st.session_state.selected_instrument}.jpg"
                        )
                        
                        with open(save_path, "wb") as f:
                            f.write(uploaded_file.getbuffer())
                        
                        # Store the reference in the database
                        conn = sqlite3.connect('votes.db')
                        cursor = conn.cursor()
                        cursor.execute(
                            "INSERT OR REPLACE INTO instrument_sheet_music (song_name, instrument, file_path) VALUES (?, ?, ?)",
                            (st.session_state.current_song, st.session_state.selected_instrument, save_path)
                        )
                        conn.commit()
                        conn.close()
                        
                        st.success(f"{st.session_state.selected_instrument} sheet music uploaded successfully!")
                        st.rerun()  # Refresh to show the uploaded image

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
            conn = sqlite3.connect('votes.db')
            cursor = conn.cursor()
            cursor.execute("INSERT INTO votes (song_name, vote) VALUES (?, ?)", (song_to_vote, vote_amount))
            conn.commit()
            conn.close()

            # Open Cash App link in a new tab
            cash_app_link = f"https://cash.app/$SolidBuildersInc?amount={vote_amount}"
            st.markdown(f"[Click here to pay in Cash App]({cash_app_link})", unsafe_allow_html=True)

            st.success("Thank you for your vote! Please confirm your payment via Cash App.")

def display_results_page():
    """Display the voting results as a pie chart."""
    st.header("Vote Results")

    # Fetch votes from the database
    conn = sqlite3.connect('votes.db')
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

def main():
    # Navigation
    page = st.sidebar.selectbox("Select a Page", ["Music Library", "Vote", "Results", "About"])

    if page == "Music Library":
        display_mp3_player()
        display_music_library()
    elif page == "Vote":
        display_voting_page()
    elif page == "Results":
        display_results_page()
    elif page == "About":
        display_about()

if __name__ == "__main__":
    main()
