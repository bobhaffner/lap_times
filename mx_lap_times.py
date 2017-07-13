#http://live.amasupercross.com/xml/sx/RaceResults.json?

from urllib.request import urlopen
from urllib.error import URLError
import twitter
import time
import pandas as pd
import itertools
import random
import config
import json
from xml.etree import cElementTree as ET
import os
import sys
import logging
import helpers

base_dir = os.path.dirname(os.path.abspath(__file__))

log_path = os.path.join(base_dir, 'log/lap_times.log')

format_str = '%(asctime)-15s %(levelname)s:%(message)s'
datefmt_str = '%m/%d/%Y %I:%M:%S %p'
logging.basicConfig(filename=log_path, format=format_str,
                    datefmt=datefmt_str, level=logging.INFO)

formatter = logging.Formatter(format_str, datefmt=datefmt_str)

stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logging.getLogger().addHandler(stream_handler)


top_x_dict = {0 : 10, 10 : 5, 15 : 3}
positions_to_tweet = 22
max_nr_attempts = 190
sleep_time = random.randint(12,16)
exit_count = 0
last_lap = "0"

race_complete = False

race_strings = ['MAIN','HEAT', 'LCQ', 'SEMI', 'LAST CHANCE QUALIFIER', 'MOTO']  #Last Chance Qualifier

url = "http://americanmotocrosslive.com/xml/mx/RaceResultsWeb.xml?"
info_url = "http://americanmotocrosslive.com/xml/mx/Announcements.json"
race_info_url = 'http://americanmotocrosslive.com/xml/mx/RaceData.json?'

points = { 1 : 25, 2 : 22, 3 : 20, 4 : 18, 5 : 16, 6 : 15, 7 : 14, 8 : 13, 9 : 12, 10 : 11,
           11 : 10, 12 : 9, 13 : 8, 14 : 7, 15 : 6, 16 : 5, 17 : 4, 18 : 3, 19 : 2, 20 : 1}


tweet_names_on_laps = [1, 5, 10, 15, 20]


def get_OA_tweet(riders, class_name):

    top_x = len(riders)

    d = get_moto_one(class_name)

    df = pd.DataFrame(columns=('riderNum', 'Points', 'MotoTwoPos'))

    for x in range(top_x):

        try:
            motoOnePoints = int(d[riders[x].attrib['N']])
        except:
            motoOnePoints = 0
            pass


        motoTwoPoints = points.get(x+1,0)
        df.loc[x] = [riders[x].attrib['N'], (motoOnePoints + motoTwoPoints), (x + 1)]

    df = df.sort(['Points','MotoTwoPos'], ascending=[False,True])
    df = df.reset_index()

    oaTweet = 'OA '

    for x in range(10):
        oaTweet +=  '(' + str((x + 1)) + ')' + df.ix[x].riderNum + '__'

    return oaTweet[:len(oaTweet) - 2]

def get_moto_one(class_name):

    d = {}

    #filePath = "home/haffner/lap/" + class_name
    file_path = os.path.join(base_dir, class_name)

    with open(file_path) as f:
        for line in f:
            (key, val) = line.split(',')
            d[key] = val

    return d


def savetop_x(riders, class_name):

    top_x = len(riders)

    file_path = os.path.join(base_dir, class_name)
    file = open(file_path, "w")

    for x in range(top_x):
        file.write(riders[x].attrib['N'] + ',' + str(points.get(x+1,0)) + '\n')

    file.close()

def getlapTimes():

    tweets = []
    global last_lap
    global positions_to_tweet
    global race_complete

    try:
        data = urlopen(info_url, timeout=3)
    except URLError as e:
        return e, None
    try:

        event_header = json.loads(data.read().decode('utf8'))

        #event_header['S'] = '250 Class Moto #2'

        class_name, event_name, event_number = helpers.get_event_info(event_header["S"].upper(),
                                                                      race_strings)

        if not event_name:  #checking to see if we care about this event
            return "Not Ready", None

    except Exception as e:
        return e, None

    try:
        race_data = urlopen(url, timeout=3)
    except URLError as e:
        return e, None

    try:
        tree = ET.parse(race_data)
        root = tree.getroot()

        riders = root.findall("./B")
        #lap = str(riders[0].attrib['L']).strip()

        length_of_announcements = len(event_header["B"])
        last_annoucement = event_header["B"][length_of_announcements-1]["M"]

        if last_annoucement.find("Session Complete") > -1 and not race_complete: # and 1 == 2:
            race_complete = True
            tweet = u"\U0001F3C1" + " "

            tweets.append(helpers.get_ro_tweet(tweet, riders, positions_to_tweet,3))
            tweets.append(tweet + helpers.get_ro(riders, "F", 10))

            #if this is moto 1 save the results
            if int(event_number) == 1:
                savetop_x(riders, class_name)
            else:
                tweets.append(tweet + get_OA_tweet(riders, class_name))

            return 'OK', tweets

        elif last_annoucement.find("Session Complete") > -1: # and 1 == 2:
            return "Not Ready", None
        else:
            lap = str(riders[0].attrib['L']).strip()
            tweet = 'L' + lap + ' '

        if race_complete: race_complete = False

        #are we still on the same lap the last time we tweeted
        if  lap == last_lap:
            return "Not Ready", None

        #Have we completed a lap yet
        gapTest = riders[1].attrib['G']
        if gapTest == '--.---' or gapTest == '00.000' or gapTest == '-.---' or gapTest == '0.000' or lap == '0':
            return 'Not Ready', None

        #riders that are currently on the lead lap
        ridersOnLeadlap = list(itertools.takewhile(lambda x: x.attrib['G'].find('ap') == -1, riders))

        #get how many 'spaced' riders will be tweeted based on the current lap number
        top_x = helpers.get_top_x(int(lap), top_x_dict)

        #Check to see if we have enough riders on the same lead lap to tweet
        if len(ridersOnLeadlap) < top_x:
            return 'Not Ready', None

        # store lap times for analyis
        helpers.store_lap_results(riders, lap, class_name, event_name, event_number)

        # Get the time left in race
        rd = urlopen(race_info_url)
        d = json.loads(rd.read().decode('utf8'))
        if d['T']:
            time_left = d['T'][3:]
            tweet = tweet + time_left + '  '


        tweet = helpers.get_ro_tweet(tweet, riders, positions_to_tweet, top_x)
        tweets.append(tweet)

        if int(lap) in tweet_names_on_laps:
            tweets.append('L' + lap + ' ' + helpers.get_ro(riders, "F", 10))

        if int(event_number) == 2:
            tweets.append('L' + lap + ' ' + get_OA_tweet(riders, class_name))

        last_lap = lap

        return 'OK', tweets

    except Exception as e:
        return e, None


if __name__ == '__main__':

    if len(sys.argv) < 2:
        tweet_this = False
    else:
        if sys.argv[1].upper() == 'TWEET':
            tweet_this = True
        else:
            tweet_this = False

    if tweet_this == True:
        #the necessary twitter authentification
        my_auth = twitter.OAuth(config.twitter["token"],
                                config.twitter["token_secret"],
                                config.twitter["consumer_key"],
                                config.twitter["consumer_secret"])
        twit = twitter.Twitter(auth=my_auth)

    while True:
        logging.info('Trying...')
        status, tweets = getlapTimes()

        if status == 'OK':
            exit_count = 0
            logging.info(tweets)
            if tweet_this == True:
                for tweet in tweets:
                    logging.info('tweeting - ' + tweet)

                    # Shorten the lap tweet if needed.
                    if len(tweet) > 140:
                        tweet = tweet[:137] + '...'

                    twit.statuses.update(status=tweet[:140]) #lap Times Tweet
        else:
            exit_count = exit_count + 1
            logging.info('Exit Count is ' + str(exit_count) + ' out of ' + str(max_nr_attempts))

        #exit_count keeps track of the number of times that getlapTimes() returns 'Not Ready'
        #This will stop the script when it exceeds max_nr_attempts
        if exit_count > max_nr_attempts:
            exit()

        logging.info(status)

        sleep_time = random.randint(12,16)
        logging.info('Sleeping for ' + str(sleep_time) + ' seconds')
        time.sleep(sleep_time) #puts the app to sleep for a predetermined amount of time
