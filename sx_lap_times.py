#http://live.amasupercross.com/xml/sx/RaceResults.json?

from urllib.request import urlopen
from urllib.error import URLError
import twitter
import time
import itertools
import random
import config
import json
from xml.etree import cElementTree as ET
import sys
import logging
import os
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

url = "http://live.amasupercross.com/xml/sx/RaceResultsWeb.xml?"
info_url = "http://live.amasupercross.com/xml/sx/Announcements.json"
race_info_url = 'http://live.amasupercross.com/xml/sx/RaceData.json?'

bubble_dict = {('450','HEAT') : 4, ('450','SEMI') : 5, ('450','LAST CHANCE QUALIFIER') : 4,
              ('250','HEAT') : 9, ('250', 'LAST CHANCE QUALIFIER') : 4, ('450', 'LCQ') : 4, ('250', 'LCQ') : 4}


tweet_names_on_laps = [1,5,10,15,20]


def get_lap_times():

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

        if last_annoucement.find("Session Complete") > -1 and not race_complete:
            race_complete = True
            tweet = u"\U0001F3C1" + " "

            if event_name != "MAIN":
                bubble_pos = bubble_dict.get((class_name, event_name),-1)
                riders[bubble_pos-1].attrib['N'] = "(" + riders[bubble_pos-1].attrib['N'] + ")"
                tweets.append(helpers.get_ro_tweet(tweet, riders, positions_to_tweet,bubble_pos))
                #tweets.append(tweet)

                #riders[bubble_pos-1].attrib['F'] = "(" + riders[bubble_pos-1].attrib['F'] + ")"
                tweets.append(tweet + helpers.get_ro(riders, "F", bubble_pos))
            else:
                tweets.append(helpers.get_ro_tweet(tweet, riders, positions_to_tweet,3))
                tweets.append(tweet + helpers.get_ro(riders, "F", 10))

            return 'OK', tweets

        elif last_annoucement.find("Session Complete") > -1:
            return "Not Ready", None
        else:
            lap = str(riders[0].attrib['L']).strip()
            tweet = 'L' + lap + "  "

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
            tweet = tweet + '[' + time_left + ']  '


        if event_name != "MAIN": #if we are in a qualifying race
            bubble_pos = bubble_dict.get((class_name, event_name),-1)
            riders[bubble_pos-1].attrib['N'] = "(" + riders[bubble_pos-1].attrib['N'] + ")"

        tweet = helpers.get_ro_tweet(tweet, riders, positions_to_tweet, top_x)
        tweets.append(tweet)

        if int(lap) in tweet_names_on_laps:
            if event_name != "MAIN":
                bubble_pos = bubble_dict.get((class_name, event_name),-1)
                #riders[bubble_pos-1].attrib['F'] = "(" + riders[bubble_pos-1].attrib['F'] + ")"
                tweets.append('L' + lap + ' ' + helpers.get_ro(riders, "F", bubble_pos))
            else:
                tweets.append('L' + lap + ' ' + helpers.get_ro(riders, "F", 10))

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
        my_auth = twitter.OAuth(config.twitter["token"], config.twitter["token_secret"], config.twitter["consumer_key"],
                                config.twitter["consumer_secret"])
        twit = twitter.Twitter(auth=my_auth)

    while True:
        logging.info('Trying...')
        status, tweets = get_lap_times()

        #exit()

        if status == 'OK':
            exit_count = 0
            logging.info(tweets)
            if tweet_this == True:
                for tweet in tweets:
                    logging.info('tweeting - ' + tweet)

                    # Shorten the lap tweet if needed.
                    if len(tweet) > 140:
                        tweet = tweet[:137] + '...'

                    twit.statuses.update(status=tweet) #lap Times Tweet
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