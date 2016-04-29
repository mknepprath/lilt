import string
import re

def invbuild(inventory):
    items = list(inventory.keys())
    i = 0
    while i < len(items):
        iq = inventory[items[i]]['quantity'] # item quantity (items[i] would resolve to item's name)
        if iq > 1: # only append quantity info if more than one
            items[i] += ' ' + u'\u2022'*iq
        i += 1
    return ', '.join(items)
def mbuild(screen_name, message):
    return '@' + screen_name + ' ' + message
def cleanstr(s):
    s_mod = re.sub(r'http\S+', '', s) # removes links
    s_mod = re.sub(r' the ', ' ', s_mod) #remove the word "the" // probably a better solution for this...
    s_mod = re.sub(' +',' ', s_mod) # removes extra spaces
    ns = ''.join(ch for ch in s_mod if ch not in set(string.punctuation)).lower().rstrip() # removes punctuation
    return ns
