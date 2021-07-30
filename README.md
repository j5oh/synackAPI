# Library for interacting with Synack API
This is a library and set of scripts that make SRT life a little easier when interacting with the platform from a linux commandline.
* Connect to platform
  * Stay connected to the platform
* Register available targets
* Connect to targets
* Download targets' scope
* Retrieve analytics from `Web Application` and `Host` targets
* Download hydra findings
* Retrieve target specific information:
  * Client names
  * Codenames
  * Slugs
  * Target types
* Enable mission-claiming bots

# Acknowledgement
Thank you Malcolm and Nicolas for helping out!

# Configuration requirements 
## synack.conf
This is a required config file, and is expected to be in the directory ~/.synack/
```
[DEFAULT]
login_wait = 15
login_url = https://login.synack.com
email = your.email@domain.tld
password = your.synack.password
authy_secret = ABCDEFGHIJKLMNOPQRSTUVWXYZ======
```
* login_wait
  * Number of seconds to wait for the platform's website to be loaded before attempting to log in. Can take a while.
* login_url
  * This should stay as is, unless Synack changes something
* email
  * The email address you use to log into the platform
* password
  * The password you use to log into the platform
* authy_secret
  * base32 secret for generating Authy tokens
  * Guillaume Boudreau provide a nice [walk through](https://gist.github.com/gboudreau/94bb0c11a6209c82418d01a59d958c93) for getting this secret
    * Follow the above to get Authy into debug mode, then use [THIS CODE](https://gist.github.com/louiszuckerman/2dd4fddf8097ce89594bb33426ab5e23#ok-thats-nice-but-i-want-to-get-rid-of-authy-now) to get your valid TOTP SECRET!

## requirements.txt
Your best bet to have all required python3 modules is to run `pip3 install -r requirements.txt`. I cannot help troubleshoot any other modules.

# Synack API python3 module

This python3 module provides a class to create objects for interacting with the Synack LP/LP+ platform.
<br>Basic use:
```
from synack import synack

s1 = synack()
s1.getSessionToken()
s1.getAllTargets()
```
## synack()
This method creates an object that can be used to interact with the LP/LP+ platform.

## connectToPlatform()
This method takes connects to the Synack platform and writes the session token to disk. It also stays connected by auto-clicking the alert.

## getSessionToken()
This method reads a file disk location of `synack.tokenPath` and stores the file contents into the `synack.token` variable. If the file does not contain a valid Synack platform authentication token, the rest of this library will not work.

## getAllTargets()
This method pulls down a descriptive JSON on all targets. Most other methods rely on this JSON and should normally be the second function method called.

## getAssessments()
This method returns a list of all Synack assessments that have been completed.

## getCodenames(category, mission_only=False)
This method takes two parameters and returns a list of codenames.

### parameters:
* category `STRING` defines the type of target you're looking for and must be one of the following:
  * "web application"
  * "host"
  * "mobile"
  * "source code"
  * "reverse engineering"
  * "hardware"
* mission_only `BOOLEAN`
  * True: returns targets that only allow SV2M missions
  * False: returns targets that are NOT SV2M only.

## clientName(codename)
This method takes the target codename and returns the client's true name.

## connectToTarget(codename)
This method takes a target codename and connects to it.

## getCategory(codename)
This method takes a target codename and returns what type of assessment the target requires.

## getTargetID(codename)
This method takes a target codename and returns the project slug. This method is generally not used by end users, but rather supports other function methods.

## getCodenameFromSlug(slug)
This method takes a project slug and returns the target codename. This method is generally not used by end users, but rather supports other function methods.

## getScope(codename)
This method takes a codename and returns its scope as a list of dicts.
* `Host` targets return the CIDR notation ranges
* `Web Application` targets return the expanded list of rules:
  * scheme: (http || https)
  * netloc: the "domain" part of the url
  * path: the path of the url
  * wildcard: if the **subdomain** of the url is a wildcard, not the path

```
https://www.example.com/*
*.example.com/path/*

[
  {
    'scheme': 'https',
    'netloc': 'www.example.com',
    'path': '/*',
    'wildcard': False
  },
  {
    'scheme': '',
    'netloc': 'example.com',
    'path': '/path/*',
    'wildcard': True
  }
]
```

## registerAll()
This method registers all unregistered targets
<br>**Thanks Ozgur for most of the leg work :)**

## getAnalytics(codename)
This method takes a codename and returns a list of all endpoints reported in that target's `Analytics` tab.

## getHydra(codename)
This method takes a codename and returns a json of all hydra reported in that target's `Hydra` tab.

## pollMissions()
This method polls the API for available missions and returns a json to send to `claimMission(missionJson)`

## claimMission(missionJson)
This method takes a json from the pollMission() function and attempts to claim available missions based on dollar value, highest to lowest