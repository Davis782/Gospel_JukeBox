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
    # Fetch notes with label_id, then join with labels to get label name
    notes_res = (
        supabase
        .table("notes")
        .select("owner_id, content, label_id")
        .eq("song_title", song_title)
        .order("owner_id", {"ascending": True})
        .execute()
    )
    notes = notes_res.data if notes_res.data else []
    if not notes:
        return []
    # Fetch all label ids for this song
    label_ids = list({n["label_id"] for n in notes if n.get("label_id")})
    if not label_ids:
        for n in notes:
            n["label"] = None
        return notes
    label_map = {}
    if label_ids:
        label_res = (
            supabase
            .table("labels")
            .select("id, name")
            .in_("id", label_ids)
            .execute()
        )
        for l in (label_res.data or []):
            label_map[l["id"]] = l["name"]
    for n in notes:
        n["label"] = label_map.get(n.get("label_id"), None)
    return notes


def add_note(song_title, owner_id, label, content):
    # Look up label_id for the given label name and song_title
    label_id = None
    label_res = (
        supabase
        .table("labels")
        .select("id")
        .eq("song_title", song_title)
        .eq("name", label)
        .maybe_single()
        .execute()
    )
    if label_res.data:
        label_id = label_res.data["id"]
    payload = {
        "song_title": song_title,
        "owner_id": owner_id,
        "label_id": label_id,
        "content": content,
        "created_at": datetime.utcnow().isoformat()
    }
    supabase.table("notes").insert(payload).execute()

# --- Sheet Music Helpers ---
def fetch_sheet_music(song_title):
    # Fetch all sheet music for a song, joining with labels
    res = (
        supabase
        .table("sheet_music")
        .select("id, file_path, label_id, upload_date, label:label_id(name)")
        .eq("song_name", song_title)
        .order("upload_date", {"ascending": False})
        .execute()
    )
    return res.data if res.data else []

def fetch_labels_for_song(song_title):
    res = (
        supabase
        .table("labels")
        .select("id, name")
        .eq("song_title", song_title)
        .execute()
    )
    return res.data if res.data else []

def insert_sheet_music(song_title, label_id, file_obj, file_name, user_id):
    # Upload file to Supabase Storage (bucket: sheet_music_files)
    bucket = "sheet_music_files"
    storage_path = f"{song_title}/{label_id}/{file_name}"
    supabase.storage.from_(bucket).upload(storage_path, file_obj, file_options={"content-type": "application/pdf"})
    # Insert reference into sheet_music table
    payload = {
        "song_name": song_title,
        "label_id": label_id,
        "file_path": storage_path,
        "owner_id": user_id,
        "upload_date": datetime.utcnow().isoformat()
    }
    supabase.table("sheet_music").insert(payload).execute()

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
        # Find label ids matching the search
        matching_labels = (
            supabase.table("labels").select("id, song_title")
            .like("name", f"%{search_query}%").execute().data or []
        )
        matching_label_ids = [r["id"] for r in matching_labels]
        note = (
            supabase.table("notes").select("song_title, label_id")
            .in_("label_id", matching_label_ids)
            .execute().data or []
        ) if matching_label_ids else []
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

    # --- Sheet Music Section ---
    st.markdown("---")
    st.markdown("### Sheet Music")
    sheet_music_list = fetch_sheet_music(selected_song)
    labels = fetch_labels_for_song(selected_song)
    label_map = {l['id']: l['name'] for l in labels}
    label_names = [l['name'] for l in labels]
    label_id_to_name = {l['id']: l['name'] for l in labels}

    # Filter by label/type
    filter_label = None
    if label_names:
        filter_label = st.selectbox("Filter sheet music by label/type", ["All"] + label_names)
    filtered_sheet_music = sheet_music_list
    if filter_label and filter_label != "All":
        filtered_sheet_music = [sm for sm in sheet_music_list if label_id_to_name.get(sm['label_id']) == filter_label]
    if filtered_sheet_music:
        for sm in filtered_sheet_music:
            label = label_id_to_name.get(sm['label_id'], "[No Label]")
            st.write(f"- [{os.path.basename(sm['file_path'])}] (Label: {label})")
    else:
        st.info("No sheet music uploaded for this song.")

    # --- Upload Sheet Music (Logged-in users) ---
    if st.session_state.get('logged_in'):
        st.markdown("#### Upload Sheet Music")
        with st.form('upload_sheet_music_form'):
            label_options = [l['name'] for l in labels]
            label_choice = st.selectbox("Select label/type for this sheet music", label_options) if label_options else None
            upload_file = st.file_uploader("Upload PDF file", type=["pdf"])
            submitted = st.form_submit_button("Upload Sheet Music")
            if submitted and upload_file and label_choice:
                label_id = next((l['id'] for l in labels if l['name'] == label_choice), None)
                if label_id:
                    insert_sheet_music(selected_song, label_id, upload_file, upload_file.name, st.session_state.username)
                    st.success("Sheet music uploaded!")
                    st.experimental_rerun()
                else:
                    st.error("Selected label not found. Please create the label first.")

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
