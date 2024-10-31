from utils.functions import *
from streamlit_lottie import st_lottie


def show_player_info():

    # Path to your local image
    image_path = "assets/pawn_moving.png"  

    # Get the base64 encoded image
    image_base64 = get_base64_image(image_path)

    # Load and inject the CSS
    css = load_css("static/styles.css", image_base64)
    st.markdown(css, unsafe_allow_html=True)

    player_name = st.text_input("Enter Player Name", "Hikaru Nakamura")

    # Initialize session state variables if they don't exist yet
    if 'sections' not in st.session_state:
        st.session_state.sections = {}
    if 'section_titles' not in st.session_state:
        st.session_state.section_titles = []
    if 'selected_section' not in st.session_state:
        st.session_state.selected_section = None

    # Button to show player info
    if st.button("Show Player Info"):
        with st.spinner("Fetching player info..."):
            try:
                # Extract sections and summaries, and store them in session state
                sections = extract_all_sections_with_summary(player_name)
                
                # If valid sections are retrieved, store them in session state
                if sections:
                    st.session_state.sections = sections
                    st.session_state.section_titles = list(sections.keys())
                    st.session_state.selected_section = st.session_state.section_titles[0]  # Default selection
            except AttributeError:
                pass

    # Ensure sections are only shown after button click
    if 'sections' in st.session_state and st.session_state.sections:
        section_titles = st.session_state.section_titles
        
        # Only update the selected section when the radio button value changes
        selected_section = st.radio(
            "Select a section to display:",
            section_titles,
            index=section_titles.index(st.session_state.get('selected_section', section_titles[0])),
            horizontal=True
        )
        
        # Store the selected section in session state
        if selected_section != st.session_state.get('selected_section'):
            st.session_state.selected_section = selected_section
        
        # Display the selected section's title and summary
        st.markdown(f"## {st.session_state.selected_section}")
        st.markdown(f"**Summary**: {st.session_state.sections[st.session_state.selected_section]['summary']}")

    # Create an expander to show the full content of the selected section
    if st.session_state.selected_section:
        with st.expander(f"See full content of {st.session_state.selected_section}"):
            # Format full content with bullet points for readability
            full_content_with_bullets = format_with_bullets(st.session_state.sections[st.session_state.selected_section]['full_content'])
            st.markdown(full_content_with_bullets)
