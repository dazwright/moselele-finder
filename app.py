import streamlit as st
import json
import random
import re

# --- 1. PAGE CONFIG & BRANDING ---
FAVICON = "https://www.moselele.co.uk/wp-content/uploads/2015/11/moselele-icon-black.jpg"
LOGO_URL = "https://www.moselele.co.uk/wp-content/uploads/2013/08/moselele-logo-black_v_small.jpg"

st.set_page_config(page_title="Moselele Database", page_icon=FAVICON, layout="wide")

# Custom CSS for the song body
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
    except Exception:
        return []

songs = load_data()

# --- 3. SESSION STATE ---
if 'favorites' not in st.session_state:
    st.session_state.favorites = []
if 'expanded_song' not in st.session_state:
    st.session_state.expanded_song = None
if 'random_set' not in st.session_state:
    st.session_state.random_set = []

# --- 4. SIDEBAR & FILTERS ---
with st.sidebar:
    st.image(LOGO_URL, width=150)
    st.header("🔍 Filters")
    
    # 4a. Inputs
    x_mode = st.radio("🎄 Season", ["Standard", "Christmas Only", "All"], index=0)
    d_filt = st.slider("Max Difficulty", 1, 5, 5)
    
    st.divider()
    
    # 4b. SILENT RANDOMIZER LOGIC
    # We define the pool here, but we do NOT call it alone on a line.
    active_pool = [s for s in songs if s['difficulty'] <= d_filt]
    if x_mode == "Standard":
        active_pool = [s for s in active_pool if "snow" not in s['url'].lower()]
    elif x_mode == "Christmas Only":
        active_pool = [s for s in active_pool if "snow" in s['url'].lower()]

    st.subheader("🎲 Randomizer")
    c1, c2 = st.columns(2)
    
    if c1.button("Pick 1", use_container_width=True):
        if active_pool:
            choice = random.choice(active_pool)
            st.session_state.random_set = [choice['title']]
            st.session_state.expanded_song = choice['title']
            st.balloons()

    if c2.button("Pick 10", use_container_width=True):
        st.session_state.expanded_song = None
        if len(active_pool) >= 10:
            selection = random.sample(active_pool, 10)
            st.session_state.random_set = [p['title'] for p in selection]
        else:
            st.session_state.random_set = [p['title'] for p in active_pool]
        
        if x_mode == "Christmas Only":
            st.snow()
        else:
            st.balloons()

    # 4c. ACTION BUTTONS (Only if random set exists)
    if len(st.session_state.random_set) > 0:
        st.success(f"Selected {len(st.session_state.random_set)} song(s)")
        
        if st.button("➕ Add all to Setlist", use_container_width=True):
            for t in st.session_state.random_set:
                if t not in st.session_state.favorites:
                    st.session_state.favorites.append(t)
            st.toast("Added!")

        if st.button("🗑️ Clear Random", use_container_width=True):
            st.session_state.random_set = []
            st.session_state.expanded_song = None
            st.rerun()

    st.divider()
    st.subheader("⭐ My Setlist")
    if not st.session_state.favorites:
        st.info("Setlist is empty.")
    else:
        for f_title in st.session_state.favorites:
            fc1, fc2 = st.columns([4, 1])
            fc1.caption(f_title)
            if fc2.button("🗑️", key=f"remove_{f_title}"):
                st.session_state.favorites.remove(f_title)
                st.rerun()

# --- 5. MAIN WINDOW DISPLAY LOGIC ---
# Filtering the list for the main search
if x_mode == "Standard":
    main_pool = [s for s in songs if "snow" not in s['url'].lower() and "snow" not in s['title'].lower()]
elif x_mode == "Christmas Only":
    main_pool = [s for s in songs if "snow" in s['url'].lower() or "snow" in s['title'].lower()]
else:
    main_pool = songs

final_filtered = [s for s in main_pool if s['difficulty'] <= d_filt]

st.title("🎸 Moselele Database")
s_query = st.text_input("Search:", placeholder="Search titles, artists, or lyrics...", key="main_search_box")

if s_query:
    sq = s_query.lower()
    main_list = [s for s in final_filtered if sq in s['title'].lower() or sq in s['artist'].lower() or sq in s.get('body', '').lower()]
else:
    main_list = final_filtered

# Priority: Push Random Set to Top
if st.session_state.random_set:
    featured_songs = [s for s in songs if s['title'] in st.session_state.random_set]
    main_list = [s for s in main_list if s['title'] not in st.session_state.random_set]
    main_list = featured_songs + main_list

# Show top 50
main_list = main_list[:50]

st.divider()

# --- 6. RENDER SONGS ---
for i, song_data in enumerate(main_list):
    is_r = song_data['title'] in st.session_state.random_set
    sc1, sc2, sc3, sc4 = st.columns([4, 1, 1, 1])
    
    display_title = f"🎲 FEATURED: {song_data['title']}" if is_r else song_data['title']
    sc1.markdown(f"### {display_title} — {song_data['artist']}")
    
    is_exp = st.session_state.expanded_song == song_data['title']
    if sc2.button("📖 Close" if is_exp else "👁️ View", key=f"v_{i}", use_container_width=True):
        st.session_state.expanded_song = song_data['title'] if not is_exp else None
        st.rerun()

    sc3.link_button("📂 PDF", song_data['url'], use_container_width=True)
    
    is_f = song_data['title'] in st.session_state.favorites
    if sc4.button("❤️" if is_f else "🤍", key=f"f_{i}", use_container_width=True):
        if is_f: st.session_state.favorites.remove(song_data['title'])
        else: st.session_state.favorites.append(song_data['title'])
        st.rerun()

    if is_exp:
        b_text = song_data.get('body', "No text.")
        b_text_bold = re.sub(r'(\[.*?\])', r'<b>\1</b>', b_text)
        st.markdown(f'<div class="song-box">{b_text_bold}</div>', unsafe_allow_html=True)
    
    st.divider()