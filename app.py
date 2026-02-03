import streamlit as st
import json
import random
import segno
import urllib.parse
import re
from io import BytesIO

# --- 1. PAGE CONFIG & BRANDING ---
FAVICON = "https://www.moselele.co.uk/wp-content/uploads/2015/11/moselele-icon-black.jpg"
LOGO_URL = "https://www.moselele.co.uk/wp-content/uploads/2013/08/moselele-logo-black_v_small.jpg"

st.set_page_config(page_title="Moselele Database", page_icon=FAVICON, layout="wide")

# Custom CSS to make the bottom preview window look like a fixed "console"
st.markdown("""
    <style>
    .big-font { font-family: monospace !important; }
    .footer-window {
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100%;
        background-color: #1e1e1e;
        color: #ffffff;
        padding: 20px;
        height: 300px;
        overflow-y: auto;
        border-top: 3px solid #ff4b4b;
        z-index: 1000;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATA LOADING ---
@st.cache_data
def load_data():
    try:
        with open('song_index.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return []

songs = load_data()

# --- 3. SESSION STATE ---
if 'favorites' not in st.session_state:
    st.session_state.favorites = []
if 'selected_song' not in st.session_state:
    st.session_state.selected_song = None

# --- 4. SIDEBAR FILTERS ---
with st.sidebar:
    st.image(LOGO_URL, width=150)
    st.header("🔍 Search Filters")
    
    xmas_mode = st.radio("🎄 Seasonality", ["Standard", "Christmas Only", "Show All"], index=0)
    diff_filter = st.slider("Max Difficulty", 1, 5, 5)
    
    st.divider()
    st.subheader("⭐ Setlist")
    for fav in st.session_state.favorites:
        c1, c2 = st.columns([4, 1])
        c1.caption(fav)
        if c2.button("🗑️", key=f"del_{fav}"):
            st.session_state.favorites.remove(fav)
            st.rerun()

# --- 5. FILTERING LOGIC ---
if xmas_mode == "Standard":
    current_list = [s for s in songs if "snow" not in s['url'].lower() and "snow" not in s['title'].lower()]
elif xmas_mode == "Christmas Only":
    current_list = [s for s in songs if "snow" in s['url'].lower() or "snow" in s['title'].lower()]
else:
    current_list = songs

filtered_songs = [s for s in current_list if s['difficulty'] <= diff_filter]

# --- 6. MAIN INTERFACE ---
st.title("🎸 Moselele Database")
query = st.text_input("Search:", placeholder="Type to find song...")

if query:
    query_l = query.lower()
    display_list = [s for s in filtered_songs if query_l in s['title'].lower() or query_l in s['artist'].lower() or query_l in s.get('body', '').lower()][:50]
else:
    display_list = filtered_songs[:50]

# --- 7. ONE COLUMN DISPLAY ---
st.divider()

for idx, s_data in enumerate(display_list):
    col1, col2, col3 = st.columns([4, 1, 1])
    col1.markdown(f"### {s_data['title']} — {s_data['artist']}")
    
    if col2.button("👁️ View Lyrics", key=f"view_{idx}", use_container_width=True):
        st.session_state.selected_song = s_data
        
    is_fav = s_data['title'] in st.session_state.favorites
    if col3.button("❤️" if is_fav else "🤍", key=f"fav_{idx}", use_container_width=True):
        if is_fav: st.session_state.favorites.remove(s_data['title'])
        else: st.session_state.favorites.append(s_data['title'])
        st.rerun()
    st.divider()

# --- 8. THE BOTTOM PREVIEW WINDOW ---
if st.session_state.selected_song:
    song = st.session_state.selected_song
    
    # Logic to Bold text in brackets [G] -> **[G]**
    raw_body = song.get('body', "No text available.")
    # Regex finds anything inside [] and wraps it in double asterisks
    bolded_body = re.sub(r'(\[.*?\])', r'**\1**', raw_body)
    
    with st.container():
        st.write("---")
        st.subheader(f"📖 Now Viewing: {song['title']}")
        
        # We use Markdown with a monospace container to keep alignment and allow bolding
        st.markdown(f"""
        <div style="background-color: #f0f2f6; padding: 20px; border-radius: 10px; font-family: monospace; white-space: pre-wrap; line-height: 1.4;">
        {bolded_body}
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("❌ Close Preview"):
            st.session_state.selected_song = None
            st.rerun()