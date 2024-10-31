# 📄 About Project

![App Flow Diagram](https://github.com/Manthan-Mistry/Chess-App/blob/main/assets/diagram-2-2.svg)

## 🔍 Project Overview
The main purpose of making this project is to showcase my ability to work around ***Data Extraction (APIs)***, ***Data Manipulation (Python)***, ***Data Visualization (Streamlit + Plotly)***, and convey findings in a clear and concise manner.  
This Streamlit app provides real-time statistics and historical data of chess players in an interactive and visually appealing format. The app allows users to explore details about player profiles, including performance in various time controls like bullet, blitz, and rapid, as well as various game variants like chess, bughouse, threecheck, chess960, kingofhill, and crazyhouse.

## 💡 Features
- **Dynamic Player Selection**: Users can select any player available from the pre-existing dataframe using a dropdown.
- **Player Profile Display**: Users can view dynamic player profiles that include avatars, names, titles, country flags, and chess-related metrics like followers and ratings, similar to Chess.com’s official site.
- **Data Filtering**: Players' rating charts are filterable by specific time periods (e.g., last year, last three years, all time) using custom-styled tabs for a smooth user experience.
- **Player Info**: The app dynamically fetches and displays players' personal life, achievements, chess career, etc., from the Wikipedia API.
- **Real-time Data**: Real-time data extraction allows users to view up-to-date statistics extracted directly from Chess.com's Public API, with a progress bar indicating data loading time.

## 📱 Interactive UI
The app uses Streamlit components for a sleek, interactive interface. Users can select players from a dropdown or text input, view data in an organized multi-column layout, and enjoy custom-styled metrics enhanced with CSS. Real-time data loading is displayed via a progress bar for a more engaging user experience.

## 💪 Challenges
- **Handling Slow Loading Times**: Using `st.cache_data` for loading data to prevent it from reloading every time the app refreshes.  
- **Image Rendering**: Had issues displaying PNG/JPG images inside markdown, so had to convert ***PNG/JPG*** format to ***Base64*** encoding.  
- **Plotly Chart Visibility**: The dark background of the app caused chart visibility issues, so I modified the `.stPlotlyChart` background to white, improving contrast and number visibility.  
- **Showing Player's Country Flag**: Extracted players' country codes and dynamically showed country flags using [flagcdn.com](https://flagcdn.com).  
- **Customizing `st.selectbox` and `st.tab` Text Color**: After a long struggle with devtools and Streamlit community issues due to shared class names, I finally solved this using a CSS hack from Streamlit creator [@andfanilo](https://discuss.streamlit.io/t/can-i-change-the-color-of-the-selectbox-widget/9601/2).

## 🔨 Technologies Used
- **Chess.com’s Public API** for live data extraction.
- **Python and Streamlit** for data processing and front-end interaction.
- **Wikipedia API** for fetching additional player details.

## ⏳ Future Plans
Future updates will include:
- Additional player vs. player comparison.
- Using a database in live data extraction to store already searched players for shorter loading times and better user experience.
- Dynamically showing the top 5 junior and top 15 senior players based on live ratings maintained by [FIDE](https://ratings.fide.com/).
