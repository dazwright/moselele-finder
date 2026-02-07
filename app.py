import streamlit as st
import pandas as pd
import os
import re
from collections import Counter
import qrcode
from io import BytesIO
from urllib.parse import quote, unquote

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
    if song_id not in st.session_state.playlist:
        st.session_state.playlist.append(song_id)
    else:
        st.session_state.playlist.remove(song_id)

def clear_playlist():
    st.session_state.playlist = []
    st.session_state.view_playlist = False

def add_genre(genre):
    if "active_genres" not in st.session_state: st.session_state.active_genres = []
    if genre not in st.session_state.active_genres:
        st.session_state.active_genres.append(genre)

def refresh_page():
    st.session_state.random_active = False
    st.session_state.active_genres = []
    st.session_state.view_playlist = False
    st.session_state["refresh_seed"] = st.session_state.get("refresh_seed", 0) + 1

def toggle_playlist_view():
    st.session_state.view_playlist = not st.session_state.get('view_playlist', False)

# --- UTILITIES ---
def generate_qr(data):
    qr = qrcode.QRCode(version=1, box_size=10, border=2)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

def clean_and_bold_lyrics(text):
    if not text: return ""
    text = re.sub(r'MOSELELE\.CO\.UK', '', text, flags=re.IGNORECASE)
    text = text.replace("**", "")
    text = re.sub(r'([^\s\-\[])(\[)', r'\1 \2', text)
    text = re.sub(r'(\])([^\s\-\]])', r'\1 \2', text)
    return re.sub(r'(\[[^\]]+\])', r'<b>\1</b>', text)

@st.cache_data
def load_all_data():
    target_file = next((f for f in POSSIBLE_SONG_FILES if os.path.exists(f)), None)
    songs = pd.read_csv(target_file) if target_file else pd.DataFrame()
    chords = pd.read_csv(CHORDS_LIB_FILE) if os.path.exists(CHORDS_LIB_FILE) else pd.DataFrame()
    if not songs.empty:
        songs.columns = [c.strip() for c in songs.columns]
        for col in songs.columns: songs[col] = songs[col].fillna("").astype(str).str.strip()
    if not chords.empty:
        chords.columns = [c.strip() for c in chords.columns]
        for col in chords.columns: chords[col] = chords[col].fillna("").astype(str).str.strip()
    return songs, chords

# --- PAGE CONFIG ---
st.set_page_config(page_title="Moselele Database", page_icon=FAVICON_PATH if os.path.exists(FAVICON_PATH) else "🎸", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    /* Ensure the Sidebar Toggle is visible on tablets */
    [data-testid="stSidebarCollapsedControl"] {
        background-color: rgba(255, 255, 255, 0.8);
        border-radius: 0 5px 5px 0;
        padding: 5px;
        top: 10px;
        left: 0;
        display: flex !important;
    }

    /* Maximize Tablet Space */
    .main .block-container { padding-top: 2rem; padding-bottom: 1rem; padding-left: 1rem; padding-right: 1rem; }
    [data-testid="stHeader"] { height: 0px; }
    
    .app-title { font-size: 1.6rem; font-weight: 700; color: #31333F; margin-bottom: 0.5rem; }

    /* Lyrics Box */
    .lyrics-box { white-space: pre-wrap; background-color: #fdfdfd; padding: 20px; border: 1px solid #eee; border-radius: 8px; font-size: 1.1rem; line-height: 1.6; color: #31333F; }
    .lyrics-box b { font-weight: 800; color: #000; }
    
    /* Small Square Logo fix */
    [data-testid="stSidebar"] img { border-radius: 0px !important; }
    </style>
""", unsafe_allow_html=True)

# --- SESSION INITIALIZATION ---
if 'playlist' not in st.session_state: st.session_state.playlist = []
if 'active_genres' not in st.session_state: st.session_state.active_genres = []
if 'view_playlist' not in st.session_state: st.session_state.view_playlist = False
if 'refresh_seed' not in st.session_state: st.session_state.refresh_seed = 42

# --- MAIN APP ---
def main():
    st.markdown('<div class="app-title">Moselele song database</div>', unsafe_allow_html=True)

    df, chord_lib = load_all_data()
    if df.empty: return

    # --- SIDEBAR ---
    if os.path.exists(LOGO_PATH): st.sidebar.image(LOGO_PATH, width=150)
    st.sidebar.button("🔄 Refresh Selection", on_click=refresh_page, use_container_width=True)
    
    st.sidebar.divider()
    search_query = st.sidebar.text_input("Search", "").lower()
    book_filter = st.sidebar.multiselect("Books", options=sorted(df['Book'].unique()) if 'Book' in df.columns else [])
    st.sidebar.multiselect("Genres", options=sorted(list(set([t.strip() for val in df['Tags'] for t in val.split(',') if t.strip()]))) if 'Tags' in df.columns else [], key="active_genres")

    # Playlist View Toggle
    st.sidebar.divider()
    playlist_count = len(st.session_state.playlist)
    if st.sidebar.button(f"❤️ View Playlist ({playlist_count})", use_container_width=True):
        toggle_playlist_view()

    if st.session_state.playlist:
        share_url = f"https://moselele-finder.streamlit.app/?playlist={quote(','.join(st.session_state.playlist))}"
        qr_img = generate_qr(share_url)
        st.sidebar.image(qr_img, caption="Share Playlist", width=120)
        st.sidebar.button("Clear Playlist", on_click=clear_playlist)

    # --- FILTERING ---
    f_df = df.copy()
    if st.session_state.view_playlist and st.session_state.playlist:
        f_df['song_id'] = f_df['Title'] + " (" + f_df['Artist'] + ")"
        f_df = f_df[f_df['song_id'].isin(st.session_state.playlist)]
    else:
        if search_query:
            f_df = f_df[f_df['Title'].str.lower().str.contains(search_query) | f_df['Artist'].str.lower().str.contains(search_query)]
        if book_filter:
            f_df = f_df[f_df['Book'].isin(book_filter)]
        if st.session_state.active_genres:
            f_df = f_df[f_df['Tags'].apply(lambda x: any(g in [s.strip() for s in x.split(',')] for g in st.session_state.active_genres))]
        if not any([search_query, book_filter, st.session_state.active_genres]):
            f_df = f_df.sample(n=min(50, len(f_df)), random_state=st.session_state.refresh_seed)

    # --- MAIN DISPLAY LOOP ---
    st.write(f"Displaying **{len(f_df)}** songs")
    
    for idx, song in f_df.iterrows():
        song_id = f"{song['Title']} ({song['Artist']})"
        is_loved = song_id in st.session_state.playlist
        heart = "❤️" if is_loved else "🤍"
        
        # COLUMN 1: Song Info | COLUMN 2: PDF | COLUMN 3: Heart
        # This puts the icons right in the main result bar
        title_col, pdf_col, heart_col = st.columns([8, 1, 1])
        
        with title_col:
            header_text = f"{song['Title']} - {song['Artist']} | {song['Book']} | P.{song['Page']}"
            exp = st.expander(header_text)
        
        with pdf_col:
            if song.get('URL'):
                st.markdown(f'<a href="{song["URL"]}" target="_blank" style="text-decoration:none; font-size:1.5rem;">📄</a>', unsafe_allow_html=True)
        
        with heart_col:
            st.button(heart, key=f"btn_h_{idx}", on_click=handle_playlist_click, args=(song_id,))

        with exp:
            # Chords & Body
            chord_str = song.get('Chords', '').strip()
            if chord_str:
                s_chords = [c.strip() for c in chord_str.split(',') if c.strip()]
                v_imgs, v_caps = [], []
                if not chord_lib.empty:
                    for cn in s_chords:
                        m = chord_lib[chord_lib['Chord Name'].str.lower() == cn.lower()]
                        if not m.empty:
                            ip = os.path.join(CHORD_IMG_DIR, str(m.iloc[0]['Path']))
                            if os.path.exists(ip):
                                v_imgs.append(ip); v_caps.append(cn)
                if v_imgs: st.image(v_imgs, width=65, caption=v_caps)
                else: st.write(f"**Chords:** {chord_str}")
            
            if song['Body']:
                st.markdown(f'<div class="lyrics-box">{clean_and_bold_lyrics(song["Body"].strip())}</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()