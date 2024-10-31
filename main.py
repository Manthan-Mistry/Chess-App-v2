import streamlit as st
from streamlit_option_menu import option_menu

# Import the functions from the other files
from templates.jr import show_junior_players
from templates.sr import show_senior_players
from templates.player_info import show_player_info
from templates.live import show_live_players
from templates.about_project import about_project

st.set_page_config(layout="wide")

# Define a dictionary to map the menu options to functions
page_content = {
    'Top Sr Players': show_senior_players,
    'Top Jr Players': show_junior_players,
    'Player Wiki': show_player_info,
    'About Project': about_project,
    'Live Stats': show_live_players
}

# Create the option menu
selected_page = option_menu(menu_title=None, 
                            options=['Top Jr Players', 'Top Sr Players', 'Player Wiki', 'Live Stats', 'About Project'],
                            icons= ['alphabet','alphabet-uppercase','wikipedia','broadcast','house'],
                            orientation='horizontal')

# Display the content based on the selected option
if selected_page in page_content:
    page_content[selected_page]()




# To-Do's For Tommorow:
# 1. Make function for displaying players info from player_info df. --> ✔✔✔✔✔✔
# 2. Make Player V/s Player page to compare two players. --> ❌❌❌
# 3. Add legend image below pie chart and stacked chart from powerpoint or figma. --> ✔✔✔✔✔✔
# 4. Can make custome chess related background. --> ✔✔✔✔✔✔
# 5. Change game_class to st.tabs from st.selectbox with and display category names with icons. --> ❌❌❌
# 6. Show players real name in selectbox but treat their username for processing. --> ✔✔✔✔✔✔
# 7. Make players rating area curve. (Rating V/s Year) --> ✔✔✔✔✔✔
# 8. Show %games below h stacked bar chart and # above as in chess.com. --> ✔✔✔✔✔✔
# 9. Highest Rating with date. --> ✔✔✔✔✔✔
# 10. Time period filtering in rating curve. --> ✔✔✔✔✔✔
# 11. Make 3 more metrics below main metrics for one for avg opponent rating and other for opponent rating (When player wins, draws, losses) 
#     and last for best wins aginst with rating and name. --> ✔✔✔✔✔✔
# 12. Make df visually attractive using (AGgrid).
# 13. Can make upgraded version that fetches info from Chess.com's Unofficial API on the go instead getting data from dataframe. --> ✔✔✔✔✔✔
# 14. Implement # 10. since its real time. --> ✔✔✔✔✔✔


# Can make show achievements and show fun-facts button and fetch info from wikipidia. --> ✔✔✔✔✔✔

# Future Version Updates:
# Make use of database in live data extraction to store already searched players for shorter loading times. 
