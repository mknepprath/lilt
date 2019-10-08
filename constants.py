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
    'You can\'t do that.',
    'That can\'t be done.',
    'Didn\'t work.',
    'Oops, can\'t do that.',
    'Sorry, you can\'t do that.',
    'That didn\'t work.',
    'Try something else.',
    'Sorry, you\'ll have to try something else.',
    'Oops, didn\'t work.',
    'Oops, try something else.',
    'Nice try, but you can\'t do that.',
    'Nice try, but that didn\'t work.',
    'Try something else, that didn\'t seem to work.'
]

FAMILIARLILT = '2705523196'
LILTBUILDER = '724754312757272576'
MKNEPPRATH = '15332057'
