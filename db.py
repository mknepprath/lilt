# -*- coding: utf-8 -*-
import os
import psycopg2
import urlparse
import json
from bot import conn, cur

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
def newmove(move, response, position):
    cur.execute("INSERT INTO moves (move, response, position) VALUES (%s, %s, %s)", (move, response, position))
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
