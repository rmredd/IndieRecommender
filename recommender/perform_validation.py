#!/usr/bin/env python

import numpy as np
import MySQLdb as mdb

import recommend_games

#Functions for performing a validation of the recommendation software

def get_meta_indie_games(cur):
    '''
    Find the title and table IDs for games which are in both the Games table and
    the metacritic games table -- requires them to have the same title
    '''

    cur.execute("SELECT title, Games.Id, Metacritic.Id FROM ")

    return title, indie_id, meta_id

if __name__ == "__main__":
    pass
