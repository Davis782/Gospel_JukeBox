import os
from dotenv import load_dotenv
from supabase import create_client, Client
import streamlit as st
from datetime import datetime
import base64
import webbrowser

# Load environment variables and initialize Supabase client
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Streamlit page config
st.set_page_config(
    page_title="Gospel JukeBox (Supabase)",
    page_icon="🎵",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Directories
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MP3_DIR = os.getenv("MP3_DIR", os.path.join(BASE_DIR, "mp3_files"))
PICTURES_DIR = os.getenv("PICTURES_DIR", os.path.join(BASE_DIR, "pictures"))
os.makedirs(MP3_DIR, exist_ok=True)
os.makedirs(os.path.join(PICTURES_DIR, "sheet_music"), exist_ok=True)

# --- Authentication ---
def login_page():
    st.header("Login")
    user = st.text_input("Username")
    pwd = st.text_input("Password", type="password")
    if st.button("Login"):
        res = (supabase
               .table("users")
               .select("username, password_hash, role")
               .eq("username", user)
               .execute())
        data = res.data[0] if res.data else None
        if data and data.get("password_hash") == pwd:
            st.session_state.logged_in = True
            st.session_state.username = user
            st.session_state.role = data.get("role")
            st.success("Logged in!")
        else:
            st.error("Invalid credentials")

# --- Content loader ---
def load_content():
    return sorted(f for f in os.listdir(MP3_DIR) if f.endswith('.mp3'))

# --- Supabase helpers ---
def get_labels_for_song_instrument(song_title, instrument):
    res = (supabase
           .table("labels")
           .select("name, owner_id")
           .eq("song_title", song_title)
           .eq("instrument", instrument)
           .execute())
    return [(r["name"], r["owner_id"]) for r in res.data] if res.data else []


def fetch_notes(song_title):
    res = (supabase
           .table("notes")
           .select("owner_id, content, label")
           .eq("song_title", song_title)
           .order("owner_id", {"ascending": True})
           .execute())
    return res.data if res.data else []


def add_note(song_title, owner_id, label, content):
    payload = {
        "song_title": song_title,
        "owner_id": owner_id,
        "label": label,
        "content": content,
        "created_at": datetime.utcnow().isoformat()
    }
    supabase.table("notes").insert(payload).execute()

# --- Main page: Music Library ---
def display_music_library():
    st.header("Music Library")
    mp3_files = load_content()

    # Search
    search_query = st.text_input("Search songs by title, sheet music label, or note label")
    if search_query:
        by_title = [s for s in mp3_files if search_query.lower() in s.lower()]
        lab = (supabase.table("labels").select("song_title")
               .like("name", f"%{search_query}%").execute().data or [])
        note = (supabase.table("notes").select("song_title")
                .like("label", f"%{search_query}%").execute().data or [])
        label_matches = [r["song_title"] for r in lab]
        note_matches = [r["song_title"] for r in note]
        filtered_songs = list(set(by_title + label_matches + note_matches))
    else:
        filtered_songs = mp3_files

    # Song selector
    selected_song = st.selectbox("Select Song", filtered_songs)
    if not selected_song:
        return
    st.subheader(selected_song.replace('.mp3', ''))

    # --- Notes Section ---
    st.markdown("---")
    st.markdown("### Notes")
    notes = fetch_notes(selected_song)
    if notes:
        unique_labels = sorted({n["label"] for n in notes if n.get("label")})
        mode = st.radio("Existing Notes View", ["All notes", "Labels only", "Filter by label"], index=0)
        if mode == "Labels only":
            if unique_labels:
                for lbl in unique_labels:
                    st.write(f"- {lbl}")
            else:
                st.info("No labels to display.")
        else:
            if mode == "Filter by label" and unique_labels:
                sel = st.selectbox("Select label to filter notes", unique_labels)
                filtered = [n for n in notes if n.get("label") == sel]
            else:
                filtered = notes
            for n in filtered:
                lbl = n.get("label", "[No Label]")
                st.text_area(f"Note by {n['owner_id']} ({lbl})", n.get("content", ""), height=100, disabled=True)
    else:
        st.info("No notes found for this song yet.")

    # --- Add New Note (Logged-in users) ---
    if st.session_state.get('logged_in'):
        st.markdown("---")
        st.markdown("#### Add Your Note")
        with st.form('add_note_form'):
            new_lbl = st.text_input("Note Label")
            new_content = st.text_area("Note Content", height=100)
            submitted = st.form_submit_button("Add Note")
            if submitted and new_content.strip():
                add_note(selected_song, st.session_state.username, new_lbl, new_content)
                st.experimental_rerun()

# --- About Page ---
def display_about():
    st.header("About")
    st.write("This is the Supabase-backed version of Gospel JukeBox.")

# --- App entry point ---
def main():
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
        st.session_state.username = None
        st.session_state.role = None

    page = st.sidebar.radio("Page", ["Login", "Music Library", "About"])
    if page == "Login":
        login_page()
    elif page == "Music Library":
        display_music_library()
    else:
        display_about()

if __name__ == "__main__":
    main()
