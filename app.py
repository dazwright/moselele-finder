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
    if "playlist" not in st.session_state:
        st.session_state.playlist = []
    if song_id not in st.session_state.playlist:
        st.session_state.playlist.append(song_id)

def clear_playlist():
    st.session_state.playlist = []

def add_genre(genre):
    if "active_genres" not in st.session_state:
        st.session_state.active_genres = []
    if genre not in st.session_state.active_genres:
        st.session_state.active_genres.append(genre)

def refresh_page():
    st.session_state.random_active = False
    st.session_state.active_genres = []
    st.session_state["refresh_seed"] = st.session_state.get("refresh_seed", 0) + 1

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
    # Scrub watermark watermarks
    text = re.sub(r'MOSELELE\.CO\.UK', '', text, flags=re.IGNORECASE)
    # Remove existing bold markers to prevent Markdown errors
    text = text.replace("**", "")
    # Bold bracketed chords using HTML <b> tags
    return re.sub(r'(\[[^\]]+\])', r'<b>\1</b>', text)

@st.cache_data
def load_all_data():
    target_file = next((f for f in POSSIBLE_SONG_FILES if os.path.exists(f)), None)
    songs = pd.read_csv(target_file) if target_file else pd.DataFrame()
    chords = pd.read_csv(CHORDS_LIB_FILE) if os.path.exists(CHORDS_LIB_FILE) else pd.DataFrame()
    
    if not songs.empty:
        songs.columns = [c.strip() for c in songs.columns]
        for col in songs.columns: 
            songs[col] = songs[col].fillna("").astype(str).str.strip()
            
    if not chords.empty:
        chords.columns = [c.strip() for c in chords.columns]
        for col in chords.columns: 
            chords[col] = chords[col].fillna("").astype(str).str.strip()
        
    return songs, chords

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="Moselele Database", 
    page_icon=FAVICON_PATH if os.path.exists(FAVICON_PATH) else "🎸", 
    layout="wide"
)

# Custom CSS for square logo and lyrics
st.markdown("""
    <style>
    [data-testid="stImage"] img { border-radius: 0px !important; }
    .lyrics-box { 
        white-space: pre-wrap; background-color: #fdfdfd; padding: 25px; 
        border: 1px solid #eee; border-radius: 8px; font-size: 1.1rem; 
        line-height: 1.6; color: #31333F; font-family: sans-serif; 
    }
    .lyrics-box b { font-weight: 800; color: #000; }
    .stExpander { border: 1px solid #e6e6e6; }
    .action-btn { 
        text-decoration: none; color: #31333F !important; border: 1px solid #ccc; 
        width: 100%; height: 38px; display: flex; align-items: center; justify-content: center; 
        border-radius: 5px; font-size: 0.85rem; background-color: #fff; margin-top: 5px; 
    }
    .stButton button { width: 100%; height: 38px; margin-top: 5px; }
    .tag-display { 
        display: inline-block; background: #e1f5fe; color: #01579b; 
        padding: 2px 10px; border-radius: 5px; margin-right: 5px; 
        font-size: 0.75rem; font-weight: bold; margin-bottom: 5px; 
    }
    </style>
""", unsafe_allow_html=True)

# --- SESSION INITIALIZATION ---
if 'playlist' not in st.session_state: st.session_state.playlist = []
if 'random_active' not in st.session_state: st.session_state.random_active = False
if 'active_genres' not in st.session_state: st.session_state.active_genres = []
if 'refresh_seed' not in st.session_state: st.session_state.refresh_seed = 42

# Handle QR Code Shared Playlist
query_params = st.query_params
if "playlist" in query_params:
    shared_items = unquote(query_params["playlist"]).split(",")
    for item in shared_items:
        if item and item not in st.session_state.playlist:
            st.session_state.playlist.append(item)

def main():
    col_logo, col_title = st.columns([1, 5])
    with col_logo:
        if os.path.exists(LOGO_PATH): st.image(LOGO_PATH, width=120)
    with col_title: st.title("Moselele song database")

    df, chord_lib = load_all_data()
    if df.empty:
        st.error("Song database not found.")
        return

    # --- SIDEBAR ---
    if os.path.exists(LOGO_PATH): st.sidebar.image(LOGO_PATH, width=150)
    st.sidebar.button("🔄 Refresh Selection", on_click=refresh_page, use_container_width=True)
    st.sidebar.divider()

    st.sidebar.header("Search & Filter")
    search_query = st.sidebar.text_input("Search", "").lower()
    seasonal = st.sidebar.checkbox("Show Christmas/Seasonal Only")
    book_filter = st.sidebar.multiselect("Books", options=sorted(df['Book'].unique()) if 'Book' in df.columns else [])
    
    # Genre Data for Cloud
    all_tags = []
    if 'Tags' in df.columns:
        for val in df['Tags']:
            all_tags.extend([t.strip() for t in val.split(',') if t.strip()])
    genre_counts = Counter(all_tags)
    st.sidebar.multiselect("Genres", options=sorted(genre_counts.keys()), key="active_genres")

    st.sidebar.divider()
    st.sidebar.subheader("Randomisers")
    c_r1, c_r2 = st.sidebar.columns(2)
    c_r1.button("Pick 1", on_click=lambda: st.session_state.update({"random_active": True, "rcount": 1}))
    c_r2.button("Pick 10", on_click=lambda: st.session_state.update({"random_active": True, "rcount": 10}))
    st.sidebar.button("Clear Randomisers", on_click=lambda: st.session_state.update({"random_active": False}))

    # Interactive Genre Cloud
    st.sidebar.divider()
    st.sidebar.subheader("Genres")
    if genre_counts:
        sorted_genres = sorted(genre_counts.items(), key=lambda x: x[1], reverse=True)
        for g, count in sorted_genres[:20]:
            st.sidebar.button(f"{g} ({count})", key=f"cloud_{g}", on_click=add_genre, args=(g,))

    # Playlist Display & QR Share
    st.sidebar.divider()
    st.sidebar.subheader(f"Playlist ({len(st.session_state.playlist)})")
    if st.session_state.playlist:
        for p in st.session_state.playlist:
            st.sidebar.caption(f"• {p}")
        
        # QR Code Section
        st.sidebar.write("---")
        base_url = "https://moselele-finder.streamlit.app/" # Ensure this matches your deployment URL
        share_url = f"{base_url}?playlist={quote(','.join(st.session_state.playlist))}"
        qr_img = generate_qr(share_url)
        st.sidebar.image(qr_img, caption="Scan to Share Playlist", use_container_width=True)
        
        st.sidebar.button("Clear Playlist", on_click=clear_playlist)
    else:
        st.sidebar.info("Playlist is empty.")

    # --- FILTERING ---
    f_df = df.copy()
    if seasonal:
        f_df = f_df[f_df['Book'].str.contains('Christmas|Winter', case=False) | f_df['Title'].str.contains('Christmas', case=False)]
    if search_query:
        f_df = f_df[f_df['Title'].str.lower().str.contains(search_query) | f_df['Artist'].str.lower().str.contains(search_query) | f_df['Body'].str.lower().str.contains(search_query)]
    if book_filter:
        f_df = f_df[f_df['Book'].isin(book_filter)]
    if st.session_state.active_genres:
        f_df = f_df[f_df['Tags'].apply(lambda x: any(g in [s.strip() for s in x.split(',')] for g in st.session_state.active_genres))]

    # Default logic (50 songs)
    if st.session_state.random_active:
        f_df = f_df.sample(n=min(st.session_state.rcount, len(f_df)))
    elif not any([search_query, book_filter, st.session_state.active_genres, seasonal]):
        f_df = f_df.sample(n=min(50, len(f_df)), random_state=st.session_state.refresh_seed)

    # --- MAIN LOOP ---
    st.write(f"Displaying **{len(f_df)}** songs")
    for idx, song in f_df.iterrows():
        song_id = f"{song['Title']} ({song['Artist']})"
        prefix = "🎲 " if st.session_state.random_active else ""
        header = f"{prefix}{song['Title']} - {song['Artist']} | Difficulty {song['Difficulty']} | {song['Book']} | Page {song['Page']}"
        
        r_col, l_col, p_col = st.columns([7.5, 1.2, 1.2])
        with r_col:
            with st.expander(header):
                if song.get('Tags'):
                    t_html = "".join([f'<span class="tag-display">{t.strip()}</span>' for t in song['Tags'].split(',') if t.strip()])
                    st.markdown(t_html, unsafe_allow_html=True)

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
                    
                    if v_imgs:
                        st.write("**Chords:**")
                        st.image(v_imgs, width=75, caption=v_caps)
                    else:
                        st.write(f"**Chords:** {chord_str}")
                
                if song['Body']:
                    lyrics_final = clean_and_bold_lyrics(song['Body'].strip())
                    st.markdown(f'<div class="lyrics-box">{lyrics_final}</div>', unsafe_allow_html=True)

        with l_col: 
            st.button("➕ List", key=f"plist_btn_{idx}", on_click=handle_playlist_click, args=(song_id,))
        with p_col:
            if song.get('URL') and song['URL'] != "":
                st.markdown(f'<a href="{song["URL"]}" target="_blank" class="action-btn">📄 PDF</a>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()