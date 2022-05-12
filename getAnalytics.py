#!/usr/bin/env python3

from synack import synack
import psycopg2
import subprocess
import sys

n = len(sys.argv)
s1 = synack()

def connect():
    s1.getSessionToken()
    s1.registerAll()
    s1.getAllTargets()

def analytics(codename):
    print(codename)
    analytics = s1.getAnalytics(codename)
    analyticsList = []
    for k in range(len(analytics)):
        analyticsList.append(analytics[k])
    with open(codename+"_analytics.txt", mode='wt', encoding='utf-8') as myfile1:
        print(analyticsList)
        myfile1.write('\n'.join(map(str,analyticsList)))


if n > 1:
    category = "Host"
    connect()
    codenames = s1.getCodenames(category)
    codename = sys.argv[1]
    analytics(codename)
elif n > 2:
    category = sys.argv[2]
    connect()
    codenames = s1.getCodenames(category)
    codename = sys.argv[1]
    analytics(codename)
else:
    print("Usage: %s target category" % (sys.argv[0]))
