#!/usr/bin/env python

import numpy as np
import MySQLdb as mdb

import clean_text
from login_script import login_mysql

def get_metacritic_game(title,cur):
    #Finds metacritic game in the database

    command = "SELECT title, num_players, genre, summary FROM Metacritic WHERE title = '"+title+"'"
    cur.execute(command)
    mygame = cur.fetchall()

    if len(mygame) == 0:
        print "ERROR: Couldn't find the game "+title
        return []

    return mygame[0]


def get_matching_indie_games(genre, game_type, num_players, ):
    #Get the list of words
    columns_command = "SHOW COLUMNS FROM Summary_words"
    cur.execute(columns_command)
    words_list = cur.fetchall()

    select_command = "SELECT Games.title, Games.rating, Games.votes, Games.theme, Games.game_type "
    for word in words_list[2:]:
        select_command += ", Summary_words."+word[0]
    select_command += " FROM Games JOIN Summary_words ON Games.Id = Summary_words.game_id WHERE "
    select_command += num_players+"= 1 AND "
    select_command += "Games.theme = '"+genre+"' AND Games.game_type LIKE '"+game_type+"' ORDER BY Games.votes DESC"
    cur.execute(select_command)
    game_data = cur.fetchall()

    return game_data, words_list[2:]

def make_metacritic_game_words_vector(summary, words_list):
    #Clean it to 
    clean_summary = clean_text.clean_summary_text(summary)
    my_words = clean_text.get_word_stems(clean_summary)

    words_vector = np.zeros(len(words_list))
    for i in range(len(words_list)):
        if words_list[i][5:] in my_words:
            words_vector[i] = 1
        
    return words_vector

def get_words_distance(words_indie_single, words_vector):
    dist = np.sum( (words_indie_single - words_vector)**2 )
    return dist

def get_all_words_distance(words_indie_matrix, words_vector):
    dist = np.zeros(len(words_indie_matrix))

    for i in range(len(words_indie_matrix)):
        dist[i] = get_words_distance(words_indie_matrix[i], words_vector)

    return dist

def get_best_match_with_rating():
    return 

def run_everything_on_input_title(title, cur):
    '''
    Returns title, theme, game_type, indiedb rating
    '''
    my_game = get_metacritic_game(title,cur)
        
    #Something here for sorting out genre labels

    game_data, words_list = get_matching_indie_games('Sci-Fi', '%Shooter', 'single_player')
    
    words_list = np.array(words_list)[:,0]

    #Separating out the summary for this game
    my_summary = my_game[-1]

    words_vector = make_metacritic_game_words_vector(my_summary, words_list)
        
    #Find the "distance" to each of the other games
    words_indie_matrix = np.array(game_data)[:,-len(words_vector):].astype(int)
    words_indie_matrix = (words_indie_matrix > 0).astype(int)
            
    dist = get_all_words_distance(words_indie_matrix, words_vector)
    rating = np.array(game_data)[:,1].astype(float)
    votes = np.array(game_data)[:,2].astype(int)
    rating_subset = np.where( (rating > 7) & (votes > 20))[0]

    sorted = rating_subset[np.argsort(dist[rating_subset])]

    game_data_arr = np.array(game_data)

    return game_data_arr[sorted[:5], 0], game_data_arr[sorted[:5],4], game_data_arr[sorted[:5],3], rating[sorted[:5]]

if __name__ == '__main__':
    con = login_mysql("../login.txt")

    with con:
        cur = con.cursor()
        
        titles, game_types, themes, ratings = run_everything_on_input_title('BioShock', cur)
        for i in range(len(titles)):

            print titles[i], game_types[i], themes[i], ratings[i]
