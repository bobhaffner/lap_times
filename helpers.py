import re
import pandas as pd
import os

from names import get_nickname

base_dir = os.path.dirname(os.path.abspath(__file__))

def get_event_info(event, race_strings):

    class_name_pattern = re.compile("\d{3}")
    class_name_list = class_name_pattern.findall(event)
    if len(class_name_list) > 0:
        class_name = str(class_name_list[0])
    else:
        class_name = None

    event_name = match_in_list(event, race_strings)

    event_number_pattern = re.compile("(\#\d{1}|\s\d{1})")

    event_number_list = event_number_pattern.findall(event)
    if len(event_number_list) > 0:
        if len(event_number_list[0]) == 2 : event_number = event_number_list[0][1]
    else:
        event_number = None

    return class_name, event_name, event_number


def match_in_list(string, race_strings):

    matching_list = [s for s in race_strings if s in string.upper()]   #[s for s in some_list if "abc" in s]

    if matching_list:
        return matching_list[0]

    return None
    
    
def get_top_x(lap, top_x_dict):
    for k in top_x_dict:
        if lap > k:
            lap_key = k
    return top_x_dict[lap_key]


def get_time(t):

    colon_pos = t.find(':')

    if colon_pos > -1:
        time_split = t.split(':')
        return int(time_split[0]) * 60 + float(time_split[1])
    elif t.find('lap') > -1:
        return -1
    else:
        return float(t)

def string_between_two_chars(string, char_1, char_2):
    string_list = []
    for x in range(0,len(string)):
        if string[x] == char_1:
            char_2_pos = string[x:].find(char_2)
            new_string = string[x + 1:(x + char_2_pos)]
            string_list.append(new_string)

    return string_list


def get_ro(riders, rider_att, top_x, tweet_pos=True, pos_sep="-", sep="__"):

    tweet = ""

    for x in range(top_x):
        rider = riders[x].attrib[rider_att]
        if rider_att == "F":
            rider = get_nickname(rider)

        if tweet_pos:
            temp =  "P" + str(x + 1) + pos_sep + rider + sep
        else:
            temp = rider + sep
        tweet+= temp

    return tweet[:-len(sep)]


def store_lap_results(riders, lap, class_name, event_name, event_number):

    d = {}
    l = []

    for i in range(len(riders)):
        keys = riders[i].keys()
        for k in keys:
            d[k] = riders[i].get(k)
        l.append(d.copy())

    pd.DataFrame(l).to_csv('{}/data/{}_{}_{}_lap_{}.csv'.format(base_dir, class_name, event_name, event_number, lap),
                           index=False)


def get_ro_tweet(tweet, riders, positions_to_tweet, top_x):
    # in MX we can't tweet all the racers and in SX we need to make sure we have at least X
    if len(riders) < positions_to_tweet:
        positions_to_tweet = len(riders)

    for x in range(positions_to_tweet):
        if x == 0:  # if this is the first place rider then no spaces are necessary
            tweet = tweet + riders[x].attrib['N']
        else:
            if x < top_x:  # add gap spaces to these riders
                # get_time() does a rough calculation of gaps and returns a 'space count'
                space_count = int(get_time(riders[x].attrib[
                                             'G'])) + 1
                tweet = tweet + "_" * space_count
                tweet = tweet + riders[x].attrib['N']
            else:  # these rider are outside of the top_x so we just put them in order and separate them by '-'
                if x == top_x:
                    tweet = tweet + ' | ' + riders[x].attrib['N']
                else:
                    tweet = tweet + '-' + riders[x].attrib['N']

    return tweet
