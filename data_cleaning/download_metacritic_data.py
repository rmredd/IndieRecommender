#!/usr/bin/env python

import urllib
import json
import numpy as np
import re

import MySQLdb as mdb

import title_cleanup
from login_script import login_mysql

#For downloading and cleaning up the two Metacritic data sets

def read_single_dataset_from_kimono(address,apikey,koffset):

    #Full URL for data retrieval
    my_url = address+"?apikey="+apikey+"&kimoffset="+str(koffset)
    print my_url

    #Actually get the data
    results = json.load(urllib.urlopen(my_url))

    #Only return the relevant parts of the data structure
    return results['results']

def split_list(text_list):
    '''
    Splits a comma-separated list of items and returns them with white space removed
    '''

    values = text_list.split(',')
    
    for i in range(len(values)):
        values[i] = values[i].strip()

    return values

def clean_genre_list(genre_text):
    '''
    Cleans a CSV text list of genres to eliminate duplicates
    '''
    
    words_list = split_list(genre_text)

    unique_words_list = np.unique(words_list)

    short_genre_text = unique_words_list[0]
    for word in unique_words_list[1:]:
        short_genre_text += ", "+word
    
    return short_genre_text

def collect_basic_metacritic_data():
    '''
    Runs through all kimono retrieved metacritic games, and returns the resulting lists of information
    Note that this also checked for missed values

    API key and address are currently hard-coded
    '''
    
    games_url = "https://www.kimonolabs.com/api/5obxxzg8"
    apikey = "ziMs6ipsOhkSt4rlCoDEL78zT1iGqvfu"
    
    #Set up the empty lists for the first batch
    title = []
    genre_list = []
    game_url = []

    #Read the most basic data set first
    
    for i in range(2):
        results = read_single_dataset_from_kimono(games_url,apikey,2500*i)
        results = results['collection1']

        for j in range(len(results)):
            title.append(re.sub(r"'",r"\\'",results[j]['Title']['text']))
            game_url.append(results[j]['Title']['href'])
            genre_list.append( re.sub(r"'",r"\\'",clean_genre_list(results[j]['Genre list'])))
            
    return title, genre_list, game_url

def make_main_metacritic_database(cur, title, genre_list, game_url):
    '''
    Adds the main initial set of data to the database (title, genres, game_url)
    Requires cursor input
    '''

    #Clear the table if it's already been made
    cur.execute('DROP TABLE IF EXISTS Metacritic')
    cur.execute('CREATE TABLE Metacritic(Id INT PRIMARY KEY AUTO_INCREMENT, title VARCHAR(100), meta_rating FLOAT, num_critic INT, user_rating FLOAT, num_users INT, num_players INT, genre VARCHAR(100), summary VARCHAR(2000), reviews VARCHAR(2000), url VARCHAR(200))')
    
    for i in range(len(title)):
        insert_command = "INSERT INTO Metacritic(title, genre, url) VALUES ('"+title[i]+"'"
        insert_command += ", '"+genre_list[i]+"', '"+game_url[i]+"')"
        print insert_command
        try:
            cur.execute(insert_command)
        except mdb.Error, e:
            print "ERROR -- unable to insert at ", i, " due to ", e
            print insert_command
            break

    return

def collect_more_metacritic_data_to_database(cur):
    '''
    Add additional data to the database using the second API
    '''

    more_info_url = "https://www.kimonolabs.com/api/3v3rrxjc"
    #My API key -- currently hard-coded
    apikey = "ziMs6ipsOhkSt4rlCoDEL78zT1iGqvfu"

    for i in range(2):
        #Get the basic data from the api
        results = read_single_dataset_from_kimono(more_info_url,apikey,2500*i)
        results = results['collection1']

        #For each element, first extract the data elements
        
        #Figure out the ID of this game in the database
        
        #Insert the genre list if it does not already exists (string with len 0)

        #Add the remaining data

    return


if __name__ == '__main__':
    #Getting mysql login data
    con = login_mysql("../login.txt")

    #Read the data in
    title, creator, release_date, engine, rating, votes, game_type, theme, players, platform, description = collect_indiedb_data()

    print "Creating the database..."
    with con:
        cursor = con.cursor()
        cleanup_and_put_in_database(title, creator, release_date, engine, rating, votes, game_type, theme, players, platform, description,
                                    cursor)
        
    
