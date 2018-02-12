export TWITTER_CONSUMER_KEY=8XlUmIKFVFLkGvuf4dkjfOWKw
export TWITTER_CONSUMER_SECRET=vR656As9ZvNIspaKjJCZSV82rnaGhyXrJXhmp9Xr8rZMVbm5wc
export TWITTER_ACCESS_TOKEN=2578652522-fDoF13LOlOnaxqO60z7SgA8FCh0qj0x37423ZzE
export TWITTER_ACCESS_TOKEN_SECRET=yFj5hRXNKqv5X2JVIVSy5MMBnsa6hY2OFdStBUDqGUZm4
export DATABASE_URL=postgres://gnibsiifkyefsh:xYeF5Yifpv8Q7eCzDwRUP8vzQt@ec2-54-83-17-9.compute-1.amazonaws.com:5432/d63nb0hmp6e1va

# pip install --ignore-installed six

# lilt-game::DATABASE=> \t
# Tuples only is on.
# lilt-game::DATABASE=> \a
# Output format is unaligned.
# lilt-game::DATABASE=> \o /Users/mknepprath/GitHub/lilt/out.json
# lilt-game::DATABASE=> select row_to_json(r) from moves as r;
# lilt-game::DATABASE=>

# VS Code - search for end of line brackets in regex mode -
# }($) replace with },

# Add [ ... ] around the whole thing

# https://jsonformatter.curiousconcept.com/s

# find & replace in regex mode
# "{\\"([\s\S]*)\\": \\"([\s\S]*)\\"}"
# {"$1": "$2"}

# select whole lines that contain string - regex ^.*null.*\n

# regex search over newline -
# ,\n  }

# for future... https://stackoverflow.com/questions/39224382/how-can-i-import-a-json-file-into-postgresql
