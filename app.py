import streamlit as st
import json
import random
import re

# --- 1. PAGE CONFIG & BRANDING ---
FAVICON = "https://www.moselele.co.uk/wp-content/uploads/2015/11/moselele-icon-black.jpg"
LOGO_URL = "https://www.moselele.co.uk/wp-content/uploads/2013/08/moselele-logo-black_v_small.jpg"

st.set_page_config(page_title="Moselele Database", page_icon=FAVICON, layout="wide")

# Custom CSS for the song body and bold chords
st.markdown("""
    <style>
    .song-box {
        background-color: #f1f1f1;
        color: #111;
        padding: 25px;
        border-radius: 8px;
        border-left: 6px solid #333;
        font-family: 'Courier New', Courier, monospace;
        white-space: pre-wrap;
        font-size: 16px;
        line-height: 1.6;
        margin-bottom: 20px;
    }
    .song-box b { color: #d32f2f; font-weight: bold; } 
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
if 'expanded_song' not in st.session_state:
    st.session_state.expanded_song = None
if 'random_id' not in st.session_state:
    st.session_state.random_id = None

# --- 4. SIDEBAR & FILTERS ---
with st.sidebar:
    st.image(LOGO_URL, width=150)
    st.header("🔍 Filters")
    xmas_mode = st.radio("🎄 Season", ["Standard", "Christmas Only", "All"], index=0)
    diff_filter = st.slider("Max Difficulty", 1, 5, 5)
    
    st.divider()
    
    st.subheader("🎲 Randomizer")
    if st.button("Pick a Random Song", use_container_width=True):
        if xmas_mode == "Standard":
            pool = [s for s in songs if "snow" not in s['url'].lower() and "snow" not in s['title'].lower()]
        elif xmas_mode == "Christmas Only":
            pool = [s for s in songs if "snow" in s['url'].lower() or "snow" in s['title'].lower()]
        else:
            pool = songs
        pool = [s for s in pool if s['difficulty'] <= diff_filter]
        
        if pool:
            pick = random.choice(pool)
            # Store the title to identify and prioritize it
            st.session_state.random_id = pick['title']
            st.session_state.expanded_song = pick['title']
            st.balloons()
    
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
search_query = st.text_input("Search:", placeholder="Search titles, artists, or lyrics...")

# Initial result list
if search_query:
    q = search_query.lower()
    display_list = [s for s in filtered_songs if q in s['title'].lower() or q in s['artist'].lower() or q in s.get('body', '').lower()]
else:
    display_list = filtered_songs

# --- PRIORITY LOGIC: Move random song to top ---
if st.session_state.random_id:
    # Find the random song in the full database
    random_song = next((s for s in songs if s['title'] == st.session_state.random_id), None)
    if random_song:
        # Remove it if it already exists in the display list to avoid duplicates
        display_list = [s for s in display_list if s['title'] != st.session_state.random_id]
        # Insert at index 0
        display_list.insert(0, random_song)

# Cap at 50 results
display_list = display_list[:50]

st.divider()

# --- 7. DISPLAY LOGIC ---
for idx, s_data in enumerate(display_list):
    # Highlight the random song visually if it's the one we just picked
    is_random = s_data['title'] == st.session_state.random_id
    
    col1, col2, col3, col4 = st.columns([4, 1, 1, 1])
    
    title_prefix = "🎲 FEATURED: " if is_random else ""
    col1.markdown(f"### {title_prefix}{s_data['title']} — {s_data['artist']}")
    
    is_expanded = st.session_state.expanded_song == s_data['title']
    if col2.button("📖 Close" if is_expanded else "👁️ View", key=f"view_{idx}", use_container_width=True):
        st.session_state.expanded_song = s_data['title'] if not is_expanded else None
        # If the user manually closes it, we stop "featuring" it at the top
        if is_random and not is_expanded:
            st.session_state.random_id = None
        st.rerun()

    col3.link_button("📂 PDF", s_data['url'], use_container_width=True)
    
    is_fav = s_data['title'] in st.session_state.favorites
    if col4.button("❤️" if is_fav else "🤍", key=f"fav_{idx}", use_container_width=True):
        if is_fav: st.session_state.favorites.remove(s_data['title'])
        else: st.session_state.favorites.append(s_data['title'])
        st.rerun()

    if is_expanded:
        raw_body = s_data.get('body', "No lyrics found.")
        bolded_body = re.sub(r'(\[.*?\])', r'<b>\1</b>', raw_body)
        st.markdown(f'<div class="song-box">{bolded_body}</div>', unsafe_allow_html=True)
    
    st.divider()