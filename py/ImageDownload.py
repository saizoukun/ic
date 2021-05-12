from io import BytesIO
import os
import logging
import requests
import urllib
from urllib.parse import urlparse
import ssl
from PIL import Image
import time
import threading
from concurrent.futures import ThreadPoolExecutor
import subprocess
import gallery_dl

ssl._create_default_https_context = ssl._create_unverified_context
logger = logging.getLogger(__name__)

class ImageDownload(object):
    def __init__(self, threadCount=10):
        self.userAgent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/603.3.8 (KHTML, like Gecko) Version/10.1.2 Safari/603.3.8"
        self.threadCount = threadCount
        self.executor = ThreadPoolExecutor(max_workers=self.threadCount)


    def imageDownload(self, imageUrl, imgFile, referer="", min_size=600):
        try:
            req = urllib.request.Request(imageUrl)
            if len(referer) == 0:
                req.headers = {
                        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/603.3.8 (KHTML, like Gecko) Version/10.1.2 Safari/603.3.8",
                    }
            else:
                req.headers = {
                        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/603.3.8 (KHTML, like Gecko) Version/10.1.2 Safari/603.3.8",
                        "Referer": f"{referer}",
                    }

            try:
                filename = list(reversed(os.path.splitext(imgFile)))[0]
                logger.debug(f"filename: {filename}")
                if filename == '.mp4':
                    urllib.request.urlretrieve(imageUrl, imgFile,)
                    logger.debug(f"file is movie: {imageUrl}")
                    return True
                else:    
                    raw_img = urllib.request.urlopen(req).read()
            except Exception:
                urllib.request.urlretrieve(imageUrl, imgFile,)
                if os.path.isfile(imgFile):
                    with Image.open(imgFile) as f:
                        if min(f.width, f.height) < min_size:
                            os.remove(imgFile)

                return True

            with Image.open(BytesIO(raw_img)) as f:
                if min(f.width, f.height) >= 320:
                    os.makedirs(os.path.dirname(imgFile), exist_ok=True)
                    f.save(imgFile)
                else:
                    logger.debug(f"file little: {imageUrl}")

            #with open(imgFile, 'wb') as f:
            #    f.write(raw_img)
            return True
        except Exception as e:
            if os.path.isfile(imgFile):
                logger.debug("could not load and delete: "+imageUrl)
                logger.debug(e)
                os.remove(imgFile)
            else:
                logger.debug("could not load: "+imageUrl)
                logger.debug("filename: "+imgFile)
                logger.debug(e)

            return False


    def twitterImageDownload(self, imageUrl, imgFile, referer="https://twitter.com/"):
        if self.imageDownload(imageUrl + ":orig", imgFile, referer=referer) == False:
            logger.info("Downloading orig: None")
            if self.imageDownload(imageUrl + ":large", imgFile, referer=referer) == False:
                logger.info("Downloading large: None")
                return self.imageDownload(imageUrl, imgFile, referer=referer)
        else:
            return True


    def twitterPhotoDownload(self, imageUrl, imgFile, referer="https://twitter.com/"):
        directory = os.path.dirname(imgFile)
        logger.info(f"direcotry: {directory}")
        subprocess.Popen(f'gallery-dl {imageUrl} -d "{directory}"', shell=True)


    def imageDownload2(self, imageUrl, imgFile):
        try:
            opener = urllib.request.build_opener()
            opener.addheaders = [
                ('Referer', "https://www.google.co.jp/"),
                ('User-Agent', self.userAgent),
            ]
            urllib.request.install_opener(opener)
            urllib.request.urlretrieve(imageUrl, imgFile,)
            return True
        except Exception as e:
            logger.error("could not load: "+imageUrl)
            logger.error(e)
            return False


    def imageDownloads(self, download_list, site="", min_size=600):
        download_errors = []
        futures = []

        for imageUrl in download_list:
            logger.debug(f"-> Downloading URL: {imageUrl[0]}, {imageUrl[1]}, {site}")
            base_fqdn = urlparse(imageUrl[0]).hostname
            if "pbs.twimg.com" in base_fqdn:
                future = self.executor.submit(self.twitterImageDownload, imageUrl[0], imageUrl[1], referer=f"https://twitter.com/")
                futures.append(future)
            elif "twitter.com" in base_fqdn:
                future = self.executor.submit(self.twitterPhotoDownload, imageUrl[0], imageUrl[1], referer=f"https://twitter.com/")
                futures.append(future)
            elif "porn-images-xxx.com" in base_fqdn:
                future = self.executor.submit(self.imageDownload, imageUrl[0], imageUrl[1], referer="", min_size=min_size)
                futures.append(future)
            elif "stat.ameba.jp" in base_fqdn:
                future = self.executor.submit(self.imageDownload, imageUrl[0], imageUrl[1], referer="", min_size=min_size)
                futures.append(future)
            elif len(site) == 0:
                future = self.executor.submit(self.imageDownload, imageUrl[0], imageUrl[1], referer=imageUrl[0], min_size=min_size)
                futures.append(future)
            else:
                future = self.executor.submit(self.imageDownload, imageUrl[0], imageUrl[1], referer=site, min_size=min_size)
                futures.append(future)

            time.sleep(0.001)

        for future in futures:
            result = future.result()
            if result == False:
                download_errors.append(result)
            time.sleep(0.001)

        return download_errors
    

