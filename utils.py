import string
import re

def mbuild(screen_name, message):
    return '@' + screen_name + ' ' + message
def cleanstr(s):
    s_mod = re.sub(r'http\S+', '', s) # removes links
    s_mod = re.sub(r' the ', ' ', s_mod) #remove the word "the" // probably a better solution for this...
    s_mod = re.sub(' +',' ', s_mod) # removes extra spaces
    ns = ''.join(ch for ch in s_mod if ch not in set(string.punctuation)).lower().rstrip() # removes punctuation
    return ns
