import streamlit as st
import json
import random
import segno
import urllib.parse
from io import BytesIO

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

# URL Syncing
query_params = st.query_params
if "setlist" in query_params and not st.session_state.favorites:
    shared_items = query_params["setlist"].split(",")
    st.session_state.favorites = [s['title'] for s in songs if s['title'] in shared_items]

# --- 4. SIDEBAR FILTERS ---
with st.sidebar:
    st.image(LOGO_URL, width=150)
    st.header("🔍 Search Filters")
    
    xmas_mode = st.radio(
        "🎄 Seasonality",
        ["Standard (Hide Snowselele)", "Christmas Only (Snowselele)", "Show All Songs"],
        index=0
    )
    
    diff_filter = st.slider("Max Difficulty", 1, 5, 5)
    
    all_artists = sorted(list(set([s.get('artist', 'Unknown') for s in songs])))
    artist_choice = st.selectbox("Filter by Artist", ["All"] + all_artists)
    
    st.divider()
    
    st.subheader("⭐ My Setlist")
    if st.session_state.favorites:
        for fav in st.session_state.favorites:
            c1, c2 = st.columns([4, 1])
            c1.caption(fav)
            if c2.button("🗑️", key=f"del_{fav}"):
                st.session_state.favorites.remove(fav)
                st.rerun()
        
        st.divider()
        base_url = "https://your-app-name.streamlit.app/" 
        encoded = urllib.parse.quote(",".join(st.session_state.favorites))
        share_url = f"{base_url}?setlist={encoded}"
        
        qr = segno.make(share_url)
        out = BytesIO()
        qr.save(out, kind='png', scale=4)
        st.image(out.getvalue(), caption="Scan to share setlist")
    else:
        st.info("Setlist is empty.")

# --- 5. FILTERING LOGIC ---
if xmas_mode == "Standard (Hide Snowselele)":
    current_list = [s for s in songs if "snow" not in s['url'].lower() and "snow" not in s['title'].lower()]
elif xmas_mode == "Christmas Only (Snowselele)":
    current_list = [s for s in songs if "snow" in s['url'].lower() or "snow" in s['title'].lower()]
    st.snow()
else:
    current_list = songs

filtered_songs = [
    s for s in current_list 
    if s['difficulty'] <= diff_filter 
    and (artist_choice == "All" or s['artist'] == artist_choice)
]

# --- 6. MAIN INTERFACE ---
col_logo, col_title = st.columns([1, 5])
with col_logo:
    st.image(LOGO_URL, width=120)
with col_title:
    st.title("Moselele Database")
    st.caption(f"Currently showing {len(filtered_songs)} songs")

query = st.text_input("Find a song by title, artist, or lyrics:", placeholder="e.g. 'Jolene'")

if query:
    query_l = query.lower()
    results = []
    for s in filtered_songs:
        if (query_l in s['title'].lower() or 
            query_l in s['artist'].lower() or 
            query_l in s.get('body', '').lower()):
            results.append(s)
    # UPDATE: Now shows top 50 matches
    display_list = results[:50] 
else:
    # UPDATE: Now shows 50 songs by default
    display_list = filtered_songs[:50]

# --- 7. DISPLAY RESULTS ---
st.divider()

# Using columns to keep the 50 results neat
cols = st.columns(2)
for idx, s_data in enumerate(display_list):
    with cols[idx % 2]:
        with st.expander(f"📖 **{s_data['title']}** — {s_data['artist']} (Lvl {s_data['difficulty']})"):
            
            b1, b2 = st.columns(2)
            b1.link_button("📂 Open PDF", s_data['url'], use_container_width=True)
            
            is_fav = s_data['title'] in st.session_state.favorites
            if b2.button("❤️ Remove" if is_fav else "🤍 Add to Setlist", key=f"fav_{idx}", use_container_width=True):
                if is_fav:
                    st.session_state.favorites.remove(s_data['title'])
                else:
                    st.session_state.favorites.append(s_data['title'])
                st.rerun()

            st.divider()
            if s_data.get('body'):
                st.text(s_data['body'])
            else:
                st.warning("Full text not available.")

# Randomizer
st.divider()
if st.button("🎲 Random Recommendation"):
    if filtered_songs:
        pick = random.choice(filtered_songs)
        st.success(f"Let's play: **{pick['title']}** by {pick['artist']}!")
        st.balloons()