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
    'Nice try! Tweet "help" for tips.',
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
]

FAMILIARLILT = '2705523196'
LILTBUILDER = '724754312757272576'
MKNEPPRATH = '15332057'
