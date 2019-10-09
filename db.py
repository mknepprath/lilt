# -*- coding: utf-8 -*-

# External
import json
import os
import psycopg2
from urllib import parse

# Internal
from constants import COLOR, DEBUG


# Initialize PostgreSQL database
parse.uses_netloc.append('postgres')
url = parse.urlparse(os.environ['DATABASE_URL'])
psql = psycopg2.connect(
    database=url.path[1:],
    user=url.username,
    password=url.password,
    host=url.hostname,
    port=url.port
)
cursor = psql.cursor()


def select(col1, table, col2, val, position=None, condition=None, quantity='one'):
    query = 'SELECT {col1} FROM {table} WHERE {col2}=\'{val}\''.format(
        col1=col1,
        table=table,
        col2=col2,
        val=val
    )

    if position:
        # Append position and condition if position is provided.
        query += ' AND position=\'{p}\' AND condition'.format(p=position)
        query += ' IS NULL;' if not condition else '=\'{condition}\';'.format(
            condition=json.dumps(condition)
        )

    cursor.execute(query)

    if quantity == 'one':
        o = cursor.fetchone()

        if DEBUG.DB:
            print(COLOR.BLUE + 'Returning ' +
                  'one.' if o else 'None.' + COLOR.END)

        return o[0] if o else o  # o would be None here. Passing it through.
    else:
        o = cursor.fetchall()

        if DEBUG.DB:
            print(COLOR.BLUE + 'Returning all:' + COLOR.END, o)

        return o


def update_user(val1, user_id, col='inventory'):
    if DEBUG.DB:
        print(COLOR.BLUE + 'Updating database.' + COLOR.END)

    query = 'UPDATE users SET {col}=\'{val1}\' WHERE id=\'{id}\';'.format(
        col=col,
        val1=json.dumps(val1) if isinstance(val1, dict) else val1,
        id=user_id
    )

    cursor.execute(query)
    psql.commit()


def delete(table, column, value):
    query = 'DELETE FROM {table} WHERE {column}=\'{value}\';'.format(
        table=table,
        column=column,
        value=value
    )
    cursor.execute(query)
    psql.commit()


def new_user(name, user_id, tweet_id):
    cursor.execute("INSERT INTO users (name, id, last_tweet_id, position, inventory, events) VALUES (%s, %s, %s, %s, %s, %s)",
                   (
                       name,
                       user_id,
                       tweet_id,
                       'start',
                       json.dumps({}),
                       json.dumps({'start': {}})
                   )
                   )
    psql.commit()


# Admin only from this point down... I believe.


def new_move(move, response, position, traits=None):
    if traits == None:
        cursor.execute("INSERT INTO moves (move, response, position) VALUES (%s, %s, %s)",
                       (move, response, position))
        psql.commit()
    else:
        tq = 0
        dbcallstart = "INSERT INTO moves (move, response, position"
        dbdata = (move, response, position)
        for trait in traits:
            tq += 1
            dbcallstart = dbcallstart + ', ' + str(trait)
            if type(traits[trait]) is dict:
                dbdata = dbdata + (json.dumps(traits[trait]),)
            else:
                # must factor if inputting json (json.dumps)
                dbdata = dbdata + (traits[trait],)
        dbcallend = ") VALUES (%s, %s, %s" + ', %s'*tq + ")"
        cursor.execute(dbcallstart + dbcallend, dbdata)
        psql.commit()


def copy_move(ogmove, new_move, position):
    cursor.execute("INSERT INTO moves (move, response, position, item, condition, trigger, drop, travel) SELECT %s, response, position, item, condition, trigger, drop, travel FROM moves WHERE move = %s AND position = %s;", (new_move, ogmove, position))
    psql.commit()


def new_item(traits):
    tq = 0
    dbcallstart = "INSERT INTO items ("
    dbdata = ()
    for trait in traits:
        tq += 1
        if tq == 1:
            dbcallstart = dbcallstart + str(trait)
        else:
            dbcallstart = dbcallstart + ', ' + str(trait)
        # must factor if inputting json (json.dumps)
        dbdata = dbdata + (traits[trait],)
    dbcallend = ") VALUES (%s" + ', %s'*(tq-1) + ")"
    cursor.execute(dbcallstart + dbcallend, dbdata)
    psql.commit()


def do(action, table, data, val=None):
    if action == 'insert':
        # 'INSERT INTO table (x, y, z) VALUES (%s, %s, %s);', ('1','2','3',)
        dbstate = 'INSERT INTO ' + table + ' ('
        # 'INSERT INTO table ('
        tq = 0
        dbdata = ()
        for key in data:
            tq += 1
            if tq == 1:
                dbstate = dbstate + str(key)
                # 'INSERT INTO table (x'
            else:
                dbstate = dbstate + ', ' + str(key)
                # 'INSERT INTO table (x, y, z'
            if type(data[key]) is dict:
                dbdata = dbdata + (json.dumps(data[key]),)
            else:
                dbdata = dbdata + (data[key],)
            # ('1','2','3',)
        dbstate = dbstate + ') VALUES (%s' + ', %s'*(tq-1) + ');'
        # 'INSERT INTO table (x, y, z) VALUES (%s, %s, %s);', ('1','2','3',)
    elif action == 'select':
        # 'SELECT a FROM table WHERE x = %s AND y = %s AND z = %s;',('1','2','3',)
        dbstate = 'SELECT ' + val + ' FROM ' + table + ' WHERE '
        # 'SELECT a FROM table WHERE '
        tq = 0
        dbdata = ()
        for key in data:
            tq += 1
            if tq == 1:
                dbstate = dbstate + str(key) + ' = %s'
                # 'SELECT a FROM table WHERE x = %s'
            else:
                dbstate = dbstate + ' AND ' + str(key) + ' = %s'
                # 'SELECT a FROM table WHERE x = %s AND y = %s AND z = %s'
            if type(data[key]) is dict:
                dbdata = dbdata + (json.dumps(data[key]),)
            else:
                dbdata = dbdata + (data[key],)
            # ('1','2','3',)
        dbstate = dbstate + ';'
        # 'SELECT a FROM table WHERE x = %s AND y = %s AND z = %s;',('1','2','3',)
    elif action == 'delete':
        # 'DELETE FROM table WHERE x = %s AND y = %s AND z = %s;',('1','2','3',)
        dbstate = 'DELETE FROM ' + table + ' WHERE '
        # 'DELETE FROM table WHERE '
        tq = 0
        dbdata = ()
        for key in data:
            tq += 1
            if tq == 1:
                dbstate = dbstate + str(key) + ' = %s'
                # 'DELETE FROM table WHERE x = %s'
            else:
                dbstate = dbstate + ' AND ' + str(key) + ' = %s'
                # 'DELETE FROM table WHERE x = %s AND y = %s AND z = %s'
            if type(data[key]) is dict:
                dbdata = dbdata + (json.dumps(data[key]),)
            else:
                dbdata = dbdata + (data[key],)
            # ('1','2','3',)
        dbstate = dbstate + ';'
        # 'DELETE FROM table WHERE x = %s AND y = %s AND z = %s;',('1','2','3',)
    elif action == 'update':
        # 'UPDATE table SET a = %s WHERE x = %s AND y = %s AND z = %s;'('0','1','2','3',)
        dbstate = 'UPDATE ' + table + ' SET ' + \
            list(val.keys())[0] + ' = %s WHERE '
        # 'UPDATE table SET a = %s WHERE '
        tq = 0
        if type(list(val.values())[0]) is dict:
            dbdata = (json.dumps(list(val.values())[0]),)
        else:
            dbdata = (list(val.values())[0],)
        # ('0',)
        for key in data:
            tq += 1
            if tq == 1:
                dbstate = dbstate + str(key) + ' = %s'
                # 'SELECT a FROM table WHERE x = %s'
            else:
                dbstate = dbstate + ' AND ' + str(key) + ' = %s'
                # 'SELECT a FROM table WHERE x = %s AND y = %s AND z = %s'
            if type(data[key]) is dict:
                dbdata = dbdata + (json.dumps(data[key]),)
            else:
                dbdata = dbdata + (data[key],)
            # ('0','1','2','3',)
        dbstate = dbstate + ';'
        # 'SELECT a FROM table WHERE x = %s AND y = %s AND z = %s;',('0','1','2','3',)
    cursor.execute(dbstate, dbdata)
    if action == 'select':
        return cursor.fetchall()
    else:
        psql.commit()
        return
