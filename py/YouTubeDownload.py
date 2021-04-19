import logging
import os
import youtube_dl
import ssl
import pathlib

ssl._create_default_https_context = ssl._create_unverified_context
logger = logging.getLogger(__name__)


class YouTubeDownload(object):
    def __init__(self):
        self.YOUTUBE_DL_URL = "https://www.youtube.com/watch?v="
        self.EXT_MUSIC = 'm4a'
        self.EXT_MOVIE = 'mp4'
        self.YOUTUBE_FORMAT = {self.EXT_MUSIC: 'bestaudio[ext=mp3]/bestaudio[ext=m4a]/bestaudio', self.EXT_MOVIE: 'bestvideo[ext=mp4]'}


    def movieGetTitle(self, movieUrl, format):
        try:
            format = format if len(format) > 0 else self.EXT_MOVIE
            dlformat = self.YOUTUBE_FORMAT[format]
            logger.info(f"downloadingUrl:{movieUrl}")
            ydl_opts = {'format':dlformat}
            with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(self.YOUTUBE_DL_URL + movieUrl, download=False)           
            logger.info(f"downloadingTitle:{info['title']}")
            return info['title']
        except Exception as e:
            logger.error("could not get Title: " + movieUrl)
            logger.error(e)
            return None        


    def movieDowonlod(self, movieUrl, format, movieFile):
        try:
            cwd = os.getcwd()
            baseDir = os.path.dirname(movieFile)
            os.chdir(baseDir)
            dlformat = self.YOUTUBE_FORMAT[format]
            ydl_opts = {'format':dlformat}
            with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                ydl.download([self.YOUTUBE_DL_URL + movieUrl])
            os.chdir(cwd)
            logger.info(f"downloading:{movieUrl}")
            return True
        except Exception as e:
            logger.error("could not load: "+movieUrl)
            logger.error(e)
            return False


    def twitterMovieDowonlod(self, movieUrl, directory, outtmpl):
        try:
            cwd = os.getcwd()
            baseDir = os.path.dirname(directory)
            logger.info(baseDir)
            os.chdir(baseDir)
            ydl_opts = {}
            if len(outtmpl) != 0:
                ydl_opts = {'outtmpl':outtmpl}

            with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                ydl.download([movieUrl])
            os.chdir(cwd)
            logger.info(f"downloading:{movieUrl}")
            return True
        except Exception as e:
            logger.error("could not load: "+movieUrl)
            logger.error(e)
            os.chdir(cwd)
            return False


    def twitterMovieGetTitle(self, movieUrl, outtmpl):
        try:
            ydl_opts = {}
            if len(outtmpl) != 0:
                ydl_opts = {'outtmpl':outtmpl}

            with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(movieUrl, download=False)
            #name = info['title'] + "-"  + info['id'] + ".mp4"          
            #name = "mv - " + info['uploader_id'] + "-" + info['id'] + ".mp4"          
            #logger.info(f"downloadingTitle:{name}")
            return info
        except Exception as e:
            logger.error("could not get Title: "+movieUrl)
            logger.error(e)
            return {}
