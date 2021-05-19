import logging
import time
import mechanize
import requests
import http.cookiejar
import json
import re
from bs4 import BeautifulSoup


logger = logging.getLogger(__name__)

class MechanizeDriver(object):
    def __init__(self):
        self.WAIT_TIME = 1
        self.browser = mechanize.Browser()
        self.referer = ""
        cj = http.cookiejar.LWPCookieJar()
        self.browser.set_cookiejar(cj)
        self.browser.set_handle_robots(False)


    def reqestUrl(self, url):
        try:
            logger.info(f"url: {url}")
            self.browser.open(url, timeout=self.WAIT_TIME)
            self.referer = url
        except Exception as e:
            logger.error(f"File Not load: {url}")
            logger.error(e)


    def closeBrowser(self, url):
        try:
            self.browser.close()
        except Exception as e:
            logger.error(e)


    def getSouce(self, url=""):
        try:
            if len(url) > 0:
                self.reqestUrl(url)
            response = self.browser.response()
            logger.info(response.geturl())
            logger.info(response.info())
            html = response.read().decode()
            link = self.browser.find_link()
            logger.info(link)

            logger.info(f"html: {html}")
            soup = BeautifulSoup(html, "lxml")
            logger.info(f"soup: {soup.text}")
            js = soup.find("script", text=re.compile("window._sharedData")).text
            logger.info(f"js: {js}")
            data = json.loads(js[js.find("{"):js.rfind("}")+1], encoding="utf-8")
            logger.info(f"data: {data}")
            return data
        except Exception as e:
            logger.error("Get Source")
            logger.error(e)


    def reqestlogin(self, url, loginC, passwordC, login, password, buttunC, rememberMeC="remember_me"):
        try:
            logger.info("")
        except Exception as e:
            logger.error(f"File Not load: {url}")
            logger.error(e)


    def twitteReqestlogin(self, login, password):
        try:
            logger.info(f"log in {login}")
            self.browser.addheaders = [("User-agent", "Mozilla/5.0 (Linux; Android 4.1.1; Nexus 7 Build/JRO03S) AppleWebKit/535.19 (KHTML, like Gecko) Chrome/18.0.1025.166 Safari/535.19)")]
            logger.info(f"log in {login}")
            self.browser.open("https://mobile.twitter.com/session/new", timeout=self.WAIT_TIME)
            logger.info(f"log in {login}")
            self.browser.select_form(action="/sessions")
            self.browser["session[username_or_email]"] = login
            self.browser["session[password]"] = password
            ret = self.browser.submit()
            logger.info(f"log in {login}")
            self.referer = self.browser.geturl()
            logger.info(f"logged in")
        except Exception as e:
            logger.error(f"Not login: {login}")
            logger.error(e)


    def twitteSearch(self, keyword):
        try:
            logger.info(f"keyword: {keyword}")
            #link = self.browser.find_link()
            for link in self.browser.links(url_regex="#search"):
                logger.info(f"link: {link}")
                self.browser.follow_link(link)
                response = self.browser.response()
                logger.info(f"URL: {response.geturl()}")
                #logger.info(f"Header: {response.info()}")
                html = response.read().decode()
                #logger.info(f"html: {html}")

                break

            for form in self.browser.forms():
                logger.info(f"form: {form}")
            
            self.browser.select_form(nr=1)
            self.browser["q"] = keyword
            response = self.browser.submit()
            query_url = response.geturl()

            url_link_list = []
            user_new_list = set()
            user_info = {}

            for link in self.browser.links(text_regex="pic.twitter.com"):
                logger.info(f"link: {link}")
                attrs = dict(link.attrs)
                user_id = attrs['data-expanded-path']
                user_id = user_id.split('/')[1]
                link_url = attrs['data-url']
                #self.twitter_getImageUrl(link_url)
                self.browser.follow_link(link)
                response = self.browser.response()
                logger.info(f"URL: {response.geturl()}")
                #logger.info(f"html: {response.read()}")
                #html = self.browser.viewing_html()
                #logger.info(f"html: {html}")


                url_link_list.append([link_url, user_id])

            for link in self.browser.links(text_regex="twitter.com"):
                logger.info(f"Other link: {link}")


            url_link_list = set(list(map(tuple, url_link_list)))
            logger.info(f"-> Found {str(len(url_link_list))} links")
            #logger.info(f"link: {url_link_list}")

            #soup = BeautifulSoup(html, "lxml")
            #with open('soup.text', 'w', encoding='utf-8') as htmltext:
            #    htmltext.write(soup.text)
            #logger.info(f"soup: {soup.text}")
            #form= soup.find("form").text
            #logger.info(f"form: {form.text}")
            
            return query_url, user_info, url_link_list, user_new_list

        except Exception as e:
            logger.error(f"Not keyword: {keyword}")
            logger.error(e)


    def twitter_getImageUrl(self, url):
        query_url = url
        logger.info("get_twitter url:{}".format(query_url))
        tweet_headers = {
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Referer": f"https://twitter.com/",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/603.3.8 (KHTML, like Gecko) Version/10.1.2 Safari/603.3.8",
            "X-Twitter-Active-User": "yes",
            "Accept-Language": "en-US",
        }

        session = requests.session()
        session.headers.update(tweet_headers)

        get_request = False
        retry = 0
        while get_request == False:
            try: 
                html = session.get(query_url)
                get_request = True
            except Exception as e:
                retry += 1
                logger.error(e)
                if retry == 3:
                    get_request = True
                time.sleep(1)

        with open('html.text', 'w', encoding='utf-8') as htmltext:
            htmltext.write(html.text)

        soup = BeautifulSoup(html.content, "lxml")
        with open('soup.text', 'w', encoding='utf-8') as htmltext:
            htmltext.write(soup.text)
