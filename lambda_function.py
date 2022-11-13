import json

import bot


def lambda_handler(event, context):

    bot.main()

    return {
        'statusCode': 200,
        'body': json.dumps('Ran bot.py!')
    }
