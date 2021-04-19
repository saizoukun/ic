import logging
import requests
import urllib
import re
import ssl
import json

ssl._create_default_https_context = ssl._create_unverified_context
logger = logging.getLogger(__name__)

class GoogleSearchMovie(object):
    def __init__(self):
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


    def search(self, keyword, site, maximum, twitterMode=False, faceMode=False):
        if twitterMode:
            query = self.query_gen("twitter @" + keyword, "")
            return self.movie_search_twitter(query, maximum, twitterMode, keyword=keyword), "twitter @" + keyword
        else:
            query = self.query_gen(keyword, site)
            return self.movie_search(query, maximum)

    def query_gen(self, keyword, site):
        # search query generator
        page = 0
        num = 0
        start = ''
        qdr = ['', 'y', 'm', 'w', 'd', 'h', '', '', '', '', '', '', '', '', '']
        while True:
            tbs = "&tbs=hq:h,qdr:{}&tbm=vid".format(qdr[page])
            if 'http' in site:
                params = urllib.parse.urlencode({"as_sitesearch": site, "q": ""})
            else:
                params = urllib.parse.urlencode({"q": keyword})

            if num > 5:
                start = (num-5)*100
                start = f'&start={start}' 

            yield self.GOOGLE_SEARCH_URL + "?" + params + tbs + start
            if page < 5:
                page += 1
            num += 1
            #https://www.google.com/search?q=%E3%82%A2%E3%83%89%E3%83%9E%E3%83%81%E3%83%83%E3%82%AF%E5%A4%A9%E5%9B%BD&hl=ja&tbs=srcf:H4sIAAAAAAAAANOuzC8tKU1K1UvOz1VLSczMqczNL8nMzwPzS8pSi_1SyCoC0bkl-dmU-UBDETUrMzi8pA6vIKi1JLMo3NDIG8wBWdWj3TQAAAA,qdr:w&tbm=vid&prmd=vnsi&sxsrf=ALeKk03AxrmrLduEfWxI0g1cAhbuXHkGUg:1586008598686&source=lnt&sa=X&ved=0ahUKEwiokYq59s7oAhUPwosBHWbpAv0QpwUIHw&biw=1194&bih=721&dpr=2


    def movie_search(self, query_gen, maximum):
        results = []
        total = 0
        while True:
            # search
            query_url = next(query_gen)
            logging.info("url:{}".format(query_url))
            html = self.session.get(query_url).text
            #with open('html.text', 'w', encoding='utf-8') as htmltext:
            #    htmltext.write(html)

            movie_url_list = re.findall(r'(vi\/)([\w=_-]*)(\/default\.jpg)', html)
            logging.info(f'len:{len(movie_url_list)}')

            # add search results
            if not len(movie_url_list):
                break
            else:
                for url in movie_url_list:
                    same = False
                    for res in results:
                        if res[1] == url[1]:
                            same = True
                            break
                    if same == False:
                        results.append(url)

                    if len(results) >= maximum:
                        return results
            total += 1
            logging.info(f"totalCount:{total}")
            logging.info(f"resultsCount:{len(results)}")
            if total >= maximum:
                break
        return results


    def movie_search_twitter(self, query_gen, maximum, twitterMode=True, keyword=""):
        results = set()
        total = 0
        no_count = 10
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
                    ori = ori.get('2003')
                    #logger.info(f"ori: {ori}")

                    ori_page = ori[2].lower()
                    ori_word = ori[3].lower()
                    #logger.info(f"ori_page: {ori_page}")
                    #logger.info(f"ori_word: {ori_word}")
                    if "twitter" in ori_word:
                        name = ori_word[ori_word.find('(')+1:ori_word.rfind(")")]
                        if (keyword in name or keyword in ori_page) and min(height, width) >= 480:
                            logger.info(f"name: {name}")
                            logger.info(f"image_url: {image_url}")
                            image_url_list.append((image_url, keyword))
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


