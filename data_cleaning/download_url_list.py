#!/usr/bin/env python

import urllib
import json

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
    type = []
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
            type.append(results[j]['Type'])
            theme.append(results[j]['Theme'])
            players.append(results[j]['Players'])
            platform.append(results[j]['Platform']['text'])
            #Some data points are missing the summary text
            if 'Sumtext' in results[j].keys():
                description.append(results[j]['Sumtext'])
            else:
                description.append('')

    return title, creator, release_date, engine, rating, votes, type, theme, players, platform, description

def cleanup_and_put_in_database(title, creator, release_data, engine, rating, votes, type, theme, players, platform, description):
    '''
    Performs additional cleanup and puts the rest of the data into an SQL table for later retrieval
    '''
    return

if __name__ == '__main__':
    #print_urllist()
    pass
