import streamlit as st
import os
import base64

# Define the application paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MP3_DIR = os.path.join(BASE_DIR, "mp3_files")
PICTURES_DIR = os.path.join(BASE_DIR, "pictures")

# Ensure directories exist
os.makedirs(MP3_DIR, exist_ok=True)
os.makedirs(PICTURES_DIR, exist_ok=True)

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

def play_audio(file_path):
    """Plays an audio file in Streamlit using the audio component."""
    try:
        with open(file_path, "rb") as audio_file:
            audio_data = audio_file.read()
            b64 = base64.b64encode(audio_data).decode()
            audio_html = f"""
                <audio controls>
                <source src="data:audio/mpeg;base64,{b64}" type="audio/mpeg">
                Your browser does not support the audio element.
                </audio>
            """
            st.markdown(audio_html, unsafe_allow_html=True)
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

def display_mp3_player():
    st.title("Gospel JukeBox")

    # Load songs and pictures
    mp3_files, picture_files = load_content()

    if not mp3_files:
        st.warning("No MP3 files found in the directory.")
        return

    # Initialize queue and history
    queue = []
    history = []

    # Display MP3 files
    st.header("Music")
    for mp3_file in mp3_files:
        file_path = os.path.join(MP3_DIR, mp3_file)

        # Play button for each MP3 file
        if st.button(f"Play {mp3_file}"):
            play_audio(file_path)
            history.append(mp3_file)  # Add to history
            lyrics = load_lyrics(file_path)  # Load lyrics for the currently playing song
            st.text_area("Lyrics", lyrics, height=200)  # Display lyrics in a context window

        if st.button(f"Add {mp3_file} to Queue"):
            queue.append(mp3_file)  # Add to queue
            st.success(f"{mp3_file} added to queue.")

        st.write("---")  # Add separator between files

    # Display Queue
    st.header("Queue")
    if queue:
        for song in queue:
            st.write(f"- {song}")
    else:
        st.write("Queue is empty.")

    # Display Pictures
    st.header("Pictures")
    if not picture_files:
        st.warning("No pictures found in the directory.")
    else:
        for picture_file in picture_files:
            st.image(os.path.join(PICTURES_DIR, picture_file), caption=picture_file)

    # Donation button
    cashapp_url = "https://cash.app/$SolidBuildersInc/"
    st.markdown(
        f'<a href="{cashapp_url}" target="_blank"><button style="background-color:#00D632; color:white; padding:8px 16px; border:none; border-radius:4px; cursor:pointer;">Donate with Cash App</button></a>',
        unsafe_allow_html=True,
    )

def main():
    display_mp3_player()  # Display the MP3 player section

if __name__ == "__main__":
    main()
