import streamlit as st
from utils.functions import *


def about_project():

    #Widget CSS Styles:
    st.markdown(
        """
        <style>
        /* Change the color of widget labels and titles */
        .stMarkdown {
            color: #ffffff;  /* Title and label text color */
        }
        
        .stSelectbox label, 
        .stTextInput label, 
        .stNumberInput label,
        .stSlider label,
        .stTabs label,
        .stCheckbox label,
        .stRadio label,
        .stMultiSelect label 
        .stTextInput, .stNumberInput, .stSlider, .stCheckbox, .stRadio, .stMultiSelect {
            color: #ffffff;  /* Color for text within widgets */
        }
        .stApp > header {
            background-color: rgba(0, 0, 0, 0);  /* Transparent background */
            color: transparent;  /* Hide the text */
        }
        h1,h3{
        color: white;
        }
        </style>
        """, unsafe_allow_html=True
    )   

    # Path to your local image
    image_path = "assets/plain_dark.png"  

    # Get the base64 encoded image
    image_base64 = get_base64_image(image_path)

    # Create the CSS to display the background image
    background_css = f"""
    <style>
        .stApp {{
            background-image: url("data:image/jpg;base64,{image_base64}");
            background-size: cover;
            background-repeat: no-repeat;
            background-attachment: fixed;
        }}
    </style>
    """

    # Inject the CSS into Streamlit !!! Important
    st.markdown(background_css, unsafe_allow_html=True)

# Load SVG file
    with open("assets/Diagram-2.svg", "r") as svg_file:
        svg_content = svg_file.read()

    # App Title:
    st.markdown("""
        <h1 style="color: white;text-align: left;">📄 About Project</h1>
    """, unsafe_allow_html=True)

    # Display SVG in Streamlit
    render_svg(svg_content, width=1500, height=500)

    st.write('')

    st.subheader("🔍 Project Overview")

    st.markdown("""
        The main purpose of making this project is to showcase my ability to work around <font color = "#69923E"><ins>***Data Extraction(APIs)***</ins>,
        <ins>***Data manipulation(Python)***</ins> <ins>***Data Visualization(Streamlit + Plotly)***</ins></font> and convey findings in clear and consise manner.
        This streamlit app provides real-time statistics and historical data of chess players 
        in an interactive and visually appealing format. The app allows users to explore details about player profiles, 
        including performance in various time controls like bullet, blitz, and rapid as well as various game varients like 
        chess, bughouse, threecheck, chess960, kingofhill and crazyhouse.
    """,unsafe_allow_html=True)

    st.subheader("💡 Features")
    st.markdown("""
        - **Dynamic Player Selection**: User can select any player available from already existing dataframe using dropdown.
        - **Player Profile Display**: Users can view dynamic player profiles that include avatars, names, titles, 
        country flags, and chess-related metrics like followers and ratings just like in chess.com's official site.
        - **Data Filtering**: Players' ratings chart is filterable by specific time periods (e.g., last year, 
        last three years, all time) using tabs styled for a smooth user experience.
        - **Player Info**: The app fetches and displays players' personal life, achievements, chess career etc. dynamically.
        from Wikipedia API.
        - **Real-time Data**: Real-time data extraction allows users to view up-to-date statistics extracted directly from [Chess.com's Public API](https://www.chess.com/news/view/published-data-api), with a progress 
        bar indicating data loading time.
    """, unsafe_allow_html=True)

    st.subheader("📱 Interactive UI")
    st.write("""
        The app uses Streamlit components for a sleek, interactive interface. Users can select 
        players from a dropdown or text input, view data in an organized multi-column layout, and enjoy custom-styled 
        metrics enhanced with CSS. Real-time data loading is displayed via a progress bar for more engaging user 
        experience.
    """)

    st.subheader("💪 Challenges")
    st.markdown("""  
        - **Handeling Slow Loading Times:** Using st.cache_data for loading data so it does not load everytime app refreshes.      
        - **Image Rendering:**  Had a problem displaying png/jpg images inside markdown, so had to convert ***PNG/JPG*** format to ***Base64*** encoding.
        - **Plotly Chart Visibiity:**  Had chart visibility issue because of the app's dark background, so with the help of browser inspect tool changes *.stPlotlyChart's* background to white providing better contrast and number visibility.
        - **Showing Player's Country Flag:** Extracted players countrycode and using flagcdn.com for dynamically showing country flag.
        - **Making st.selectbox and st.tab text color different:** After long long struggle of using devtools and streamlit community issues since they share same classname, I was finally able to solve this issue using css hack from streamlit creator @andfanilo. [Checkout thread](https://discuss.streamlit.io/t/can-i-change-the-color-of-the-selectbox-widget/9601/2)
        
    """, unsafe_allow_html=True)

    st.subheader("🔨 Technologies Used")
    st.write("""
        - **Chess.com's Public API** for live data extraction.
        - **Python and Streamlit** for data processing and front-end interaction.
        - **Wikipedia API** for fetching additional player details.
    """)

    st.subheader("⏳ Future Plans")
    st.markdown("""
        Future updates will include,
        - Additional player V/s player comparison.
        - Usage of database in live data extraction to store already searched players for shorter loading times and better user experience.
        - Dynamic way of showing Top 5 Jr and Top 15 Sr players based on live rating maintained by [FIDE](https://ratings.fide.com/).
    """, unsafe_allow_html=True)
