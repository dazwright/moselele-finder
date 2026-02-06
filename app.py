import streamlit as st
import pandas as pd
import os
import re
from collections import Counter
import qrcode
from io import BytesIO
from urllib.parse import quote

# --- CONFIGURATION ---
POSSIBLE_SONG_FILES = ["moselele_songs_final_clean.csv", "moselele_songs_cleaned.csv", "moselele_songs.csv"]
CHORDS_LIB_FILE = "chords.csv"
CHORD_IMG_DIR = "chord_images"
MEDIA_DIR = "media"
FAVICON_PATH = os.path.join(MEDIA_DIR, "moselele-icon-black.jpg")
LOGO_PATH = os.path.join(MEDIA_DIR, "moselele-logo-black_v_small.jpg")

# --- CALLBACKS ---
def handle_playlist_click(song_id):
    if "playlist" not in st.session_state: st.session_state.playlist = []
    if song_id not in st.session_state.playlist: st.session_state.playlist.append(song_id)

def clear_playlist():
    st.session_state.playlist = []

def add_genre(genre):
    if "active_genres" not in st.session_state: st.session_state.active_genres = []
    if genre not in st.session_state.active_genres: st.session_state.active_genres.append(genre)

def refresh_page():
    st.session_state.random_active = False
    st.session_state.active_genres = []
    st.session_state["refresh_seed"] = st.session_state.get("refresh_seed", 0) + 1

# --- QR CODE GENERATOR ---
def generate_qr(data):
    qr = qrcode.QRCode(version=1, box_size=10, border=2)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

# --- TEXT PROCESSING ---
def clean_and_bold_lyrics(text):
    if not text: return ""
    text = re.sub(r'MOSELELE\.CO\.UK', '', text, flags=re.IGNORECASE)
    text = text.replace("**", "")
    return re.sub(r'(\[[^\]]+\])', r'<b>\1</b>', text)

@st.cache_data
def load_data():
    target_file = next((f for f in POSSIBLE_SONG_FILES if os.path.exists(f)), None)
    if not target_file: return pd.DataFrame()
    df = pd.read_csv(target_file)
    df.columns = [c.strip() for c in df.columns]
    for col in df.columns: df[col] = df[col].fillna("").astype(str).strip()
    return df

# --- PAGE CONFIG ---
st.set_page_config(page_title="Moselele Database", page_icon=FAVICON_PATH if os.path.exists(FAVICON_PATH) else "🎸", layout="wide")

st.markdown("""
    <style>
    [data-testid="stImage"] img { border-radius: 0px !important; }
    .lyrics-box { white-space: pre-wrap; background-color: #fdfdfd; padding: 25px; border: 1px solid #eee; border-radius: 8px; font-size: 1.1rem; line-height: 1.6; color: #31333F; font-family: sans-serif; }
    .lyrics-box b { font-weight: 800; color: #000; }
    .stExpander { border: 1px solid #e6e6e6; }
    .action-btn { text-decoration: none; color: #31333F !important; border: 1px solid #ccc; width: 100%; height: 38px; display: flex; align-items: center; justify-content: center; border-radius: 5px; font-size: 0.85rem; background-color: #fff; margin-top: 5px; }
    .stButton button { width: 100%; height: 38px; margin-top: 5px; }
    </style>
""", unsafe_allow_html=True)

# --- SESSION INITIALIZATION ---
if 'playlist' not in st.session_state: st.session_state.playlist = []
if 'active_genres' not in st.session_state: st.session_state.active_genres = []

def main():
    col_logo, col_title = st.columns([1, 5])
    with col_logo:
        if os.path.exists(LOGO_PATH): st.image(LOGO_PATH, width=120)
    with col_title: st.title("Moselele song database")

    df = load_data()
    chord_lib = pd.read_csv(CHORDS_LIB_FILE) if os.path.exists(CHORDS_LIB_FILE) else pd.DataFrame()

    # --- SIDEBAR ---
    st.sidebar.button("🔄 Refresh Selection", on_click=refresh_page, use_container_width=True)
    st.sidebar.divider()
    
    # SEARCH & FILTERS
    search_query = st.sidebar.text_input("Search", "").lower()
    selected_genres = st.sidebar.multiselect("Genres", options=[], key="active_genres") # Simplified for space

    # PLAYLIST & QR SECTION
    st.sidebar.divider()
    st.sidebar.subheader(f"Playlist ({len(st.session_state.playlist)})")
    if st.session_state.playlist:
        for p in st.session_state.playlist:
            st.sidebar.caption(f"• {p}")
        
        # QR Code Generation
        st.sidebar.write("---")
        st.sidebar.write("**Scan to Share Playlist**")
        base_url = "https://moselele-finder.streamlit.app/" # Adjust to your actual URL
        share_str = ",".join(st.session_state.playlist)
        qr_url = f"{base_url}?playlist={quote(share_str)}"
        
        qr_img = generate_qr(qr_url)
        st.sidebar.image(qr_img, use_container_width=True)
        
        if st.sidebar.button("Clear Playlist", on_click=clear_playlist): st.rerun()

    # --- FILTERING & MAIN LOOP (Standard Logic) ---
    # [Insert filtering/loop logic here as per previous versions]

if __name__ == "__main__":
    main()