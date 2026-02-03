import streamlit as st
import json
import random
import re

# --- 1. PAGE CONFIG & BRANDING ---
FAVICON = "https://www.moselele.co.uk/wp-content/uploads/2015/11/moselele-icon-black.jpg"
LOGO_URL = "https://www.moselele.co.uk/wp-content/uploads/2013/08/moselele-logo-black_v_small.jpg"

st.set_page_config(page_title="Moselele Database", page_icon=FAVICON, layout="wide")

# Custom CSS
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
if 'random_set' not in st.session_state:
    st.session_state.random_set = []

# --- 4. SIDEBAR & FILTERS ---
with st.sidebar:
    st.image(LOGO_URL, width=150)
    st.header("🔍 Filters")
    xmas_mode = st.radio("🎄 Season", ["Standard", "Christmas Only", "All"], index=0)
    diff_filter = st.slider("Max Difficulty", 1, 5, 5)
    
    st.divider()
    
    st.subheader("🎲 Randomizer")
    
    # 4a. Logic performed silently (no st.write/st.markdown here)
    pool = [s for s in songs if s['difficulty'] <= diff_filter]
    if xmas_mode == "Standard":
        pool = [s for s in pool if "snow" not in s['url'].lower()]
    elif xmas_mode == "Christmas Only":
        pool = [s for s in pool if "snow" in s['url'].lower()]

    col_r1, col_r2 = st.columns(2)
    
    if col_r1.button("Pick 1", use_container_width=True):
        if pool:
            pick = random.choice(pool)
            st.session_state.random_set = [pick['title']]
            st.session_state.expanded_song = pick['title']
            st.balloons()

    if col_r2.button("Pick 10", use_container_width=True):
        st.session_state.expanded_song = None
        if len(pool) >= 10:
            st.session_state.random_set = [p['title'] for p in random.sample(pool, 10)]
        else:
            st.session_state.random_set = [p['title'] for p in pool]
        st.snow() if xmas_mode == "Christmas Only" else st.balloons()

    # 4b. Status and Actions (Only shows if a set exists)
    if st.session_state.random_set:
        st.success(f"Generated {len(st.session_state.random_set)} songs")
        
        if st.button("➕ Add all to Setlist", use_container_width=True):
            for title in st.session_state.random_set:
                if title not in st.session_state.favorites:
                    st.session_state.favorites.append(title)
            st.toast("Songs added!")

        if st.button("🗑️ Clear Selection", use_container_width=True):
            st.session_state.random_set = []
            st.session_state.expanded_song = None
            st.rerun()

    st.divider()
    st.subheader("⭐ My Setlist")
    if not st.session_state.favorites:
        st.info("Setlist is empty.")
    else:
        # We loop and display favorites without printing the list object itself
        for fav in st.session_state.favorites:
            c1, c2 = st.columns([4, 1])
            c1.caption(fav)
            if c2.button("🗑️", key=f"del_{fav}"):
                st.session_state.favorites.remove(fav)
                st.rerun()

# --- 5. DATA FILTERING ---
# We keep this outside the sidebar to ensure the main window updates correctly
if xmas_mode == "Standard":
    current_list = [s for s in songs if "snow" not in s['url'].lower() and "snow" not in s['title'].lower()]
elif xmas_mode == "Christmas Only":
    current_list = [s for s in songs if "snow" in s['url'].lower() or "snow" in s['title'].lower()]
else:
    current_list = songs

filtered_songs = [s for s in current_list if s['difficulty'] <= diff_filter]

# --- 6. MAIN INTERFACE ---
st.title("🎸 Moselele Database")
search_query = st.text_input("Search:", placeholder="Search titles, artists, or lyrics...", key="main_search_input")

if search_query:
    q = search_query.lower()
    display_list = [s for s in filtered_songs if q in s['title'].lower() or q in s['artist'].lower() or q in s.get('body', '').lower()]
else:
    display_list = filtered_songs

# Pin Random Songs to Top
if st.session_state.random_set:
    featured = [s for s in songs if s['title'] in st.session_state.random_set]
    display_list = [s for s in display_list if s['title'] not in st.session_state.random_set]
    display_list = featured + display_list

display_list = display_list[:50]

st.divider()

# --- 7. DISPLAY LOOP ---
for idx, s_data in enumerate(display_list):
    is_random = s_data['title'] in st.session_state.random_set
    col1, col2, col3, col4 = st.columns([4, 1, 1, 1])
    
    title_label = f"🎲 FEATURED: {s_data['title']}" if is_random else s_data['title']
    col1.markdown(f"### {title_label} — {s_data['artist']}")
    
    is_expanded = st.session_state.expanded_song == s_data['title']
    if col2.button("📖 Close" if is_expanded else "👁️ View", key=f"view_{idx}", use_container_width=True):
        st.session_state.expanded_song = s_data['title'] if not is_expanded else None
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