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

    select_command = "SELECT title, Games.Id, Metacritic.Id, Games.game_type, Games.theme, Games.single_player, Games.multiplayer, "
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

def run_validation_test_single_game(title, game_type, theme, players, meta_genre, cur):
    '''
    Runs a validation test on a single game.
    '''

    title_match, gt_match, theme_match, rate_match, sim_match = recommend_games.run_everything_on_input_title(title, [], cur, nvalues=10)
    
    if title in title_match:
        print "Gotcha! "
    else:
        print "Oops, missed it."
    print title, game_type, theme, players, meta_genre
    for i in range(len(title_match)):
        print title_match[i], gt_match[i], theme_match[i], rate_match[i], sim_match[i]

    return

if __name__ == "__main__":
    con = login_mysql("../login.txt")

    with con:
        cur = con.cursor()
        titles, indie_ids, game_types, theme, players, meta_genres = get_meta_indie_games(cur)

        run_validation_test_single_game(titles[0], game_types[0], themes[0], players[0], meta_genre[0])
        
