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
            title.append(results[j]['Title']['text'])
            game_url.append(results[j]['Title']['href'])
            genre_list.append( clean_genre_list(results[j]['Genre list']))
            
    return title, genre_list, game_url

def make_main_metacritic_database(cur, title, genre_list, game_url):
    '''
    Adds the main initial set of data to the database (title, genres, game_url)
    Requires cursor input
    '''

    #Clear the table if it's already been made
    cur.execute('DROP TABLE IF EXISTS Metacritic')
    cur.execute('CREATE TABLE Metacritic(Id INT AUTO_INCREMENT, title VARCHAR(100), meta_rating FLOAT, num_critic INT, user_rating FLOAT, num_users INT, num_players INT, genre VARCHAR(60), summary VARCHAR(2000), reviews VARCHAR(2000), url VARCHAR(200))')
    
    for i in len(title):
        insert_commaned = "INSERT INTO Metacritic(title, genre, url) VALUES ('"+title[i]+"'"
        insert_command += ", '"+genre_list[i]+"', '"+game_url[i]+"')"
        cur.execute(insert_command)

    return

def collect_more_metacritic_data_to_database(cur):
    '''
    Add additional data to the database using the second API
    '''

    more_info_url = "https://www.kimonolabs.com/api/3v3rrxjc"
    #My API key -- currently hard-coded
    apikey = "ziMs6ipsOhkSt4rlCoDEL78zT1iGqvfu"

    return

def cleanup_and_put_in_database(title, creator, release_date, engine, rating, votes, game_type, theme, players, platform, description,
                                cursor):
    '''
    Performs additional cleanup and puts the rest of the data into an SQL table for later retrieval
    Requires a mysql cursor
    '''

    #Get number of games
    ngames = len(title)

    #Remove any single quotes from title strings
    title_new = np.copy(title)
    for i in range(ngames):
        title_new[i] = re.sub(r"\'",r"\\'",title[i])

    #Clean the unicode from the creator names
    creator_old = np.copy(np.array(creator))
    for i in range(ngames):
        if type(creator[i]) is 'unicode':
            creator[i] = title_cleanup.replace_right_quote(creator[i])

    #Clean unicode from engine names
    engine_new = np.copy(engine)
    for i in range(ngames):
        engine_new[i] = title_cleanup.replace_right_quote(engine[i])
    
    #Fix games types with apostrophes
    game_type = np.array(game_type)
    hack_places = np.where(game_type == "Hack 'n' Slash")[0]
    for i in range(len(hack_places)):
        game_type[hack_places[i]] = "Hack n Slash"

    #Split up the player modes into a nice matrix
    clean_play = get_tidy_modes_list(players).astype(int)

    #Split up the platform lists as well
    clean_plats,unique_platforms = get_tidy_platform(platform)
    clean_plats = clean_plats.astype(int)

    #Save most results into a temporary file
    f = open("../game_basics_list.txt",'w')
    for i in range(len(title)):
        try:
            print >> f, title_new[i]+','+creator[i]+','+release_date[i]+','+engine_new[i]+','+rating[i]+','+votes[i]+','+game_type[i]+','+theme[i]+','+players[i]+','+platform[i]    
        except UnicodeEncodeError:
            print i, " -- " ,title_new[i]+','+creator[i]+','+release_date[i]+','+engine_new[i]+','+rating[i]+','+votes[i]+','+game_type[i]+','+theme[i]+','+players[i]+','+platform[i]    

    f.close()
    
    #Fix types
    votes = np.array(votes).astype(int)
    rating = np.array(rating)
    unrated = np.where(rating == '-')[0]
    rating[unrated] = 0*unrated -1
    rating = np.array(rating).astype(float)

    #Extract the release day
    release_day = np.zeros(ngames).astype(int)
    for i in range(ngames):
        try:
            release_day[i] = int(release_date[i][4:6].split(',')[0])
        except ValueError:
            print release_date[i]
            release_day[i] = -1

    #Create the initial database
    cursor.execute("DROP TABLE IF EXISTS Games")
    
    #Setup the creation table.  Note that we have a medium int value for each mode and platform
    command_create_table = "CREATE TABLE Games(Id INT PRIMARY KEY AUTO_INCREMENT, title VARCHAR(100), creator VARCHAR(100), engine VARCHAR(100), rating FLOAT, votes INT, "
    command_create_table += "release_day INT, release_year INT, release_month VARCHAR(4), "
    command_create_table += "game_type VARCHAR(50), theme VARCHAR(50), single_player BOOL, multiplayer BOOL, coop BOOL, mmo BOOL "
    for some_platform in unique_platforms:
        command_create_table += ", "+some_platform+" BOOL"
    command_create_table += ")"
    print "Table creation command: "
    print command_create_table
    cursor.execute(command_create_table)
    values_names = "title, creator, engine, rating, votes, release_day, release_year, release_month, game_type, theme, single_player, multiplayer, coop, mmo"
    for some_platform in unique_platforms:
        values_names += ", "+some_platform
    for i in range(ngames):
        insert_statement = "INSERT INTO Games("+values_names+") VALUES ('"+title_new[i]+"', '"+re.sub(r"\'",r"\\'",creator[i]).strip()+"', '"+re.sub(r"\'",r"\\'",engine_new[i])
        insert_statement += "', "+str(rating[i])+", "+str(votes[i])
        year = release_date[i][-4:]
        if not re.match(r'\d\d\d\d',year):
            year = '-1'
        insert_statement += ", "+str(release_day[i])+", "+year+", '"+release_date[i][:3]+"', '"+game_type[i]+"', '"+theme[i]+"', "+str(clean_play[i,0])+", "
        insert_statement += str(clean_play[i,1])+", " +str(clean_play[i,2])+ ", " + str(clean_play[i,3])
        for j in range(len(unique_platforms)):
            insert_statement += ", "+str(clean_plats[i,j])
        insert_statement += ")"
        if i == 0:
            print ""
            print "Template insert statement..."
            print insert_statement
            print ""
        try:
            cursor.execute(insert_statement)
        except mdb.Error, e:
            print "There is an error in the following insert statement, at item ",i,":"
            print insert_statement
            break

    print "Finished inserting main tags, moving to descriptions"

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
        
    
