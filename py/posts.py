import logging
import re
import ssl
import urllib
import json
import time
from bs4 import BeautifulSoup
from requests_html import HTMLSession, HTML
from datetime import datetime
from urllib.parse import quote

ssl._create_default_https_context = ssl._create_unverified_context
logger = logging.getLogger(__name__)

session = HTMLSession()

def get_posts(query, pages=25):
    """Gets posts for a given user, via the Instagram frontend API."""

    logger.info(f"get_posts: {query}")
    after_part = ""
    if query.startswith("#"):
        hashtag = query.replace("#", "")
        hashtag = quote(hashtag)
        url = f"https://www.instagram.com/explore/tags/{hashtag}"
        referer = f"https://www.instagram.com/explore/tags/{hashtag}"
    else:
        url = f"https://www.instagram.com/{query}/"
        referer = f"https://www.instagram.com/{query}/"
    url += after_part

    headers = {
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Referer": referer,
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/603.3.8 (KHTML, like Gecko) Version/10.1.2 Safari/603.3.8",
        "X-Requested-With": "XMLHttpRequest",
        "Accept-Language": "en-US",
        "x-csrftoken": "",
    }

    def gen_posts(pages):
        logger.info(f"gen_posts: {str(pages)}")
        logger.info(f"gen_posts: {url}")
        userInfo = {}

        r = session.get(url, headers=headers)
        soup = BeautifulSoup(r.content, "lxml")
        js = soup.find("script", text=re.compile("window._sharedData")).text
        data = json.loads(js[js.find("{"):js.rfind("}")+1], encoding="utf-8")
        csrftoken = data["config"]["csrf_token"]

        media_type = ""
        if query.startswith("#"):
            data = data["entry_data"]["TagPage"][0]["graphql"]["hashtag"]
            userInfo["id"] = data["id"]
            userInfo["full_name"] = data["name"]
            media_type = "edge_hashtag_to_media"
        else:
            data = data["entry_data"]["ProfilePage"][0]["graphql"]["user"]
            userInfo["username"] = data["username"]
            userInfo["id"] = data["id"]
            userInfo["full_name"] = data["full_name"]
            userInfo["detail"] = data["biography"]
            userInfo["follower_count"] = data["edge_followed_by"]["count"]
            userInfo["followed_count"] = data["edge_follow"]["count"]
            logger.info(userInfo)
            media_type = "edge_owner_to_timeline_media"

        has_next_page = True
        while pages > 0 and has_next_page:
            try:
                soup = BeautifulSoup(r.content, "lxml")
                if soup.find("script", text=re.compile("window._sharedData")):
                    js = soup.find("script", text=re.compile("window._sharedData")).text
                    data = json.loads(js[js.find("{"):js.rfind("}")+1], encoding="utf-8")
                    if query.startswith("#"):
                        data = data["entry_data"]["TagPage"][0]["graphql"]["hashtag"]
                    else:
                        data = data["entry_data"]["ProfilePage"][0]["graphql"]["user"]
                else:
                    with open('soup.text', 'w', encoding='utf-8') as htmltext:
                        htmltext.write(soup.text)
                    data = json.loads(soup.text, encoding="utf-8")
                    with open('data.json', 'w', encoding='utf-8') as htmltext:
                        json.dump(data, htmltext, indent=2, ensure_ascii=False)
                    if query.startswith("#"):
                        data = data["data"]["hashtag"]
                    else:
                        data = data["data"]["user"]
                    
                page_info = data[media_type]["page_info"]
                data = data[media_type]["edges"]
                #logger.info(json.dumps(data))
            except Exception as e:
                logger.error("aaaaaaaaaa")
                logger.error(soup.text)
                logger.error(e)
                break

            posts = []
            for post in data:
                post = post["node"]
                try:
                    text = post["edge_media_to_caption"]["edges"][0]["node"]["text"]
                except Exception as e:
                    #logger.error(f"post: {post}")
                    logger.error(e)
                    continue

                post_id = post["id"]
                post_name = post["owner"]["username"] if post["owner"].get("username") else post["owner"]["id"]
                post_userid = post["owner"]["id"]
                post_url = post["display_url"]
                if query.startswith("#"):
                    is_repost = False
                else:
                    is_repost = False if post["owner"]["id"] == userInfo["id"] else False
                    
                if post.get("edge_liked_by"):
                    likes = int(post["edge_liked_by"]["count"])
                elif post.get("edge_media_preview_like"):
                    likes = int(post["edge_media_preview_like"]["count"])
                hashtags = [hashtag_node[0].split(' ')[0] for hashtag_node in re.findall("#(.+)(\s|$)", text)]
                #print(hashtags)
                #time = datetime.fromtimestamp(int(post["taken_at_timestamp"]) / 1000.0)

                #TODO 複数枚は？
                photos = [post_url]

                #TODO VIDEOは？
                videos = []

                posts.append(
                    {
                        "postId": post_id,
                        "postUrl": post_url,
                        "userid": post_userid,
                        "username": post_name,
                        "isRepost": is_repost,
                        #"time": time,
                        "text": text,
                        "likes": likes,
                        "entries": {
                            "hashtags": hashtags,
                            "photos": photos,
                            "videos": videos,
                        },
                    }
                )

            for post in posts:
                yield post

            has_next_page = page_info['has_next_page']
            if has_next_page:
                end_cursor = page_info['end_cursor']
                headers['x-csrftoken'] = csrftoken
                next_url = "https://www.instagram.com/graphql/query/"
                variables = {}
                if query.startswith("#"):
                    variables['tag_name'] = hashtag
                    variables['include_reel'] = False
                    variables['include_logged_out'] = True
                else:
                    variables['id'] = post_userid if is_repost == False else userInfo["id"]
                    variables['first'] = 12
                    variables['after'] = end_cursor
                params = {}
                params['query_hash'] = "7437567ae0de0773fd96545592359a6b"
                params['variables'] = json.dumps(variables)
                params = urllib.parse.urlencode(params)
                next_url = next_url + "?" + params
                logger.info(f"next_url: {next_url}")
                time.sleep(0.05)
                r = session.get(next_url, params={}, headers=headers)
            pages += -1

    yield from gen_posts(pages)


# for searching:
#
# https://instagram.com/i/search/timeline?vertical=default&q=foof&src=typd&composed_count=0&include_available_features=1&include_entities=1&include_new_items_bar=true&interval=30000&latent_count=0
# replace 'foof' with your query string.  Not sure how to decode yet but it seems to work.
