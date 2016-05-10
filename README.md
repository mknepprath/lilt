Lilt
====

Working with Tweepy, Heroku, and PostgreSQL to build Lilt.

Builder Syntax
----

Example tweet: ```@familiarlilt la do~insert~moves~move~move|look around~response|You're in an empty room.```

*   ```liltadd``` (```la```): Initiates an admin-level PostgreSQL statement. Restricted to [@liltbuilder](http://twitter.com/liltbuilder) and [@mknepprath](http://twitter.com/mknepprath) exclusively.
*   ```do```: Calls the most flexible db function available, allowing one to SELECT FROM, UPDATE, INSERT INTO, and DELETE FROM any table in Lilt's database.
* ```~```: Arguments for the database statement are delineated by tildes.
* ```insert``` (```select```, ```update```, ```delete```): Specifies the type of statement being made.
