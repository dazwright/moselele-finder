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
    /* Maximize Tablet Space */
    .main .block-container { padding-top: 1rem; padding-bottom: 1rem; }
    [data-testid="stHeader"] { visibility: hidden; }
    
    /* Title Styling */
    .app-title { font-size: 1.8rem; font-weight: 700; margin-bottom: 1rem; color: #31333F; }

    /* Lyrics Box */
    .lyrics-box { white-space: pre-wrap; background-color: #fdfdfd; padding: 20px; border: 1px solid #eee; border-radius: 8px; font-size: 1.1rem; line-height: 1.6; color: #31333F; }
    .lyrics-box b { font-weight: 800; color: #000; }
    
    /* Action Buttons in Header */
    .header-btn { text-decoration: none; color: #31333F !important; padding: 2px 8px; border: 1px solid #ccc; border-radius: 4px; background: white; font-size: 0.8rem; margin-left: 5px; }
    
    /* Sidebar adjustments for Mobile/Tablet */
    [data-testid="stSidebar"] { border-right: 1px solid #eee; }
    </style>
""", unsafe_allow_html=True)

# --- SESSION INITIALIZATION ---
if 'playlist' not in st.session_state: st.session_state.playlist = []
if 'active_genres' not in st.session_state: st.session_state.active_genres = []
if 'view_playlist' not in st.session_state: st.session_state.view_playlist = False
if 'refresh_seed' not in st.session_state: st.session_state.refresh_seed = 42

# Handle QR Link
if "playlist" in st.query_params:
    shared = unquote(st.query_params["playlist"]).split(",")
    for s in shared:
        if s and s not in st.session_state.playlist: st.session_state.playlist.append(s)

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
    
    all_tags = []
    if 'Tags' in df.columns:
        for val in df['Tags']: all_tags.extend([t.strip() for t in val.split(',') if t.strip()])
    genre_counts = Counter(all_tags)
    st.sidebar.multiselect("Genres", options=sorted(genre_counts.keys()), key="active_genres")

    # Playlist Section
    st.sidebar.divider()
    playlist_label = f"❤️ Playlist ({len(st.session_state.playlist)})"
    if st.sidebar.button(playlist_label, use_container_width=True, help="Click to view these songs"):
        toggle_playlist_view()

    if st.session_state.playlist:
        if st.session_state.view_playlist:
            st.sidebar.info("Currently viewing Playlist items.")
        
        share_url = f"https://moselele-finder.streamlit.app/?playlist={quote(','.join(st.session_state.playlist))}"
        qr_img = generate_qr(share_url)
        st.sidebar.image(qr_img, caption="Share Playlist", width=150)
        st.sidebar.button("Clear Playlist", on_click=clear_playlist)

    # --- FILTERING ---
    f_df = df.copy()
    
    # Priority View: If Playlist Heading was clicked
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

    # --- MAIN LOOP ---
    st.write(f"Displaying **{len(f_df)}** songs")
    
    for idx, song in f_df.iterrows():
        song_id = f"{song['Title']} ({song['Artist']})"
        is_loved = song_id in st.session_state.playlist
        heart = "❤️" if is_loved else "🤍"
        
        # Header with integrated actions
        header_text = f"{song['Title']} - {song['Artist']} | {song['Book']} | P.{song['Page']}"
        
        exp = st.expander(header_text)
        with exp:
            # Action Row inside expander to save vertical space
            act_col, pdf_col = st.columns([1, 1])
            with act_col:
                st.button(f"{heart} Favourite", key=f"heart_{idx}", on_click=handle_playlist_click, args=(song_id,))
            with pdf_col:
                if song.get('URL'):
                    st.markdown(f'<a href="{song["URL"]}" target="_blank" class="action-btn" style="display:block; text-align:center; height:38px; line-height:38px; border:1px solid #ccc; border-radius:5px; text-decoration:none; color:black; background:#fff;">📄 PDF</a>', unsafe_allow_html=True)

            # Chords
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