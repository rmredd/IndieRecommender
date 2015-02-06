#!/usr/bin/env python

import numpy as np
import MySQLdb as mdb

from login_script import login_mysql
import recommend_games

#Functions for performing a validation of the recommendation software

def get_meta_indie_games(cur):
    '''
    Find the title and table IDs for games which are in both the Games table and
    the metacritic games table -- requires them to have the same title

    Also acquires all the other relevant data: game_type, theme, 

    Restricts to PC games only
    '''

    select_command = "SELECT Games.title, Games.Id, Metacritic.Id, Games.game_type, Games.theme, Games.single_player, Games.multiplayer, "
    select_command += "Games.mmo, Games.coop, Metacritic.genre FROM Games JOIN Metacritic ON Games.title = Metacritic.title "
    select_command += "WHERE ( Games.Windows = 1 OR Games.Mac = 1 OR Games.Linux = 1 )"
    cur.execute(select_command)
    results = cur.fetchall()
    
    results = np.array(results)
    titles = results[:,0]
    indie_ids = results[:,1].astype(int)
    meta_ids = results[:,2].astype(int)
    game_types = results[:,3]
    themes = results[:,4]
    players = results[:,5:9].astype(int)
    meta_genres = results[:,9]

    return titles, indie_ids, meta_ids, game_types, themes, players, meta_genres

def run_validation_test_single_game(indie_id, title, game_type, theme, players, meta_genre, words_list, 
                                    words_index, words_matrix, cur, min_rating = 7., min_votes=20):
    '''
    Runs a validation test on a single game.

    Returns title of best-match game, its similarity rating, and the rating of the input game
    '''

    (title_match, gt_match, theme_match, rate_match, sim_match, 
     urls, rel_words) = recommend_games.run_everything_on_input_title(title, [], words_matrix,
                                                                      cur, nvalues=2,
                                                                      min_rating=min_rating,
                                                                      min_votes = min_votes)
    if title == title_match[0]:
        best_place = 1
    else:
        best_place = 0
    
    #Get the self-similarity of the input game.  If this is in the output already, get it; otherwise, calculate it from scratch
    if title == title_match[0]:
        sim_self = sim_match[0]
    elif title == title_match[1]:
        sim_self = sim_match[1]
    else:
        cur.execute('SELECT summary FROM Metacritic WHERE title = "'+title+'"')
        meta_summary = cur.fetchall()[0][0]

        #Get the idf normalizations
        cur.execute("SELECT idf FROM idf_vals")
        idf = cur.fetchall()
        idf = np.array(idf).astype(float)[:,0]
        
        #Get the vector on the metacritic side
        words_vector = recommend_games.make_metacritic_game_words_vector(meta_summary, words_index, idf)
        words_vector = np.array(words_vector).astype(float)
        #Get the vector on the indie side
        select_command = "SELECT Games.rating "
        for word in words_list:
            select_command += ", Summary_words."+word
        select_command += " FROM Games JOIN Summary_words ON Games.Id = Summary_words.game_id WHERE Games.id="+str(indie_id)
        cur.execute(select_command)
        words_vector_indie = cur.fetchall()[0]
        words_vector_indie = np.array(words_vector_indie[1:]).astype(float)
        sim_self = recommend_games.get_words_distance(words_vector_indie, words_vector)

    return title_match[best_place], sim_match[best_place], sim_self

if __name__ == "__main__":
    #Get the words matrix from csv file
    words_matrix = pd.read_csv("../words_tf_idf.csv").as_matrix()
    words_matrix = words_matrix[:,1:]

    con = login_mysql("../login.txt")

    with con:
        cur = con.cursor()
        print "Getting list of overlap games..."
        titles, indie_ids, meta_ids, game_types, themes, players, meta_genres = get_meta_indie_games(cur)
        print "Getting word list..."
        words_list, words_index = recommend_games.get_list_of_words(cur)
        print "Found ", len(titles), " games that are in both databases"
        sim_self_all = np.zeros(len(titles))
        sim_other_all = np.zeros(len(titles))
        print "Starting validation..."
        for i in range(len(titles)):
            sim_title, sim_other, sim_self = run_validation_test_single_game(indie_ids[i], titles[i], game_types[i], 
                                                                             themes[i], players[i], meta_genres[i], 
                                                                             words_list, words_index, words_matrix,
                                                                             cur, min_votes=-1, min_rating=-2)
            print i, "True: ", titles[i], sim_self
            print "    Match: ", sim_title, sim_other
            sim_self_all[i] = sim_self
            sim_other_all[i] = sim_other

        print len(np.where(sim_self_all > sim_other_all)[0]), " games of ", len(titles), " are their own best match."
        print np.mean(sim_self_all), np.mean(sim_other_all), np.mean(sim_self_all-sim_other_all), np.std(sim_self_all-sim_other_all)
