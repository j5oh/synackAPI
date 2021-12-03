#!/usr/bin/env python3

from synack import synack
import psycopg2
import subprocess
import os
import sys

s1 = synack()
s1.getSessionToken()

payouts = s1.getTransactions()
for i in range(len(payouts)):
    print(payouts[i])
