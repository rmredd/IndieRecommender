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


if __name__ == '__main__':
    print_urllist()
