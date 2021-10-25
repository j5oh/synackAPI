#!/usr/bin/env python3

from synack import synack
import psycopg2
import subprocess
import os
import sys

s1 = synack()
#s1.Proxy = True
s1.getSessionToken()
s1.getAllTargets()
args = len(sys.argv)
arg_1 = str(sys.argv[1].lower())

if arg_1 == "web":
    category = "Web Application"
    codenames = s1.getCodenames(category)
elif arg_1 == "host":
    category = "Host"
    codenames = s1.getCodenames(category)
elif arg_1 == "mobile":
    category = "mobile"
    codenames = s1.getCodenames(category)
elif arg_1 == "re":
    category = "reverse engineering"
    codenames = s1.getCodenames(category)
elif arg_1 == "hardware":
    category = "hardware"
    codenames = s1.getCodenames(category)
elif arg_1 == "sc":
    category = "source code"
    codenames = s1.getCodenames(category)
else:
    codenames = [arg_1]
    category = s1.getCategory(codenames[0])

# def enumerateSubdomains(netloc):
#     Stuff in here

scope = ()
if category == "Host":
    for i in range(len(codenames)):
        codename = codenames[i]
        print(codename)
        cidrs = s1.getScope(codename)
        ips = s1.getIPs(cidrs)
        targetPath = "./"+codename.upper()+"/"
        if os.path.isdir(targetPath) == False:
            os.mkdir(targetPath)
        filePath = "./"+codename.upper()+"/scope.txt"
        if os.path.exists(filePath):
            os.remove(filePath)
        with open('./'+codename.upper()+'/scope.txt', mode='wt', encoding='utf-8') as myfile:
            myfile.write('\n'.join(ips))
            myfile.write('\n')

if category == "Web Application":
    for i in range(len(codenames)):
        print(codenames[i])
        tupleList = set()
        codename = codenames[i]
        scope = s1.getScope(codename)
        for j in range(len(scope)):
            scheme = scope[j]['scheme']
            netloc = scope[j]['netloc']
            path = scope[j]['netloc']
            port = scope[j]['port']
            wildcard = scope[j]['wildcard']
            tupleList.add(netloc)
            if wildcard == True:
# You can add a subdomain enumeration call here...
# I did. :)
#                subdomains = enumerateSubdomains(netloc)
                tupleList.add(netloc)
            else:
                tupleList.add(netloc)
        scopeList = list(tupleList)
        targetPath = "./"+codename.upper()+"/"
        if os.path.isdir(targetPath) == False:
            os.mkdir(targetPath)
        filePath = "./"+codename.upper()+"/scope.txt"
        if os.path.exists(filePath):
            os.remove(filePath)
        with open('./'+codename.upper()+'/scope.txt', mode='wt', encoding='utf-8') as myfile:
            myfile.write('\n'.join(scopeList))
            myfile.write('\n')
