import os
import base64
import sqlite3
import streamlit as st
from datetime import datetime
import matplotlib.pyplot as plt
from mutagen.mp3 import MP3  # To get the length of the MP3 files

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

# Initialize SQLite database
def init_db():
    conn = sqlite3.connect('votes.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS votes (
            song_name TEXT,
            vote INTEGER
        )
    ''')
    conn.commit()
    conn.close()

init_db()

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

    # Get song length
    audio = MP3(file_path)
    st.session_state.current_playback_time = audio.info.length  # Length in seconds

    st.session_state.current_lyrics = load_lyrics(file_path)

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
    if st.session_state.audio_playing and st.session_state.current_song:
        elapsed_time = (datetime.now() - datetime.strptime(st.session_state.play_time, "%H:%M:%S")).total_seconds()
        if elapsed_time >= st.session_state.current_playback_time:  # Check against song length
            st.session_state.song_ended = True

    if st.session_state.song_ended:
        st.session_state.song_ended = False  # Reset flag
        if st.session_state.autoplay and st.session_state.queue:
            play_from_queue(0)  # Automatically play next song

    with st.sidebar:
        st.title("Gospel JukeBox 🎵")

        # Display Currently Playing Song
        if st.session_state.audio_playing and st.session_state.current_song:
            st.markdown("### Now Playing")
            st.audio(f"data:audio/mpeg;base64,{st.session_state.audio_data}", format='audio/mpeg')

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

        # Display Queue
        st.markdown("### Current Queue")
        if st.session_state.queue:
            for i, song in enumerate(st.session_state.queue):
                st.write(f"{i + 1}. {song.replace('.mp3', '')}")
                if st.button(f"▶️ Play {song}", key=f"play_queue_{i}"):
                    play_from_queue(i)
        else:
            st.write("Queue is empty.")

# ==========================================
def display_music_library():
    """Display the music library page."""
    st.header("Music Library")
    mp3_files = load_content()  # Load the songs
    selected_song = st.selectbox("Select a song to play", options=mp3_files)

    if st.button("▶️ Play Selected Song") and selected_song:
        play_audio(os.path.join(MP3_DIR, selected_song), selected_song)

    if st.button("➕ Add to Queue") and selected_song:
        if add_to_queue(selected_song):
            st.success(f"{selected_song} added to queue.")
        else:
            st.info(f"{selected_song} is already in queue.")

    # Display current song details if one is playing
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
                # Sheet Music Display with Error Handling and Image Upload Option
                sheet_music_path = os.path.join(PICTURES_DIR, "sheet_music", f"{os.path.splitext(st.session_state.current_song)[0]}_sheet.jpg")
                
                if os.path.exists(sheet_music_path):
                    st.markdown("### Sheet Music")
                    st.image(sheet_music_path, caption="Sheet Music", use_column_width=True)
                else:
                    st.warning("No sheet music available for this song.")
                    uploaded_file = st.file_uploader("Upload Sheet Music (JPG, PNG, PDF, etc.)", type=["jpg", "png", "pdf"])
                    
                    if uploaded_file:
                        save_path = os.path.join(PICTURES_DIR, "sheet_music", uploaded_file.name)
                        with open(save_path, "wb") as f:
                            f.write(uploaded_file.getbuffer())
                        st.success("Sheet music uploaded successfully!")

def display_mp3_player():
    """Display the MP3 player in the sidebar."""
    with st.sidebar:
        st.title("Gospel JukeBox 🎵")

        # Display Currently Playing Song
        if st.session_state.audio_playing and st.session_state.current_song:
            st.markdown("### Now Playing")
            st.audio(f"data:audio/mpeg;base64,{st.session_state.audio_data}", format='audio/mpeg')

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

        # Display Queue
        st.markdown("### Current Queue")
        if st.session_state.queue:
            for i, song in enumerate(st.session_state.queue):
                st.write(f"{i + 1}. {song.replace('.mp3', '')}")
                if st.button(f"▶️ Play {song}", key=f"play_queue_{i}"):
                    play_from_queue(i)
        else:
            st.write("Queue is empty.")

def add_to_queue(song_name):
    """Add a song to the queue dynamically without full page refresh."""
    if song_name not in st.session_state.queue:
        st.session_state.queue.append(song_name)  # Add song to queue
        st.session_state.queue = list(set(st.session_state.queue))  # Ensure unique entries
        return True
    return False
# ===========================================


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
    - View pictures related to the ministry
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
