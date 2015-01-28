#!/usr/bin/python

#Basics script for re-obtaining summaries
#May operate only on summaries for which there are issues

import numpy as np
import MySQLdb as mdb
import re
import urllib
import title_cleanup

from login_script import login_mysql


def get_title_and_url_from_line(line):
    title_stuff, url = line.split(' , ')
    url = url.strip()

    title = re.search(r'\d+\s([\w\W]*)',title_stuff)
    title = title.group(1)
    title = title.strip()
    
    return title, url


def add_indie_url_data(filename,cur):
    '''
    Takes in a filename and a MySQLdb cursor
    Parses list of Indie games, and adds (or updates) their URLs to the database
    Prints a warning if game is not found
    '''

    #First, check to see if URLs have been added yet
    cur.execute("SHOW COLUMNS FROM Games")
    rows = cur.fetchall()
    has_url = False
    for row in rows:
        if row[0] == 'url':
            has_url = True
            break
    if not has_url:
        cur.execute("ALTER TABLE Games ADD url VARCHAR(200)")
        print "Adding url column to the Games table"

    f = open(filename)

    for line in f:
        #Read the line, and get out the title and URL
        title, url = get_title_and_url_from_line(line)

        #Fix issues with apostrophes
        title = re.sub(r"'",r"\\'",title)

        #Get this game's ID; it not found, move on
        cur.execute("SELECT Id FROM Games WHERE title = '"+title+"'")
        rows = cur.fetchall()
        if len(rows) == 0:
            print "Unable to find game ",title," in the database.  Moving to next game..."
            continue

        #If the game is found, update the URL field
        myid = rows[0][0]
        cur.execute("UPDATE Games SET url = '"+url+"' WHERE Id = "+str(myid))

    f.close()

    return

def get_clean_indie_summary(text):
    #First, extract just the summary section
    match = re.search(r'<div class="tooltip"></div>[\w\W]*?<p>([\w\W]*?)</div>',text)
    
    if match:
        sub_text = match.group(1)
    else:
        print "Error reading summary"
        sub_text = ""

    #Strip HTML tags and replace with a space
    summary = re.sub(r'<[^<>]+>',' ',sub_text)

    summary = re.sub(r"\&quot;",r" ",summary)
    summary = re.sub(r"\&amp;",r" ",summary)
    if not re.match(r"\\",summary):
        summary = re.sub(r"'",r"\\'",summary)
    #Fixing stupid unicode issues
    summary = title_cleanup.replace_right_quote(unicode(summary,errors='ignore'))

    return summary

def read_indie_game_summary(url):
    '''
    For a single Indie game url, read and return the summary (cleaned of HTML tags)
    '''
    
    try:
        ufile = urllib.urlopen(url)
        text = ufile.read()
    except IOError:
        print "Unable to read from url: ", url
        return ""    

    return get_clean_indie_summary(text)

def update_indie_summaries_in_database(cur,index_min = 0):
    '''
    If there's an error, and the summary is blank, don't touch the database
    '''
    
    #First, read in the list of Ids and urls
    cur.execute("SELECT Id, url FROM Games")
    rows = cur.fetchall()

    for row in rows:
        my_id = row[0]
        my_url = row[1]

        #Function for skipping things that have been updated already
        if my_id < index_min:
            continue

        if my_id % 100 == 0:
            print "Complete through ", my_id

        if my_url == "" or my_url == None:
            print "No url for ", my_id
            continue
        summary = read_indie_game_summary(my_url)
        if summary == "":
            print "There was been an error in the read for ", my_id
            continue

        try:
            if len(summary) > 2000:
                #Trim if necessary
                summary = summary[:2000]
            cur.execute("UPDATE Game_descr SET description = '"+summary+"' WHERE Id = "+str(my_id))
        except mdb.Error, e:
            print "Error in command for item ",my_id," with summary:"
            print summary
            print "Error was: ",e
            break

    return

if __name__ == "__main__":
    
    con = login_mysql("../login.txt")
    
    with con:
        cur = con.cursor()
        update_indie_summaries_in_database(cur,index_min=8215)
