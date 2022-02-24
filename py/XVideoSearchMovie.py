import logging
import requests
import urllib
import re
import ssl

ssl._create_default_https_context = ssl._create_unverified_context

class XVideoSearchMovie(object):
    def __init__(self):
        self.XVIDEO_SEARCH_URL = "https://www.youtube.com/results"
        self.session = requests.session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:10.0) \
                Gecko/20100101 Firefox/10.0"
            }
        )

    def search(self, keyword, maximum):
        query = self.query_gen(keyword)
        return self.movie_search(query, maximum)

    def query_gen(self, keyword,):
        # search query generator
        page = 0
        #HD以上
        qdr = ['', 'EgYIBRABIAE%253D', 'EgQIBCAB', 'EgYIAxABIAE%253D', 'EgYIAhABIAE%253D', 'EgYIARABIAE%253D', '', '', '', '', '', '', '', '', '']
        #NORMAL
        #qdr = ['', 'EgIIBQ%253D%253D', 'EgQIBBAB', 'EgQIAxAB', 'EgQIAhAB', 'EgQIARAB', '', '', '', '', '', '', '', '', '']
        while True:
            tbs = qdr[page] if qdr[page] == '' else "&sp={}".format(qdr[page])
            params = urllib.parse.urlencode({"search_query": keyword})
            yield self.YOUTUBE_SEARCH_URL + "?" + params + tbs
            if page < 6:
                page += 1

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

            movie_url_list = re.findall(r'(vi\/)([\w=_-]*)(\/hqdefault\.jpg)', html)
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
