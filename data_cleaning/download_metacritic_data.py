#!/usr/bin/env python

import urllib
import urllib2
import json
import numpy as np
import re
import time

import MySQLdb as mdb

import title_cleanup
from login_script import login_mysql
from login_script import get_apikey

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
    apikey = get_apikey("apikey.txt")
    
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
    cur.execute('CREATE TABLE Metacritic(Id INT PRIMARY KEY AUTO_INCREMENT, title VARCHAR(100), meta_rating FLOAT, num_critics INT, user_rating FLOAT, num_users INT, genre VARCHAR(100), summary VARCHAR(2000), reviews VARCHAR(2000), url VARCHAR(200), single_player BOOL, multiplayer BOOL, mmo BOOL, coop BOOL)')
    
    for i in range(len(title)):
        insert_command = "INSERT INTO Metacritic(title, genre, url) VALUES ('"+title[i]+"'"
        insert_command += ", '"+genre_list[i]+"', '"+game_url[i]+"')"
        try:
            cur.execute(insert_command)
        except mdb.Error, e:
            print "ERROR -- unable to insert at ", i, " due to ", e
            print insert_command
            break

    return

def get_num_player_code(num_players):
    '''
    Converts text number of players to a set of integer codes
    Corresponds to single, multi, mmo, coop labels
    '''
    num_player_code = np.zeros(4)
    if num_players == '1 Player':
        num_player_code[0] = 1
    if num_players == 'Massively Multiplayer':
        num_player_code[2] = 1
    num_player_split = num_players.split('-')
    if len(num_player_split) == 2:
        if num_player_split[0] == '1':
            num_player_code[0] = 1
        num_player_code[1] = 1
    if num_players[-6:] == 'Online':
        num_player_code[1] = 1

    return num_player_code

def collect_more_metacritic_data_to_database(cur):
    '''
    Add additional data to the database using the second API
    '''

    more_info_url = "https://www.kimonolabs.com/api/3v3rrxjc"
    #My API key -- currently hard-coded
    apikey = get_apikey("apikey.txt")

    for i in range(2):
        #Get the basic data from the api
        results = read_single_dataset_from_kimono(more_info_url,apikey,2500*i)
        results = results['collection1']

        for j in range(len(results)):
            #For each element, first extract the data elements
            title = re.sub(r"'",r"\\'",results[j]['title']['text'])
            if 'user_score' in results[j].keys():
                user_score = results[j]['user_score']['text']
                num_users = results[j]['num_users']
            else:
                user_score = '-1'
                num_users = '0'
            if 'metascore' in results[j].keys():
                meta_score = results[j]['metascore']['text']
                num_critics = results[j]['num_critics'].split()[0]
            else:
                meta_score = -1
                num_critics = '0'
            genre = re.sub(r"'",r"\\'",title_cleanup.replace_right_quote(results[j]['genre']))
            if 'num_players' in results[j].keys():
                num_players = results[j]['num_players']
            else:
                num_players = ''
            if 'Summary' in results[j].keys():
                if type(results[j]['Summary']) == dict:
                    summary = re.sub(r"'",r"\\'",title_cleanup.replace_right_quote(results[j]['Summary']['text']))
                else:
                    summary = re.sub(r"'",r"\\'",title_cleanup.replace_right_quote(results[j]['Summary']))
            else:
                summary = ''

            #Do some processing -- assign the number of players
            num_player_code = get_num_player_code(num_players)

            #Figure out the ID of this game in the database
            cur.execute("SELECT Id, genre FROM Metacritic WHERE title = '" + title + "'")
            fetched = cur.fetchall()
            if len(fetched) > 1:
                print "Warning: more than one game title matched "+title
            fetched = fetched[0]
            fetched_id = fetched[0]
            fetched_genre = fetched[1]

            #Don't change the genre if the fetched genre is more detailed
            if len(fetched_genre) > len(genre):
                genre = re.sub(r"'",r"\\'",fetched_genre)

            #Add the remaining data
            update_command = "UPDATE Metacritic SET "
            update_command += "user_rating = "+str(user_score)
            update_command += ", num_users = "+str(num_users)
            update_command += ", meta_rating = "+str(meta_score)
            update_command += ", num_critics = "+num_critics
            update_command += ", genre = '"+genre+"'"
            update_command += ", summary = '"+summary+"'"
            update_command += ", single_player = "+str(num_player_code[0])
            update_command += ", multiplayer = "+str(num_player_code[1])
            update_command += ", mmo = "+str(num_player_code[2])
            update_command += ", coop = "+str(num_player_code[3]) 
            update_command += " WHERE Id = "+str(fetched_id)

            #Run a final cleanup, to handle any unicode stupidity
            update_command = title_cleanup.replace_right_quote(update_command)

            try:
                cur.execute(update_command)
            except mdb.Error, e:
                print "Item", j, "Error in MySQL command which follows: "
                print update_command
                print e
                break

    return


def recollect_metacritic_summaries(cur):
    '''
    For each item in the database, pull the metacritics URL and get the full summary text
    '''

    user_agent = "Firefox/2.0.0.11"

    cur.execute("SELECT Id, url FROM Metacritic")
    fetched = cur.fetchall()

    count = 0
    for Id, url in fetched:
        try:
            request = urllib2.Request(url)
            opener = urllib2.build_opener()
            request.add_header('User-Agent', user_agent)
            text = opener.open(request).read()
        except:
            print "Unable to locate URL for ", url
            continue
        #Check to see if we've been forbidden
        if re.match(r"Error 403 Forbidden",text):
            print "Issue -- access forbidden?"
            print text
            break
            
        #Find the expanded text blurb
        sum_match = re.search(r'<meta property="og:description" content="([\w\W]*?)">',text)
        if sum_match:
            summary = sum_match.group(1)
        else:
            summary = ""
            print "Something failed: ", Id, url
            continue

        #Update the database
        if summary != '':
            #deal with annoying apostrophes
            if len(summary) > 2000:
                summary = summary[:2000]
            update_command = 'UPDATE Metacritic SET summary = "'+re.sub(r"'",r"\\'",summary)+'" WHERE Id = '+str(Id)
            try:
                cur.execute(update_command)
            except mdb.Error, e:
                print "MySQL Error in command: ",update_command
                print "Making second attempt..."
                summary = re.sub(r"'",r"\\'",summary)
                update_command = "UPDATE Metacritic SET summary = '"+re.sub(r"'",r"\\'",summary)+"' WHERE Id = "+str(Id)
                
        time.sleep(1)
        count +=1
        if count == 1:
            print count, summary
        if count % 100 == 0:
            print "Finished through ",count

    return


if __name__ == '__main__':
    #Getting mysql login data
    con = login_mysql("../login.txt")

    #Read the data in
    print "Getting the first set of data"
    #title, genre_list, game_url = collect_basic_metacritic_data()

    print "Creating the initial database..."
    with con:
        cur = con.cursor()
        #make_main_metacritic_database(cur,title, genre_list, game_url)
    
        #print "Adding to the database..."
        #collect_more_metacritic_data_to_database(cur)

        print "Updating the summary text to full..."
        recollect_metacritic_summaries(cur)

    print "Mission accomplished."
