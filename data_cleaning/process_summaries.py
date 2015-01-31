#!/usr/bin/env python

import numpy as np
import re
import nltk
import MySQLdb as mdb
import pandas as pd
import cPickle as pickle

import title_cleanup
from login_script import login_mysql

#Scripts for cleaning up the summary data and creating a useful array for the text

def clean_summary_text(text):
    '''
    Main set of routines that cleans up the text, ready for stemming
    Note that this also removes HTML code
    '''

    #Make everything lowercase
    clean_text = text.lower()

    #Strip HTML tags, repleace with a space
    clean_text = re.sub(r'<[^<>]+>',' ',clean_text)

    #Replace numbers with 'number'
    clean_text = re.sub(r'[0-9]+', r'number',clean_text)

    #Handle URLs
    clean_text = re.sub(r'(http|https)://[^\s]*', r'httpaddr',clean_text)

    #Handle email addresses -- strings containing '@'
    clean_text = re.sub(r'[^\s]+@[^\s]+', r'emailaddr',clean_text)

    #Replace dollar sign
    clean_text = re.sub(r'[$]+', r'dollar',clean_text)

    #Remove any remaining alphanumeric characters
    clean_text = re.sub('[\\@$\/\#\.\-:&\*\+\=\[\]?!\(\)\{\},\'\">\_<;%]',r'',clean_text)

    #Remove excess white spaces, and replace with a single space
    clean_text = re.sub(r'\s+',r' ',clean_text)

    #Remove stupid characters
    clean_text = re.sub(r'~',r' ',clean_text)
    clean_text = re.sub(r'\|',r' ', clean_text)
    clean_text = re.sub(r'\^',r' ', clean_text)
    
    #Strip beginning/ending white space
    clean_text = clean_text.strip()

    return clean_text
    
def get_word_stems(text):
    '''
    Gets all word stems from a block of cleaned text
    '''

    #Split text into words
    words = text.split()

    stem_text = []
    stemmer = nltk.stem.porter.PorterStemmer()
    for word in words:
        stem_text.append(stemmer.stem(word))
    return stem_text

def get_all_word_stems(summary_list):
    '''
    Returns a set of lists of words after cleaning a list of summaries
    '''
    words_list = []
    
    for summary in summary_list:
        words = clean_summary_text(summary)
        words = get_word_stems(words)
        words_list.append(words)

    return words_list

def get_all_words_list(words_list):
    '''
    Compiles a list of all words in a set of text summaries that have already been stemmed
    '''
    count_words = 0L
    for i in range(len(words_list)):
        count_words += len(words_list[i])
    all_words = np.repeat('                    ',count_words)
    count_words = 0L
    for i in range(len(words_list)):
        if len(words_list[i]) == 0:
            continue
        all_words[count_words:count_words+len(words_list[i])] = words_list[i]
        count_words += len(words_list[i])

    return all_words

def get_words_from_database(cur):
    '''
    Gets the summary texts from the database, and returns the cleaned word lists and game IDs
    '''
    
    cur.execute('SELECT game_id, description FROM Game_descr')
    descr = cur.fetchall()
    game_ids = np.array(descr)[:,0].astype(int)

    words_list = get_all_word_stems(np.array(descr)[:,1])

    return words_list, game_ids

def get_num_docs_with_words(words_index, words_list):
    '''
    Takes as input the dict that takes words to the relevant index, and the overall
    list of words across the game summaries corpus
    '''

    words_ndocs = np.zeros(len(words_index)).astype(int)

    for words_set in words_list:
        words_ndocs_tmp = np.zeros(len(words_index)).astype(int)
        for word in words_set:
            if word in words_index:
                words_ndocs_tmp[words_index[word]] = 1
        words_ndocs += words_ndocs_tmp

    return words_ndocs

def get_idf(ndocs, words_ndocs):
    '''
    Calculates inverse document frequency for the list of common words
    Includes handling for case where term does not appear
    '''

    idf = np.log(ndocs/(1+words_ndocs.astype(float)))

    return idf

def get_tf_idf(words_index, game_words, idf):
    '''
    Get the tf-idf values for a single game's words
    Requires input of idf (which is the same for all documents) and the list of words in the game summary
    Also requires input of the words index for getting matrix positions
    '''

    #Get the game words into a series, and do some counting
    game_words_series = pd.Series(game_words)
    game_words_text = game_words_series.value_counts().index
    game_words_count = game_words_series.value_counts()
    
    #We'll be using augmented frequency, for term frequency, to avoid issues with varying document length
    max_freq_doc = np.max(game_words_count)

    #Term frequency
    tf = np.zeros(len(words_index))
    for i in range(len(game_words_text)):
        if game_words_text[i] in words_index.keys():
            tf[words_index[game_words_text[i]]] = 0.5 + 0.5*game_words_count[i] / max_freq_doc

    return tf*idf

def produce_database_of_common_words(words_list, game_ids, cur, nwords=1000):
    '''
    Produce a database of word counts, for the (default) 1000 most common words in the overall list
    Note also requires cursor as input
    '''

    #Get the number of documents (=number of indie games)
    ndocs = len(words_list)
    
    #Get the list of all words
    cur.execute('DROP TABLE IF EXISTS Summary_words')
    
    print "Getting overall word list.  This may take a little while..."
    all_words = get_all_words_list(words_list)
    words_series = pd.Series(all_words)

    print "Moving on..."
    #Get the 1000 most common words
    words_common = words_series.value_counts()
    words_common_text = words_common.index[:nwords]
    words_common_count = words_common[:nwords]
    print "Total number of words (non-unique): ",len(all_words)
    print "Common words: ",words_common_text
    #Create a dictionary object for sorting out words later
    words_common_index = dict([])
    for i in range(nwords):
        words_common_index[words_common_text[i]] = i

    #Make the idf weights
    words_ndocs = get_num_docs_with_words(words_common_index, words_list)
    idf = get_idf(ndocs, words_ndocs)

    #Create a table with columns for game id and word weights
    create_command = "CREATE TABLE Summary_words(Id INT PRIMARY KEY AUTO_INCREMENT, game_id INT "
    for i in range(nwords):
        create_command += ", stem_" + words_common_text[i] + " FLOAT"
    create_command += ")"
    print create_command
    cur.execute(create_command)

    #Set up the basics of the insert command
    insert_base_command = "INSERT INTO Summary_words (game_id"
    for i in range(nwords):
        insert_base_command += ", stem_" + words_common_text[i]
    insert_base_command += ") VALUES ("

    #Now, loop over all entries
    for i in range(len(words_list)):
        if i % 1000 == 0:
            print "Finished through ", i

        tf_idf = get_tf_idf(words_common_index,words_list[i], idf)
        
        #Create the rest of the insertion command
        insert_command = insert_base_command + str(game_ids[i])
        for j in range(nwords):
            insert_command += ", "+str(tf_idf[j])
        insert_command += ")"

        cur.execute(insert_command)

    #Create a shorter table for saving the baseline idf values
    cur.execute("DROP TABLE IF EXISTS idf_vals")
    create_command = "CREATE TABLE idf_vals(Id INT PRIMARY KEY AUTO_INCREMENT"
    for i in range(nwords):
        create_command += ", stem_" + words_common_text[i] + " FLOAT"
    create_command += ")"
    print create_command
    cur.execute(create_command)
    insert_command = "INSERT INTO idf_vals("
    for i in range(nwords):
        if i == 0:
            insert_command += "stem_" + words_common_text[0]
        else:
            insert_command += ", stem_" + words_common_text[i]
    insert_command += ") VALUES ("
    for i in range(nwords):
        if i == 0:
            insert_command += str(idf[i])
        else:
            insert_command += ", "+str(idf[i])
    insert_command += ")"
    cur.execute(insert_command)
    
    return


def produce_pickle_of_common_words(words_list, game_ids, cur, output_dir, nwords=1000):
    '''
    Works the same as produce_database_of..., but saves the data to a pair of pickle files
    instead of to the MySQL database, because the number of columns in the array of word values
    is generally too large
    Note that this still creates the idf_vals table in the database
    '''

    #Get the number of documents (=number of indie games)
    ndocs = len(words_list)
    
    print "Getting overall word list.  This may take a little while..."
    all_words = get_all_words_list(words_list)
    words_series = pd.Series(all_words)

    print "Moving on..."
    #Get the 1000 most common words
    words_common = words_series.value_counts()
    words_common_text = words_common.index[:nwords]
    words_common_count = words_common[:nwords]
    print "Total number of words (non-unique): ",len(all_words)
    print "Common words: ",words_common_text
    #Create a dictionary object for sorting out words later
    words_common_index = dict([])
    for i in range(nwords):
        words_common_index[words_common_text[i]] = i

    #Make the idf weights
    words_ndocs = get_num_docs_with_words(words_common_index, words_list)
    idf = get_idf(ndocs, words_ndocs)

    #Make the empty array for holding the tf_idf results
    words_tf_idf = np.zeros([len(words_list), nwords])
    #Make the data matrix
    for i in range(len(words_list)):
        if i % 1000 == 0:
            print "Finished through ", i
            
        words_tf_idf[i] = get_tf_idf(words_common_index,words_list[i], idf)
    
    #Pickle this array
    pickle.dump(words_tf_idf, open(output_dir+"words_tf_idf.pkl", 'wb') )

    #Create a shorter table for saving the baseline idf values
    cur.execute("DROP TABLE IF EXISTS idf_vals")
    create_command = "CREATE TABLE idf_vals(Id INT PRIMARY KEY AUTO_INCREMENT, word VARCHAR(50), idf FLOAT)"
    cur.execute(create_command)
    for i in range(nwords):
        insert_command = "INSERT INTO idf_vals(word) VALUES ('"+word_common_text[i]+"', "+str(idf[i])+")"
        cur.execute(insert_command)

    return


if __name__ == "__main__":
    #Run the whole darn thing to make the database we need
    con = login_mysql('../login.txt')
    
    print "Logged in, let's go..."
    with con:
        cur = con.cursor()
        words_list, game_ids = get_words_from_database(cur)
        print "Data acquired."

        #produce_database_of_common_words(words_list, game_ids, cur, nwords=1000)
        produce_pickle_of_common_words(words_list, game_ids, cur, "../", nwords=1000)

    print "All done!"
