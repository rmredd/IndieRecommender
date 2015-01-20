#!/usr/bin/env python

import urllib
import json
import numpy as np
import re

import MySQLdb as mdb

import title_cleanup

def read_single_dataset_from_kimono(address,apikey,koffset):

    #Full URL for data retrieval
    my_url = address+"?apikey="+apikey+"&kimoffset="+str(koffset)
    print my_url

    #Actually get the data
    results = json.load(urllib.urlopen(my_url))

    #Only return the relevant parts of the data structure
    return results['results']

def print_urllist():
    '''
    Prints list of indieDB sites from the Kimono input
    Prints to a text file labeled 'gamelist.txt'
    '''

    address = "https://www.kimonolabs.com/api/7jleppae"
    #My API key -- currently hard-coded
    apikey = "ziMs6ipsOhkSt4rlCoDEL78zT1iGqvfu"

    f = open('gamelist.txt','w')
    

    for i in range(5):
        results = read_single_dataset_from_kimono(address,apikey,i*2500)
        print "Found ",len(results['collection1'])," results."

        for j in range(len(results['collection1'])):
            print >> f, 2500*i+j, title_cleanup.replace_right_quote(results['collection1'][j]['property1']['text']),' , ', results['collection1'][j]['property1']['href']

    f.close()

    return


def collect_indiedb_data():
    '''
    Runs through all kimono retrieved indiedb games, and returns the resulting lists
    Note that this removes duplicates, and removes unicode beyond ascii encoding

    Also notes which games have been dropped from the list

    API key and address are currently hard-coded
    '''
    
    games_url = "https://www.kimonolabs.com/api/dhngio36"
    #My API key -- currently hard-coded
    apikey = "ziMs6ipsOhkSt4rlCoDEL78zT1iGqvfu"

    #Set up the empty lists
    title = []
    creator = []
    release_date = []
    engine = []
    rating = []
    votes = []
    game_type = []
    theme = []
    players = []
    platform = []
    description = []

    for i in range(5):
        results = read_single_dataset_from_kimono(games_url,apikey,2500*i)
        results = results['collection1']
        for j in range(len(results)):
            #Check to see if this is a duplicate
            if len(title) > 0:
                if title[-1] == title_cleanup.replace_right_quote(results[j]['Title']['text']):
                    #Duplicate case
                    #Check to see if the duplicate has some information that we're missing otherwise
                    if 'Maker_release' in results[j].keys() and creator[-1] == '':
                        creator[-1] = results[j]['Maker_release']['text'].split('|')[0]
                    if 'Sumtext' in results[j].keys() and description[-1] == '':
                        description[-1] = results[j]['Sumtext']
                    if 'Releasedate' in results[j].keys():
                        try:
                            release_date[-1] = results[j]['Releasedate'][9:]
                        except TypeError:
                            #Fix the problem using other data if we can
                            if 'Maker_release' in results[j].keys():
                                release_date[-1] = results[j]['Maker_release']['text'].split('|')[1][10:]
                    continue
            #Not a duplicate
            title.append(title_cleanup.replace_right_quote(results[j]['Title']['text']))
            #Some data points failed to get the creator name
            if 'Maker_release' in results[j].keys():
                creator.append(results[j]['Maker_release']['text'].split('|')[0])
            else:
                creator.append('')
            #Catch errors in reading the release date
            try:
                release_date.append(results[j]['Releasedate'][9:])
            except TypeError:
                if 'Maker_release' in results[j].keys():
                    release_date.append(results[j]['Maker_release']['text'].split('|')[1][10:])
                else:
                    release_date.append('')
            engine.append(results[j]['Engine']['text'])
            rating.append(results[j]['Avg Rating'])
            votes.append(results[j]['Votecount'].split()[0])
            game_type.append(results[j]['Type'])
            theme.append(results[j]['Theme'])
            players.append(results[j]['Players'])
            platform.append(results[j]['Platform']['text'])
            #Some data points are missing the summary text
            if 'Sumtext' in results[j].keys():
                description.append(results[j]['Sumtext'])
            else:
                description.append('')

    return title, creator, release_date, engine, rating, votes, game_type, theme, players, platform, description

def split_list(text_list):
    '''
    Splits a comma-separated list of items and returns them with white space removed
    '''

    values = text_list.split(',')
    
    for i in range(len(values)):
        values[i] = values[i].strip()

    return values

def get_tidy_modes_list(players):
    #Split the players into separate categories, and give 0 or 1 for whether that mode exists
    play_mode = np.zeros([len(players), 4]) #Columns are single, multiplayer, coop, MMO
    for i in range(len(players)):
        clean_play = split_list(players[i])
        if 'Single' in clean_play or 'Single Player' in clean_play:
            play_mode[i,0] = 1
        if 'Multiplayer' in clean_play:
            play_mode[i,1] = 1
        if 'Co-op' in clean_play:
            play_mode[i,2] = 1
        if 'MMO' in clean_play:
            play_mode[i,3] = 1

    return play_mode

def get_tidy_platform(platform):
    #Get the list of possible platforms
    #Get the unique listing first
    temp_unique = np.unique(platform)
    #Break this down by comma-separated platforms
    uniq_p_list = []
    for some_plats in temp_unique:
        split_plats = split_list(some_plats)
        for plat in split_plats:
            uniq_p_list.append(plat)
    #Get the final uniq results
    plat_list = np.unique(uniq_p_list)
    nplats = len(plat_list)

    #Now, tidy up
    clean_plats = np.zeros([len(platform),nplats])
    for i in range(len(platform)):
        single_platform_list = split_list(platform[i])
        for j in range(nplats):
            if plat_list[j] in single_platform_list:
                clean_plats[i,j] = 1

    return clean_plats, plat_list

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
        

def create_description_table(description, cursor):
    '''
    Creation and cleanup for just the raw description data table
    '''
    ngames = len(description)

    #Save plain text descriptions in a second table
    cursor.execute("DROP TABLE IF EXISTS Game_descr")
    cursor.execute("CREATE TABLE Game_descr(Id INT PRIMARY KEY AUTO_INCREMENT, game_id INT, description VARCHAR(2001))")
    for i in range(ngames):
        if description[i] != '':
            if type(description[i]) == dict:
                my_descript = re.sub(r"\'",r"\\'",description[i]['text'])
            else:
                my_descript = re.sub(r"\'",r"\\'",description[i])
            my_descript = my_descript.encode('ascii','backslashreplace')
            my_descript = re.sub(r'\\u\d\d\d\d',r'',my_descript)
        else:
            my_descript = 'BLANK'

        if len(my_descript) > 2000:
            my_descript = my_descript[:2000]

        insert_statement = "INSERT INTO Game_descr(game_id, description) VALUES ("+str(i+1)+",'"+my_descript+"')"
        print i, insert_statement
        try:
            cursor.execute(insert_statement)
        except UnicodeEncodeError:
            print "Unicode issues, sorry."
            print my_descript
            break
        except mdb.Error, e:
            print "Failed insert statement: "
            print insert_statement
            print e
            break

    print "Table insertion complete"

    return

if __name__ == '__main__':
    #Getting mysql login data
    f = open("../login.txt")
    mysql_login = f.read()
    f.close()
    mysql_login = mysql_login.split()

    hostname = mysql_login[0]
    username = mysql_login[1]
    password = mysql_login[2]

    #Read the data in
    title, creator, release_date, engine, rating, votes, game_type, theme, players, platform, description = collect_indiedb_data()

    print "Opening the database connection..."
    con = mdb.connect(hostname,username,password,'indiedb')

    with con:
        cursor = con.cursor()
        cleanup_and_put_in_database(title, creator, release_date, engine, rating, votes, game_type, theme, players, platform, description,
                                    cursor)
        
    
