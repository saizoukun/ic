import logging
from os import access
import requests
import urllib
from urllib.parse import urlparse
from bs4 import BeautifulSoup
import re
import ssl
import datetime
import twitter_scraper
import json
import time
from posts import get_posts
import gallery_dl

ssl._create_default_https_context = ssl._create_unverified_context
logger = logging.getLogger(__name__)
class GoogleSearch(object):
    def __init__(self, myAccountType):
        self.GOOGLE_SEARCH_URL = "https://www.google.co.jp/search"
        self.session = requests.session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/603.3.8 (KHTML, like Gecko) Version/10.1.2 Safari/603.3.8",
#                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:10.0) \
#                    Gecko/20100101 Firefox/10.0"
            }
        )
        self.search_headers = [{
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/603.3.8 (KHTML, like Gecko) Version/10.1.2 Safari/603.3.8",
        },
        {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:10.0) \
                    Gecko/20100101 Firefox/10.0"
        }]

        self.tweet_headers = {
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Referer": f"https://twitter.com/",
            #"Referer": "https://twitter.com/sw.js",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/603.3.8 (KHTML, like Gecko) Version/10.1.2 Safari/603.3.8",
            "X-Twitter-Active-User": "yes",
            #"X-Requested-With": "XMLHttpRequest",
            "Accept-Language": "en-US",
            #"Accept-Language": "ja,en-US;q=0.9,en;q=0.8",
        }
        self.instagram_headers = {
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Referer": "https://www.instagram.com/",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/603.3.8 (KHTML, like Gecko) Version/10.1.2 Safari/603.3.8",
            #"X-Requested-With": "XMLHttpRequest",
            #"Accept-Language": "en-US",
            "Accept-Language": "ja,en-US;q=0.9,en;q=0.8",
            "x-csrftoken": "",
        }
        self.accountType = myAccountType


    def search(self, keyword, site, maximum=100, faceMode=False, siteMode=False, twitterMode=False):
        logger.info(f"twitterMode:{twitterMode}")
        logger.info(f"site:{site}")
        if twitterMode and len(site) == 0:
            if keyword.startswith('@'):
                query = self.query_gen("twitter " + keyword, "", False)
                return self.image_search_twitter(query, maximum, twitterMode, keyword=keyword), "twitter " + keyword
            elif keyword.startswith('#'):
                query = self.query_gen("twitter " + keyword, "", False)
                return self.image_search_twitter(query, maximum, twitterMode, keyword=keyword), "twitter " + keyword
            else:
                query = self.query_gen(keyword, "https://twitter.com/" + keyword + "/", False)
                return self.image_search_twitter(query, maximum, twitterMode, keyword=keyword), "twitter @" + keyword
        elif siteMode:
            return self.image_search_site(site, title=keyword, twitterMode=twitterMode)
        else:
            query = self.query_gen(keyword, site, faceMode)
            return self.image_search(query, maximum, twitterMode, keyword=keyword), keyword


    def linkSearch(self, site, url_link_list, keyword="", limit=0, count=0, twitterMode=False):
        return self.link_search_site(site, url_link_list, keyword=keyword, limit=limit, count=count, twitterMode=twitterMode)


    def query_gen(self, keyword, site, faceMode):
        # search query generator
        page = 0
        qdr = ['', 'y', 'm', 'w', 'd', 'h']
        now = datetime.datetime.now()
        keyword = keyword.replace('　', ' ')
        keyword = keyword.split(' ')
        keyword[0] = '"' + keyword[0] + '"'
        keyword = ' '.join(keyword)
        logger.debug(f"keyword:[{keyword}]")

        while True:
            if page < len(qdr):
                kikan = ""
                tbs = "isz:lt,islt:svga,ic:color,itp:photo,qdr:{}".format(qdr[page])
                if faceMode:
                    tbs = "isz:lt,islt:svga,ic:color,itp:face,qdr:{}".format(qdr[page])
            else:
                tbs = "isz:lt,islt:svga,ic:color,itp:photo"
                if faceMode:
                    tbs = "isz:lt,islt:svga,ic:color,itp:face"

                num = page -len(qdr)
                before = now - datetime.timedelta(weeks=num)
                after = now - datetime.timedelta(weeks=(num+1))
                kikan = "before:{} after:{}".format(before.strftime('%Y-%m-%d'), after.strftime('%Y-%m-%d'))

            if 'http' in site:
                params = urllib.parse.urlencode({"as_sitesearch": site, "q": kikan, "tbm": "isch", "ijn": str(
                    page), "tbs": tbs, "safe": "images", "num": "100"})
            else:
                params = urllib.parse.urlencode({"q": keyword + " " + kikan, "tbm": "isch", "ijn": str(
                    page), "tbs": tbs, "safe": "images", "num": "100"})

            yield self.GOOGLE_SEARCH_URL + "?" + params

            page += 1

        page = 0


    def image_search(self, query_gen, maximum, twitterMode=False, keyword=""):
        logger.info(f"image_search:[{keyword}]")

        results = set()
        total = 0
        no_count = 10

        while True:
            # search
            if '.html' in keyword:
                with open(keyword, 'r', encoding='utf-8') as htmltext:
                    html = htmltext.read()
            else:
                try:
                    query_url = next(query_gen)
                except Exception as e:
                    logging.error(e)
                    break

                logger.info("url:{}".format(query_url))
                html = self.session.get(query_url).text
                #with open('html.text', 'w', encoding='utf-8') as htmltext:
                #    htmltext.write(html)

            if twitterMode:
                image_url_list = re.findall(r'"(https://[\w%,#!&*/\+\?\._-]*\.)(jpg).*"', html)
                twiurl = f'(https://mobile.twitter.com/{keyword}/status/[\w]+|https://twitter.com/{keyword}/status/[\w]+)(\?|")';
                image_url_list += re.findall(twiurl, html)
            else:
                image_url_list = re.findall(r'"(https://[\w%,#!&*/\+\?\._-]*\.)(png|gif|jpg)"', html)

            if len(image_url_list) == 0:
                no_count += 1
                if no_count > 10:
                    break
            else:
                no_count = 0

            # add search results
            image_url_list = [url for url in image_url_list if "auction" not in urlparse(url[0] + url[1]).hostname]
            image_url_list = set(image_url_list)
            results = image_url_list | results
                
            total += 1
            logger.debug(f"totalCount:{total}")
            logger.debug(f"resultsCount:{len(results)}")
            if total >= maximum or len(results) >= maximum:
                break
            elif '.html' in keyword:
                break

        logger.info(f"resultsCount:{len(results)}")
        return set(list(results)[0:maximum])


    def image_search_twitter(self, query_gen, maximum, twitterMode=True, keyword=""):
        logger.info(f"image_search_twitter:[{keyword}]")

        results = set()
        total = 0
        no_count = 10

        keyname = keyword.replace('#', '')
        keyname = keyname.replace('@', '')

        while True:
            # search
            try:
                query_url = next(query_gen)
            except Exception as e:
                logging.error(e)
                break
            
            keyword = keyword.lower()
            logger.info("keyword:{}".format(keyword))
            logger.info("url:{}".format(query_url))
            html = self.session.get(query_url).text

            if twitterMode:
                with open('html.text', 'w', encoding='utf-8') as htmltext:
                    htmltext.write(html)

                if '["GRID_STATE0",' in html:
                    data = json.loads(html[html.find('["GRID_STATE0",'):html.rfind(',"","","",1,[]')] +"]")
                    data = data[2]
                    #print(json.dumps(data))
                    with open('soup.text', 'w', encoding='utf-8') as htmltext:
                        json.dump(data, htmltext, indent=2, ensure_ascii=False)
                else:
                    data = []

                image_url_list = []
                for url in data:
                    image_url = url[1][3][0]
                    if 'g:' in image_url:
                        image_url = image_url[0:image_url.rfind("g:")+1]
                    #logger.info(f"image_url: {image_url}")
                    height = url[1][3][1]
                    width = url[1][3][2]
                    #logger.info(f"height: {height}")
                    #logger.info(f"width: {width}")
                    ori = url[1][9]
                    if ori:
                        ori = ori.get('2003')
                        ori_page = ori[2].lower()
                        ori_word = ori[3].lower()
                        #logger.info(f"ori: {ori}")
                        #logger.info(f"ori_page: {ori_page}")
                        #logger.info(f"ori_word: {ori_word}")
                    else:
                        ori = ""
                        ori_page = ""
                        ori_word = ""
                        
                    if "twitter" in ori_word and min(height, width) >= 480:
                        name = ori_word[ori_word.find('(')+1:ori_word.rfind(")")]
                        logger.debug(f"name: {name}")
                        logger.debug(f"image_url: {image_url}")
                        if keyword.startswith('#'):
                            image_url_list.append((image_url, keyword))
                        elif keyword.startswith('@') and (keyword in name or keyword in ori_page):
                            image_url_list.append((image_url, keyword))
                        elif keyword in name or keyword in ori_page:
                            image_url_list.append((image_url, '@' + keyword))
                        #else:
                            #image_url_list.append((image_url, name))

            else:
                image_url_list = re.findall(r'"(https://[\w%,#!&*/\+\?\._-]*\.)(png|gif|jpg)"', html)

            if len(image_url_list) == 0:
                no_count += 1
                if no_count > 10:
                    break
            else:
                no_count = 0

            # add search results
            image_url_list = [url for url in image_url_list if "auction" not in urlparse(url[0] + url[1]).hostname]
            image_url_list = set(image_url_list)
            results = image_url_list | results
                
            total += 1
            logger.debug(f"totalCount:{total}")
            logger.debug(f"resultsCount:{len(results)}")
            if total >= maximum or len(results) >= maximum:
                break

        logger.info(f"resultsCount:{len(results)}")
        return set(list(results)[0:maximum])


    def image_search_site(self, site, title="", twitterMode=False):
        logger.info(f"image_search_site:[{title}]")

        results = []
        query_url = site
        url_parse = urlparse(query_url)
        base_fqdn = url_parse.netloc
        logging.info("title:{}".format(title))
        logging.info("url:{}".format(query_url))
        html = self.session.get(query_url).text
        with open('html.text', 'w', encoding='utf-8') as htmltext:
            htmltext.write(html)

        soup = BeautifulSoup(html, "lxml")
        if len(title) == 0:
            title = soup.find('title').text
        links = soup.find_all("img")
        image_url_list = []
        if twitterMode:
            image_url_list += re.findall(r'"(https://[\w%,#!&*/\+\?\._-]*\.)(jpg).*"', html)
            image_url_list += re.findall(r'"(https://[\w%,#!&*/\+\?\._-]*\.)(mp4).*"', html)
        else:
            image_url_list += re.findall(r'src="(https://[\w%,#!&*/\+\?\._-]*\.)(jpg|png|mp4|gif)[\w%,#!&*/\+\?\._=-]*"', html)
            href_list = re.findall(r'href="([\w%,:#!&*/\+\?\._-]*\.)(jpg|png|mp4|gif)"', html)
            logger.info(href_list)
            image_url_list += href_list

        for link in links:
            print("link", link)
            src = link.get("src")
            if src:
                #print("src", src)
                src = src if "http" in src else f'{url_parse.scheme}://{url_parse.netloc}' + src
                if twitterMode:
                    # https://pbs.twimg.com/media/EXgQ7pWUYAEmu2Y.jpg:small
                    src = re.findall(r'"(https://[\w%,#!&*/\+\?\._-]*\.)(jpg).*"', src)
                    #src = re.findall(r'"(https://[\w%,#!&*/\+\?\._-]*\.)(jpg).*".+"https://twitter.com/am_s_e/status/\d+[\?lang.*","|","]', src)
                    
                    #print(src)
                    if len(src) > 0:
                        for img in src:
                            if len(img) != 0:
                                image_url_list.append([img[0], ".jpg"])
                else:
                    src = re.findall(r'(http[s]*://[\w%,#!&*/\+\?\.-]*\.)(png|gif|jpg).*', src)
                    #print("src", src)
                    if len(src) > 0:
                        image_url_list.append(src[0])

        # リンクの画像を取得
        links = soup.find_all("a", href=re.compile('(.png|.jpg|.gif|.mp4)'))
        links += soup.find_all("link", href=re.compile('(.png|.jpg|.gif|.mp4)'))

        for link in links:
            src = link.get("href")
            logger.debug(f"src: {src}")
            if "http" not in src:
                continue
            not_same = True
            for url in image_url_list:
                if url == src:
                    not_same = False
                    break
            if not_same: 
                image_url_list.append([src, ""])

        for url in image_url_list:
            same = False
            for res in results:
                if res == url:
                    same = True
                    break
            if same == False:
                href = url[0] if "http" in url[0] else f'{url_parse.scheme}://{url_parse.netloc}' + url[0]
                #logger.info(f"href: {href}")
                url =[href, url[1], '']
                results.append(url)
        logger.info(f"results: {results}")
        logger.info(f"resultsCount:{len(results)}")
        return results, title


    def link_search_site(self, site, url_link_list, keyword="", limit=0, count=0, twitterMode=False):
        logger.info(f"link_search_site:[{keyword}]")

        query_url = site
        logger.info("url:{}".format(query_url))
        base_fqdn = urlparse(query_url).netloc
        html = self.session.get(query_url).text
        #with open('html.text', 'w', encoding='utf-8') as htmltext:
        #    htmltext.write(html)

        soup = BeautifulSoup(html, "lxml")
        if len(keyword) == 0:
            links = soup.find_all("a")
            links += soup.find_all("link")
        else:
            links = soup.find_all("a", href=re.compile(keyword))
            links += soup.find_all("link", href=re.compile(keyword))
        
        #print(links)
        url_list = []
        for link in links:
            logger.debug(f"link: {link}")
            if twitterMode :
                src = link.get("data-expanded-path")
                if src == None:
                    continue
                src = "https://twitter.com" + link.get("data-expanded-path")
            else:
                src = link.get("href")
            logger.debug(f"src: {src}")
            if src is None:
                continue
            elif "#" in src:
                continue
            elif "http" in src:
                if twitterMode == False:
                    link_fqdn = urlparse(src).netloc
                    if base_fqdn != link_fqdn:
                        continue
            else:
                continue
            not_same = True
            for url in url_link_list:
                if url == src:
                    not_same = False
                    break
            if not_same: 
                url_list.append(src)

        url_list = set(url_list)
        url_link_list += url_list
        if limit > count:
            for url in url_list:
                self.link_search_site(url, url_link_list, keyword=keyword, limit=limit, count=count+1)

        #logger.debug(f"results: {url_link_list}")
        logger.info(f"url_list Count:{len(url_link_list)}")

        return url_link_list


    def get_twitter_user_search(self, keyword="", need_keyword="", or_keyword="", not_keyword="", page=25):
        logger.info(f"get_twitter_user_search:[{keyword}]")

        #query_url = "https://mobile.twitter.com/search?"
        query_url = "https://twitter.com/search?"

        if keyword.startswith("#"):
            names = []
            try:
                tweets = twitter_scraper.get_tweets(keyword, pages=page)
                for tweet in tweets:
                    names.append(tweet['username'])
            except Exception as e:
                logger.error(e)
                return []
            names = list(set(names))

        elif keyword.startswith("@"):
            self.get_twitter_name(keyword=keyword)
            return [keyword]

        else:
            search_keyword = []
            if len(keyword) > 0:
                search_keyword.append(keyword)
            if len(need_keyword) > 0:
                search_keyword.append('"' + need_keyword + '"')
            if len(or_keyword) > 0:
                search_keyword.append('(' + or_keyword + ')')
            if len(not_keyword) > 0:
                search_keyword.append('-' + not_keyword)
            
            if len(search_keyword) == 0:
                return

            #search_keyword.append('lang:ja')

            params = {}
            #params['lang'] = 'ja'
            params['q'] = ' '.join(search_keyword)
            params['src'] = 'typed_query'

            params = urllib.parse.urlencode(params)
            query_url = query_url + params
            logger.info(f"url: {query_url}")

            session = requests.session()
            session.headers.update(self.tweet_headers)
            r = session.get(query_url)
            logger.debug(f"response: {r}")
            html = r.text
            with open('html.text', 'w', encoding='utf-8') as htmltext:
                htmltext.write(html)

            soup = BeautifulSoup(html, "lxml")
            names = soup.find_all('span', class_='username u-dir u-textTruncate')
            names = [name.text.strip().replace('@', '') for name in names]
        return names


    def get_twitter_connect_user_search(self, user):
        query_url = "https://twitter.com/" + user
        logger.info("get_twitter_name url:{}".format(query_url))

        session = requests.session()
        session.headers.update(self.tweet_headers)

        get_request = False
        retry = 0
        while get_request == False:
            try: 
                html = session.get(query_url).text
                get_request = True
            except Exception as e:
                retry += 1
                logger.error(e)
                if retry == 3:
                    get_request = True
                time.sleep(1)

        #with open('html.text', 'w', encoding='utf-8') as htmltext:
        #    htmltext.write(html)

        soup = BeautifulSoup(html, "lxml")
        user_id = soup.find('div', class_='ProfileNav')
        if user_id.get('data-user-id'):
            user_id = user_id['data-user-id']

        logger.info(f"user_id: {user_id}")
        after_part = (
            f"include_available_features=1&include_entities=1&include_new_items_bar=true"
        )

        url = f"https://twitter.com/i/profiles/show/{user}/timeline/tweets?"

        query_url = url + after_part

        #query_url = "https://twitter.com/i/connect_people?"
        params = {}
        params['lang'] = 'ja'
        #params['user_id'] = user_id

        params = urllib.parse.urlencode(params)
        #query_url = query_url + '&' + params
        logger.info(f"url: {query_url}")

        html = session.get(query_url).text
        with open('html.text', 'w', encoding='utf-8') as htmltext:
            htmltext.write(html)

        #soup = BeautifulSoup(html, "lxml")
        #names = soup.find_all('span', class_='username u-dir u-textTruncate')
        #names = [name.text.strip().replace('@', '') for name in names]
        #return names


    def get_twitter_name(self, keyword=""):
        query_url = "https://twitter.com/" + keyword
        logger.info("get_twitter_name url:{}".format(query_url))
        account_type = self.accountType.default_account_type
        detail = ""

        get_request = False
        retry = 0
        while get_request == False:
            try: 
                html = self.session.get(query_url).text
                get_request = True
            except Exception as e:
                retry += 1
                logger.error(e)
                if retry == 3:
                    get_request = True
                time.sleep(1)

        #with open('html.text', 'w', encoding='utf-8') as htmltext:
        #    htmltext.write(html)

        soup = BeautifulSoup(html, "lxml")
        name = soup.find('div', class_='fullname')
        detail = soup.find('div', class_='bio')

        name, account_type, detail = self.accountType.get_accounty_type(name, keyword, detail, html)

        #url_link_list = []
        #self.linkSearch(query_url, url_link_list, keyword="https://t.co/", limit=0, twitterMode=True)
        #logger.info(f"-> Found {str(len(url_link_list))} links")
        #logger.debug(f"link: {url_link_list}")
    
        return name, account_type, detail


    def get_twitter_image(self, keyword="", page=25, getRetweet=False):
        keyword = keyword.replace("@", "")
        query_url = "https://twitter.com/" + keyword
        logger.info("get_twitter_image:{}".format(query_url))
        url_link_list = []
        tweets = {}
        user_list = set()
        user_new_list = set()
        try:
            name, account_type, _ = self.get_twitter_name(keyword=keyword)
            if account_type in self.accountType.account_type_ok_class.keys():
                tweets = twitter_scraper.get_tweets(keyword, pages=page)
        except Exception as e:
            logger.error("aaa")
            logger.error(e)
            return query_url, keyword, url_link_list, user_new_list

#        try:
        for tweet in tweets:
            tweetName = tweet['username']
            if tweet['isRetweet']:
                if getRetweet and keyword != tweetName:
                    user_list.add(tweetName)
                logger.debug(f"retweet: {tweetName}")
                continue

            entry = tweet['entries']
            photos = entry.get('photos', [])
            for photo in photos:
                url_link_list.append([photo, tweetName])

            videos = entry.get('videos', [])
            if len(videos) > 0:
                tweetId = tweet['tweetId']
                #logger.info(f'video url:{tweetId}')
                url = '{}/status/{}'.format(query_url, tweetId)
                url_link_list.append([url, tweetName])
            #for video in videos:
                #size = '720x960'
                #videoId = video.get('id')
                #url = 'https://video.twimg.com/ext_tw_video/{}/pu/vid/{}/{}.mp4'.format(tweetId, size, videoId)

        for user_name in user_list:
            _, account_type, _ = self.get_twitter_name(keyword=user_name)
            if self.accountType.check_account_type(account_type):
                user_new_list.add(user_name)

#        except Exception as e:
            
#            logger.error(e)

        url_link_list = set(list(map(tuple, url_link_list)))
        logger.info(f"-> Found {str(len(url_link_list))} links")
        logger.debug(f"link: {url_link_list}")

        return query_url, name, url_link_list, user_new_list


    def get_twitter_image2(self, keyword="", page=25, getRetweet=False):
        query_url = "https://twitter.com/" + keyword
        #logger.info("url:{}".format(query_url))
        url_link_list = []
        tweets = {}
        user_list = set()
        user_new_list = set()
        try:
            name, account_type, _ = self.get_twitter_name(keyword=keyword)
            if account_type in self.accountType.account_type_ok_class.keys():
                tweets = twitter.items()
        except Exception as e:
            logger.error("aaa")
            logger.error(e)
            return query_url, keyword, url_link_list, user_new_list

#        try:
        for tweet in tweets:
            tweetName = tweet['username']
            if tweet['isRetweet']:
                if getRetweet and keyword != tweetName:
                    user_list.add(tweetName)
                logger.debug(f"retweet: {tweetName}")
                continue

            entry = tweet['entries']
            photos = entry.get('photos', [])
            for photo in photos:
                url_link_list.append([photo, tweetName])

            videos = entry.get('videos', [])
            if len(videos) > 0:
                tweetId = tweet['tweetId']
                #logger.info(f'video url:{tweetId}')
                url = '{}/status/{}'.format(query_url, tweetId)
                url_link_list.append([url, tweetName])
            #for video in videos:
                #size = '720x960'
                #videoId = video.get('id')
                #url = 'https://video.twimg.com/ext_tw_video/{}/pu/vid/{}/{}.mp4'.format(tweetId, size, videoId)

        for user_name in user_list:
            _, account_type, _ = self.get_twitter_name(keyword=user_name)
            if self.accountType.check_account_type(account_type):
                user_new_list.add(user_name)

#        except Exception as e:
            
#            logger.error(e)

        url_link_list = set(list(map(tuple, url_link_list)))
        logger.info(f"-> Found {str(len(url_link_list))} links")
        logger.debug(f"link: {url_link_list}")

        return query_url, name, url_link_list, user_new_list


    def get_twitter_user(self, keyword="", page=25):
        query_url = "https://twitter.com/hashtag/" + keyword
        logger.info("url:{}".format(query_url))
        name_list = []
        tweets = {}
        try:
            #tweets = twitter_scraper.get_tweets(urllib.parse.quote(keyword), pages=page)
            session = requests.session()
            session.headers.update(
                {
                    "Accept": "application/json, text/javascript, */*; q=0.01",
                    "Referer": f"https://twitter.com/",
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/603.3.8 (KHTML, like Gecko) Version/10.1.2 Safari/603.3.8",
                    "X-Twitter-Active-User": "yes",
                    "X-Requested-With": "XMLHttpRequest",
                    "Accept-Language": "en-US",
                }
            )

            html = session.get("https://twitter.com/hashtag/" + urllib.parse.quote(keyword)).text
            #with open('html.text', 'w', encoding='utf-8') as htmltext:
            #    htmltext.write(html)
            soup = BeautifulSoup(html, "lxml")
            names = soup.find_all('span', class_='username')
            for name in names:
                print(name.text)
            if name == None:
                return ""
            #r = session.get(url, params={"max_position": last_tweet}, headers=headers)

        except Exception as e:
            logging.error(e)
            return query_url, name_list

        for tweet in tweets:
            name = tweet['username']
            name_list.append(name)

        logger.info(f"-> Found {str(len(name_list))} links")
        logger.debug(f"link: {name_list}")

        return query_url, name_list


    def get_instagram_name(self, keyword=""):
        query_url = "https://www.instagram.com/" + keyword
        logger.info("get_instagram_name url:{}".format(query_url))
        user_info = {}
        user_info['name'] = keyword
        user_info['account_type'] = self.accountType.default_account_type
        user_info['detail'] = ""

        session = requests.session()
        session.headers.update(self.instagram_headers)

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

        js = soup.find("script", text=re.compile("window._sharedData")).text
        data = json.loads(js[js.find("{"):js.rfind("}")+1])
        print(json.dumps(data))
        with open('soup.text', 'w', encoding='utf-8') as htmltext:
            json.dump(data, htmltext, indent=2, ensure_ascii=False)

        user_info['following_count'] = data['entry_data']['ProfilePage'][0]['graphql']['user']['edge_follow']['count']
        user_info['follower_count'] = data['entry_data']['ProfilePage'][0]['graphql']['user']['edge_followed_by']['count']

        user_info['detail'] = data['entry_data']['ProfilePage'][0]['graphql']['user']['biography']
        user_info['name'] = data['entry_data']['ProfilePage'][0]['graphql']['user']['full_name']

        print(user_info)
        return user_info


    def get_instagram_image(self, keyword="", page=25, getRepost=False):
        url_link_list = []
        posts = {}
        user_info = {}
        user_list = set()
        user_new_list = set()
        try:
            if keyword.startswith("#"):
                hashtag = keyword.replace("#", "")
                query_url = f"https://www.instagram.com/explore/tags/{hashtag}"
                posts = get_posts(keyword, pages=page)
            else:
                query_url = f"https://www.instagram.com/{keyword}/"
                user_info = self.get_instagram_name(keyword=keyword)
                if user_info['account_type'] in self.account_type_ok_class.keys():
                    logger.info(f"name: {user_info['name']}")
                    posts = get_posts(keyword, pages=page)

        except Exception as e:
            logger.error(e)
            return query_url, keyword, url_link_list, user_new_list

        try:
            for post in posts:
                postName = post['username']
                if post['isRepost']:
                    if getRepost and keyword != postName:
                        user_list.add(postName)
                    logger.debug(f"repost: {postName}")
                    continue

                entry = post['entries']
                photos = entry.get('photos', [])
                for photo in photos:
                    url_link_list.append([photo, postName])

                videos = entry.get('videos', [])
                if len(videos) > 0:
                    postId = post['postId']
                    #logger.info(f'video url:{postId}')
                    url = '{}/status/{}'.format(query_url, postId)
                    url_link_list.append([url, postName])

            for user_name in user_list:
                _, account_type, _ = self.get_twitter_name(keyword=user_name)
                if account_type == GoogleSearch.account_type_class.get("uraaka") \
                    or (account_type > GoogleSearch.account_type_class.get("glayuser") \
                        and account_type < GoogleSearch.account_type_class.get("niji")):
                    user_new_list.add(user_name)

        except Exception as e:
            logger.error(e)

        url_link_list = set(list(map(tuple, url_link_list)))
        logger.info(f"-> Found {str(len(url_link_list))} links")
        logger.debug(f"link: {url_link_list}")

        return query_url, user_info, url_link_list, user_new_list


    def get_instagram_user(self, keyword="", page=25):
        query_url = f"https://www.instagram.com/explore/tags/{keyword}/"
        name_list = []
        posts = {}
        try:
            posts = get_posts(keyword, pages=page)

        except Exception as e:
            logging.error(e)
            return query_url, name_list

        for post in posts:
            name = post['username']
            name_list.append(name)

        logger.info(f"-> Found {str(len(name_list))} links")
        logger.debug(f"link: {name_list}")

        return query_url, name_list
