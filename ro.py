import urllib2
from xml.etree import cElementTree as ET
import subprocess
import sys
import json


def findSameNames(riders):

    names = []
    sameNames = []

    for rider in riders:
        if rider.attrib["F"][3:] in names:
            sameNames.append(rider.attrib["F"][3:])
        names.append(rider.attrib["F"][3:])

    return sameNames

def get_ro(riders, rider_att, top_x, tweetPos=True, posSep="-", sep="__"):

    tweet = ""

    if rider_att == "F":
        sameNames = findSameNames(riders)

    for x in range(top_x):
        rider = riders[x].attrib[rider_att]
        if rider_att == "F":
            rider = rider.replace(". ", "")
            if rider[1:] not in sameNames:
                rider = rider[1:]

        if tweetPos:
            temp =  "P" + str(x + 1) + posSep + rider + sep
        else:
            temp = rider + sep
        tweet+= temp

    return tweet[:-len(sep)]


if __name__ == '__main__':

    if len(sys.argv) < 4:
        print ("Not enough info. Example: python ro.py SX Name 10")
        exit()

    if sys.argv[1].upper() == "MX":
        url = "http://americanmotocrosslive.com/xml/mx/RaceResultsWeb.xml?"
        info_url = "http://americanmotocrosslive.com/xml/mx/Announcements.json"
    elif sys.argv[1].upper() == "SX" or sys.argv[1].upper() == "MEC":
        url = "http://live.amasupercross.com/xml/sx/RaceResultsWeb.xml?"
        info_url = "http://live.amasupercross.com/xml/sx/Announcements.json"
    else:
        print (sys.argv[1] + " is wrong.  Should be MX, SX or MEC")
        exit()

    if sys.argv[2].upper() == "NUM":
        rideAtt = "N"
    elif sys.argv[2].upper() == "NAME":
        rideAtt = "F"
    else:
        print (sys.argv[2] + " is wrong. Should be Name or Num")
        exit()

    try:
        header = urllib2.urlopen(info_url, timeout=3)
    except urllib2.URLError, e:
        print (e)
        exit()

    try:
        race_data = urllib2.urlopen(url, timeout=3)
    except urllib2.URLError, e:
        print (e)
        exit()

    try:

        event_header = json.loads(header.read())
        event_desc = event_header["S"]


        tree = ET.parse(race_data)
        root = tree.get_root()
        riders = root.findall("./B")

        if not sys.argv[3].isdigit():
            top_x = len(riders)
        elif int(sys.argv[3]) > len(riders):
            top_x = len(riders)
        else:
            top_x = int(sys.argv[3])

        tweet = event_desc + "--" + get_ro(riders, rideAtt, top_x, posSep="-", sep=" ")
        print (tweet)

        #process for copying the tweet to the clipboard
        p = subprocess.Popen(['pbcopy'], stdin=subprocess.PIPE)
        p.stdin.write(tweet)
        p.stdin.close()

    except Exception as e:
        print (e)


