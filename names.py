import numpy as np

names_to_tweet = {
    'Z. Osborne' : ['Wacko', 'Zach', 'Zacho', 'og338'],
    'J. Grant' : ['Grant', '\U0001F60E', 'JG'],
    'E. Tomac' : ['ET', 'Tomac'],
    'J. Martin' : ['JMart', 'Jerma'],
    'A. Martin' : ['\U0001F417', 'AMart', 'Big Al', 'Troll'],
    'B. Baggett' : ['El Chupacabra', 'BB4'],
    'B. Tickle' : ['Tick'],
    'J. Barcia' : ['Bam Bam', 'Bazza'],
    'D. Wilson' : ['Deano'],
    'M. Musquin' : ['Marv'],
    'C. Reed' : ['Reedy', 'Chad'],
    'A. Cianciarulo' : ['AC', 'Baby Jesus'],
    'D. Ferrandis' : ['Senor Fernandez', 'Ferrandis'],
    'P. Nicoletti' : ['Filthy', 'Phil'],
    'T. Bowers' : ['The Bear', '\U0001F43B'],
    'J. Anderson' : ['El Hombre'],
    'A. Ray' : ['Aray'],
    'C. Webb' : ['Coop'],
    'A. Enticknap' : ['722'],
    'T. Enticknap' : ['723']
}


def get_nickname(name):
    nicknames = names_to_tweet.get(name, [name[name.find(' ') + 1:]])
    return nicknames[np.random.randint(0, len(nicknames))]


