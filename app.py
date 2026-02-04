import streamlit as st
import json
import random
import re

# --- 1. PAGE CONFIG & BRANDING ---
FAVICON = "https://www.moselele.co.uk/wp-content/uploads/2015/11/moselele-icon-black.jpg"
LOGO_URL = "https://www.moselele.co.uk/wp-content/uploads/2013/08/moselele-logo-black_v_small.jpg"

st.set_page_config(page_title="Moselele", page_icon=FAVICON, layout="wide")

# Custom CSS
st.markdown("""
    <style>
    .song-title { font-size: 1.05rem !important; margin-bottom: 0px; font-weight: bold; }
    .song-meta { font-size: 0.85rem; color: #555; margin-top: -4px; }
    .song-box {
        background-color: #f8f9fa;
        color: #111;
        padding: 20px;
        border-radius: 5px;
        border-left: 5px solid #000;
        font-family: 'Courier New', Courier, monospace;
        white-space: pre-wrap;
        font-size: 15px;
        line-height: 1.5;
    }
    .song-box b { color: #cc0000; }
    </style>
""", unsafe_allow_html=True)

# --- 2. DATA LOADING ---
@st.cache_data
def load_data():
    try:
        with open('song_index.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return []

all_songs = load_data()

# --- 3. SESSION STATE ---
if 'favorites' not in st.session_state: st.session_state.favorites = []
if 'expanded' not in st.session_state: st.session_state.expanded = None
if 'initial_shuffle' not in st.session_state:
    sampled = random.sample(all_songs, min(50, len(all_songs)))
    st.session_state.initial_shuffle = sorted(sampled, key=lambda x: x.get('difficulty', 3))

# --- 4. SIDEBAR & FILTERS ---
with st.sidebar:
    st.image(LOGO_URL, width=120)
    st.header("🔍 Filters")
    
    x_mode = st.radio("🎄 Mode", ["Standard", "Christmas", "All"])
    d_max = st.slider("Max Difficulty", 1, 5, 5)
    
    # NEW: Book Filter
    # Get unique book numbers, sorted numerically
    unique_books = sorted(list(set([str(s.get('book', 'N/A')) for s in all_songs if s.get('book') != "N/A"])), key=lambda x: int(x))
    book_choice = st.selectbox("Select Book", ["All Books"] + unique_books)
    
    st.divider()
    st.subheader("⭐ Setlist")
    for f_title in st.session_state.favorites:
        fc1, fc2 = st.columns([4, 1])
        fc1.caption(f_title)
        if fc2.button("🗑️", key=f"remove_{f_title}"):
            st.session_state.favorites.remove(f_title)
            st.rerun()

# --- 5. MAIN FILTERING & SORTING LOGIC ---
# Base filter for Difficulty and Season
pool = [s for s in all_songs if s.get('difficulty', 3) <= d_max]
if x_mode == "Standard": 
    pool = [s for s in pool if "snow" not in s['url'].lower()]
elif x_mode == "Christmas": 
    pool = [s for s in pool if "snow" in s['url'].lower()]

# Apply Book Filter and determine Sort Key
if book_choice != "All Books":
    pool = [s for s in pool if str(s.get('book')) == book_choice]
    # SORT BY PAGE NUMBER (Natural sort: Page 2 before Page 10)
    pool = sorted(pool, key=lambda x: int(x.get('page', 0)) if str(x.get('page')).isdigit() else 999)
else:
    # SORT BY DIFFICULTY (Default)
    pool = sorted(pool, key=lambda x: x.get('difficulty', 3))

# Search Query logic
st.title("🎸 Moselele Database")
query = st.text_input("Search:", placeholder="Type song, artist, or lyric...")

if query:
    q = query.lower()
    display_list = [s for s in pool if q in s['title'].lower() or q in s['artist'].lower() or q in s.get('body','').lower()]
    # If searching, we maintain the sort order defined above (Page if Book selected, else Difficulty)
else:
    # On load / No search
    if book_choice != "All Books":
        display_list = pool[:50]
    else:
        # Respect the initial 50 random songs but filter them
        display_list = [s for s in st.session_state.initial_shuffle if s in pool][:50]

st.divider()

# --- 6. RENDER LIST ---
for i, s in enumerate(display_list):
    c1, c2, c3, c4 = st.columns([5, 1, 1, 1])
    
    with c1:
        st.markdown(f"<div class='song-title'>{s['title']} — {s['artist']}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='song-meta'>Difficulty: {s['difficulty']} | Book: {s['book']} | Page: {s['page']}</div>", unsafe_allow_html=True)
    
    is_exp = st.session_state.expanded == s['title']
    if c2.button("👁️ View" if not is_exp else "📖 Close", key=f"v_{i}", use_container_width=True):
        st.session_state.expanded = s['title'] if not is_exp else None
        st.rerun()
    
    c3.link_button("📂 PDF", s['url'], use_container_width=True)
    
    is_f = s['title'] in st.session_state.favorites
    if c4.button("❤️" if is_f else "🤍", key=f"f_{i}", use_container_width=True):
        if is_f: st.session_state.favorites.remove(s['title'])
        else: st.session_state.favorites.append(s['title'])
        st.rerun()

    if is_exp:
        body = s.get('body', "No lyrics available.")
        # Bold [Chords]
        bolded = re.sub(r'(\[.*?\])', r'<b>\1</b>', body)
        st.markdown(f"<div class='song-box'>{bolded}</div>", unsafe_allow_html=True)
    
    st.divider()