#!/usr/bin/env python

import numpy as np
import MySQLdb as mdb
import re

import clean_text
from login_script import login_mysql

def get_list_of_words(cur):
    '''
    Get the list (and ordering) of words currently being used in the database
    Returns the list of words (with stem initial portion label) and a dict of words and indices
    '''
    cur.execute("SHOW COLUMNS FROM Summary_words")
    words_list = cur.fetchall()
    words_list = words_list[2:]
    words_list = np.array(words_list)[:,0]
    #Make the dict we need to get the indices right
    words_index = {}
    for i in range(len(words_list)):
        words_index[words_list[i][5:]] = i

    return words_list, words_index

def get_metacritic_game(title,cur):
    #Finds metacritic game in the database

    command = 'SELECT title, genre, summary, single_player, multiplayer, mmo, coop FROM Metacritic WHERE title = "'+title+'"'
    cur.execute(command)
    mygame = cur.fetchall()

    if len(mygame) == 0:
        print "ERROR: Couldn't find the game "+title
        return []

    return mygame[0]

def get_list_of_metacritic_titles(cur):
    '''
    Gets the full list of metacritic titles that are in the database, and sorts to make them alphabetical
    '''

    cur.execute("SELECT title FROM Metacritic")
    title_list = cur.fetchall()
    title_list = np.array(title_list)
    title_list = title_list[:,0]
    title_list.sort()

    return title_list

def extract_game_type_info(my_game):
    '''
    This tests the extracted game information from a metacritic data set for a single game -- essentially
    attempting to translate this into 
    '''

    #Initially, metacritic game type and genre info is mixed, so split that up
    genre_list = my_game[1].split(',')
    #Make sure each element has white space stripped
    for i in range(len(genre_list)):
        genre_list[i] = genre_list[i].strip()

    game_types = []
    #Getting game type information
    if 'Shooter' in genre_list:
        game_types.append('First Person Shooter')
        game_types.append('Third Person Shooter')
        game_types.append('Tactical Shooter')
        game_types.append('Real Time Shooter')
    if 'Beat Em Up' in genre_list:
        game_types.append('Hack n Slash')
        game_types.append('Combat Sim')
        game_types.append('Fighting')
    if 'Sports' in genre_list:
        game_types.append('Baseball')
        game_types.append('Football')
        game_types.append('Basketball')
        game_types.append('Soccer')
        game_types.append('Wrestling')
        game_types.append('Golf')
        game_types.append('Hockey')
        game_types.append('Alternative Sport')
    if 'PC-Style RPG' in genre_list or 'Role-Playing' in genre_list:
        game_types.append('Role Playing')
    if 'Console-Style RPG' in genre_list:
        game_types.append('Role Playing')
    if 'Action RPG' in genre_list:
        game_types.append('Role Playing')
    if 'Action Adventure' in genre_list:
        game_types.append('Adventure')
    if 'Platformer' in genre_list:
        game_types.append('Platformer')
    if 'Strategy' in genre_list and 'Turn-Based' in genre_list:
        game_types.append('Turn-Based Strategy')
        game_types.append('Grand Strategy')
        game_types.append('Turn-Based Tactics')
    if 'Strategy' in genre_list and 'Real-Time' in genre_list:
        game_types.append('Real Time Strategy')
        game_types.append('Real Time Tactics')
        game_types.append('Tower Defense')
    if 'Strategy' in genre_list and 'Real-Time' not in genre_list:
        if 'Turn-Based' not in genre_list:
            game_types.append('Real Time Strategy')
            game_types.append('Turn-Based Strategy')
            game_types.append('Grand Strategy')
    if 'Other Strategy Games' in genre_list:
        game_types.append('Real Time Strategy')
        game_types.append('Real Time Tactics')
        game_types.append('Turn-Based Strategy')
        game_types.append('Grand Strategy')
        game_types.append('Turn-Based Tactics')
        game_types.append('Tower Defense')
    if 'Puzzle' in genre_list or 'Logic' in genre_list or re.search(r'puzzle',my_game[2]):
        game_types.append('Puzzle Compilation')
    if 'Virtual Life' in genre_list:
        game_types.append('Visual Novel')
        game_types.append('Virtual Life')
    if 'Driving' in genre_list or 'Racing' in genre_list:
        game_types.append('Racing')
        game_types.append('Car Combat')
    if 'Demolition Derby' in genre_list:
        game_types.append('Car Combat')
    if 'Sim' in genre_list or 'Simulation' in genre_list:
        game_types.append('Realistic Sim')
        game_types.append('Futuristic Sim')
    if 'Edutainment' in genre_list:
        game_types.append('Educational')
        game_types.append('Family')
    if 'Arcade' in genre_list or 'Pinball' in genre_list:
        game_types.append('Arcade')
    if 'Interactive Movie' in genre_list:
        game_types.append('Cinematic')
    if 'Rhythm' in genre_list:
        game_types.append('Rhythm')
    if 'Hidden Object' in genre_list:
        game_types.append('Point and Click')
    #Check for "roguelike"
    if re.search(r"roguelike",my_game[2]):
        game_types.append('Roguelike')
    #Check for "4X"
    if re.search(r"4X", my_game[2]):
        game_types.append('4X')

    genres = []
    #Getting genre information
    if 'Sci-Fi' in genre_list:
        genres.append('Sci-Fi')
    if 'Fantasy' in genre_list:
        genres.append('Fantasy')
    if 'Fighter' in genre_list:
        genres.append('Fighter')
    if 'Horror' in genre_list:
        genres.append('Horror')
    if 'Historic' in genre_list:
        genres.append('History')
        genres.append('Antiquity')
        genres.append('Medieval')
    if 'WWII' in genre_list or 'WWI' in genre_list:
        genres.append('History')
        genres.append('War')
    if 'Nature' in genre_list:
        genres.append('Nature')
    if 'Sports' in genre_list:
        genres.append('Sport')
    if 'Wargame' in genre_list:
        genres.append('War')

    #Getting player information
    players = []
    if my_game[3] == '1':
        players.append('single_player')
    if my_game[4] == '1':
        players.append('multiplayer')
    if my_game[5] == '1':
        players.append('mmo')
    if my_game[6] == '1':
        players.append('coop')
    #If coop is mentioned in the summary description, add it
    if 'coop' not in players:
        if re.match(r'cooper', my_game[2]) or re.match(r'co-op', my_game[2]):
            players.append('coop')

    #Make sure we've got unique lists
    game_types = np.unique(game_types)
    genres = np.unique(genres)

    return game_types, genres, players


def get_matching_indie_games(platforms, genre, game_type, num_players, cur):
    #Get the list of words
    columns_command = "SHOW COLUMNS FROM Summary_words"
    cur.execute(columns_command)
    words_list = cur.fetchall()

    select_command = "SELECT Games.title, Games.rating, Games.votes, Games.theme, Games.game_type "
    for word in words_list[2:]:
        select_command += ", Summary_words."+word[0]
    select_command += " FROM Games JOIN Summary_words ON Games.Id = Summary_words.game_id"

    #If we're doing any additional selections, add a where statement
    if len(genre) > 0 or len(game_type) > 0 or len(num_players) > 0:
        select_command += " WHERE "

    #Select on the number of players
    if len(num_players) == 1:
        select_command += "Games."+num_players[0]+"= 1 "
    if len(num_players) > 1:
        select_command += "(Games."+num_players[0]+"=1 "
        for player in num_players[1:]:
            select_command += " OR Games."+player+"=1"
        select_command += ") "
    #Add additional and statement if necessary
    if len(num_players) > 0 and (len(game_type) > 0 or len(genre) > 0):
        select_command += " AND "

    #Set up the game type selection
    if len(game_type) == 1:
        select_command += "Games.game_type = '"+game_type[0]+"'"
    if len(game_type) > 1:
        select_command += "(Games.game_type = '"+game_type[0]+"'"
        for some_type in game_type[1:]:
            select_command += " OR Games.game_type = '"+some_type+"'"
        select_command += ")"
    if len(game_type) > 0 and len(genre) > 0:
        select_command += " AND "

    #And, finally, genre selection
    if len(genre) == 1:
        select_command += "Games.theme = '"+genre[0]+"'"
    if len(genre) > 1:
        select_command += "(Games.theme = '"+genre[0]+"'"
        for some_genre in genre[1:]:
            select_command += " OR Games.theme = '"+some_genre+"'"
        select_command += ")"

    #Now, throw in platform selection
    if len(platforms) > 0:
        select_command += " AND "
    if len(platforms) == 1:
        select_command += "Games."+platforms[0]+"=1"
    if len(platforms) > 1:
        select_command += "(Games."+platforms[0]+"=1"
        for platform in platforms[1:]:
            select_command += " OR Games."+platform+"=1"
        select_command += ")"

    cur.execute(select_command)
    game_data = cur.fetchall()

    return game_data, words_list[2:]

def make_metacritic_game_words_vector(summary, words_index, idf):
    '''
    Make the tf-idf vector for a single game
    Does so from a summary and the dict of words and indices being used
    Note that this requires the idf to be read in from the database earlier
    '''

    clean_summary = clean_text.clean_summary_text(summary)
    #Make sure the encoding is fixed
    clean_summary = clean_text.replace_right_quote(unicode(clean_summary,errors='ignore'))
    my_words = clean_text.get_word_stems(clean_summary)

    return clean_text.get_tf_idf(words_index, my_words, idf)

def get_words_distance(words_indie_single, words_vector):
    '''
    Gets the angle between the word vectors
    '''
    dist = np.sum( words_indie_single*words_vector) / np.sqrt(np.sum(words_indie_single**2)) / np.sqrt(np.sum(words_vector**2))

    if np.isnan(dist) or np.isinf(dist):
        dist = 0.
    return dist

def get_all_words_distance(words_indie_matrix, words_vector):
    dist = np.zeros(len(words_indie_matrix))

    for i in range(len(words_indie_matrix)):
        dist[i] = get_words_distance(words_indie_matrix[i], words_vector)

    #Deal with nan results
    nan_list = np.where( np.isnan(dist) )[0]
    if len(nan_list) > 0:
        dist[nan_list] = 0.*nan_list

    return dist

def run_everything_on_input_title(title, platforms, cur, nvalues=5, min_rating=7., min_votes=20):
    '''
    Returns title, game_type, theme, indiedb rating, and similarity rating
    Returns nvalues total matches, default 5
    '''
    my_game = get_metacritic_game(title,cur)
        
    #Sort out the game type and genre labels
    game_types, genres, players = extract_game_type_info(my_game)

    #Includes matching on a list of options
    game_data, words_list = get_matching_indie_games(platforms, genres, game_types, players,cur)
    #If we don't find any matches, select all games that match the platform(s)
    if len(game_data[0]) == 0:
        game_data, words_list = get_matching_indie_games(platforms, [], [], [], cur)

    words_list = np.array(words_list)[:,0]
    #Make the dict we need to get the indices right
    words_index = {}
    for i in range(len(words_list)):
        words_index[words_list[i][5:]] = i
    
    #Separating out the summary for this game
    my_summary = my_game[2]
    
    #Read in the idf normalizations
    cur.execute("SELECT * FROM idf_vals WHERE Id = 1")
    idf = cur.fetchone()
    idf = idf[1:]
    idf = np.array(idf).astype(float)
    leftovers = cur.fetchall() #In case something weird happens and there's more than one row

    words_vector = make_metacritic_game_words_vector(my_summary, words_index, idf)

    #Find the "distance" to each of the other games
    words_indie_matrix = np.array(game_data)[:,-len(words_vector):].astype(float)

    similarity_rating = get_all_words_distance(words_indie_matrix, words_vector)
    rating = np.array(game_data)[:,1].astype(float)
    votes = np.array(game_data)[:,2].astype(int)
    rating_subset = np.where( (rating > min_rating) & (votes > min_votes))[0]
    #If we need to be less restrictive, loosen the restrictions
    if len(rating_subset) < nvalues:
        rating_subset = np.array(range(len(rating)))

    sorted = rating_subset[np.argsort(similarity_rating[rating_subset])]
    sorted = sorted[::-1]

    game_data_arr = np.array(game_data)

    #Returns: titles, game_types, themes (genres), indie db rating, and the similarity rating
    return game_data_arr[sorted[:nvalues], 0], game_data_arr[sorted[:nvalues],4], game_data_arr[sorted[:nvalues],3], rating[sorted[:nvalues]], similarity_rating[sorted[:nvalues]]

if __name__ == '__main__':
    con = login_mysql("../login.txt")

    with con:
        cur = con.cursor()
        
        titles, game_types, themes, ratings, sim_ratings = run_everything_on_input_title('BioShock', [], cur)
        for i in range(len(titles)):

            print titles[i], game_types[i], themes[i], ratings[i], sim_ratings[i]
