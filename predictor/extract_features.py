#!/usr/bin/env python

# Series of functions for doing final data cleaning, and puts everything into a feature vector for 
# later learning

import numpy as np
import pandas as pd
import MySQLdb as mdb

def make_success_vector(rating, votes, min_rating, min_votes):
    '''
    This is the current method of defining game "success"
    A game must have a rating>9 and votes>100, or
    have a rating > 0 AND a metacritic_rating > 75

    This should be changed in the future, e.g., if revenue info is available
    '''

    success_vector = np.zeros(len(rating))
    success_slice = np.where( (rating >= min_rating) & (votes > min_votes) )[0] 
    success_vector[success_slice] = 0*success_slice+1

    return success_vector

def process_single_game(game,prior_game=False):
    '''
    The input should be a single row in the format of the MySQL database
    The Id, title, creator, engine and release_day columns are currently stripped
    Release_month is converted to an integer, 1-12
    game_type and theme are expanded into a series of yes-no (1 or 0) columns
    Unless told otherwise, it is assumed that this is the creator's first game
    '''

    #List of columns, based on MySQLdb stuffs
    mycolumns = ['Id', 'title', 'creator', 'engine', 'rating', 'votes', 'release_day', 
                 'release_year', 'release_month', 'game_type', 'theme', 'single_player', 
                 'multiplayer', 'coop', 'mmo', 'Android', 'AndroidConsole', 'AndroidTab',
                 'DC', 'DOS', 'DS', 'Flash', 'GBA', 'GCN', 'Linux', 'Mac', 'Metro', 'MetroTab',
                 'Mobile', 'PS2', 'PS3', 'PS4', 'PSP', 'SNES', 'VITA', 'Web', 'Wii', 'WiiU', 
                 'Windows', 'X360', 'XBONE', 'XBOX', 'iPad', 'iPhone']

    game_type_list = np.array(['Arcade', 'Platformer', 'Adventure', 'First Person Shooter', 'Role Playing',
                               'Family', 'Puzzle Compilation', 'Real Time Strategy', 'Turn Based Strategy',
                               'Point and Click', 'Third Person Shooter', 'Racing', 'Educational', 'Realistic Sim',
                               'Tower Defense', 'Roguelike', 'Cinematic', 'Fighting', 'Visual Novel', 'Hack n Slash',
                               'Tactical Shooter', 'Party', 'Rhythm', 'Alternative Sport', 'Futuristic Sim', 'Stealth',
                               'Turn Based Tactics', 'Virtual Life', 'Grand Strategy', 'Car Combat', 'Combat Sim',
                               'Real Time Shooter', 'Real Time Tactics', '4X', 'Soccer', 'Basketball', 'Golf',
                               'Football', 'Wrestling', 'Hockey', 'Baseball'])

    sports_list = ['Soccer', 'Basketball', 'Golf',
                   'Football', 'Wrestling', 'Hockey', 'Baseball']

    theme_list = np.array(['Sci-Fi', 'Fantasy', 'Abstract', 'Comic', 'Horror', 'Comedy', 'Realism', 'War',
                           'Nature', 'Anime', 'Medieval', 'Education', 'Sport', 'Fighter', 'History',
                           'Noire', 'Antiquity', 'Western', 'Movie', 'Mafia'])

    month_dict = {'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6, 'Jul': 7, 'Aug': 8,
                  'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12}

    #Set the game vector
    game_vector = np.zeros( 2+len(game_type_list) - len(sports_list)+1 + len(theme_list) + len(mycolumns[11:]) +1)
    #Release year
    count = 0
    game_vector[0] = int(game[7])
    count += 1
    #Release month
    try:
        game_vector[count] = month_dict[game[8]]
    except KeyError:
        print "Issue: month label is ",game[8]
    count += 1
    #Game type values
    game_type_place = np.where(game[9] == game_type_list)[0]
    if game[9] in sports_list:
        game_vector[36] = 1
    else:
        game_vector[count+game_type_place] = 1
    count += len(game_type_list) - len(sports_list)+1
    #Game theme value
    theme_place = np.where(game[10] == theme_list)[0]
    game_vector[count+theme_place] = 1
    count += len(theme_list)
    #Remaining values -- play mode(s) and platform(s)
    game_vector[count:count+len(game[11:])] = np.array(game[11:]).astype(int)
    count += len(game[11:])
    #And, if there's a prior game, indicate such
    if prior_game:
        game_vector[count] = 1

    return game_vector

def process_single_game_summary(game_summary, vocab_list):
    '''
    Converts the text summary of a game into a feature vector
    Gives 1 if a word is present, zero otherwise
    Not implemented in the first run
    '''
    return

def has_made_prior_game(game_id,games_df):
    '''
    Uses information in a pandas dataframe to determine whether or not a game with a given ID is the first made
    by its listed creator; returns bool
    '''

    creator = games_df[games_df['Id'].astype(int) == game_id]['creator']
    #Collect games made by given creator
    c_games_df = games_df[games_df['creator'] == creator[creator.index[0]]]
    if len(c_games_df) <= 1:
        #Only one (or no) game(s), and therefore, false
        return False
    years = c_games_df['release_year']
    my_year = c_games_df[c_games_df['Id'].astype(int) == game_id]['release_year']
    if int(my_year[my_year.index[0]]) > int(years.min()):
        #If the desired game has a later year, there is a prior game -- so, fire away
        return True

    return False

def process_games_from_db(cur):
    '''
    Returns the matrix of game vectors drawn from the MySQL database
    It also computes the success vector
    '''
    #First, collect the data from the database
    mycolumns = ['Id', 'title', 'creator', 'engine', 'rating', 'votes', 'release_day',
                 'release_year', 'release_month', 'game_type', 'theme', 'single_player',
                 'multiplayer', 'coop', 'mmo', 'Android', 'AndroidConsole', 'AndroidTab',
                 'DC', 'DOS', 'DS', 'Flash', 'GBA', 'GCN', 'Linux', 'Mac', 'Metro', 'MetroTab',
                 'Mobile', 'PS2', 'PS3', 'PS4', 'PSP', 'SNES', 'VITA', 'Web', 'Wii', 'WiiU', 'Windows', 'X360', 'XBONE', 'XBOX', 'iPad', 'iPhone']
    select_command = "SELECT Id"
    for column_name in mycolumns[1:]:
        select_command += ", "+column_name
    select_command += " FROM Games"
    cur.execute(select_command)
    games_rows = cur.fetchall()

    
    #Set up the pandas dataframe
    games_df = pd.DataFrame(np.array(games_rows), columns = mycolumns)

    #Now, create the feature matrix
    game_matrix = []
    for game in games_rows:
        game_matrix.append( process_single_game( game, prior_game=has_made_prior_game(int(game[0]),games_df)) )

    game_matrix = np.array(game_matrix)

    return game_matrix, games_df

def make_full_success_vector(games_df,min_rating,min_votes):
    #Finish off by making the success vector
    ngames = len(games_df)
    rating = games_df['rating'].get_values().astype(float)
    votes = games_df['votes'].get_values().astype(int)
    success_vector = make_success_vector(rating, votes, min_rating, min_votes)

    return success_vector

def evaluate_test(function_result, expected_result):
    '''
    Simple test evaluation function
    '''

    if function_result == expected_result:
        print "Passed"
    else:
        print "Failed: ", function_result, expected_result
    return

def evaluate_test_array(function_result, expected_result):
    '''
    Simple test evaluation function
    '''

    if len(function_result) != len(expected_result):
        print "Failed: Arrays of differing length"
        return
    fail_match = np.where(function_result != expected_result)[0]
    if len(fail_match) == 0:
        print "Passed"
    else:
        print "Failed at: ", fail_match, function_result[fail_match], expected_result[fail_match]
    return

def run_tests():
    '''
    Run a series of unit tests
    '''

    #Testing the process_single_game function
    print "Testing process_single_game..."
    game1 = (1L, 'Coming Out Simulator 2014', 'Nicky Case', 'Custom Built', -1.0, 0L, 30L, 2014L, 'Jun', 'Visual Novel', 'Realism', 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0)
    game2 = (62L, 'I Shall Remain', 'Scorpius Games', 'Custom Built', 8.2, 157L, 12L, 2015L, 'Jan', 'Role Playing', 'Horror', 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0)
    game3 = (9441L, 'Dwarf Fortress', 'Bay 12 Games', 'Custom Built', 9.4, 709L, 5L, 2006L, 'Aug', 'Real Time Strategy', 'Antiquity', 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0)
    game4 = (4638L, 'Shadowrun: Dragonfall', 'Harebrained Schemes', 'Unity', 9.5, 4L, 27L, 2014L, 'Feb', 'Role Playing', 'Sci-Fi', 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0)

    game_vec1 = np.zeros(91)
    game_vec1[0] = 2014
    game_vec1[1] = 6
    game_vec1[20] = 1 #36 is highest point for game type
    game_vec1[43] = 1 #
    game_vec1[57:] = [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0]
    evaluate_test_array(process_single_game(game1),game_vec1)
    game_vec2 = np.zeros(91)
    game_vec2[0] = 2015
    game_vec2[1] = 1
    game_vec2[6] = 1 #36 is highest point for game type
    game_vec2[41] = 1 #
    game_vec2[57:] = [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0,0]
    evaluate_test_array(process_single_game(game2),game_vec2)
    game_vec4 = np.zeros(91)
    game_vec4[0] = 2014
    game_vec4[1] = 2
    game_vec4[6] = 1 #36 is highest point for game type
    game_vec4[37] = 1 #sci-fi
    game_vec4[57:] = [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1]
    evaluate_test_array(process_single_game(game4,prior_game=True),game_vec4)

    feature_list = ['release_year', 'release_month', 'Arcade', 'Platformer', 'Adventure', 'First Person Shooter', 'Role Playing',
                    'Family', 'Puzzle Compilation', 'Real Time Strategy', 'Turn Based Strategy',
                    'Point and Click', 'Third Person Shooter', 'Racing', 'Educational', 'Realistic Sim',
                    'Tower Defense', 'Roguelike', 'Cinematic', 'Fighting', 'Visual Novel', 'Hack n Slash',
                    'Tactical Shooter', 'Party', 'Rhythm', 'Alternative Sport', 'Futuristic Sim', 'Stealth',
                    'Turn Based Tactics', 'Virtual Life', 'Grand Strategy', 'Car Combat', 'Combat Sim',
                    'Real Time Shooter', 'Real Time Tactics', '4X', 'Sports_type',
                    'Sci-Fi', 'Fantasy', 'Abstract', 'Comic', 'Horror', 'Comedy', 'Realism', 'War',
                    'Nature', 'Anime', 'Medieval', 'Education', 'Sport', 'Fighter', 'History',
                    'Noire', 'Antiquity', 'Western', 'Movie', 'Mafia',
                    'single_player',
                    'multiplayer', 'coop', 'mmo', 'Android', 'AndroidConsole', 'AndroidTab',
                    'DC', 'DOS', 'DS', 'Flash', 'GBA', 'GCN', 'Linux', 'Mac', 'Metro', 'MetroTab',
                    'Mobile', 'PS2', 'PS3', 'PS4', 'PSP', 'SNES', 'VITA', 'Web', 'Wii', 'WiiU',
                    'Windows', 'X360', 'XBONE', 'XBOX', 'iPad', 'iPhone','prior_game']
    print "Using a total of: ", len(feature_list), " features"

    #Read in the SQL data and dump into a pandas dataframe
    f = open("../login.txt")
    login_txt = f.read()
    f.close()
    login = login_txt.split()
    con = mdb.connect(login[0], login[1], login[2], 'indiedb')

    mycolumns = ['Id', 'title', 'creator', 'engine', 'rating', 'votes', 'release_day',
                 'release_year', 'release_month', 'game_type', 'theme', 'single_player',
                 'multiplayer', 'coop', 'mmo', 'Android', 'AndroidConsole', 'AndroidTab',
                 'DC', 'DOS', 'DS', 'Flash', 'GBA', 'GCN', 'Linux', 'Mac', 'Metro', 'MetroTab',
                 'Mobile', 'PS2', 'PS3', 'PS4', 'PSP', 'SNES', 'VITA', 'Web', 'Wii', 'WiiU', 'Windows', 'X360', 'XBONE', 'XBOX', 'iPad', 'iPhone']

    with con:
        cur = con.cursor()
        cur.execute("SELECT * FROM Games")
        rows = cur.fetchall()
        games_df = pd.DataFrame(np.array(rows),columns=mycolumns)

        #Testing has_made_prior_game
        print "Testing has_made_prior_game..."
        evaluate_test(has_made_prior_game(1,games_df),False)
        evaluate_test(has_made_prior_game(62,games_df),False)
        evaluate_test(has_made_prior_game(4368,games_df),True)

        print "Testing process_games_from_db..."
        game_matrix, games_df = process_games_from_db(cur)
        success = make_full_success_vector(games_df, 9., 50)
        print game_matrix[4637], success[4637]
        print game_matrix[4638], success[4638]
    return

if __name__ == '__main__':
    run_tests()
