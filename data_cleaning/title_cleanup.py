#!/usr/bin/env python

import re
import unicodedata

def remove_trademark_label(text):
    if text[-1] == u'\u2122':
        return text[:len(text)-1]
    else:
        return text

def replace_right_quote(text):
    temptext = unicodedata.normalize('NFKD',text)
    temptext = temptext.encode('ascii','backslashreplace')
    temptext = re.sub(r'\\u2019',"'",temptext)
    #Remove remaining odd characters
    temptext = re.sub(r'\\u\d\d\d\d','',temptext)    
    return temptext
