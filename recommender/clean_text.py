#!/usr/bin/env python

import numpy as np
import re
import nltk
import pandas as pd

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
