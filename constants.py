# -*- coding: utf-8 -*-

"""
Colors, error messages, Twitter account IDs.
"""


class COLOR:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class DEBUG:  # These should probably be all True or all False at this time.
    BOT = False
    DB = False
    ITEM = False


ERROR_MESSAGES = [
    'Didn\'t work.',
    'Nice try, but that didn\'t work.',
    'Nice try, but you can\'t do that.',
    'Oops, can\'t do that.',
    'Oops, didn\'t work.',
    'Oops, try something else.',
    'Sorry, you can\'t do that.',
    'Sorry, you\'ll have to try something else.',
    'That can\'t be done.',
    'That didn\'t work.',
    'That doesn\'t seem to do anything.',
    'Try something else.',
    'Try something else, that didn\'t seem to work.',
    'You can\'t do that.',
    'That didn\'t work. Tip: try "look around" to see what\'s nearby.',
    'Hmm, nothing happened. Tip: try "inspect" to examine things more closely.',
    'That didn\'t seem to work. Tip: say "check inventory" to see what you\'re carrying.',
    'Nothing happened. Tip: you can "go to" places you\'ve discovered.',
    'That didn\'t work. Tip: try "pick up" to grab items you find.',
    'Hmm, try something else. Tip: "talk to" characters you meet to learn more.',
    'That can\'t be done. Tip: try "use X on Y" to combine items with things.',
    'Nothing happened. Tip: some things can be opened — try "open" if you see a container.',
]

LILT = '109795611970306358'
LILTBUILDER = '_'
MKNEPPRATH = '231610'  # FIXME: 60930??
