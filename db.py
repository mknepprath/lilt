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
    port=url.port
)
cur = conn.cursor()

def dbselect(col1, table, col2, val, position=None, condition=None):
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
def dbupdate(val1, val2, col='inventory'):
    if (col != 'inventory') and (col != 'events') and (col != 'attempts'):
        cur.execute("UPDATE users SET " + col + " = %s WHERE id = %s;", (val1, val2))
    elif col == 'attempts':
        cur.execute("UPDATE attempts SET " + col + " = %s WHERE move = %s", (val1, val2))
    else:
        cur.execute("UPDATE users SET " + col + " = %s WHERE id = %s;", (json.dumps(val1), val2))
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
