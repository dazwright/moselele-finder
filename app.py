# --- DISPLAY ---
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

                # Chord Image Logic
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
                    lyrics_with_bold = clean_and_bold_lyrics(song['Body'].strip())
                    st.markdown(f'<div class="lyrics-box">{lyrics_with_bold}</div>', unsafe_allow_html=True)

        with l_col: 
            st.button("➕ List", key=f"plist_btn_{idx}", on_click=handle_playlist_click, args=(song_id,))
        with p_col:
            if song.get('URL') and song['URL'] != "":
                st.markdown(f'<a href="{song["URL"]}" target="_blank" class="action-btn">📄 PDF</a>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()