import math

import requests

from lxml import objectify
import pprint

BASEURL = 'https://server21033.contentdm.oclc.org'  # CONTENTdm backend URL
APIURL = BASEURL + '/dmwebservices/index.php'


def getMetadata(nick, ptr):
    url = (APIURL) + '?q=dmGetItemInfo/%s/%s/json' % (nick, ptr)
    print(url)
    response = requests.get(url)
    return response.json()


def getCpdPages(nick, ptr):
    url = (APIURL) + '?q=dmGetCompoundObjectInfo/%s/%s/json' % (nick, ptr)
    print(url)
    response = requests.get(url)
    return response.json()


def getTotalRec(nick):
    url = (APIURL) + '?q=dmQueryTotalRecs/%s|0/xml' % (nick)
    response = requests.get(url)
    obj = objectify.fromstring(response.content)
    return obj.totalrecs.total


def query(nick, searchstrings, field, sortby, maxrecs, resume):
    url = (APIURL) + '?q=dmQuery/%s/%s/%s/%s/%s/%s/json' % (nick, searchstrings, field, sortby, maxrecs, resume)
    print(url)
    response = requests.get(url)
    return response.json()


def getAllPtr(nick, maxitems=0):
    if maxitems > 0:
        cnt = maxitems
    else:
        cnt = getTotalRec(nick)
        print('found %s records in collection %s...' % (cnt, nick))
    get = 100
    ptrs = []
    iters = math.ceil(cnt / get)
    print(iters)
    for c in range(0, iters+1):
        resume = (c * get) + 1
        print('get %s results starting at %s...' % (get, resume))
        r = query(nick, '*', 'title', 'title', get, resume)
        for record in r['records']:
            ptr = record['pointer']
            ptrs.append(ptr)
    return ptrs


def isCpd(nick, ptr):
    record = getMetadata(nick, ptr)
    file = record['find']

    a = file.split('.')
    if a[1] == 'cpd':
        return True
    else:
        return False
