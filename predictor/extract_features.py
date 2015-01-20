#!/usr/bin/env python

# Series of functions for doing final data cleaning, and puts everything into a feature vector for 
# later learning

import numpy as np
import pandas as pd
import MySQLdb as mdb

def make_success_vector(rating, votes, metacritic_rating):
    '''
    This is the current method of defining game "success"
    A game must have a rating>9 and votes>100, or
    have a rating > 0 AND a metacritic_rating > 75

    This should be changed in the future, e.g., if revenue info is available
    '''

    success_vector = np.zeros(len(rating))
    success_slice = np.where( (rating > 9) & (votes > 100) )[0] 
    success_vector[success_slice] = 0*success_slice+1
    success_slice = np.where( (rating > 0) & (metacritic_rating > 75) )[0] 
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

    

    return game_vector

def process_single_game_summary(game_summary, vocab_list):
    '''
    Converts the text summary of a game into a feature vector
    Gives 1 if a word is present, zero otherwise
    Not implemented in the first run
    '''
    return

def process_games_from_db():
    '''
    Returns the matrix of game vectors drawn from the MySQLdb
    For convenience of later analysis, it also returns a list of feature labels
    '''
    return game_matrix, success_vector, feature_labels

if __name__ == '__main__':
    pass
