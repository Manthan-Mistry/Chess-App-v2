import requests
import streamlit as st
from datetime import datetime,timedelta
import pandas as pd
import re
import time
import plotly.graph_objects as go
import plotly.express as px
import wikipedia
from chessdotcom import Client
import base64
import pyodbc
from sqlalchemy import create_engine, text
from typing import List, Dict, Union, Optional, Tuple, Any


PLOT_BGCOLOR = "#fff"

headers = {'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36'}
Client.request_config["headers"]["User-Agent"] = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36")

win_conditions = ['win']
lose_conditions = ['resigned', 'checkmated', 'timeout', 'abandoned']
draw_conditions = ['agreed', 'stalemate', '50move','repetition','timevsinsufficient','insufficient']

color_map = {'resigned':'#69923E','timeout':'#4E7837','checkmated':'#4B4847','abandoned':'#2C2B29','others':'#161619'}
color_list = ['rgba(78,120,55,0.8)','rgba(105,146,62,0.8)','rgba(75,72,71,0.8)','rgba(44,43,41,0.8)','rgba(22,22,25,1)']

# Function to load and inject CSS from a file
def load_css(css_file_path: str, image_base64: str) -> str:
    """
    Loads a CSS file, replaces a placeholder with an image in base64 format, 
    and returns the CSS wrapped in a <style> tag for embedding in HTML.

    Args:
        css_file_path (str): The path to the CSS file.
        image_base64 (str): The base64 encoded string of the image to be embedded.

    Returns:
        str: The CSS content wrapped in <style> tags with the base64 image inserted.
    """
    with open(css_file_path, "r") as f:
        css_content = f.read()
    
    css_content = css_content.replace("{{image_base64}}", image_base64)    
    return f"<style>{css_content}</style>"

#Load Jr Data:
@st.cache_data(show_spinner=False)
def jr_data() -> pd.DataFrame:
    """
    Load junior players' statistics from a CSV file and preprocess the DataFrame.

    Returns:
    pd.DataFrame: A DataFrame containing junior players' statistics without the 'game_pgn' column.
    """
    df = pd.read_csv('data/TOP_5_Jr_Players_Stats2.csv')
    return df

#Load Sr Data:
@st.cache_data(show_spinner=False)
def sr_data() -> pd.DataFrame:
    """
    Load senior players' statistics from a CSV file and preprocess the DataFrame.

    Returns:
    pd.DataFrame: A DataFrame containing senior players' statistics, excluding 'daily' game time class.
    """
    df = pd.read_csv('data/TOP_15_Sr_Players_Stats_New.csv')
    df[df['game_time_class']!='daily']
    return df

# Load Live Player Data:
@st.cache_data(show_spinner=False)
def load_data(player: str) -> pd.DataFrame:
    return get_player_stats(player.lower())

# Function to get monthly archives for a player
def get_archives(player_name: str) -> List[str]:
        """
        Fetches the game archives of a player from the Chess.com API.

        Args:
            player_name (str): The username of the chess player on Chess.com.

        Returns:
            List[str]: A list of URLs representing the archives for the player.
            If the request fails, returns an empty list.
        """
        
        response = requests.get(f"https://api.chess.com/pub/player/{player_name}/games/archives", headers = headers)
        if response.status_code == 200:
            archives = response.json().get('archives', [])
            return archives
        else:
            print(f"Failed to retrieve data: {response.status_code}")
            return []

# Function to get games from a monthly archive
def get_games_from_archive(url: str) -> List[Dict]:
    """
    Fetches games from a specific archive URL provided by the Chess.com API.

    Args:
        url (str): The URL of the Chess.com archive to fetch games from.

    Returns:
        List[Dict]: A list of game data in dictionary format. 
        If the request fails, returns an empty list.
    """
    response = requests.get(url, headers = headers)
    if response.status_code == 200:
        games = response.json().get('games', [])
        return games
    else:
        print(f"Failed to retrieve data from {url}: {response.status_code}")
        return []

# Formatting value in proper date format:
def convert_to_date(value: Union[int, float, str]) -> str:
    """
    Converts a Unix timestamp or date string to a formatted 'dd-mm-yyyy' date string.

    Args:
        value (Union[int, float, str]): The value to be converted, which can be a Unix timestamp (int or float) 
                                        or a date string in the format '%Y-%m-%d %H:%M:%S'.

    Returns:
        str: The formatted date string in 'dd-mm-yyyy' format. 
             If the value cannot be converted, returns the original value.
    """
    try:
        if isinstance(value, (int, float)):  # Check if the value is numeric (Unix timestamp)
            date = datetime.utcfromtimestamp(value).date()  # Extract only the date part
        else:  # Assume it's already a string date
            date = pd.to_datetime(value, format='%Y-%m-%d %H:%M:%S', errors='coerce').date()
        
        # Format the date as dd-mm-yyyy
        return date.strftime('%d-%m-%Y')
    except (ValueError, TypeError):
        return value

# Extracting opening names from game_data(JSON):
def get_openings_2(game: Dict) -> Optional[str]:
    """
    Extracts the opening name from a given chess game dictionary using the 'pgn' field.

    Args:
        game (Dict): A dictionary representing the chess game data, typically containing a 'pgn' key.

    Returns:
        Optional[str]: The name of the chess opening if found, otherwise None.
    """
    try:
        pgn = game.get("pgn", "")
        # Extract the opening name using a more reliable method
        if "ECOUrl" in pgn:
            opening_name = pgn.split('ECOUrl')[1].split('openings/')[1].split('"]')[0]
            opening_name = re.split(r'-(\d)', opening_name)[0].replace('"]', '').split("\n")[0]
            return opening_name
        else:
            return None
    except IndexError:
        return None

# Extracting game_date from game_data(JSON):
def get_date(pgn: Optional[str]) -> Optional[str]:
    """
    Extracts the date of a chess game from the PGN (Portable Game Notation) string.

    Args:
        pgn (Optional[str]): The PGN string containing the game details. 
                             It should contain the '[Date ' field for the date extraction.

    Returns:
        Optional[str]: The date of the game in 'yyyy.mm.dd' format if found, otherwise None.
    """
    if pgn is not None:
        date = pgn.split('[Date ')[1].split(']\n[Round')[0].replace('"','')
        return date
    else:
        None

# Extracting all stats from game_data(JSON):
def get_player_stats(player_name: str) -> pd.DataFrame:
    """
    Retrieves and processes all archived chess games for a specific player from Chess.com, 
    extracting relevant game statistics.

    Args:
        player_name (str): The username of the chess player on Chess.com.

    Returns:
        pd.DataFrame: A DataFrame containing details for each game including URLs, dates, 
                      time controls, ratings, results, and accuracies.
    """

    # Main script
    start_time = time.time()  # Record the start time

    archives = get_archives(player_name)

    all_games = []

    for archive_url in archives:
        games = get_games_from_archive(archive_url)
        if isinstance(games, list):  # Ensure games is a list
            all_games.extend(games)

    # Extracting the relevant attributes for each game
    formatted_games = []

    for game in all_games:
        if isinstance(game, dict):  # Ensure each game is a dictionary
            game_data = {
                "game_url": game.get("url"),
                "game_date": get_date(game.get("pgn")),
                "game_time_control": game.get("time_control"),
                "game_time_class": game.get("time_class"),
                "game_variant": game.get("rules"),
                "opening": get_openings_2(game),
                "white_rating": game.get("white", {}).get("rating"),
                "white_result": game.get("white", {}).get("result"),
                "white_username": game.get("white", {}).get("username"),
                "white_accuracy": game.get("accuracies", {}).get("white"),
                "black_rating": game.get("black", {}).get("rating"),
                "black_result": game.get("black", {}).get("result"),
                "black_username": game.get("black", {}).get("username"),
                "black_accuracy": game.get("accuracies", {}).get("black")
            }
            formatted_games.append(game_data)

    # Calculate and print execution time
    end_time = time.time()  # Record the end time
    execution_time = end_time - start_time

    print(f'Time Taken: {execution_time} sec.')
    
    df = pd.DataFrame(formatted_games)
    return df

def get_player_profile(username: str) -> Optional[Dict]:
    """
    Fetches the player profile data from Chess.com using the player's username.

    Args:
        username (str): The Chess.com username of the player.

    Returns:
        Optional[Dict]: A dictionary containing the player's profile data if the request is successful, 
                        otherwise None.
    """
    url = f'https://api.chess.com/pub/player/{username}'
    response = requests.get(url, headers = headers)
    
    # Check if the response is successful
    if response.status_code == 200:
        try:
            return response.json()
        except ValueError:
            print(f"Error: Invalid JSON response for {username}")
            return None
    else:
        print(f"Error: Received status code {response.status_code} for {username}")
        return None

def get_player_info(username: str) -> pd.DataFrame:
    """
    Retrieves the player's profile information from Chess.com and formats it into a DataFrame.

    Args:
        username (str): The Chess.com username of the player.

    Returns:
        pd.DataFrame: A DataFrame containing the player's information, including avatar, ID, 
                      URL, name, title, followers, country, and other relevant details.
    """
    df = []
    
    info = get_player_profile(username)  # Get the player's profile data

    if info:

        avatar_url = info.get('avatar', '')

        player_info = {
            'Avatar': avatar_url,
            'ID': info.get('player_id', ''),
            'URL': info.get('url', ''),
            'Profile': info.get('url', ''),
            'Name': info.get('name', ''),
            'Username': info.get('username', ''),
            'Title': info.get('title', ''),
            'Followers': info.get('followers', ''),
            'Country': info.get('country', ''),
            'Location': info.get('location', ''),
            'Last Online': info.get('last_online', ''),
            'Joined': info.get('joined', ''),
            'Status': info.get('status', ''),
            'Is Streamer': info.get('is_streamer', False),
            'Verified': info.get('verified', False),
            'Twitch URL': info.get('twitch_url', ''),
        }

        df.append(player_info)  # Append to the DataFrame list

    # Return the DataFrame
    return pd.DataFrame(df)

# Extracting opening names with colors:
def get_openings_as(df: pd.DataFrame, player: str, color: str) -> Tuple[List[str], List[str]]:
    """
    Analyzes the openings played by a specified player in a given color and returns the most played 
    and most accurate openings.

    Args:
        df (pd.DataFrame): The DataFrame containing game data including opening details.
        player (str): The username of the player whose openings are being analyzed.
        color (str): The color of the player ('white' or 'black').

    Returns:
        Tuple[List[str], List[str]]: A tuple containing two lists:
            - The first list contains the five most played openings.
            - The second list contains the five most accurate openings.
    """

    df2 = df[(df[f'{color}_username'] == player)]
    temp_df = df2.groupby(['opening']).agg({'game_variant':'count',f'{color}_accuracy':'mean'})
    most_played_openings = list(temp_df.sort_values(by ='game_variant', ascending = False).reset_index()['opening'])[:5]
    most_accurate_openings = list(temp_df.sort_values(by = f'{color}_accuracy', ascending = False).reset_index()['opening'])[:5]
    
    
    return most_played_openings, most_accurate_openings

# Extracting least played opening names:
def get_least_played_openings(df: pd.DataFrame, player: str) -> List[str]:
    """
    Retrieves the least played openings by a specified player.

    Args:
        df (pd.DataFrame): The DataFrame containing game data including opening details.
        player (str): The username of the player whose openings are being analyzed.

    Returns:
        List[str]: A list containing the five least played openings by the player.
    """
    
    # Filter for games where the player was either white or black
    df2 = df[(df['white_username'] == player) | (df['black_username'] == player)]
    
    # Group by the opening and count the number of games played for each opening
    temp_df = df2.groupby('opening').agg({'game_variant': 'count'}).reset_index()
    
    # Sort by the number of games played in ascending order to get the least played openings
    least_played_openings = list(temp_df.sort_values(by='game_variant', ascending=True)['opening'])[:5]
    
    return least_played_openings

# For displaying player stats:
def display_player_stats(df: pd.DataFrame, player: str) -> Tuple[int, float, float, int, int, int, int, float, float, float,
                                                                  int, int, int, int, float, float, float,
                                                                  int, List[str], List[str], List[str], List[str]]:
    """
    Calculates and displays statistics for a specified player based on game data.

    Args:
        df (pd.DataFrame): The DataFrame containing game data.
        player (str): The username of the player whose stats are to be calculated.

    Returns:
        Tuple[int, float, float, int, int, int, int, float, float, float,
              int, int, int, int, float, float, float,
              int, List[str], List[str], List[str], List[str]]:
              A tuple containing various statistics:
              - Total games played
              - White accuracy
              - Black accuracy
              - Wins as white
              - Losses as white
              - Draws as white
              - Total games as white
              - White win ratio
              - White loss ratio
              - White draw ratio
              - Wins as black
              - Losses as black
              - Draws as black
              - Total games as black
              - Black win ratio
              - Black loss ratio
              - Black draw ratio
              - Number of unique openings
              - Most played openings as white
              - Most accurate openings as white
              - Most played openings as black
              - Most accurate openings as black
    """
    
    df2 = df[(df['white_username'] == player) | (df['black_username'] == player)]
    
    total_games = len(df[(df['white_username'] == player) | (df['black_username'] == player)])
    opening_lines = len(df[(df['white_username'] == player) | (df['black_username'] == player)]['opening'].unique())
    white_accuracy = round(df[(df['white_username'] == (player)) & (df['white_accuracy'] != 0)]['white_accuracy'].mean(),2)  
    black_accuracy = round(df[(df['black_username'] == (player)) & (df['black_accuracy'] != 0)]['black_accuracy'].mean(),2)
    
    wins_as_white = len(df[(df['white_username'] == player) 
                               & (df['white_result'].isin(win_conditions))])
    
    loss_as_white = len(df[(df['white_username'] == player) 
                               & (df['white_result'].isin(lose_conditions))])
    
    draws_as_white = len(df[(df['white_username'] == player) &
                             (df['white_result'].isin(draw_conditions))])

    total_games_white = len(df[(df['white_username'] == player)])
    white_win_ratio = round((wins_as_white / total_games_white)*100,2) 
    white_loss_ratio = round((loss_as_white / total_games_white)*100,2)
    white_draw_ratio = round((draws_as_white / total_games_white)*100,2)

    wins_as_black = len(df[(df['black_username'] == player) 
                               & (df['black_result'].isin(win_conditions))])
    
    loss_as_black = len(df[(df['black_username'] == player) 
                               & (df['black_result'].isin(lose_conditions))])
    
    draws_as_black = len(df[(df['black_username'] == player) &
                             (df['black_result'].isin(draw_conditions))])
    
    total_games_black = df[(df['black_username'] == player)].shape[0]   
    black_win_ratio = round((wins_as_black / total_games_black)*100,2)
    black_loss_ratio = round((loss_as_black / total_games_black)*100,2)
    black_draw_ratio = round((draws_as_black / total_games_black)*100,2)
    

    temp_df = df2.groupby(['opening']).agg({'game_variant':'count','white_accuracy':'mean'})
    
    most_played_openings = temp_df.sort_values(by ='game_variant', ascending = False).reset_index()['opening'][:3]
    most_accurate_openings = temp_df.sort_values(by ='white_accuracy', ascending = False).reset_index()['opening'][:3]
    
    white_most_played_openings, white_most_accurate_openings = get_openings_as(df, player, 'white')
    black_most_played_openings, black_most_accurate_openings = get_openings_as(df, player, 'black')

    return (total_games, white_accuracy, black_accuracy,
            wins_as_white, loss_as_white, draws_as_white, total_games_white, white_win_ratio, white_loss_ratio, white_draw_ratio,
            wins_as_black, loss_as_black, draws_as_black, total_games_black, black_win_ratio, black_loss_ratio, black_draw_ratio,
            opening_lines, white_most_played_openings, white_most_accurate_openings, black_most_played_openings, black_most_accurate_openings)

# Create Horizontal Bar chart just as in chess.com:
def create_horizontal_stacked_bar_chart(win_pct: float, draw_pct: float, lose_pct: float, 
                                         num_win: int, num_draw: int, num_lose: int, 
                                         height: int, width: int) -> go.Figure:

    """
    Creates a horizontal stacked bar chart for player statistics.

    Parameters:
    - white_win_pct (float): Win percentage.
    - draw_pct (float): Draw percentage.
    - lose_pct (float): Loss percentage.
    - height (int): Height of the chart in pixels.

    Returns:
    - fig (plotly.graph_objects.Figure): The Plotly figure object.
    """
     # Create a horizontal stacked bar chart
    fig = go.Figure()

    # Add the "Win" bar
    fig.add_trace(go.Bar(
        y=['Player'],
        x=[win_pct],
        name='Win Rate',
        orientation='h',
        marker_color='#69923E',
        text=[f"<b>{num_win}  </b>"],  # Display number of games won
        textposition='none'  # Hide default text position
    ))

    # Add the "Draw" bar
    fig.add_trace(go.Bar(
        y=['Player'],
        x=[draw_pct],
        name='Draw Rate',
        orientation='h',
        marker_color='#A9A9A9',
        text=[f"<b>{num_draw}</b>"],  # Display number of draws
        textposition='none'  # Hide default text position
    ))

    # Add the "Lose" bar
    fig.add_trace(go.Bar(
        y=['Player'],
        x=[lose_pct],
        name='Loss Rate',
        orientation='h',
        marker_color='#ff5733',
        text=[f"<b>{num_lose}</b>"],  # Display number of losses
        textposition='none'  # Hide default text position
    ))

    # Add annotations for percentage labels below the bar
    fig.add_annotation(
        x=win_pct / 4.5, y=-1.5, 
        text=f"<b>{round(win_pct)}% Won </b>", showarrow=False, 
        font_size=12, font_color='#69923E'
    )  # Position below the bar
    fig.add_annotation(
        x=win_pct + draw_pct / 2, y=-1.5, 
        text=f"<b>{round(draw_pct)}% Draw </b>", showarrow=False, 
        font_size=12, font_color='#A9A9A9'
    )  # Position below the bar
    fig.add_annotation(
        x=win_pct + draw_pct + lose_pct / 1.35, y=-1.5, 
        text=f"<b>{round(lose_pct)}% Lost </b>", showarrow=False, 
        font_size=12, font_color='#ff5733'
    )  # Position below the bar

    # Add annotations for number of games above the bar
    fig.add_annotation(
        x=win_pct / 8, y=1.6, 
        text=f"<b>{num_win}</b>", showarrow=False, 
        font_size=12, font_color='green'
    )  # Position above the bar
    fig.add_annotation(
        x=win_pct + draw_pct / 2, y=1.6, 
        text=f"<b>{num_draw}</b>", showarrow=False, 
        font_size=12, font_color='grey'
    )  # Position above the bar
    fig.add_annotation(
        x=win_pct + draw_pct + lose_pct / 1.2, y=1.6, 
        text=f"<b>{num_lose}</b>", showarrow=False, 
        font_size=12, font_color='red'
    )  # Position above the bar

    # Update the layout
    fig.update_layout(
        barmode='stack',
        title='',
        xaxis_title='',
        yaxis_title='',
        xaxis=dict(tickformat=".0%",showticklabels=False),  # Hide x-axis labels)
        yaxis=dict(showticklabels=False),  # Hide y-axis labels),
        legend=dict(visible=False),  # Hide the legend
        margin=dict(l=0, r=0, t=10, b=10),  # Increase top and bottom margins for labels
        height=height,  # Set the height of the chart
        width = width
    )

    return fig

# Get Player Avatar:
def get_player_avatar(profile_df: pd.DataFrame, username: str) -> Optional[str]:
    """
    Retrieve the avatar (profile photo URL) for the specified player from the profile DataFrame.

    Parameters:
    - username (str): The username of the player.
    - profile_df (pd.DataFrame): The DataFrame containing player profile information.

    Returns:
    - str: The URL of the player's avatar if found.
    - None: If the player is not found in the DataFrame.
    """
    # Filter the DataFrame to find the player's profile information
    player_profile = profile_df[profile_df['username'] == username.lower()]
    
    # Check if the player was found
    if not player_profile.empty:
        # Return the profile photo URL
        return player_profile.iloc[0]['recent_avatar_url']  # Adjust column name if different
    else:
        # Return None if the player was not found
        return None

def get_sr_player_avatar(sr_profile_df: pd.DataFrame, username: str) -> Union[str, None]:
    """
    Retrieve the avatar (profile photo URL) for the specified player from the profile DataFrame.

    Parameters:
    - username (str): The username of the player.
    - profile_df (pd.DataFrame): The DataFrame containing player profile information.

    Returns:
    - str: The URL of the player's avatar if found.
    - None: If the player is not found in the DataFrame.
    """
    # Filter the DataFrame to find the player's profile information
    sr_player_profile = sr_profile_df[sr_profile_df['username'] == username]
    
    # Check if the player was found
    if not sr_player_profile.empty:
        # Return the profile photo URL
        return sr_player_profile.iloc[0]['recent_avatar_url'].strip()  # Adjust column name if different
    else:
        # Return None if the player was not found
        return '-'

# Function to create pie chart for player's wins (how opponent lost)
def player_win_chart(df: pd.DataFrame, player: str, w: int, h: int) -> Any:
    """
    Creates a pie chart showing how the specified player won their games.

    Parameters:
    - df (pd.DataFrame): The DataFrame containing game results and player information.
    - player (str): The username of the player whose win chart is being created.
    - w (int): The width of the chart in pixels.
    - h (int): The height of the chart in pixels.

    Returns:
    - plotly.graph_objects.Figure: A Plotly figure object containing the pie chart.
    """

    other_condition = 'other'

    # Filter games where player won
    won_games = df[((df['white_username'] == player) & (df['white_result'].isin(win_conditions))) |
                   ((df['black_username'] == player) & (df['black_result'].isin(win_conditions)))]

    # Classify how the opponent lost
    won_games = won_games.copy()
    
    won_games['opponent_loss_reason'] = won_games.apply(
        lambda row: row['black_result'] if row['white_username'] == player else row['white_result'],
        axis=1
    )

    # Filter and label opponent loss reasons
    opponent_loss_reasons = won_games['opponent_loss_reason'].apply(lambda x: x if x in lose_conditions else other_condition)

    # Calculate percentages
    loss_counts = opponent_loss_reasons.value_counts(normalize=True) * 100

    # Create pie chart
    fig = go.Figure(data=[go.Pie(
        labels=loss_counts.index,
        values=loss_counts,
        hole=0.5,
        marker=dict(colors=color_list),
        direction='clockwise'
        
    )]) 
    
    fig.update_layout(showlegend=False,
                      width=w, height=h,
                      margin=dict(l=0, r=0, t=60, b=20), title_x = 0.15,
                      title=dict(text= f"How {player} won games:", y= 0.95),
                      paper_bgcolor=PLOT_BGCOLOR,
                      plot_bgcolor="skyblue"
                      )
    
    fig.update_traces(marker = dict(line = dict(color = '#ffffff', width = 2)),
                    #   textinfo = 'percent+label',
                      textfont = dict(color = 'white'))

    return fig

# Function to create pie chart for player's draws.
def player_draw_chart(df: pd.DataFrame, player: str, w: int, h: int) -> Any:
    """
    Creates a pie chart showing how the specified player drew their games.

    Parameters:
    - df (pd.DataFrame): The DataFrame containing game results and player information.
    - player (str): The username of the player whose draw chart is being created.
    - w (int): The width of the chart in pixels.
    - h (int): The height of the chart in pixels.

    Returns:
    - plotly.graph_objects.Figure: A Plotly figure object containing the pie chart.
    """

    draw_conditions = ['stalemate', 'insufficient material', 'repetition', '50-move rule', 'agreed draw', 'timeout draw']  # Add any other draw conditions

    other_condition = 'other'

    # Filter games where the result was a draw
    drawn_games = df[((df['white_username'] == player) & (df['white_result'].isin(draw_conditions))) |
                     ((df['black_username'] == player) & (df['black_result'].isin(draw_conditions)))]

    # Classify how the player drew
    drawn_games = drawn_games.copy()

    drawn_games['player_draw_reason'] = drawn_games.apply(
        lambda row: row['white_result'] if row['white_username'] == player else row['black_result'],
        axis=1
    )

    # Filter and label player draw reasons
    player_draw_reasons = drawn_games['player_draw_reason'].apply(lambda x: x if x in draw_conditions else other_condition)

    # Calculate percentages
    draw_counts = player_draw_reasons.value_counts(normalize=True) * 100

    # Create pie chart
    fig = go.Figure(data=[go.Pie(
        labels=draw_counts.index,
        values=draw_counts,
        hole=0.5,
        marker=dict(colors=color_list),
        direction='clockwise'
    )])

    fig.update_layout(showlegend=False,
                      width=w, height=h,
                      margin=dict(l=0, r=0, t=60, b=20), title_x=0.15,
                      title=dict(text=f"How {player} drew games:", y=0.95),
                      paper_bgcolor=PLOT_BGCOLOR,
                      plot_bgcolor="skyblue"
                      )

    fig.update_traces(marker=dict(line=dict(color='#ffffff', width=2)),
                      textfont=dict(color='white'))

    return fig

# Function to create pie chart for player's losses (how the player lost)
def player_loss_chart(df: pd.DataFrame, player: str, w: int, h: int) -> Any:
    """
    Creates a pie chart showing how the specified player lost their games.

    Parameters:
    - df (pd.DataFrame): The DataFrame containing game results and player information.
    - player (str): The username of the player whose loss chart is being created.
    - w (int): The width of the chart in pixels.
    - h (int): The height of the chart in pixels.

    Returns:
    - plotly.graph_objects.Figure: A Plotly figure object containing the pie chart.
    """
    other_condition = 'other'

    # Filter games where player lost
    lost_games = df[((df['white_username'] == player) & (df['white_result'].isin(lose_conditions))) |
                    ((df['black_username'] == player) & (df['black_result'].isin(lose_conditions)))]

    # Classify how the player lost
    lost_games = lost_games.copy()

    lost_games['player_loss_reason'] = lost_games.apply(
        lambda row: row['white_result'] if row['white_username'] == player else row['black_result'],
        axis=1
    )

    # Filter and label player loss reasons
    player_loss_reasons = lost_games['player_loss_reason'].apply(lambda x: x if x in lose_conditions else other_condition)

    # Calculate percentages
    loss_counts = player_loss_reasons.value_counts(normalize=True) * 100

    # Create pie chart
    fig = go.Figure(data=[go.Pie(
        labels=loss_counts.index,
        values=loss_counts,
        hole=0.5,
        marker=dict(colors=color_list),
        direction='clockwise'
    )]) 
    
    fig.update_layout(showlegend=False,
                      width=w, height=h,
                      margin=dict(l=0, r=0, t=60, b=20), title_x = 0.15,
                      title=dict(text= f"How {player} lost games:", y= 0.95),
                      paper_bgcolor=PLOT_BGCOLOR,
                      plot_bgcolor="skyblue"
                      ) 

    fig.update_traces(marker = dict(line = dict(color = '#ffffff', width = 2)),
                    #   textinfo = 'percent+label',
                      textfont = dict(color = 'white'))

    return fig

# Function to show al stats as color white:
def  show_white_stats(total_games_white: int, white_win_ratio: float, white_draw_ratio: float, 
                     white_loss_ratio: float, wins_as_white: int, draws_as_white: int, 
                     loss_as_white: int, white_most_accurate_openings: List[str], 
                     white_most_played_openings: List[str]) -> None:
    """
    Displays statistics for a player playing as White in a Streamlit app.

    Parameters:
    - total_games_white (int): Total number of games played as White.
    - white_win_ratio (float): Win ratio as a percentage.
    - white_draw_ratio (float): Draw ratio as a percentage.
    - white_loss_ratio (float): Loss ratio as a percentage.
    - wins_as_white (int): Total wins as White.
    - draws_as_white (int): Total draws as White.
    - loss_as_white (int): Total losses as White.
    - white_most_accurate_openings (List[str]): List of most accurate openings played as White.
    - white_most_played_openings (List[str]): List of most played openings as White.
    """
    st.session_state.tab_selected = 'white'
    
    #Show Player as White Stats:
    with st.container(height = 375):
        st.markdown(f"""
        <div class="metrics-row">
            <div class="metric-container-spec">
                <div class="metric-label">◻ Total Games</div>
                <div class="metric-value">{total_games_white}</div>
            </div>
            <div class="metric-container-spec">
                <div class="metric-label">◻ Total Wins</div>
                <div class="metric-value">{wins_as_white}</div>
                <div class="metric-delta-grey">{white_win_ratio}%</div>
            </div>
            <div class="metric-container-spec">
                <div class="metric-label">◻ Total Draws</div>
                <div class="metric-value">{draws_as_white}</div>
                <div class="metric-delta-grey">{white_draw_ratio}%</div>
            </div>
            <div class="metric-container-spec">
                <div class="metric-label">◻ Total Losses</div>
                <div class="metric-value">{loss_as_white}</div>
                <div class="metric-delta-grey">{white_loss_ratio}%</div>
            </div>
        </div>
    """, unsafe_allow_html=True)

        
        # st.write()
        st.divider()
        #Display Most Accurate and Most Played openings:

        # Define emojis for medals
        gold_medal = "🥇"
        silver_medal = "🥈"
        bronze_medal = "🥉"

        col1, col2, col3 = st.columns([3.5,1,2])

        with col1:
            st.markdown('**Most Accurate Openings White**', unsafe_allow_html=True)
            st.markdown(f"{gold_medal} {white_most_accurate_openings[0]}")
            st.markdown(f"{silver_medal} {white_most_accurate_openings[1]}")
            st.markdown(f"{bronze_medal} {white_most_accurate_openings[2]}")

        # with col2: #??????
            #     st.markdown(
            #         """
            #         <style>
            #         .divider {
            #             width: 3px;
            #             background-color: #00000;
            #             height: 100%;
            #             display: inline-block;
            #             vertical-align: middle;
            #         }
            #         </style>
            #         <div class="divider"></div>
            #         """,
            #         unsafe_allow_html=True
            #     )

        with col3:
            st.markdown('**Most Played Openings White**')
            st.markdown(f"{gold_medal} {white_most_played_openings[0]}")
            st.markdown(f"{silver_medal} {white_most_played_openings[1]}")
            st.markdown(f"{bronze_medal} {white_most_played_openings[2]}")

def show_black_stats(total_games_black: int, black_win_ratio: float, black_draw_ratio: float, 
                     black_loss_ratio: float, wins_as_black: int, draws_as_black: int, 
                     loss_as_black: int, black_most_accurate_openings: List[str], 
                     black_most_played_openings: List[str]) -> None:
    """
    Displays statistics for a player playing as Black in a Streamlit app.

    Parameters:
    - total_games_black (int): Total number of games played as Black.
    - black_win_ratio (float): Win ratio as a percentage.
    - black_draw_ratio (float): Draw ratio as a percentage.
    - black_loss_ratio (float): Loss ratio as a percentage.
    - wins_as_black (int): Total wins as Black.
    - draws_as_black (int): Total draws as Black.
    - loss_as_black (int): Total losses as Black.
    - black_most_accurate_openings (List[str]): List of most accurate openings played as Black.
    - black_most_played_openings (List[str]): List of most played openings as Black.
    """
    with st.container(height = 450):
            st.markdown(f"""
            <div class="metrics-row">
                <div class="metric-container-spec">
                    <div class="metric-label">◼ Total Games</div>
                    <div class="metric-value">{total_games_black}</div>
                </div>
                <div class="metric-container-spec">
                    <div class="metric-label">◼ Total Wins</div>
                    <div class="metric-value">{wins_as_black}</div>
                    <div class="metric-delta-grey">{black_win_ratio}%</div>
                </div>
                <div class="metric-container-spec">
                    <div class="metric-label">◼ Total Draws</div>
                    <div class="metric-value">{draws_as_black}</div>
                    <div class="metric-delta-grey">{black_draw_ratio}%</div>
                </div>
                <div class="metric-container-spec">
                    <div class="metric-label">◼ Total Losses</div>
                    <div class="metric-value">{loss_as_black}</div>
                    <div class="metric-delta-grey">{black_loss_ratio}%</div>
                </div>
            </div>
        """, unsafe_allow_html=True)

            st.divider()

            #Display Most Accurate and Most Played openings:

            # Define emojis for medals
            gold_medal = "🥇"
            silver_medal = "🥈"
            bronze_medal = "🥉"

            col1, col2, col3 = st.columns([3.5,1,2])

            with col1:
                st.markdown('**Most Accurate Openings Black**', unsafe_allow_html=True)
                st.markdown(f"{gold_medal} {black_most_accurate_openings[0]}")
                st.markdown(f"{silver_medal} {black_most_accurate_openings[1]}")
                st.markdown(f"{bronze_medal} {black_most_accurate_openings[2]}")
            
            with col2:
                ''
            
            with col3:
                st.markdown('**Most Played Openings Black**')
                st.markdown(f"{gold_medal} {black_most_played_openings[0]}")
                st.markdown(f"{silver_medal} {black_most_played_openings[1]}")
                st.markdown(f"{bronze_medal} {black_most_played_openings[2]}")

def filter_data_by_time_period(df: pd.DataFrame, time_period: str) -> pd.DataFrame:
    """
    Filters the DataFrame based on the specified time period relative to the maximum game date.

    Parameters:
    - df (pd.DataFrame): The DataFrame containing game data with a 'game_date' column.
    - time_period (str): The time period to filter by. Options are 'Last 1 Year', 'Last 3 Years', or 'All Time'.

    Returns:
    - pd.DataFrame: Filtered DataFrame based on the specified time period.
    """
    max_date = df['game_date'].max()
    if time_period == 'Last 1 Year':
        return df[df['game_date'] >= (max_date - pd.DateOffset(years=1))]
    elif time_period == 'Last 3 Years':
        return df[df['game_date'] >= (max_date - pd.DateOffset(years=3))]
    else:
        return df
    
def create_rating_chart(df: pd.DataFrame, selected_playername: str, selected_player: str, players_dict: dict, width: int, height: int, time_period: str):
    """
    Creates a smoothed rating chart for the selected player over the specified time period.

    Parameters:
    - df (pd.DataFrame): DataFrame containing game data with 'game_date', 'white_username', 'black_username', 
                         'white_rating', and 'black_rating'.
    - selected_playername (str): Name of the selected player for display.
    - selected_player (str): Username of the selected player.
    - players_dict (dict): Dictionary containing player data for special handling.
    - width (int): Width of the chart.
    - height (int): Height of the chart.
    - time_period (str): Time period for filtering data.

    Returns:
    - plotly.graph_objects.Figure: A Plotly Figure object for the rating chart.
    """

    df['game_date'] = pd.to_datetime(df['game_date'])

    # Filter for games where the player is either white or black
    filtered_df = df[(df['white_username'] == selected_player) | (df['black_username'] == selected_player)]

    # Filter by selected time period
    filtered_df = filter_data_by_time_period(filtered_df, time_period)

    # Check if filtered data is empty before proceeding
    if filtered_df.empty:
        st.warning(f"No data available for {time_period}.")
        return None

    # Melt the DataFrame to get a unified rating column
    melted_df = pd.melt(filtered_df, 
                        id_vars=['game_date'], 
                        value_vars=['white_rating', 'black_rating'], 
                        var_name='color', 
                        value_name='rating')

    # Group by game_date and get the maximum rating per day
    max_rating_per_day = melted_df.groupby('game_date')['rating'].max().reset_index()

    # Apply a rolling average with a window of 12 for smoothing
    max_rating_per_day['smoothed_rating'] = max_rating_per_day['rating'].rolling(window=12).mean()

    # Filter out rows where the smoothed rating is NaN
    filtered_smoothed_df = max_rating_per_day.dropna(subset=['smoothed_rating'])

    # Check if there's any data to plot
    if filtered_smoothed_df.empty:
        st.error("No data available after applying smoothing.")
        return None

    # Find the minimum and maximum game dates for the smoothed rating data
    min_date_smooth = filtered_smoothed_df['game_date'].min()
    max_date_smooth = filtered_smoothed_df['game_date'].max()

    # Find the highest rating and corresponding date
    highest_rating = filtered_smoothed_df['rating'].max()
    highest_rating_date = filtered_smoothed_df.loc[filtered_smoothed_df['rating'].idxmax(), 'game_date']

    # Format the date as desired (e.g., Month-Year format)
    highest_actual_rating_date_str = highest_rating_date.strftime('%d-%B-%Y')

    # Create the area plot with Plotly Express
    fig = px.area(filtered_smoothed_df, 
                  x='game_date', 
                  y='smoothed_rating', 
                  title = f"Rating (smoothed) of {selected_playername} for {time_period}",
                  labels={'game_date': '', 'smoothed_rating': ''},
                  color_discrete_sequence=['#4E7837'],
                #   line_shape='spline',
                  width=width, 
                  height=height)

    # Dynamically set x-axis range to span from the earliest to the latest smoothed data date
    fig.update_xaxes(range=[min_date_smooth, max_date_smooth])  # Format x-axis as Month-Year
    
    # Customize x-axis ticks based on the selected time period
    if time_period == 'Last 1 Year':
        # Show months for better granularity
        fig.update_xaxes(
            tickformat="%b\n%Y",  # Month-Year format (e.g., Jan 2022)
            tickvals=pd.date_range(start=min_date_smooth, end=max_date_smooth, freq='MS').strftime('%Y-%m-%d'),
            ticktext=pd.date_range(start=min_date_smooth, end=max_date_smooth, freq='MS').strftime('%b %Y'),
        )
    elif time_period == 'Last 3 Years':
        fig.update_xaxes(
            tickvals=pd.date_range(start=min_date_smooth, end=max_date_smooth, freq='YS').strftime('%Y'),
            ticktext=pd.date_range(start=min_date_smooth, end=max_date_smooth, freq='YS').strftime('%Y'),
        )
    else:  # All Time (keep default settings)
        fig.update_xaxes(
            tickformat="%Y",  # Year format for all time
        )

    # Set y-axis range based on the smoothed rating data
    min_smoothed_rating = 2000 if selected_player in players_dict else filtered_smoothed_df['smoothed_rating'].min()
    max_smoothed_rating = filtered_smoothed_df['smoothed_rating'].max()

    # max_y_value = max(highest_rating, max_smoothed_rating)

    fig.update_yaxes(range=[min_smoothed_rating, max_smoothed_rating])

   # Add a "card-like" annotation for the highest actual rating above the curve, without arrow
    fig.add_annotation(
        x=0.8,  # Fix annotation position on the right-hand side of the plot
        xref='paper', 
        y=max_smoothed_rating-20,  # Position the label above the actual highest rating
        text=f"Highest Rating<br><b>{int(highest_rating)}</b><br>{highest_actual_rating_date_str}",  # Multiline text
        showarrow=False,  # No arrow
        font=dict(color="black", size=12),  # Adjust font size
        align="center",  # Center-align the text
        bgcolor="white",  # White background to make it card-like
        bordercolor="#f1f1f1",  # Add border to the text box for a card effect
        borderwidth=2,  # Border thickness
        borderpad=5 # Padding inside the card
    )

    fig.update_layout(margin=dict(l=0, r=0, t=50, b=0))

    return fig

def render_rating_chart_with_tabs(df: pd.DataFrame, selected_playername: str, selected_player: str, players_dict: dict, width: int = 800, height: int = 400):
    """
    Renders rating charts for a selected player across different time periods in Streamlit tabs.

    Parameters:
    - df (pd.DataFrame): DataFrame containing game data for the player.
    - selected_playername (str): The name of the selected player.
    - selected_player (str): The username of the selected player.
    - players_dict (dict): Dictionary containing player data for special handling.
    - width (int): Width of the charts.
    - height (int): Height of the charts.
    """

    tab1, tab2, tab3 = st.tabs(["Last 1 Year", "Last 3 Years", "All Time"])

    with tab1:
        fig = create_rating_chart(df, selected_playername, selected_player, players_dict, width=800, height=400, time_period='Last 1 Year')
        if fig:
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

    with tab2:
        fig = create_rating_chart(df, selected_playername, selected_player, players_dict, width=800, height=400, time_period='Last 3 Years')
        if fig:
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

    with tab3:
        fig = create_rating_chart(df, selected_playername, selected_player, players_dict, width=800, height=400, time_period='All Time')
        if fig:
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

# Calculate Avg. Opponent Rating: 
def calculate_avg_opponent_rating(filtered_df: pd.DataFrame, selected_player: str) -> float:
    """
    Calculate the average rating of opponents that the selected player has faced.

    Parameters:
    filtered_df (pd.DataFrame): The DataFrame containing game data with player ratings.
    selected_player (str): The username of the player for whom to calculate opponent ratings.

    Returns:
    float: The average opponent rating rounded to the nearest whole number.
    """
    # Melt the filtered DataFrame to combine white and black ratings into one column
    melted_df = filtered_df.melt(
        id_vars=['game_url'],  # Keep game_url or any other identifier if available
        value_vars=['white_rating', 'black_rating'],  # Columns to melt
        var_name='side',  # New column for side (white or black)
        value_name='opponent_rating'  # Column for ratings
    )
    
    # Filter out the selected player's rating, since we're calculating opponent ratings
    melted_df = melted_df[~(
        ((melted_df['side'] == 'white_rating') & (filtered_df['white_username'] == selected_player).reindex(melted_df.index, fill_value=False)) |
        ((melted_df['side'] == 'black_rating') & (filtered_df['black_username'] == selected_player).reindex(melted_df.index, fill_value=False))
    )]
    
    # Calculate the average opponent rating
    avg_opponent_rating = melted_df['opponent_rating'].mean()
    
    return round(avg_opponent_rating)

# Function to return the selected player's best win
def get_best_win(df: pd.DataFrame, selected_player: str, win_conditions: list) -> tuple[str, float] | tuple[None, None]:
    """
    Get the best win (highest-rated opponent) for the selected player based on specified win conditions.

    Parameters:
    df (pd.DataFrame): The DataFrame containing game data, including player usernames and results.
    selected_player (str): The username of the player whose best win is to be found.
    win_conditions (list): A list of conditions that define a win (e.g., ['1-0', '0-1', '1/2']).

    Returns:
    tuple[str, float] | tuple[None, None]: A tuple containing the opponent's name and rating for the best win,
                                             or (None, None) if there are no wins.
    """

    win_df = df[((df['white_username'] == selected_player) & (df['white_result'].isin(win_conditions))) |
                ((df['black_username'] == selected_player) & (df['black_result'].isin(win_conditions)))].copy()

    if win_df.empty:
        return None, None  # No wins

    # Add opponent's rating and name
    win_df['opponent_rating'] = win_df.apply(
        lambda row: row['black_rating'] if row['white_username'] == selected_player else row['white_rating'], axis=1)

    win_df['opponent_name'] = win_df.apply(
        lambda row: row['black_username'] if row['white_username'] == selected_player else row['white_username'], axis=1)

    # Get best win
    best_win = win_df.loc[win_df['opponent_rating'].idxmax()]

    return best_win['opponent_name'].capitalize(), best_win['opponent_rating']

# Extract Player Summary from Wikipedia API:
def extract_all_sections_with_summary(player_name: str) -> dict | None:
    """
    Extract sections from a Wikipedia page about a player, including the first paragraph and a summary.

    Parameters:
    player_name (str): The name of the player whose Wikipedia page is to be extracted.

    Returns:
    dict | None: A dictionary containing section titles, first paragraphs, full content, and summaries,
                  or None if the page cannot be found or leads to a disambiguation page.
    """

    try:
        # Fetch the Wikipedia page
        page = wikipedia.page(player_name)
        content = page.content

        # Dictionary to hold section titles, content, and summaries
        sections = {}
        
        # Split the content into sections
        lines = content.split('\n')
        current_section = None
        section_content = []

        for line in lines:
            # Check for section headers (usually they are underlined with '== ... ==')
            if line.startswith('==') and line.endswith('=='):
                if current_section:
                    # Create a summary by taking the first 2-3 sentences
                    full_text = '\n'.join(section_content) if section_content else 'No content available'
                    summary = '. '.join(full_text.split('. ')[:2]) + '.' if section_content else 'No content available'

                    # Save the previous section content and summary
                    sections[current_section] = {
                        'first_paragraph': section_content[0] if section_content else 'No content available',
                        'full_content': full_text,
                        'summary': summary
                    }
                # Start a new section
                current_section = line.strip('== ').strip()
                section_content = []
            else:
                # Collect content for the current section
                section_content.append(line.strip())

        # Add the last section
        if current_section:
            full_text = ''.join(section_content) if section_content else 'No content available'
            summary = '. '.join(full_text.split('. ')[:2]) + '.' if section_content else 'No content available'

            sections[current_section] = {
                'first_paragraph': section_content[0] if section_content else 'No content available',
                'full_content': full_text.strip(),
                'summary': summary.strip()
            }

        return sections
    
    except wikipedia.exceptions.PageError:
        st.error(f"Page for '{player_name}' not found. Please check the name and try again.")
        return None
    except wikipedia.exceptions.DisambiguationError as e:
        st.error(f"'{player_name}' leads to a disambiguation page. Please be more specific. Options include: {', '.join(e.options[:5])}...")
        return None

# Format paragraphs with bullet points:
def format_with_bullets(content: str) -> str:
    """
    Format the provided content into bullet points, grouping lines by year.

    Parameters:
    content (str): The content to format, where lines may start with a year.

    Returns:
    str: The formatted content as a Markdown string with bullet points.
    """
    # Split content into lines
    lines = content.split('\n')

    # Regular expression to detect lines starting with a year (e.g., "2016:", "2017:")
    year_pattern = re.compile(r'^\d{4}:')
    
    # List to store formatted content
    formatted_content = []
    current_year_line = None
    
    for line in lines:
        line = line.strip()

        # Takes care of extra-bullet point in fulltext:
        if not line:
            continue

        if year_pattern.match(line):
            # If a line starts with a year, save it as the current year line
            if current_year_line:
                # If there's an existing year line, append it to the formatted content
                formatted_content.append(f"* {current_year_line.strip()}")
            current_year_line = line
        else:
            # If the line doesn't start with a year, append it to the current year line
            if current_year_line:
                current_year_line += f" {line}"
            else:
                formatted_content.append(f"* {line}")  # For lines without a year, add them normally

    # Append the last year line if it exists
    if current_year_line:
        formatted_content.append(f"* {current_year_line}")

    # Join the formatted content into paragraphs and return as Markdown
    return '\n\n'.join(formatted_content)

# Function to get country code from country URL
def get_country_code(country_url: str) -> str:
    """
    Extract the country code from a given URL.

    Parameters:
    country_url (str): The URL containing the country code.

    Returns:
    str: The extracted country code.
    """
    return country_url.split('/')[-1]

# Function to encode the local image file to base64
def get_base64_image(image_path: str) -> str:
    """
    Convert an image file to a base64 encoded string.

    Parameters:
    image_path (str): The path to the image file to encode.

    Returns:
    str: The base64 encoded string representation of the image.
    """
    with open(image_path, "rb") as file:
        encoded = base64.b64encode(file.read()).decode()
    return encoded

#Function to render SVG for flowdiagram:
def render_svg(svg: str, width: int = None, height: int = None) -> None:
    """Renders the given SVG string in Streamlit with optional width and height.

    Args:
        svg (str): A string containing the SVG content.
        width (int, optional): The desired width of the image in pixels.
        height (int, optional): The desired height of the image in pixels.
    """
    b64 = base64.b64encode(svg.encode('utf-8')).decode('utf-8')
    
    # Create the HTML for the image, with optional width and height
    img_style = ""
    if width:
        img_style += f'width="{width}px" '
    if height:
        img_style += f'height="{height}px" '
    
    html = f'<img src="data:image/svg+xml;base64,{b64}" alt="svg" {img_style}/>'
    st.markdown(html, unsafe_allow_html=True)

# Example: Load your images as base64 if needed
def load_image(image_path: str) -> str:
    """
    Load an image from the specified path and encode it in base64.

    Parameters:
    image_path (str): The file path to the image.

    Returns:
    str: The base64 encoded string representation of the image.
    """

    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

# Get Rapid rating:
def get_game_class_rating(df: pd.DataFrame, player: str, game_class: str) -> float:
    """
    Retrieve the highest rating of a player in a specified game time class.

    Parameters:
    df (pd.DataFrame): The DataFrame containing game data with player ratings.
    player (str): The username of the player whose rating is to be retrieved.
    game_class (str): The game time class to filter by ('rapid', 'blitz', or 'bullet').

    Returns:
    float: The highest rating for the specified game time class, or None if no ratings are available.
    
    Raises:
    ValueError: If an invalid game time class is provided.
    """

    if game_class not in ['rapid', 'blitz', 'bullet']:
        raise ValueError(f"Invalid game time class: {game_class}. Choose from 'rapid', 'blitz', or 'bullet'.")
    
    # Filter the DataFrame by the specified game time class
    class_df = df[((df['white_username'] == player) | (df['black_username'] == player)) & (df['game_time_class'] == game_class)]
    
    # Check if there are ratings for the given game time class
    if not class_df.empty:
        # Return the highest rating for the specified game time class
        max_white_rating = class_df['white_rating'].max()
        max_black_rating = class_df['black_rating'].max()
        
        # Return the highest rating between the two
        return max(max_white_rating, max_black_rating)
    else:
        return None 
    
#-------------------------------------------------------------- DataBase Functions : --------------------------------------------------------------#

# Initialize the connection using pyodbc
def init_connection():
    connection_string = (
        "Driver={ODBC Driver 17 for SQL Server};"
        "Server=DESKTOP-M7PK0Q6;"  # Update with your actual server name
        "Database=chess_players;"   # Update with your database name
        "Trusted_Connection=yes;"
    )
    conn = pyodbc.connect(connection_string)
    return conn

def get_player_stats_live(player_name: str, conn) -> pd.DataFrame:
    """
    Retrieves chess player stats from the database if available; otherwise, 
    fetches live data from Chess.com and stores it in the database.

    Args:
        player_name (str): The username of the chess player on Chess.com.
        conn: The pyodbc database connection object.

    Returns:
        pd.DataFrame: A DataFrame containing details for each game including URLs, dates, 
                      time controls, ratings, results, and accuracies.
    """
    # Step 1: Check if player data already exists in the database
    query = "SELECT * FROM player_game_data WHERE player_name = ?"
    
    try:
        existing_data = pd.read_sql(query, conn, params=(player_name,))
        
        if not existing_data.empty:
            # Player data exists in the database, return the existing data
            print(f"Data found for {player_name} in the database.")
            return existing_data
    except Exception as e:
        st.write(f"Error fetching data from the database: {e}")

    # Step 2: Player data not in the database, proceed with live data extraction
    print(f"No data found for {player_name} in the database. Fetching from Chess.com...")
    start_time = time.time()  # Record the start time

    archives = get_archives(player_name)  # Fetch game archives

    all_games = []

    for archive_url in archives:
        games = get_games_from_archive(archive_url)
        if isinstance(games, list):  # Ensure games is a list
            all_games.extend(games)

    # Extracting the relevant attributes for each game
    formatted_games = []

    for game in all_games:
        if isinstance(game, dict):  # Ensure each game is a dictionary
            game_data = {
                "player_name": player_name,
                "game_url": game.get("url"),
                "game_date": get_date(game.get("pgn")),
                "game_time_control": game.get("time_control"),
                "game_time_class": game.get("time_class"),
                "game_variant": game.get("rules"),
                "opening": get_openings_2(game),
                "white_rating": game.get("white", {}).get("rating"),
                "white_result": game.get("white", {}).get("result"),
                "white_username": game.get("white", {}).get("username"),
                "white_accuracy": game.get("accuracies", {}).get("white",0.0), # Make sure to fill with 0.0 to adjust datatype with database.
                "black_rating": game.get("black", {}).get("rating"),
                "black_result": game.get("black", {}).get("result"),
                "black_username": game.get("black", {}).get("username"),
                "black_accuracy": game.get("accuracies", {}).get("black",0.0) # Make sure to fill with 0.0 to adjust datatype with database. 
            }
            formatted_games.append(game_data)

    # Convert the extracted data to a DataFrame
    df = pd.DataFrame(formatted_games)

    # Step 3: Save the new data to the database
    try:
        cursor = conn.cursor()
        for index, row in df.iterrows():

            # Insert each row into the player_game_data table
            insert_query = """
                INSERT INTO player_game_data (
                    player_name, game_url, game_date, game_time_control, game_time_class, game_variant, 
                    opening, white_rating, white_result, white_username, white_accuracy, 
                    black_rating, black_result, black_username, black_accuracy, last_updated
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            cursor.execute(insert_query, (
                row['player_name'], row['game_url'], row['game_date'], row['game_time_control'], 
                row['game_time_class'], row['game_variant'], row['opening'], 
                row['white_rating'], row['white_result'], row['white_username'], row['white_accuracy'],
                row['black_rating'], row['black_result'], row['black_username'], row['black_accuracy'],
                datetime.now().date()
            ))
        conn.commit()
        print(f"{player_name}'s Data saved to the database.")
    except Exception as e:
        print(f"Error saving data to the database: {e}")

    # Calculate and print execution time
    end_time = time.time()  # Record the end time
    execution_time = end_time - start_time
    print(f'Time Taken: {execution_time} sec.')

    return df

def update_player_stats_live(player_name: str, conn) -> pd.DataFrame:
    """
    Updates chess player stats in the database.

    Args:
        player_name (str): The username of the chess player on Chess.com.
        conn: The pyodbc database connection object.

    Returns:
        pd.DataFrame: A DataFrame containing details for each game including URLs, dates, 
                      time controls, ratings, results, and accuracies.
    """

    # Step 1: Player data not in the database, proceed with live data extraction
    st.write("Updating player data. Please wait...")
    start_time = time.time()  # Record the start time

    archives = get_archives(player_name)  # Fetch game archives

    all_games = []

    for archive_url in archives:
        games = get_games_from_archive(archive_url)
        if isinstance(games, list):  # Ensure games is a list
            all_games.extend(games)

    # Extracting the relevant attributes for each game
    formatted_games = []

    for game in all_games:
        if isinstance(game, dict):  # Ensure each game is a dictionary
            game_data = {
                "player_name": player_name,
                "game_url": game.get("url"),
                "game_date": get_date(game.get("pgn")),
                "game_time_control": game.get("time_control"),
                "game_time_class": game.get("time_class"),
                "game_variant": game.get("rules"),
                "opening": get_openings_2(game),
                "white_rating": game.get("white", {}).get("rating"),
                "white_result": game.get("white", {}).get("result"),
                "white_username": game.get("white", {}).get("username"),
                "white_accuracy": game.get("accuracies", {}).get("white",0.0), # Make sure to fill with 0.0 to adjust datatype with database.
                "black_rating": game.get("black", {}).get("rating"),
                "black_result": game.get("black", {}).get("result"),
                "black_username": game.get("black", {}).get("username"),
                "black_accuracy": game.get("accuracies", {}).get("black",0.0) # Make sure to fill with 0.0 to adjust datatype with database. 
            }
            formatted_games.append(game_data)

    # Convert the extracted data to a DataFrame
    df = pd.DataFrame(formatted_games)

    # Step 3: Save the new data to the database
    try:
        cursor = conn.cursor()
        for index, row in df.iterrows():

            # Insert each row into the player_game_data table
            insert_query = """
                INSERT INTO player_game_data (
                    player_name, game_url, game_date, game_time_control, game_time_class, game_variant, 
                    opening, white_rating, white_result, white_username, white_accuracy, 
                    black_rating, black_result, black_username, black_accuracy, last_updated
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) 
            """
            cursor.execute(insert_query, (
                row['player_name'], row['game_url'], row['game_date'], row['game_time_control'], 
                row['game_time_class'], row['game_variant'], row['opening'], 
                row['white_rating'], row['white_result'], row['white_username'], row['white_accuracy'],
                row['black_rating'], row['black_result'], row['black_username'], row['black_accuracy'],
                datetime.now().date()
            ))
        conn.commit()
        print(f"{player_name}'s Data saved to the database.")
    except Exception as e:
        print(f"Error saving data to the database: {e}")

    # Calculate and print execution time
    end_time = time.time()  # Record the end time
    execution_time = end_time - start_time
    print(f'Time Taken: {execution_time} sec.')

    return df

# Fetch all players from the database
def get_all_players():
    conn = init_connection()
    cursor = conn.cursor()
    
    # Query to get distinct player names
    cursor.execute("SELECT DISTINCT player_name FROM player_game_data")
    players = cursor.fetchall()
    
    player_list = [player[0] for player in players]
    cursor.close()
    conn.close()
    
    return player_list

def delete_all_player_data():
    conn = init_connection()
    cursor = conn.cursor()

    # SQL query to delete all player data
    delete_query = "DELETE FROM player_game_data"
    
    try:
        # Execute the query
        st.success(f"player data deleted successfully for {get_all_players()}.")
        cursor.execute(delete_query)
        conn.commit()
    except Exception as e:
        st.error(f"Error: {e}")
    finally:
        cursor.close()
        conn.close()

# Function to delete all data and extract new data for each player
def refresh_all_player_data():
    
    # Step 1: Get all players from the database
    players = get_all_players()

    # Step 2: Delete all player data
    delete_all_player_data()
    
    # Step 3: Extract data for each player from the API and save it to the DB
    for player in players:
        try:
            # Extract player data from API and save it to DB
            update_player_stats_live(player, init_connection())
            st.success(f"Data for {player} updated successfully.")
        except Exception as e:
            st.error(f"Failed to update data for {player}: {e}")

def fetch_data_from_sql(player_name: str, player_name_column: str = "player_name") -> pd.DataFrame:
    """
    Fetches player game data from an SQL database based on the provided player name.
    
    Args:
        player_name (str): The name of the player whose data is being fetched.
        connection_string (str): The connection string for the SQL database.
        player_name_column (str): The column name in the database that stores player names (default is "player_name").
    
    Returns:
        pd.DataFrame: A pandas DataFrame containing the player's game data. If an error occurs, returns an empty DataFrame.
    """
    # Connect to the database using pyodbc
    conn = init_connection()
    
    try:
        # Define the query with parameter placeholders
        query = f"SELECT * FROM player_game_data WHERE {player_name_column} = ?"
        
        # Fetch the data using read_sql with pyodbc cursor
        df = pd.read_sql(query, conn, params=[player_name])
        
    except Exception as e:
        print(f"Error fetching data: {e}")
        df = pd.DataFrame()  # Return an empty DataFrame in case of error
    
    finally:
        conn.close()  # Ensure the connection is closed after execution
    
    return df

