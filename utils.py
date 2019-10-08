# -*- coding: utf-8 -*-

"""
Utility/helper functions.
"""

import string
import re


def build_inventory_tweet(inventory):
    # Only used when a player requests their inventory. This creates the
    # inventory string, with quantity indicated by bullet points.

    # Get a list of items in the player's inventory. We will modify this with
    # the quantity.
    items = list(inventory.keys())

    # Loop through each item.
    item_index = 0
    while item_index < len(items):
        # Item quantity (items[item_index] would resolve to item's name).
        item_quantity = inventory[items[item_index]]['quantity']

        # If the quantity is greater than 1, add bullet points (1 per).
        if item_quantity > 1:
            items[item_index] += ' ' + (u'\u2022' * item_quantity)

        # Next item.
        item_index += 1

    # Return a string that contains the list of items.
    return ', '.join(items)


def build_tweet(screen_name, message):
    return '@' + screen_name + ' ' + message


def filter_tweet(tweet):
    # Removes links and lowercases the text.
    modified_tweet = re.sub(r'http\S+', '', tweet).lower()
    # Remove the word "the". Probably a better solution for this...
    modified_tweet = re.sub(r' the ', ' ', modified_tweet)
    # Removes extra spaces.
    modified_tweet = re.sub(' +', ' ', modified_tweet)
    # Removes punctuation.
    modified_tweet = ''.join(ch for ch in modified_tweet if ch not in set(
        string.punctuation)).rstrip()

    return modified_tweet
