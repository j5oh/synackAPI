#!/usr/bin/env python3
import OpenSSL
import datetime
import requests
import ssl
import socket

def process_server_cert(url, port=443, name=None):
    if name is None:
        name = url
    process_cert(name, ssl.get_server_certificate((url, port)))

def process_cert(name, cert):
    x509 = OpenSSL.crypto.load_certificate(OpenSSL.crypto.FILETYPE_PEM, cert)
    exp_date = datetime.datetime.strptime(x509.get_notAfter().decode(), '%Y%m%d%H%M%SZ')
    now = datetime.datetime.now()
    
    exp_days = (exp_date-now).days
    print(f'{name}: Expires {exp_date.strftime("%Y-%m-%d")} ({exp_days} days)')
    
    if exp_days <= 7:
        print('****************************************************************')
        print(f'WARNING: {name} is expiring soon! Send Synack a support ticket!')
        print('****************************************************************')

# Platform
process_server_cert('platform.synack.com')

# LP CA cert
process_cert('CA cert', requests.get("https://storage.googleapis.com/wolfacid-prod-public/ca-root.cer").content)

# LP Test
process_server_cert('synack-launchpoint-test.com')

# LP+
process_server_cert('amberjack.synack-lp.com')

# TuPoC
process_server_cert('x1.pe')

# TODO: LP OpenVPN certs in the configuration file (how do we get these?)

