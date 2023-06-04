import ipaddress
from netaddr import IPNetwork
import requests
import re
import os
import json
import base64
from pathlib import Path
import warnings
import operator
import sys
import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
import configparser
import time
import pyotp
from urllib.parse import urlparse

warnings.filterwarnings("ignore")


class synack:
    def __init__(self):
        self.session = requests.Session()
        self.jsonResponse = []
        self.assessments = []
        self.token = ""
        self.notificationToken = ""
        self.url_registered_summary = "https://platform.synack.com/api/targets/registered_summary"
        self.url_scope_summary = "https://platform.synack.com/api/targets/"
        self.url_activate_target = "https://platform.synack.com/api/launchpoint"
        self.url_assessments = "https://platform.synack.com/api/assessments"
        self.url_vulnerabilities = "https://platform.synack.com/api/vulnerabilities"
        self.url_drafts = "https://platform.synack.com/api/drafts"
        self.url_unregistered_slugs = "https://platform.synack.com/api/targets?filter%5Bprimary%5D=unregistered&filter%5Bsecondary%5D=all&filter%5Bcategory%5D=all&sorting%5Bfield%5D=dateUpdated&sorting%5Bdirection%5D=desc&pagination%5Bpage%5D="
        self.url_profile = "https://platform.synack.com/api/profiles/me"
        self.url_analytics = "https://platform.synack.com/api/listing_analytics/categories?listing_id="
        self.url_hydra = "https://platform.synack.com/api/hydra_search/search/"
        self.url_logout = "https://platform.synack.com/api/logout"
        self.url_notification_token = "https://platform.synack.com/api/users/notifications_token"
        self.url_notification_api = "https://notifications.synack.com/api/v2/"
        self.url_transactions = "https://platform.synack.com/api/transactions"
        self.url_lp_credentials = "https://platform.synack.com/api/launchpoint/credentials"
        self.webheaders = {}
        self.configFile = str(Path.home()) + "/.synack/synack.conf"
        self.firefoxProfile = str(Path.home()) + "/.synack/selenium.profile"
        self.config = configparser.ConfigParser()
        self.config.read(self.configFile)
        self.email = self.config["DEFAULT"]["email"]
        self.password = self.config["DEFAULT"]["password"]
        self.login_wait = int(self.config["DEFAULT"]["login_wait"])
        self.login_url = self.config["DEFAULT"]["login_url"]
        self.authySecret = self.config["DEFAULT"]["authy_secret"]
        self.sessionTokenPath = self.config["DEFAULT"].get("session_token_path", "/tmp/synacktoken")
        self.notificationTokenPath = self.config["DEFAULT"].get("notification_token_path", "/tmp/notificationtoken")
        self.connector = False
        self.webdriver = None
        self.headless = False
        # set to false to use the requests-based login
        self.gecko = self.config["DEFAULT"].getboolean("gecko", True)
        self.proxyport = self.config["DEFAULT"].getint("proxyport", 8080)

        ## Set to 'True' for troubleshooting with Burp Suite ##
        self.Proxy = self.config["DEFAULT"].getboolean("proxy", False)

    #########
    def getAuthy(self):
        totp = pyotp.TOTP(self.authySecret)
        totp.digits = 7
        totp.interval = 10
        totp.issuer = "synack"
        return totp.now()

    ## Get Synack platform session token ##
    def getSessionToken(self):
        if Path(self.sessionTokenPath).exists():
            with open(self.sessionTokenPath, "r") as f:
                self.token = f.readline()
            f.close()
        else:
            self.connectToPlatform()
        self.webheaders = {"Authorization": "Bearer " + self.token}
        response = self.try_requests("GET", self.url_profile, 10)
        profile = response.json()
        self.webheaders["user_id"] = profile["user_id"]

    #################################################
    ## Function to attempt requests multiple times ##
    #################################################

    def try_requests(self, func, URL, times, extra=None):
        http_proxy = "http://127.0.0.1:%d" % self.proxyport
        https_proxy = "http://127.0.0.1:%d" % self.proxyport
        proxyDict = {"http": http_proxy, "https": https_proxy}

        url = urlparse(URL)
        scheme = url.scheme
        netloc = url.netloc
        path = url.path
        port = url.port
        platform = "platform.synack"

        if self.Proxy == True:
            for attempt in range(times):
                try:
                    if func == "PUT":
                        putData = json.dumps({"listing_id": extra})
                        newHeaders = dict(self.webheaders)
                        newHeaders["Content-Type"] = "application/json"
                        response = self.session.put(URL, headers=newHeaders, data=putData, proxies=proxyDict, verify=False)
                        if response.status_code == 401 and platform in netloc:
                            self.connectToPlatform()
                            self.getSessionToken()
                        else:
                            return response
                    elif func == "GET":
                        if extra == None:
                            response = self.session.get(URL, headers=self.webheaders, proxies=proxyDict, verify=False)
                            if response.status_code == 401 and platform in netloc:
                                self.connectToPlatform()
                                self.getSessionToken()
                            else:
                                return response
                        else:
                            parameters = {"page": extra}
                            response = self.session.get(URL, headers=self.webheaders, params=parameters, proxies=proxyDict, verify=False)
                            if response.status_code == 401 and platform in netloc:
                                self.connectToPlatform()
                                self.getSessionToken()
                            else:
                                return response
                    elif func == "POST":
                        response = self.session.post(URL, headers=self.webheaders, proxies=proxyDict, json=extra, verify=False)
                        if response.status_code == 401 and platform in netloc:
                            self.connectToPlatform()
                            self.getSessionToken()
                        else:
                            return response
                    elif func == "PATCH":
                        newHeaders = dict(self.webheaders)
                        newHeaders["Content-Type"] = "application/json"
                        # PATCH request does not support `json=` parameter
                        response = self.session.patch(URL, headers=newHeaders, proxies=proxyDict, data=extra, verify=False)
                        if response.status_code == 401 and platform in netloc:
                            self.connectToPlatform()
                            self.getSessionToken()
                        else:
                            return response
                    elif func == "DELETE":
                        response = self.session.delete(URL, headers=self.webheaders, proxies=proxyDict, json=extra, verify=False)
                        if response.status_code == 401 and platform in netloc:
                            self.connectToPlatform()
                            self.getSessionToken()
                        else:
                            return response
                except Exception as err:
                    last_err = err
            raise last_err
        else:
            for attempt in range(times):
                try:
                    if func == "PUT":
                        putData = json.dumps({"listing_id": extra})
                        newHeaders = dict(self.webheaders)
                        newHeaders["Content-Type"] = "application/json"
                        response = self.session.put(URL, headers=newHeaders, data=putData, verify=False)
                        if response.status_code == 401 and platform in netloc:
                            self.connectToPlatform()
                            self.getSessionToken()
                        else:
                            return response
                    elif func == "GET":
                        if extra == None:
                            response = self.session.get(URL, headers=self.webheaders, verify=False)
                            if response.status_code == 401 and platform in netloc:
                                self.connectToPlatform()
                                self.getSessionToken()
                            else:
                                return response
                        else:
                            parameters = {"page": extra}
                            response = self.session.get(URL, headers=self.webheaders, params=parameters, verify=False)
                            if response.status_code == 401 and platform in netloc:
                                self.connectToPlatform()
                                self.getSessionToken()
                            else:
                                return response
                    elif func == "POST":
                        response = self.session.post(URL, headers=self.webheaders, json=extra, verify=False)
                        if response.status_code == 401 and platform in netloc:
                            self.connectToPlatform()
                            self.getSessionToken()
                        else:
                            return response
                    elif func == "PATCH":
                        # PATCH request does not support `json=` parameter
                        newHeaders = dict(self.webheaders)
                        newHeaders["Content-Type"] = "application/json"
                        response = self.session.request("PATCH", URL, headers=newHeaders, data=extra, verify=False)
                        if response.status_code == 401 and platform in netloc:
                            self.connectToPlatform()
                            self.getSessionToken()
                        else:
                            return response
                    elif func == "DELETE":
                        response = self.session.delete(URL, headers=self.webheaders, json=extra, verify=False)
                        if response.status_code == 401 and platform in netloc:
                            self.connectToPlatform()
                            self.getSessionToken()
                        else:
                            return response
                    else:
                        raise ValueError("Choose a real HTTP method.")
                except Exception as err:
                    last_err = err
            raise last_err

    ####################################################
    ## Function to find all occurrences of nested key ##
    ####################################################

    def findkeys(self, node, kv):
        if isinstance(node, list):
            for i in node:
                for x in self.findkeys(i, kv):
                    yield x
        elif isinstance(node, dict):
            if kv in node:
                yield node[kv]
            for j in node.values():
                for x in self.findkeys(j, kv):
                    yield x

    ##############################################
    ## Returns a JSON of all registered targets ##
    ## This must be the first call after object ##
    ## instantiation - it populates the json    ##
    ##############################################
    def getAllTargets(self):
        self.jsonResponse.clear()
        response = self.try_requests("GET", self.url_registered_summary, 10)
        self.jsonResponse[:] = response.json()
        return response.status_code

    ########################################
    ## Returns a list of web or host target codenames
    ## that are (mission only / not mission only)
    ## category: web || host || RE || mobile || sourceCode || hardware
    ## mission_only: True || False
    ########################################
    def getCodenames(self, category, mission_only=False):
        categories = ("web application", "re", "mobile", "host", "source code", "hardware")
        category = category.lower()
        if category == "web":
            category = "web application"
        if category == "re":
            category = "reverse engineering"
        if category == "sourcecode":
            category = "source code"
        if category not in categories:
            raise Exception("Invalid category.")
        targets = []
        for i in range(len(self.jsonResponse)):
            if mission_only == True:
                if self.jsonResponse[i]["vulnerability_discovery"] == False:
                    if self.jsonResponse[i]["category"]["name"].lower() == category.lower():
                        targets.append(self.jsonResponse[i]["codename"])
                    else:
                        continue
                else:
                    continue
            elif mission_only == False:
                if self.jsonResponse[i]["vulnerability_discovery"] == True:
                    if self.jsonResponse[i]["category"]["name"].lower() == category.lower():
                        targets.append(self.jsonResponse[i]["codename"])
                    else:
                        continue
                else:
                    continue
        return targets

    #########################################
    ## This returns the "slug" of a target ##
    ## based on the codename ##
    #########################################

    def getTargetID(self, codename):
        for i in range(len(self.jsonResponse)):
            if self.jsonResponse[i]["codename"].lower() == codename.lower():
                return self.jsonResponse[i]["id"]

    ##################################
    ## This retuens the codemane of ##
    ## a target based on the slug   ##
    ##################################
    def getCodenameFromSlug(self, slug):
        for i in range(len(self.jsonResponse)):
            if self.jsonResponse[i]["id"].lower() == slug.lower():
                return self.jsonResponse[i]["codename"]

    #################################
    ## This private method returns ##
    ## the organization ID         ##
    #################################
    def __getOrgID(self, codename):
        for i in range(len(self.jsonResponse)):
            if self.jsonResponse[i]["codename"].lower() == codename.lower():
                return self.jsonResponse[i]["organization_id"]

    ######################################
    ## This returns the target category ##
    ######################################
    def getCategory(self, codename):
        for i in range(len(self.jsonResponse)):
            if self.jsonResponse[i]["codename"].lower() == codename.lower():
                return self.jsonResponse[i]["category"]["name"]

    #####################################################
    ## This will connect you to the target by codename ##
    #####################################################
    def connectToTarget(self, codename):
        slug = self.getTargetID(codename)
        response = self.try_requests("PUT", self.url_activate_target, 10, slug)
        time.sleep(5)
        return response.status_code

    #####################################################
    ## This will disconnect you from the target        ##
    #####################################################
    def disconnectTarget(self):
        response = self.try_requests("PUT", self.url_activate_target, 10, "")
        time.sleep(5)
        return response.status_code

    ########################################################
    ## This just returns the "real" client name sometimes ##
    ########################################################
    def clientName(self, codename):
        for i in range(len(self.jsonResponse)):
            if self.jsonResponse[i]["codename"].lower() == codename.lower():
                return self.jsonResponse[i]["name"]

    ################################
    ## This gets the target scope ##
    ################################

    @staticmethod
    def parseScope(scopeList):

        results = []

        for i in scopeList:

            scopeRule = i["rule"]
            scopeType = i["scope"]

            port = None
            scopeRule = scopeRule.rstrip("*")
            wildcard = False

            if scopeRule[0] == "*":
                wildcard = True

                scopeRule = ".".join(scopeRule.split(".")[1:])
            else:
                wildcard = True

            if ":" in scopeRule:
                port = scopeRule.split(":")[1].split("/")[0]
                scopeRule = scopeRule.split(":")[0]

            if not scopeRule.startswith("http"):

                if port and port in [8000, 80, 8080]:
                    scopeRule = f"http://{scopeRule}"

                else:
                    scopeRule = f"https://{scopeRule}"

            url = urlparse(scopeRule)

            scopeDict = {
                "scheme": url.scheme,
                "netloc": url.netloc,
                "path": url.path,
                "port": url.port,
                "wildcard": wildcard,
                "fullURI": f"{url.scheme}://{url.netloc}",
            }
            if (scopeType, scopeDict) not in results:
                results.append((scopeType, scopeDict))
        return list(results)

    def getScope(self, codename):
        category = self.getCategory(codename)
        orgID = self.__getOrgID(codename)
        slug = self.getTargetID(codename)
        if category.lower() == "web application":
            scopeURL = f"https://platform.synack.com/api/asset/v2/assets?organizationUid[]={orgID}&listingUid[]={slug}"
            inScopeRules = []
            oosRules = []
            response = self.try_requests("GET", scopeURL, 10)
            jsonResponse = response.json()
            for scopeListing in jsonResponse:

                listingType = scopeListing["listings"][0]["scope"]

                for scopeTuple in self.parseScope(scopeListing["scopeRules"]):
                    scopeType = scopeTuple[0]
                    scopeDict = scopeTuple[1]

                    if scopeType == "in" and listingType == "in":
                        inScopeRules.append(scopeDict)
                    else:
                        oosRules.append(scopeDict)

            return (list(inScopeRules), list(oosRules))
        if category.lower() == "host":
            scopeURL = "https://platform.synack.com/api/targets/" + slug + "/cidrs?page=all"
            cidrs = []
            try:
                response = self.try_requests("GET", scopeURL, 10)
            except requests.exceptions.RequestException as e:
                raise SystemExit(e)
            temp = json.dumps(response.json()["cidrs"]).replace("[", "").replace("]", "").replace('"', "").replace(", ", "\n").split("\n")
            cidrs.extend(temp)
            cidrs = list(set(cidrs))
            return cidrs

    ########################################
    ## This converts CIDR list to IP list ##
    ## This is a much faster method, previous method was causing problems on large hosts ##
    ########################################
    def getIPs(self, cidrs):
        IPs = []
        for i in range(len(cidrs)):
            if cidrs[i] != "":
                for ip in IPNetwork(cidrs[i]):
                    IPs.append(str(ip))
        return IPs

    ##############################################
    ## This gets all of your passed assessments ##
    ##############################################
    def getAssessments(self):
        self.assessments.clear()
        response = self.try_requests("GET", self.url_assessments, 10)
        jsonResponse = response.json()
        for i in range(len(jsonResponse)):
            if jsonResponse[i]["written_assessment"]["passed"] == True:
                self.assessments.append(jsonResponse[i]["category_name"])
            i += 1

    ##########################################################
    ## This gets endpoints from Web Application "Analytics" ##
    ##########################################################
    def getAnalytics(self, codename, status="all"):
        slug = self.getTargetID(codename)
        if status.lower() == "accepted":
            url_analytics = self.url_analytics + slug + "&status=accepted"
        elif status.lower() == "in_queue":
            url_analytics = self.url_analytics + slug + "&status=in_queue"
        elif status.lower() == "rejected":
            url_analytics = self.url_analytics + slug + "&status=rejected"
        else:
            url_analytics = self.url_analytics + slug
        response = self.try_requests("GET", url_analytics, 10)
        jsonResponse = response.json()
        analytics = []
        targetType = self.getCategory(codename)
        if targetType == "Web Application":
            if "value" in jsonResponse:
                for value in range(len(jsonResponse["value"])):
                    for exploitable_location in range(len(jsonResponse["value"][value]["exploitable_locations"])):
                        analyticsDict = {}
                        if jsonResponse["value"][value]["exploitable_locations"][exploitable_location]["type"] == "url":
                            try:
                                URI = urlparse(str(jsonResponse["value"][value]["exploitable_locations"][exploitable_location]["value"]))
                                scheme = URI.scheme
                            except:
                                scheme = "https"
                            ## URL
                            #                                analyticsDict['uri'] = urlparse(str(jsonResponse['value'][value]['exploitable_locations'][exploitable_location]['value']))
                            port = str(URI.port)
                            if port != "None":
                                analyticsDict["port"] = port
                            else:
                                if scheme == "http":
                                    analyticsDict["port"] = "80"
                                elif scheme == "https":
                                    analyticsDict["port"] = "443"
                            analyticsDict["codename"] = codename
                            analyticsDict["vuln_category"] = str(jsonResponse["value"][value]["categories"][0])
                            if len(jsonResponse["value"][value]["categories"]) == 2:
                                analyticsDict["vuln_subcategory"] = str(jsonResponse["value"][value]["categories"][1])
                            else:
                                pass
                            analyticsDict["scheme"] = "URL"
                            try:
                                analyticsDict["protocol"] = URI.scheme
                            except:
                                analyticsDict["protocol"] = "http"
                                pass
                            try:
                                analyticsDict["vuln_location"] = analyticsDict["protocol"] + "://" + URI.netloc + URI.path
                            except:
                                analyticsDict["vuln_location"] = ""
                                pass
                            if status.lower() == "rejected":
                                analyticsDict["status"] = "rejected"
                            else:
                                analyticsDict["status"] = str(
                                    jsonResponse["value"][value]["exploitable_locations"][exploitable_location]["status"]
                                )
                            analytics.append(analyticsDict)
            return analytics
        elif targetType == "Host":
            #'codename', 'vuln_category', 'vuln_subcategory', 'vuln_location', 'type', 'protocol', 'port', 'path', 'status'
            if "value" in jsonResponse:
                for value in range(len(jsonResponse["value"])):
                    for exploitable_location in range(len(jsonResponse["value"][value]["exploitable_locations"])):
                        analyticsDict = {}
                        if jsonResponse["value"][value]["exploitable_locations"][exploitable_location]["type"] == "url":
                            try:
                                URI = urlparse(str(jsonResponse["value"][value]["exploitable_locations"][exploitable_location]["value"]))
                                scheme = URI.scheme
                            except:
                                scheme = "https"
                            ## URL
                            #                                analyticsDict['uri'] = urlparse(str(jsonResponse['value'][value]['exploitable_locations'][exploitable_location]['value']))
                            port = str(URI.port)
                            if port != "None":
                                analyticsDict["port"] = port
                            else:
                                if scheme == "http":
                                    analyticsDict["port"] = "80"
                                elif scheme == "https":
                                    analyticsDict["port"] = "443"
                            analyticsDict["codename"] = codename
                            analyticsDict["vuln_category"] = str(jsonResponse["value"][value]["categories"][0])
                            if len(jsonResponse["value"][value]["categories"]) == 2:
                                analyticsDict["vuln_subcategory"] = str(jsonResponse["value"][value]["categories"][1])
                            else:
                                pass
                            analyticsDict["scheme"] = "URL"
                            try:
                                analyticsDict["protocol"] = URI.scheme
                            except:
                                analyticsDict["protocol"] = "http"
                                pass
                            try:
                                analyticsDict["vuln_location"] = analyticsDict["protocol"] + "://" + URI.netloc + URI.path
                            except:
                                analyticsDict["vuln_location"] = ""
                                pass
                            if status.lower() == "rejected":
                                analyticsDict["status"] = "rejected"
                            else:
                                analyticsDict["status"] = str(
                                    jsonResponse["value"][value]["exploitable_locations"][exploitable_location]["status"]
                                )
                            analytics.append(analyticsDict)
                        elif jsonResponse["value"][value]["exploitable_locations"][exploitable_location]["type"] == "ip":
                            ## IP
                            analyticsDict["codename"] = codename
                            analyticsDict["vuln_category"] = str(jsonResponse["value"][value]["categories"][0])
                            if len(jsonResponse["value"][value]["categories"]) == 2:
                                analyticsDict["vuln_subcategory"] = str(jsonResponse["value"][value]["categories"][1])
                            else:
                                pass
                            analyticsDict["scheme"] = "HOST"
                            analyticsDict["protocol"] = str(
                                jsonResponse["value"][value]["exploitable_locations"][exploitable_location]["protocol"]
                            )
                            analyticsDict["vuln_location"] = str(
                                jsonResponse["value"][value]["exploitable_locations"][exploitable_location]["address"]
                            )
                            analyticsDict["port"] = str(
                                jsonResponse["value"][value]["exploitable_locations"][exploitable_location]["port"]
                            )
                            if status.lower() == "rejected":
                                analyticsDict["status"] = "rejected"
                            else:
                                analyticsDict["status"] = str(
                                    jsonResponse["value"][value]["exploitable_locations"][exploitable_location]["status"]
                                )
                            analytics.append(analyticsDict)
            return analytics

    #############################################
    ## This registers all unregistered targets ##
    #############################################

    def registerAll(self):
        self.getAssessments()
        pageNum = 1
        next_page = True
        unregistered_slugs = []
        while next_page:
            url_slugs = self.url_unregistered_slugs + str(pageNum)
            response = self.try_requests("GET", url_slugs, 10)
            jsonResponse = response.json()
            if len(jsonResponse) != 0:
                for i in range(len(jsonResponse)):
                    if jsonResponse[i]["category"]["name"] in self.assessments:
                        unregistered_slugs.append(str(jsonResponse[i]["slug"]))
                pageNum += 1
            else:
                next_page = False
                pageNum += 1
        for i in range(len(unregistered_slugs)):
            url_register_slug = "https://platform.synack.com/api/targets/" + unregistered_slugs[i] + "/signup"
            data = '{"ResearcherListing":{"terms":1}}'
            response = self.try_requests("POST", url_register_slug, 10, data)
            slug = unregistered_slugs[i]
        self.getAllTargets()
        for i in range(len(unregistered_slugs)):
            codename = self.getCodenameFromSlug(unregistered_slugs[i])
            if codename == None:
                print("Error registerring " + unregistered_slugs[i] + "!")
            else:
                print("Successfully registered " + str(codename))

    ###############
    ## Keepalive ##
    ###############

    def connectToPlatform(self):
        if self.gecko:
            return self.connectToPlatformGecko()
        else:
            return self.connectToPlatformRequests()

    def connectToPlatformRequests(self):
        # Pull a valid CSRF token for requests in login flow
        response = self.try_requests("GET", "https://login.synack.com/", 10)
        # <meta name="csrf-token" content="..."/>
        m = re.search('<meta name="csrf-token" content="([^"]*)"', response.text)
        csrf_token = m.group(1)
        self.webheaders["X-CSRF-Token"] = csrf_token

        # fix broken Incapsula cookies - regression removed
        for cookie_name in self.session.cookies.iterkeys():
            cookie_value = self.session.cookies.get(cookie_name)
            if cookie_value.find("\r") > -1 or cookie_value.find("\n") > -1:
                print("Fixing cookie %s" % cookie_name)
                cookie_value = re.sub("\r\n *", "", cookie_value)
                cookie_obj = requests.cookies.create_cookie(name=cookie_name, value=cookie_value, path="/")
                self.session.cookies.clear(domain="login.synack.com", path="/", name=cookie_name)
                self.session.cookies.set_cookie(cookie_obj)

        data = {"email": self.email, "password": self.password}
        response = self.try_requests("POST", "https://login.synack.com/api/authenticate", 1, data)
        jsonResponse = response.json()
        if not jsonResponse["success"]:
            print("Error logging in: " + jsonResponse)
            return False

        progress_token = jsonResponse["progress_token"]

        data = {"authy_token": self.getAuthy(), "progress_token": progress_token}
        response = self.try_requests("POST", "https://login.synack.com/api/authenticate", 1, data)
        jsonResponse = response.json()

        grant_token = jsonResponse["grant_token"]

        # 2 requests required here to confirm the grant token - once to the HTML page and once to the API
        response = self.try_requests("GET", "https://platform.synack.com/?grant_token=" + grant_token, 1)
        self.webheaders["X-Requested-With"] = "XMLHttpRequest"
        response = self.try_requests("GET", "https://platform.synack.com/token?grant_token=" + grant_token, 1)
        jsonResponse = response.json()
        access_token = jsonResponse["access_token"]

        self.token = access_token
        with open(self.sessionTokenPath, "w") as f:
            f.write(self.token)
        f.close()

        # Remove these headers so they don't affect other requests
        del self.webheaders["X-Requested-With"]
        del self.webheaders["X-CSRF-Token"]

    def connectToPlatformGecko(self):
        isExist = os.path.exists(self.firefoxProfile)
        if not isExist:
            os.makedirs(self.firefoxProfile)
        options = Options()
        options.add_argument("-profile")
        options.add_argument(self.firefoxProfile)
        firefox_capabilities = DesiredCapabilities.FIREFOX
        firefox_capabilities["marionette"] = True

        if self.headless == True:
            options.headless = True
        else:
            options.headless = False
        #        driver = webdriver.Firefox(options=options)
        driver = webdriver.Firefox(capabilities=firefox_capabilities, options=options)
        driver.get(self.login_url)
        assert "Synack" in driver.title
        ## Fill in the email address ##
        email_path = "/html/body/div[2]/div/div/div[2]/form/fieldset/input"
        driver.find_element_by_xpath(email_path).click()
        driver.find_element_by_xpath(email_path).send_keys(self.email)
        ## Fill in the password ##
        password_path = "/html/body/div[2]/div/div/div[2]/form/fieldset/div[1]/input"
        driver.find_element_by_xpath(password_path).click()
        driver.find_element_by_xpath(password_path).send_keys(self.password)
        ## Click the login button ##
        login_path = "/html/body/div[2]/div/div/div[2]/form/fieldset/div[2]/button"
        driver.find_element_by_xpath(login_path).click()
        time.sleep(5)
        ## Hope the authy works! ##
        authy_path = "/html/body/div[2]/div/div/div[2]/form/fieldset/input"
        driver.find_element_by_xpath(authy_path).click()
        driver.find_element_by_xpath(authy_path).send_keys(self.getAuthy())
        authy_submit_path = "/html/body/div[2]/div/div/div[2]/form/fieldset/div[1]/button"
        driver.find_element_by_xpath(authy_submit_path).click()
        while True:
            self.token = driver.execute_script("return sessionStorage.getItem('shared-session-com.synack.accessToken')")
            if isinstance(self.token, str):
                break
        ## Write the session token to /tmp/synacktoken ##
        with open(self.sessionTokenPath, "w") as f:
            f.write(self.token)
        f.close()
        print("Connected to platform.")
        if self.headless == True:
            driver.quit()
        if self.connector == True:
            self.webdriver = driver
        return 0

    ###########
    ## Vulns ##
    ###########

    def getVulns(self, status="accepted"):
        pageNum = 1
        results = []
        while True:
            url_vulnerabilities = self.url_vulnerabilities + "?filters%5Bstatus%5D=" + status + "&page=" + str(pageNum) + "&per_page=5"
            response = self.try_requests("GET", url_vulnerabilities, 10)
            vulnsResponse = response.json()
            if len(vulnsResponse) == 0:
                break
            else:
                results = results + vulnsResponse
                pageNum += 1
        return results

    def getVuln(self, identifier):  # e.g. optimusant-4
        url_vuln = self.url_vulnerabilities + "/" + identifier
        response = self.try_requests("GET", url_vuln, 10)
        vuln_response = response.json()
        return vuln_response

    ###########
    ## Drafts ##
    ###########

    def getDrafts(self):
        pageNum = 1
        results = []
        while True:
            url_drafts = self.url_drafts + "?page=" + str(pageNum) + "&per_page=5"
            response = self.try_requests("GET", url_drafts, 10)
            draftsResponse = response.json()
            if len(draftsResponse) == 0:
                break
            else:
                results = results + draftsResponse
                pageNum += 1
        return results

    def deleteDraft(self, id):
        # careful!!
        url_delete = self.url_drafts + "/" + str(id)
        response = self.try_requests("DELETE", url_delete, 1)
        if response.status_code == 200:
            return True
        else:
            return False

    ###########
    ## Hydra ##
    ###########

    def getHydra(self, codename):
        slug = self.getTargetID(codename)
        pageNum = 1
        hydraResults = []
        while True:
            url_hydra = self.url_hydra + "?page=" + str(pageNum) + "&listing_uids=" + slug + "&q=%2Bport_is_open%3Atrue"
            response = self.try_requests("GET", url_hydra, 10)
            hydraResponse = response.json()
            if len(hydraResponse) == 0:
                break
            else:
                hydraResults = hydraResults + hydraResponse
                pageNum += 1
        return hydraResults

    ###################
    ## Mission stuff ##
    ###################

    ## Poll for missions ##
    ## REMOVED FROM CLASS FILE ##

    ####################
    ## CLAIM MISSIONS ##
    ####################

    ## REMOVED FROM CLASS FILE ##

    ########################
    ## Notification Token ##
    ########################

    def getNotificationToken(self):
        response = self.try_requests("GET", self.url_notification_token, 10)
        try:
            jsonResponse = response.json()
        except:
            jsonResponse = {}
            return 1
        self.notificationToken = jsonResponse["token"]
        with open(self.notificationTokenPath, "w") as f:
            f.write(self.notificationToken)
        return 0

    ############################
    ## Read All Notifications ##
    ############################

    def markNotificationsRead(self):
        if not self.notificationToken:
            self.getNotificationToken()
        readNotifications = self.url_notification_api + "read_all?authorization_token=" + self.notificationToken
        del self.webheaders["Authorization"]
        response = self.try_requests("POST", readNotifications, 10)
        self.webheaders["Authorization"] = "Bearer " + self.token
        try:
            textResponse = str(response.content)
        except:
            return 1
        return 0

    ########################
    ## Read Notifications ##
    ########################

    def pollNotifications(self):
        pageIterator = 1
        breakOuterLoop = 0
        notifications = []
        if not self.notificationToken:
            self.getNotificationToken()
        while True:
            notificationsUrl = (
                self.url_notification_api
                + "notifications?pagination%5Bpage%5D="
                + str(pageIterator)
                + "&pagination%5Bper_page%5D=15&meta=1"
            )
            self.webheaders["Authorization"] = "Bearer " + self.notificationToken
            response = self.try_requests("GET", notificationsUrl, 10)
            self.webheaders["Authorization"] = "Bearer " + self.token
            try:
                jsonResponse = response.json()
            except:
                return 1
            if not jsonResponse:
                break
            for i in range(len(jsonResponse)):
                if jsonResponse[i]["read"] == False:
                    notifications.append(jsonResponse[i])
                else:
                    breakOuterLoop = 1
                    break
            if breakOuterLoop == 1:
                break
            else:
                pageIterator = pageIterator + 1
        return notifications

    #############################
    ## Get Current Target Slug ##
    #############################

    def getCurrentTargetSlug(self):
        response = self.try_requests("GET", self.url_activate_target, 10)
        try:
            jsonResponse = response.json()
        except:
            return 1
        if jsonResponse["slug"]:
            return jsonResponse["slug"]

    ##############
    ## Get ROEs ##
    ##############

    def getRoes(self, slug):
        requestURL = self.url_scope_summary + str(slug)
        response = self.try_requests("GET", requestURL, 10)
        roes = list()
        try:
            jsonResponse = response.json()
        except:
            return 1
        if not jsonResponse["roes"]:
            return roes
        else:
            for i in range(len(jsonResponse["roes"])):
                roes.append(jsonResponse["roes"][i])
            return roes

    ######################
    ## Get Transactions ##
    ######################
    def getTransactions(self):
        pageIterator = 1
        breakOuterLoop = 0
        transactions = []
        while True:
            transactionUrl = self.url_transactions + "?page=" + str(pageIterator) + "&per_page=15"
            response = self.try_requests("GET", transactionUrl, 10)
            try:
                jsonResponse = response.json()
            except:
                return 1
            if not jsonResponse:
                break
            for i in range(len(jsonResponse)):
                if jsonResponse[i]["title"] == "CashOut":
                    if float(jsonResponse[i]["amount"]) < 0:
                        amount = float(jsonResponse[i]["amount"]) * -1
                    else:
                        amount = float(jsonResponse[i]["amount"])
                    ts = datetime.datetime.fromtimestamp(jsonResponse[i]["created_at"])
                    transactions.append(ts.strftime("%Y-%m-%d") + "," + str(amount))
            pageIterator = pageIterator + 1
        return transactions

    ########################
    ## Get LP Credentials ##
    ########################
    def getLPCredentials(self):
        response = self.try_requests("GET", self.url_lp_credentials, 10)
        try:
            creds = response.json()
            creds["openvpn_file"] = base64.b64decode(creds["openvpn_file"])
            return creds
        except:
            return
