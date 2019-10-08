# Lilt

Uses Tweepy, Heroku, and PostgreSQL to build Lilt, a Twitter text adventure.

How To Run:

1. Clone this repo.
1. Install [Homebrew](https://brew.sh) if you haven't yet.
1. Run `brew install postgresql`.
1. `pip3 install psycopg2-binary` (Note: This is why running `pip install -r requirements.txt` will not work - I'm running the `psycopg2-binary` locally, not `psycopg2`)
1. `pip3 install tweepy`
1. `pip3 install urllib3`
1. Export environment variables - `DATABASE_URL` & Twitter auth tokens.
1. Run the app once: `python3 bot.py`, or start the clock: `python3 clock.py`.

NOTE: SOMETIMES `DATABASE_URL` WILL CHANGE. From Heroku's PostgreSQL
administration page:

> Heroku rotates credentials periodically and updates applications where this database is attached.

I believe Heroku would manage this automatically if the database had been set up
under the same app as this bot. In the case of Lilt, however, the database is under a
separate app called "lilt-game". If an error occurs due to a permissions issue,
I will likely need to go to lilt-game -> Resources -> Heroku Postgres -> Settings
and get the new URI from there.

## Builder Syntax

Lilt includes admin functionality for certain Twitter users that allows them to
have full access to Lilt's databases through tweets. Available commands are
detailed below.

Example `insert` tweet: `@familiarlilt la do~insert~moves~move|look around~response|You're in an empty room.`

- `liltadd` (`la`): Initiates an admin-level PostgreSQL statement. Restricted to [@liltbuilder](http://twitter.com/liltbuilder) and [@mknepprath](http://twitter.com/mknepprath) exclusively.
- `do`: Calls the most flexible db function available, allowing one to SELECT FROM, UPDATE, INSERT INTO, and DELETE FROM any table in Lilt's database.
- `~`: Arguments for the database statement are delineated by tildes.
- `insert` (`select`, `update`, `delete`): Specifies the type of statement being made.
- `moves` (`items`, `users`, etc): Specifies the table being manipulated.
- `move|look around`: Column/value pairs that will be added to the specified table.

Example `update` tweet: `@familiarlilt la do~update~moves~drop|marbles~response|You trip and drop your marbles.`

- `drop|marbles`: The first column/value pair in an `update` statement is the one that will be updated. In this example, the `drop` column will be updated where the response to a player's `move` is set to "You trip and drop your marbles."

Example `select` tweet: `@familiarlilt la do~select~item~max~name|banana`

- `trigger`: The value in this column is what will be returned for rows that have the name `banana`. In this example, it would return `5`, as that is the max amount of bananas one can carry.

Example `delete` tweet: `@familiarlilt la do~delete~moves~move|look at cat~response|What cat?`

- `move|look at cat~response|What cat?`: Deletes rows that match these conditions in the table specified.

#### Other Options

Example `copy` tweet: `@familiarlilt la copy~look around~scan room~room`
Creates new move with all the same data as move being copied, so `scan room` would have the same response, condition, etc.
