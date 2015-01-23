#!/usr/bin/env python

import numpy as np
import MySQLdb as mdb

import clean_text
from login_script import login_mysql

def get_metacritic_game(title,cur):
    #Finds metacritic game in the database

    command = "SELECT title, num_players, genre, summary FROM Metacritic WHERE title = '"+title+"'"
    print command
    cur.execute(command)
    mygame = cur.fetchall()

    if len(mygame) == 0:
        print "ERROR: Couldn't find the game "+title
        return []
    print mygame[0]

    return mygame[0]


def get_matching_indie_games(genre, game_type, num_players, ):
    #Get the list of words
    columns_command = "SHOW COLUMNS FROM Summary_words"
    cur.execute(columns_command)
    words_list = cur.fetchall()

    select_command = "SELECT Games.title, Games.rating, Games.votes, Games.genre FROM Games JOIN Summary_words ON Games.Id = Summary_words.game_id WHERE"
    select_command += "Games.genre = '"+genre+"' AND Games.game_type LIKE '"+game_type+"' ORDER BY votes, rating DESC"

    return game_data, words_list


if __name__ == '__main__':
    con = login_mysql("../login.txt")

    with con:
        cur = con.cursor()
        
        mygame = get_metacritic_game('BioShock',cur)
        
        
