def main():
    # Header
    header_left, header_right = st.columns([3, 2])

    # Combined GIF and title
    with header_left:
        st.markdown("""
            <div style="display: flex; align-items: center; gap: 0;">
                <img src="https://cdn.dribbble.com/users/42048/screenshots/8350927/robotintro_dribble.gif" 
                    alt="Robot" width="160" height="160" 
                    style="object-fit: contain; mix-blend-mode: multiply;">
                <div style='background: linear-gradient(135deg, #1e3a8a, #2563eb); 
                            padding: 0.8rem 1.5rem; 
                            border-radius: 12px; 
                            display: inline-block;
                            margin-left: -10px;'>
                    <h1 style='margin:0; font-size: 2.2rem; color: white; font-weight: 700;'>
                        Badea Board Foresight
                    </h1>
                </div>
            </div>
        """, unsafe_allow_html=True)

    # Badea logo
    with header_right:
        st.markdown("""
            <div style="margin-top: 20px;">
        """, unsafe_allow_html=True)
        try:
            st.image("badea.jpg", width=800)
        except:
            st.warning("Please add badea.jpg to your project directory")
        st.markdown("""
            </div>
        """, unsafe_allow_html=True)

    # Configure OpenAI
    if not configure_openai():
        st.warning("⚠️ Enter Secret key in sidebar to continue")
        return

    # Main content area
    left_col, right_col = st.columns([2, 1])
    
    with left_col:
        st.markdown('<div class="input-container">', unsafe_allow_html=True)
        input_type = st.radio("Select input type:", ["PDF Document", "Text Input"], horizontal=True)
        
        # Initialize doc_content in session state if not present
        if 'doc_content' not in st.session_state:
            st.session_state.doc_content = None
        
        if input_type == "PDF Document":
            uploaded_file = st.file_uploader("Upload PDF", type=['pdf'])
            if uploaded_file:
                st.session_state.doc_content = read_pdf(uploaded_file)
        else:
            # Create form for text input
            with st.form(key='text_input_form'):
                text_input = st.text_area("Enter text for analysis", height=200)
                submit_text = st.form_submit_button("Submit Text")
                
                if submit_text and text_input.strip():
                    st.session_state.doc_content = text_input
        
        st.markdown('</div>', unsafe_allow_html=True)

    with right_col:
        st.markdown('<div class="button-container">', unsafe_allow_html=True)
        if st.session_state.doc_content:
            if st.button("What's happening?"):
                st.session_state.results = []  # Clear previous results
                analyze_whats_happening(st.session_state.doc_content)
            
            if st.button("Why this happens?"):
                st.session_state.results = []  # Clear previous results
                analyze_why_this_happens(st.session_state.doc_content)
            
            if st.button("What could happen?"):
                st.session_state.results = []  # Clear previous results
                analyze_what_could_happen(st.session_state.doc_content)
            
            if st.button("What should the Board consider?"):
                st.session_state.results = []  # Clear previous results
                analyze_board_considerations(st.session_state.doc_content)
        else:
            st.info("Please provide input and submit to enable analysis")
            
        st.markdown('</div>', unsafe_allow_html=True)

    # Display results with PDF download options
    display_results()

    # Add download functionality for all results
    if st.session_state.results:
        st.sidebar.markdown("### 💾 Download Results")
        
        # Prepare download data
        download_data = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "analyses": st.session_state.results
        }
        
        # JSON download
        json_data = json.dumps(download_data, indent=2)
        b64_json = base64.b64encode(json_data.encode()).decode()
        st.sidebar.download_button(
            label="Download JSON",
            file_name="boardlytics_analysis.json",
            mime="application/json",
            data=b64_json,
        )
        
        # Clear results button
        if st.sidebar.button("Clear All Results"):
            st.session_state.results = []
            st.experimental_rerun()

if __name__ == "__main__":
    main()
