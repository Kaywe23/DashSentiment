from tweepy import Stream
from tweepy import OAuthHandler
from tweepy.streaming import StreamListener
import json
from unidecode import unidecode
import itertools
import re
import LokalesMLTraining
import sqlite3
import time
import os
import sys
sys.path.insert(0, os.path.realpath(os.path.dirname(__file__)))
os.chdir(os.path.realpath(os.path.dirname(__file__)))

#connect to database
connection = sqlite3.connect('twitter.db')
c = connection.cursor()

#create table (unix, tweet, sentiment)
def create_table():
    try:
        c.execute("CREATE TABLE IF NOT EXISTS sentiment(unix REAL, tweet TEXT, sentiment REAL)")
        c.execute("CREATE INDEX fast_unix ON sentiment(unix)")
        c.execute("CREATE INDEX fast_tweet ON sentiment(tweet)")
        c.execute("CREATE INDEX fast_sentiment ON sentiment(sentiment)")
        connection.commit()
    except Exception as e:
        print(str(e))
create_table()


#connect to twitter application: consumer key, consumer secret, access token, access secret
ckey="NEeGe0n4IeiNrjnGEsfBCIyPz"
csecret="HTaxaiAniHvUcYxkLc5frXa84QpcvoeFHsvzE8lkSuv5fOYh4W"
atoken="915492425975640065-4Er0fTQ0Xg4F52WZ2OhWqHYPn9uARsi"
asecret="aTXUYeBux0QDLuCcdXKl6ZY9QeyMCl6ZuLVdTmzIGcak2"

#Apostrophes and special symbols for filter
APOSTROPHES = {"'s":"is", "'re":"are", "'ve":"have", "'ll":"will", "'t":"not","'d":"would", "'em":"them"}
regex = r"(?<!\d)[/!$%@=?#+<>^,;:)%](?!\d)"

#Twitter listener
class listener(StreamListener):

    def on_data(self, data):
        try:
            #load twitter json
            data = json.loads(data)

            #decode json
            tweet = unidecode(data['text'])

            # Apostrophes filter lookup
            words = tweet.split()
            reformed = [APOSTROPHES[word] if word in APOSTROPHES else word for word in words]
            reformed = " ".join(reformed)
            tweets = reformed

            # removal of urls
            tweets = re.sub(r'\w+:\/{2}[\d\w-]+(\.[\d\w-]+)*(?:(?:\/[^\s/]*))*', '', tweets)

            # split attached words
            tweets = " ".join(re.findall('[A-Z][^A-Z]*', tweets))

            # standardizing words
            tweets = ''.join(''.join(s)[:2] for _, s in itertools.groupby(tweets))

            # removal of punctuations
            tweet = re.sub(regex, "", tweets, 0)

            # Import Method of DNN Application
            if tweet is not None:
                sentiment = LokalesMLTraining.useDNN(tweet)
                time_ms = data['timestamp_ms']
                #print time_ms, tweet, sentiment
                c.execute("INSERT INTO sentiment (unix, tweet, sentiment) VALUES (?, ?, ?)",
                         (time_ms, tweet, sentiment))
                c.execute(
                    "DELETE FROM sentiment WHERE unix NOT IN (SELECT unix FROM sentiment ORDER BY unix DESC LIMIT 50000)")
                connection.commit()


        except KeyError as e:
            print(str(e))

        return(True)

    def on_error(self, status):
        print status

while True:

    try:
        auth = OAuthHandler(ckey, csecret)
        auth.set_access_token(atoken, asecret)
        twitterStream = Stream(auth, listener())
        twitterStream.filter(track=["a","e","i","o","u"])
    except Exception as e:
        print(str(e))
        time.sleep(5)

