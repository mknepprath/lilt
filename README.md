Lilt
====

Working with Tweepy, Heroku, and PostgreSQL to build Lilt, a Twitter text adventure.

Builder Syntax
----

Example ```insert``` tweet: ```@familiarlilt la do~insert~moves~move|look around~response|You're in an empty room.```

* ```liltadd``` (```la```): Initiates an admin-level PostgreSQL statement. Restricted to [@liltbuilder](http://twitter.com/liltbuilder) and [@mknepprath](http://twitter.com/mknepprath) exclusively.
* ```do```: Calls the most flexible db function available, allowing one to SELECT FROM, UPDATE, INSERT INTO, and DELETE FROM any table in Lilt's database.
* ```~```: Arguments for the database statement are delineated by tildes.
* ```insert``` (```select```, ```update```, ```delete```): Specifies the type of statement being made.
* ```moves``` (```items```, ```users```, etc): Specifies the table being manipulated.
* ```move|look around```: Column/value pairs that will be added to the specified table.

Example ```update``` tweet: ```@familiarlilt la do~update~moves~drop|marbles~response|You trip and drop your marbles.```

* ```drop|marbles```: The first column/value pair in an ```update``` statement is the one that will be updated. In this example, the ```drop``` column will be updated where the response to a player's ```move``` is set to "You trip and drop your marbles."

Example ```select``` tweet: ```@familiarlilt la do~select~item~max~name|banana```

* ```trigger```: The value in this column is what will be returned for rows that have the name ```banana```. In this example, it would return ```5```, as that is the max amount of bananas one can carry.

Example ```delete``` tweet: ```@familiarlilt la do~delete~moves~move|look at cat~response|What cat?```

* ```move|look at cat~response|What cat?```: Deletes rows that match these conditions in the table specified.
