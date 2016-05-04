# -*- coding: utf-8 -*-
import os
import psycopg2
import urlparse
import json

# init postgresql database
urlparse.uses_netloc.append("postgres")
url = urlparse.urlparse(os.environ["DATABASE_URL"])
conn = psycopg2.connect(
    database=url.path[1:],
    user=url.username,
    password=url.password,
    host=url.hostname,
    port=url.port)
cur = conn.cursor()

def select(col1, table, col2, val, position=None, condition=None):
    if condition != None:
        cur.execute("SELECT " + col1 + " FROM " + table + " WHERE move = %s AND position = %s AND condition = %s;", (val,position,json.dumps(condition)))
    elif position != None:
        cur.execute("SELECT " + col1 + " FROM " + table + " WHERE move = %s AND position = %s AND condition IS NULL;", (val,position))
    else:
        cur.execute("SELECT " + col1 + " FROM " + table + " WHERE " + col2 + " = %s;", (val,))
    o = cur.fetchone()
    if o == None:
        return o
    else:
        return o[0]
def update(val1, val2, col='inventory'):
    if (col != 'inventory') and (col != 'events') and (col != 'attempts'):
        cur.execute("UPDATE users SET " + col + " = %s WHERE id = %s;", (val1, val2))
    elif col == 'attempts':
        cur.execute("UPDATE attempts SET " + col + " = %s WHERE move = %s", (val1, val2))
    else:
        cur.execute("UPDATE users SET " + col + " = %s WHERE id = %s;", (json.dumps(val1), val2))
    conn.commit()
def delete(table, col, val):
    if table == 'console':
        cur.execute("DELETE FROM " + table + " WHERE " + col + " != %s;", (val,))
        conn.commit()
    else:
        cur.execute("DELETE FROM " + table + " WHERE " + col + " = %s;", (val,))
        conn.commit()
def newuser(name, id, tweet_id, position, inventory, events):
    cur.execute("INSERT INTO users (name, id, last_tweet_id, position, inventory, events) VALUES (%s, %s, %s, %s, %s, %s)", (name, id, tweet_id, position, json.dumps(inventory), json.dumps(events)))
    conn.commit()
def newmove(move, response, position, traits=None):
    if traits == None:
        cur.execute("INSERT INTO moves (move, response, position) VALUES (%s, %s, %s)", (move, response, position))
        conn.commit()
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
                dbdata = dbdata + (traits[trait],) # must factor if inputting json (json.dumps)
        dbcallend = ") VALUES (%s, %s, %s" + ', %s'*tq + ")"
        cur.execute(dbcallstart + dbcallend, dbdata)
        conn.commit()
def copymove(ogmove, newmove, position):
    cur.execute("INSERT INTO moves (move, response, position, item, condition, trigger, drop, travel) SELECT %s, response, position, item, condition, trigger, drop, travel FROM moves WHERE move = %s AND position = %s;", (ogmove, newmove, position))
    conn.commit()
def newitem(traits):
    tq = 0
    dbcallstart = "INSERT INTO items ("
    dbdata = ()
    for trait in traits:
        tq += 1
        if tq == 1:
            dbcallstart = dbcallstart + str(trait)
        else:
            dbcallstart = dbcallstart + ', ' + str(trait)
        dbdata = dbdata + (traits[trait],) # must factor if inputting json (json.dumps)
    dbcallend = ") VALUES (%s" + ', %s'*(tq-1) + ")"
    cur.execute(dbcallstart + dbcallend, dbdata)
    conn.commit()
def storeerror(move, position):
    attempt = dbselect('attempts', 'attempts', 'move', move, position)
    if attempt == None:
        cur.execute("INSERT INTO attempts (move, position, attempts) VALUES (%s, %s, %s)", (str(move),str(position),1))
        conn.commit()
    else:
        dbupdate(attempt+1, move, 'attempts')
    return "Stored the failed attempt for future reference."
def log(rec, s):
    if rec:
        cur.execute("INSERT INTO console (log, time) VALUES (%s, 'now')", (str(s),))
        conn.commit()
        print str(s)
        return
    else:
        pass
