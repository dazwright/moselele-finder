import streamlit as st
import json
import random
import segno
import urllib.parse
from io import BytesIO
from thefuzz import process

# --- PAGE CONFIG ---
FAVICON = "https://www.moselele.co.uk/wp-content/uploads/2015/11/moselele-icon-black.jpg"
st.set_page_config(page_title="Moselele Database", page_icon=FAVICON, layout="wide")

# Official Moselele logo
LOGO_URL = "https://www.moselele.co.uk/wp-content/uploads/2013/08/moselele-logo-black_v_small.jpg"

@st.cache_data
def load_data():
    try:
        with open('song_index.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return []

songs = load_data()

# --- SESSION STATE ---
if 'favorites' not in st.session_state:
    st.session_state.favorites = []

# --- SIDEBAR ---
with st.sidebar:
    st.image(LOGO_URL, width=150)
    st.header("🔍 Filters")
    diff_filter = st.slider("Difficulty", 1, 5, 5)
    
    st.subheader("⭐ Setlist")
    if st.session_state.favorites:
        for fav in st.session_state.favorites:
            c1, c2 = st.columns([4, 1])
            c1.caption(fav)
            if c2.button("🗑️", key=f"del_{fav}"):
                st.session_state.favorites.remove(fav)
                st.rerun()
    else:
        st.info("Setlist is empty.")

# --- MAIN INTERFACE ---
col_logo, col_title = st.columns([1, 5])
with col_logo:
    st.image(LOGO_URL, width=100)
with col_title:
    st.title("Moselele Database")

# Filter Logic
filtered_songs = [s for s in songs if s['difficulty'] <= diff_filter]

# Search Bar (Searches Title, Artist, and Body)
query = st.text_input("Search title, artist, or lyrics:", placeholder="e.g. 'Creep' or 'Raindrops keep falling'")

if query:
    query_l = query.lower()
    results = []
    for s in filtered_songs:
        if query_l in s['title'].lower() or query_l in s['artist'].lower() or query_l in s.get('body', '').lower():
            results.append(s)
    display_list = results[:20]
else:
    display_list = filtered_songs[:20]

# --- DISPLAY RESULTS ---
st.divider()

for idx, s_data in enumerate(display_list):
    # Each song gets its own expander
    with st.expander(f"📖 **{s_data['title']}** — {s_data['artist']} (Level {s_data['difficulty']})"):
        
        # Action Buttons
        btn_col1, btn_col2 = st.columns(2)
        btn_col1.link_button("📂 Open Original PDF", s_data['url'], use_container_width=True)
        
        is_fav = s_data['title'] in st.session_state.favorites
        if btn_col2.button("❤️ Remove" if is_fav else "🤍 Add to Setlist", key=f"fav_{idx}", use_container_width=True):
            if is_fav: st.session_state.favorites.remove(s_data['title'])
            else: st.session_state.favorites.append(s_data['title'])
            st.rerun()

        st.write("---")
        
        # DISPLAY FULL BODY
        if s_data.get('body'):
            st.subheader("Lyrics & Chords")
            # We use st.text to preserve the \n and monospace font for chord alignment
            st.text(s_data['body'])
        else:
            st.warning("Full text not available for this song. Please use the PDF button above.")

st.divider()
if st.button("🎲 Random Song"):
    if filtered_songs:
        pick = random.choice(filtered_songs)
        st.success(f"Try playing: **{pick['title']}**")
        st.text(pick.get('body', 'Text not available'))