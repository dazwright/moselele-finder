import streamlit as st
import json
import random
import segno
import urllib.parse
from io import BytesIO
from thefuzz import process

# --- PAGE CONFIG ---
# This updates the browser tab icon to the official Moselele favicon
FAVICON_URL = "https://www.moselele.co.uk/wp-content/uploads/2015/11/moselele-icon-black.jpg"
st.set_page_config(page_title="Moselele Database", page_icon=FAVICON_URL, layout="wide")

# --- LOGO & TITLE ---
# Official Moselele logo for the header and sidebar
LOGO_URL = "https://www.moselele.co.uk/wp-content/uploads/2013/08/moselele-logo-black_v_small.jpg"

col1, col2 = st.columns([1, 5])
with col1:
    st.image(LOGO_URL, width=120)
with col2:
    st.title("Moselele Database")
    st.caption("The complete searchable index of individual song sheets.")

# --- DATA LOADING ---
@st.cache_data
def load_data():
    try:
        with open('song_index.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        st.error("Index file not found! Please run your scraper.py first.")
        return []

songs = load_data()
song_titles = [s['title'] for s in songs]

# --- SESSION STATE ---
if 'favorites' not in st.session_state:
    st.session_state.favorites = []

# URL Query Parameter handling (for syncing setlists)
query_params = st.query_params
if "setlist" in query_params and not st.session_state.favorites:
    shared_titles = query_params["setlist"].split(",")
    st.session_state.favorites = [t for t in shared_titles if t in song_titles]

# --- SIDEBAR: FILTERS & SHARING ---
with st.sidebar:
    st.image(LOGO_URL, width=150)
    st.divider()
    
    st.header("🔍 Filters")
    diff_filter = st.slider("Difficulty (1-Easy, 5-Hard)", 1, 5, 5)
    
    all_artists = sorted(list(set([s.get('artist', 'Unknown') for s in songs])))
    artist_choice = st.selectbox("Artist", ["All"] + all_artists)
    
    st.subheader("🎸 Chord Check")
    known_chords = st.multiselect("Hide songs containing unknown chords:", 
                                  ["C", "G", "F", "Am", "Dm", "Em", "G7", "C7", "D", "A", "E", "Bb", "Bm"])
    
    st.divider()
    
    st.subheader("⭐ Current Setlist")
    if st.session_state.favorites:
        for fav in st.session_state.favorites:
            c1, c2 = st.columns([4, 1])
            c1.caption(fav)
            if c2.button("🗑️", key=f"del_{fav}"):
                st.session_state.favorites.remove(fav)
                st.rerun()
        
        # QR Syncing
        st.divider()
        # Replace 'moselele-finder.streamlit.app' with your actual live URL after deploying
        base_url = "https://moselele-finder.streamlit.app/" 
        encoded = urllib.parse.quote(",".join(st.session_state.favorites))
        share_url = f"{base_url}?setlist={encoded}"
        
        qr = segno.make(share_url)
        out = BytesIO()
        qr.save(out, kind='png', scale=4)
        st.image(out.getvalue(), caption="Scan to sync setlist")
    else:
        st.info("Your setlist is empty.")

# --- FILTERING LOGIC ---
filtered_songs = [
    s for s in songs 
    if s['difficulty'] <= diff_filter 
    and (artist_choice == "All" or s['artist'] == artist_choice)
]

if known_chords:
    filtered_songs = [
        s for s in filtered_songs 
        if all(chord in known_chords for chord in s.get('chords', []))
    ]

# --- SEARCH & DISPLAY ---
query = st.text_input("Search song database:", placeholder="Start typing a song or artist name...")

if query:
    titles_to_search = [s['title'] for s in filtered_songs]
    matches = process.extract(query, titles_to_search, limit=12)
    display_list = [m[0] for m in matches if m[1] > 55]
else:
    display_list = [s['title'] for s in filtered_songs[:20]]

if not display_list:
    st.warning("No songs found matching those filters.")
else:
    cols = st.columns(2)
    for idx, t in enumerate(display_list):
        s_data = next(s for s in songs if s['title'] == t)
        with cols[idx % 2]:
            with st.expander(f"**{s_data['title']}** — {s_data['artist']}"):
                st.write(f"💪 **Difficulty:** {s_data['difficulty']} | 🎸 **Chords:** {', '.join(s_data.get('chords', []))}")
                
                b1, b2 = st.columns(2)
                b1.link_button("📄 Open PDF", s_data['url'], use_container_width=True)
                
                is_fav = s_data['title'] in st.session_state.favorites
                label = "❤️ In Setlist" if is_fav else "🤍 Add to Setlist"
                if b2.button(label, key=f"btn_{t}", use_container_width=True):
                    if is_fav:
                        st.session_state.favorites.remove(s_data['title'])
                    else:
                        st.session_state.favorites.append(s_data['title'])
                    st.rerun()

st.divider()
if st.button("🎲 Random Song Recommendation"):
    if filtered_songs:
        pick = random.choice(filtered_songs)
        st.success(f"How about **{pick['title']}** by **{pick['artist']}**?")
        st.link_button("View Sheet", pick['url'])