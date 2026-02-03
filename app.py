import streamlit as st
import json
import random
import re
import urllib.parse

# --- 1. PAGE CONFIG & BRANDING ---
FAVICON = "https://www.moselele.co.uk/wp-content/uploads/2015/11/moselele-icon-black.jpg"
LOGO_URL = "https://www.moselele.co.uk/wp-content/uploads/2013/08/moselele-logo-black_v_small.jpg"

st.set_page_config(page_title="Moselele Database", page_icon=FAVICON, layout="wide")

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
if 'expanded_song' not in st.session_state:
    st.session_state.expanded_song = None

# --- 4. SIDEBAR FILTERS ---
with st.sidebar:
    st.image(LOGO_URL, width=150)
    st.header("🔍 Filters")
    xmas_mode = st.radio("🎄 Season", ["Standard", "Christmas Only", "All"], index=0)
    diff_filter = st.slider("Max Difficulty", 1, 5, 5)
    
    st.divider()
    st.subheader("⭐ Setlist")
    if not st.session_state.favorites:
        st.info("Setlist is empty.")
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
query = st.text_input("Search:", placeholder="Search titles, artists, or lyrics...")

if query:
    query_l = query.lower()
    display_list = [s for s in filtered_songs if query_l in s['title'].lower() or query_l in s['artist'].lower() or query_l in s.get('body', '').lower()][:50]
else:
    display_list = filtered_songs[:50]

st.divider()

# --- 7. ONE COLUMN DISPLAY WITH INLINE EXPANSION ---
for idx, s_data in enumerate(display_list):
    # Main Song Row
    col1, col2, col3, col4 = st.columns([4, 1, 1, 1])
    
    col1.markdown(f"### {s_data['title']} — {s_data['artist']}")
    
    # Toggle View Logic
    is_expanded = st.session_state.expanded_song == s_data['title']
    if col2.button("📖 Close" if is_expanded else "👁️ View", key=f"view_{idx}", use_container_width=True):
        st.session_state.expanded_song = s_data['title'] if not is_expanded else None
        st.rerun()

    # PDF Link
    col3.link_button("📂 PDF", s_data['url'], use_container_width=True)
    
    # Favorite Button
    is_fav = s_data['title'] in st.session_state.favorites
    if col4.button("❤️" if is_fav else "🤍", key=f"fav_{idx}", use_container_width=True):
        if is_fav: st.session_state.favorites.remove(s_data['title'])
        else: st.session_state.favorites.append(s_data['title'])
        st.rerun()

    # THE EXPANDED WINDOW
    if is_expanded:
        # 1. Process the body text for bold brackets
        raw_body = s_data.get('body', "No lyrics found.")
        # Replaces [Anything] with **[Anything]**
        bolded_body = re.sub(r'(\[.*?\])', r'**\1**', raw_body)
        
        # 2. Render inside a clean markdown block
        # Using a triple-backtick 'fenced' block inside HTML for perfect alignment
        st.markdown(
            f"""
            <div style="background-color: #f1f1f1; color: #111; padding: 20px; border-radius: 8px; border-left: 6px solid #333; margin-top: 10px;">
                <pre style="font-family: 'Courier New', Courier, monospace; white-space: pre-wrap; font-size: 14px; line-height: 1.5; border: none; background: none; margin: 0; padding: 0;">{bolded_body}</pre>
            </div>
            """, 
            unsafe_allow_html=True
        )
        
        if st.button("🔼 Close Lyrics", key=f"close_{idx}"):
            st.session_state.expanded_song = None
            st.rerun()
    
    st.divider()