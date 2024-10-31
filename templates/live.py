import pandas as pd
import streamlit as st
import time

from utils.functions import *


def show_live_players():

    # Path to your local image
    image_path = "assets/pawn_moving.png"  
    # Get the base64 encoded image
    image_base64 = get_base64_image(image_path)

    # Load and inject the CSS
    css = load_css("static/styles.css", image_base64)
    st.markdown(css, unsafe_allow_html=True)

    players_dict = {
        'Gukesh D.':'GukeshDommaraju',
        'Nodirbek Abdusattarov':'ChessWarrior7197',
        'Pragnananddha R':'rpragchess',
        'Vincent Keymer':'VincentKeymer',
        'Javokhir Sindarov':'Javokhir_Sindarov05'
    }

    win_conditions =  ['win']
    lose_conditions = ['resigned', 'checkmated', 'timeout', 'abandoned']
    draw_conditions = ['agreed', 'stalemate', '50move','repetition','timevsinsufficient','insufficient']

    selected_player = st.text_input(label='Enter Chess.com Username: ') # Make Sure playername is not in lowercase !!!! Very Very Important
    st.session_state.selected_player = selected_player
    selected_player.strip().lower()

    # Initialize session state for the button press if it doesn't exist
    if 'button_pressed' not in st.session_state:
        st.session_state.button_pressed = False

    # Button to trigger player info extraction
    if st.button('Extract Player Info'):
        st.session_state.button_pressed = True  # Store button press in session state

    # Run the data extraction and display logic only if the button was pressed
    if st.session_state.button_pressed:

        # Initialize progress bar and status text outside the if-else block
        progress_bar = st.progress(0)
        status_text = st.empty()

        # Run the data extraction and display logic only if the button was pressed
        if st.session_state.button_pressed:

            # Slow loading animation for live data extraction
            status_text.text("Loading player data... 0%")

            # Simulate loading from 0% to 40%
            for i in range(0, 41):  
                time.sleep(0.05)
                progress_bar.progress(i / 100)
                status_text.text(f"Loading player data... {i}%")
                
            # Load live data (e.g., call your live extraction function)
            df = get_player_stats(selected_player)

            # Increment progress to 70%
            for i in range(41, 71):  
                time.sleep(0.3)
                progress_bar.progress(i / 100)
                status_text.text(f"Loading player data... {i}%")

            # Finish progress from 70% to 100%
            for i in range(71, 101):  
                time.sleep(0.05)
                progress_bar.progress(i / 100)
                status_text.text(f"Loading player data... {i}%")

            # Once loading is complete, display the data
            status_text.text("Loading complete!")

            # Remove the progress bar and status text
            progress_bar.empty()
            status_text.empty()


        # if selected_player in get_all_players():

        #     for i in range(0, 101):  # Fast increment from 0% to 100%
        #         time.sleep(0.01)  # Fast loading for cached data
        #         progress_bar.progress(i / 100)
        #         status_text.text(f"Loading player data... {i}%")
            
        #     # Fetch data from database
        #     df = fetch_data_from_sql(selected_player)

        # else:

        #     # Initialize progress bar and percentage
        #     progress_bar = st.progress(0)  # Start progress at 40%
        #     status_text = st.empty()
        #     status_text.text("Loading player data... 0%")

        #     # Simulate some fake loading from 0% to 40%
        #     for i in range(0, 41):  # Simulate loading from 0% to 40%
        #         time.sleep(0.05)  # Simulate loading
        #         progress_bar.progress(i / 100)
        #         status_text.text(f"Loading player data... {i}%")
                

        #     # Simulate progress increase before function runs
        #     for i in range(41, 71):  # Increment from 40% to 70%
        #         time.sleep(0.5)  # Simulate loading
        #         progress_bar.progress(i / 100)
        #         status_text.text(f"Loading player data... {i}%")

        #     # Load player data (this is where get_player_stats() is called)
        #     df = get_player_stats_live(selected_player, init_connection())

        #     # Finish progress
        #     for i in range(71, 101):  # Finish the progress from 70% to 100%
        #         time.sleep(0.05)  # Simulate loading
        #         progress_bar.progress(i / 100)
        #         status_text.text(f"Loading player data... {i}%")

        #     # Once loading is complete, display the data
        #     status_text.text("Loading complete!")
        #     # st.dataframe(df)

        #     # Remove the progress bar and status text
        #     progress_bar.empty()
        #     status_text.empty()

        # Reset button state
        st.session_state.button_pressed = False

        temp_df = df[((df['white_username'] == st.session_state.selected_player) | (df['black_username'] == st.session_state.selected_player))]

        # Debugging: Check filtering logic and resulting DataFrame
        
        if temp_df.empty:
            st.write('No data found for the selected player and game time class.')

        # Proceed with win/loss/draw filtering if temp_df is not empty
        if not temp_df.empty:
            win_df = temp_df[((temp_df['white_username'] == selected_player) & (temp_df['white_result'].isin(win_conditions))) |
                            ((temp_df['black_username'] == selected_player) & (temp_df['black_result'].isin(win_conditions)))]

            draw_df = temp_df[((temp_df['white_username'] == selected_player) & (temp_df['white_result'].isin(draw_conditions))) |
                            ((temp_df['black_username'] == selected_player) & (temp_df['black_result'].isin(draw_conditions)))]

            loss_df = temp_df[((temp_df['white_username'] == selected_player) & (temp_df['white_result'].isin(lose_conditions))) |
                            ((temp_df['black_username'] == selected_player) & (temp_df['black_result'].isin(lose_conditions)))]

            # Display player stats (only if temp_df is not empty)
        (total_games, white_accuracy, black_accuracy,
        wins_as_white, loss_as_white, draws_as_white, total_games_white, white_win_ratio, white_loss_ratio, white_draw_ratio,
        wins_as_black, loss_as_black, draws_as_black, total_games_black, black_win_ratio, black_loss_ratio, black_draw_ratio,
        opening_lines,white_most_played_openings, white_most_accurate_openings, black_most_played_openings, black_most_accurate_openings) = display_player_stats(temp_df, selected_player)

        with st.container():
            avatar_url_main = get_player_info(selected_player)['Avatar'][0]
            title = get_player_info(selected_player)['Title'][0] #if selected_player in players_dict.values() else ''
            name = get_player_info(selected_player)['Name'][0]
            username = get_player_info(selected_player)['Username'][0]
            country_code = get_player_info(selected_player)['Country'][0].split('country/')[1]
            location = get_player_info(selected_player)['Location'][0]
            last_online = pd.to_datetime(get_player_info(selected_player)['Last Online'][0], unit='s').strftime('%b %d, %Y')
            joined = pd.to_datetime(get_player_info(selected_player)['Joined'][0],  unit='s').strftime('%b %d, %Y')
            followers = get_player_info(selected_player)['Followers'][0]
            is_streamer = get_player_info(selected_player)['Verified'][0]
            is_diomand = '💎' if selected_player in players_dict.values() else ''

            # bg_color = '#9c4418' if selected_player in players_dict.values() else '#2b2b4b'

            # Bootstrap CSS and Icons CDN
            st.markdown("""
                <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css">
                <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons/font/bootstrap-icons.css" rel="stylesheet">
            """, unsafe_allow_html=True)

        # Player-Info CSS Styles:
        st.write(
        f"""
        <div class="profile-container">
            <div style="display: flex; justify-content: left;">
                <img src="{avatar_url_main}" style="border-radius: 10%; border: 2px solid #69923e; width: 150px;">
            </div>
            <div class="player-info">
                <div class="name-section">
                    <div class="title">{title}</div>
                    <div class="player-name">{username}</div>
                    <div class="country-flag">
                        <img src="https://flagcdn.com/40x30/{country_code.lower()}.png" alt="Country Flag">
                    </div>
                    <div class="badge">{is_diomand}</div>
                </div>
                <div class="full-name-location">
                    {name} &bull; 📌{location}
                </div>
                <div class="additional-info">
                    <div class="info-box">
                        <span class="bi bi-activity" style = "font-size: 1rem; font-weight: bold; margin-right: 10px;"></span> Online on:<br> {last_online}
                    </div>
                    <div class="info-box">
                        <span class="bi bi-calendar" style = "font-size: 1rem; font-weight: bold; margin-right: 10px;"></span> Joined on:<br> {joined}
                    </div>
                    <div class="info-box">
                        <span class="bi bi-people-fill" style = "font-size: 1rem; font-weight: bold; margin-right: 10px;"></span> Followers:<br> {followers}
                    </div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
        )

        st.write('') ## Margin setting :)
        st.write('')
        st.write('')
        
        st.markdown(f"""
            <div class="metrics-row">
                <div class="metric-container">
                    <div class="metric-label">Total Games <br> </div>
                    <div class="metric-value">{total_games}</div>
                </div>
                <div class="metric-container">
                    <div class="metric-label">Avg Accuracy as White <br> </div>
                    <div class="metric-value"> {white_accuracy:.2f}%</div>
                </div>
                <div class="metric-container">
                    <div class="metric-label">Avg Accuracy as Black <br> </div>
                    <div class="metric-value">{black_accuracy:.2f}%</div>
                </div>
            </div>
        """, unsafe_allow_html=True)
                    

        avg_rating = calculate_avg_opponent_rating(temp_df, st.session_state.selected_player)
        best_opponent_name, best_opponent_rating = get_best_win(df, st.session_state.selected_player, win_conditions)

        avg_rating_win = calculate_avg_opponent_rating(win_df, st.session_state.selected_player)
        avg_rating_draw = calculate_avg_opponent_rating(draw_df, st.session_state.selected_player)
        avg_rating_loss = calculate_avg_opponent_rating(loss_df, st.session_state.selected_player)

        win_png = load_image("assets/win3.png")  
        draw_png = load_image("assets/draw2.png")  
        loss_png = load_image("assets/loss2.png") 

        st.markdown(f"""
            <div class="metrics-row">
                <div class="metric-container">
                    <div class="metric-label">Avg Opponent Rating</div>
                    <div class="metric-value">{round(avg_rating)}</div>
                </div>
                <div class="metric-container">
                    <div class="metric-label">Best Win</div>
                    <div class="metric-value">{best_opponent_rating}</div>
                    <div class="metric-delta">{best_opponent_name}</div>
                </div>
                <div class="metric-container">
                    <div class="metric-label-spec">Avg Opponent Rating <br> when player...</div>
                    <div class="metric-value-spec">
                        <span class="value-win">
                            <img src="data:image/png;base64,{win_png}" width="18" height="18"/> {round(avg_rating_win)}
                        </span>
                        <span class="value-draw">
                            <img src="data:image/png;base64,{draw_png}" width="18" height="18"/> {round(avg_rating_draw)}
                        </span>
                        <span class="value-loss">
                            <img src="data:image/png;base64,{loss_png}" width="18" height="18"/> {round(avg_rating_loss)}
                        </span>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)

        #     # https://discuss.streamlit.io/t/display-svg/172/5 --> code reference.
            
        rapid_img = load_image('assets/stopwatch.png')
        blitz_img = load_image('assets/flash.png')
        bullet_img = load_image("assets/bullet3.png")

        rapid_rating = get_game_class_rating(df, selected_player, 'rapid')
        blitz_rating = get_game_class_rating(df, selected_player, 'blitz')
        bullet_rating = get_game_class_rating(df, selected_player, 'bullet')

        st.markdown(f"""
            <div class="metrics-row">
                <div class="metric-container">
                    <i class = "bi bi-stopwatch-fill" style="font-size:1rem; color:#69923E;"></i>
                    <div class="metric-label">Best Rapid Rating <br> </div>
                    <div class="metric-value">{get_game_class_rating(df, selected_player, 'rapid')}</div>
                </div>
                <div class="metric-container">
                    <i class = "bi bi-lightning-fill" style="font-size:1rem; color:yellow;"></i>
                    <div class="metric-label">Best Blitz Rating <br> </div>
                    <div class="metric-value">{get_game_class_rating(df, selected_player, 'blitz')}</div>
                </div>
                <div class="metric-container">
                    <div class="metric-icon" style="margin-right: 10px;">
                        <img src="data:image/png;base64,{bullet_img}" style="width: 16px; height: 16px; margin-left: 10px;">
                    </div>
                    <div class="metric-label">Best Bullet Rating <br> </div>
                    <div class="metric-value">{get_game_class_rating(df, selected_player, 'bullet')}</div>
                </div>
            </div>
        """, unsafe_allow_html=True)

        if st.session_state.get('screen_width', 1200) >= 768:
            # Desktop or large screen - 3 columns
            col1, col2, col3 = st.columns(3, gap='large')
        else:
            # Phone - 1 column
            col1, col2, col3 = st.container(), st.container(), st.container()

        with col1:
            st.plotly_chart(player_win_chart(df, selected_player, 400, 300), config={'displayModeBar': False}, use_container_width=True)    
            image_path = 'assets/Pie Chart Legend (1).png'
            st.write('')
            st.image(image = image_path, use_column_width=True)    

        with col2:
            st.plotly_chart(player_draw_chart(df, selected_player, 400, 300),  config={'displayModeBar': False}, use_container_width=True)
            image_path = 'assets/New Draw Pie Chart Legend (1).png'
            st.write('')
            st.image(image = image_path, use_column_width=True)

        with col3:
            st.plotly_chart(player_loss_chart(df, selected_player, 400 , 300),  config={'displayModeBar': False}, use_container_width=True)
            image_path = 'assets/Lose Pie Chart Legend.png'
            st.write('')
            st.image(image = image_path, use_column_width=True)  

        if 'tab_selected' not in st.session_state:
            st.session_state.tab_selected = 'white'
            
        tab_white, tab_black = st.tabs(["⬜ White", "⬛ Black"])

        # Tab for White Stats
        with tab_white:
            st.session_state.tab_selected = 'white'

            #Show Player as White Stats:
            show_white_stats(total_games_white, white_win_ratio, white_draw_ratio, white_loss_ratio, wins_as_white, draws_as_white, loss_as_white,
                            white_most_accurate_openings, white_most_played_openings)


        with tab_black:
            st.session_state.tab_selected = 'black'

            #Show Player as Black Stats:
            show_black_stats(total_games_black, black_win_ratio, black_draw_ratio, black_loss_ratio, wins_as_black, draws_as_black, loss_as_black, 
                            black_most_accurate_openings, black_most_played_openings)

        render_rating_chart_with_tabs(df, selected_playername=selected_player, selected_player=selected_player, players_dict=players_dict, width=1180, height=400)
        st.caption("Note: The rating curve shown is smoothed using a rolling average to provide a clearer trend. The highest rating annotation reflects the actual unsmoothed rating.")
