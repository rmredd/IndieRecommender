#!/usr/bin/python

#Basics script for re-obtaining summaries
#May operate only on summaries for which there are issues

import numpy as np
import MySQLdb as mdb
import re

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

        #Get this game's ID; it not found, move on
        cur.execute("SELECT Id FROM Games WHERE title = '"+title+"'")
        rows = cur.fetchall()
        if len(rows) == 0:
            print "Unable to find game ",title," in the database.  Moving to next game..."

        #If the game is found, update the URL field
        myid = rows[0][0]
        print myid
        cur.execute("UPDATE Games SET url = '"+url+"' WHERE Id = "+myid)

    f.close()

    return

def read_indie_game_summary():
    '''
    For a single Indie game url, read and return the summary (cleaned of HTML tags)
    '''
    return

if __name__ == "__main__":
    
    con = login_mysql("../login.txt")
    
    with con:
        cur = con.cursor()
        add_indie_url_data("../gamelist.txt",cur)
