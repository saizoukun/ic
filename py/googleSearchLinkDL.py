import os
import sys
import platform
import pathlib
import glob
import logging
import threading
import time
import argparse
import urllib
import ssl
import hashlib
import numpy as np
import csv
from concurrent.futures import ThreadPoolExecutor
from bs4 import BeautifulSoup
import re
from PIL import Image
from tabulate import tabulate
from urllib.parse import urlparse
#import ffmpeg

import YouTubeDownload
import GoogleSearch
import GoogleSearchMovie
import YoutubeSearchMovie
import ImageControl
import ImageDownload
import GooglePhotos
import ObjectDetectionAPI
import SqliteAPI
import MechanizeDriver
import AccountType

#import SudachiAPI

ISIOS = 'iPhone' in platform.platform() or 'iPad' in platform.platform()
if ISIOS:
    import ui
    import IOSPhotos
    myPhotos = IOSPhotos.IOSPhotos()
else:
    import GoogleTensorFlow
    #import SeleniumDriver
    #import TesseractAPI

isys :bool = True

log_base = "dl"
log_ext = ".log" 
log_name = log_base + log_ext
log_number = 0
if 'Linux' in platform.platform():
    log_name = os.path.join("/content/", log_name)
#while os.path.isfile(log_name):
#    log_number = log_number + 1
#    log_name = os.path.join(os.path.dirname(log_name), log_base + "_" + str(log_number).zfill(2) + log_ext)

formatter = logging.Formatter('%(asctime)s:%(name)s(%(threadName)s):%(levelname)s %(message)s')
file_handler = logging.FileHandler(filename=log_name, encoding='utf-8')
file_handler.setLevel(level=logging.DEBUG)
file_handler.setFormatter(formatter)
stream_handler = logging.StreamHandler()
stream_handler.setLevel(level=logging.INFO)
stream_handler.setFormatter(formatter)
logging.basicConfig(level=logging.DEBUG, handlers=[file_handler, stream_handler])
logger = logging.getLogger(__name__)
ssl._create_default_https_context = ssl._create_unverified_context


google = GoogleSearch.GoogleSearch()
googleM = GoogleSearchMovie.GoogleSearchMovie()
youtubeM = YoutubeSearchMovie.YoutubeSearchMovie()
imageDownload = ImageDownload.ImageDownload()
youtube = YouTubeDownload.YouTubeDownload()
myImages = ImageControl.ImageControl(True, 20)
myAcccountType = AccountType.AccountType()

SJA_KEYWORD = myAcccountType.SJA_KEYWORD
SA_KEYWORD = myAcccountType.SA_KEYWORD
SG_KEYWORD = myAcccountType.SG_KEYWORD
ST_KEYWORD = myAcccountType.ST_KEYWORD
SE_KEYWORD = myAcccountType.SE_KEYWORD
SML_KEYWORD = myAcccountType.SML_KEYWORD

def getFileListDir(image_dir, image_type=0):
    image_list = []
    directory = str((pathlib.Path(image_dir)).resolve())
    if os.path.isdir(directory):
        if image_type == 1:
            image_list = sorted([img for img in os.listdir(directory) if os.path.splitext(img)[1] == '.mp4'])
        elif image_type == 2:
            image_list = sorted([img for img in os.listdir(directory) if os.path.splitext(img)[1] == '.png' or os.path.splitext(img)[1] =='.jpeg' or os.path.splitext(img)[1] =='.jpg' or os.path.splitext(img)[1] =='.gif' or os.path.splitext(img)[1] == '.mp4'])
        else:
            image_list = sorted([img for img in os.listdir(directory) if os.path.splitext(img)[1] == '.png' or os.path.splitext(img)[1] =='.jpeg' or os.path.splitext(img)[1] =='.jpg' or os.path.splitext(img)[1] =='.gif'])
    return image_list


def getFileListDirCount(image_dir, image_type=0):
    return len(getFileListDir(image_dir, image_type=image_type))


def getFileList(image_dir, sub_dir_check=True):
    logger.info(f"target: {image_dir}")
    image_dir = str((pathlib.Path(image_dir)).resolve())

    if sub_dir_check == False:
        path = pathlib.Path(os.path.join(image_dir))
        image_list = [f for f in sorted(path.glob('*.jpg')) if os.path.isfile(f)]
        image_list += [f for f in sorted(path.glob('*.jpeg')) if os.path.isfile(f)]
        image_list += [f for f in sorted(path.glob('*.png')) if os.path.isfile(f)]
        image_list += [f for f in sorted(path.glob('*.gif')) if os.path.isfile(f)]
        return image_list

    sub_dirs = [name for name in os.listdir(image_dir) if name != ".DS_Store" and os.path.isdir(os.path.join(image_dir, name))]    
    logger.info(f"sub_dir: {len(sub_dirs)}")
    file_list = []
    for sdir in sub_dirs:
        logger.info(f"target sub_dir: {sdir}")

        path = pathlib.Path(os.path.join(image_dir, sdir))
        image_list = [f for f in sorted(path.glob('*.jpg')) if os.path.isfile(f)]
        image_list += [f for f in sorted(path.glob('*.jpeg')) if os.path.isfile(f)]
        image_list += [f for f in sorted(path.glob('*.png')) if os.path.isfile(f)]
        image_list += [f for f in sorted(path.glob('*.gif')) if os.path.isfile(f)]

        logger.info(f"{sdir} images: {len(image_list)}")
        file_list += image_list
    return file_list


def movieDownloads(download_list):

    download_errors = []
    for movieUrl in download_list:
        logger.debug(f"-> Downloading URL: {movieUrl[0]}")
        logger.debug(f"-> Downloading movie: {movieUrl[1]}")

        base_fqdn = urlparse(movieUrl[0]).hostname
        if "twitter.com" in base_fqdn:
            if youtube.twitterMovieDowonlod(movieUrl[0], movieUrl[1], 'mv - %(uploader_id)s - %(id)s.%(ext)s') == False:
                download_errors.append(movieUrl[0])
                continue
        else:
            if youtube.movieDowonlod(movieUrl[0], movieUrl[2], movieUrl[1]) == False:
                download_errors.append(os.path.basename(movieUrl[1]))
            else:
                #mp3に変換
                logger.info("dummy")
            
        time.sleep(0.005)

    return download_errors


def mainSearchMovie(nums, keywords, site, directory, threadCount, searchYoutube=False, music=False, twitterMode=False, faceMode=False):

    os.makedirs(directory, exist_ok=True)
    os.makedirs(os.path.join(directory, keywords), exist_ok=True)

    # search movies
    logger.info(f"Begining searching {keywords}")
    if searchYoutube:
        results = youtubeM.search(keywords, maximum=nums)
    else:
        results = googleM.search(keywords, site, maximum=nums, twitterMode=twitterMode, faceMode=faceMode)
    logger.info(f"-> Found {str(len(results))} movies")

    url_movie_list = []
    for url in results:
        if music:
            type = youtube.EXT_MUSIC
        else:
            type = youtube.EXT_MOVIE

        movieTitle = youtube.movieGetTitle(url[1], type)
        if movieTitle == None:
            continue
        movieFile = os.path.join(
            *[directory, keywords, movieTitle + '-' + url[1] + "." + type])
        url_movie_list.append([url[1], movieFile, type])

    # download
    download_errors = movieDownloads(url_movie_list)

    new_movie_list = []
    for movie in url_movie_list:
        if os.path.isfile(movie[1]) == False:
            logger.info(f"File Not Found: {movie[1]}")
            continue
        new_movie_list.append(movie[1])

    logger.info("-" * 50)
    logger.info("Complete downloaded")
    logger.info(f"├─ Successful downloaded {len(results) - len(download_errors)} movies")
    logger.info(f"└─ Failed to download {len(download_errors)}")
    logger.info(f"└─ saved movieFile {len(new_movie_list)}")


def mainSearch(nums, keyword, site, directory, threadCount=1, faceMode=False, siteMode=False, twitterMode=False, instaMode=False, removeMode=False, base_directory="", sub_keywords=[], min_size=600):
    user_list = set()
    if nums == 0:
        return user_list

    logger.info(f"Begining searching {keyword}")
    os.makedirs(directory, exist_ok=True)
    name = ""
    url_link_list = ()

    # search images
    if twitterMode and len(site) == 0:
        site, name, url_link_list, user_list = google.get_twitter_image(keyword, nums, getRetweet=faceMode)
        logger.info(f"{keyword} is {name}")

        if siteMode == False:
            site = ''
            word = '@' + keyword
        else:
            word = keyword

        keywords = "twitter @" + keyword
        results, title = google.search(word, site, maximum=nums, faceMode=False, siteMode=False, twitterMode=twitterMode)
        results = url_link_list | results
    elif instaMode and len(site) == 0:
        site, name, url_link_list, user_list = google.get_instagram_image(keyword, nums, getRepost=faceMode)
        logger.info(f"{keyword} is {name}")

        keywords = "instagram @" + keyword
        if siteMode == False:
            results = url_link_list
            title = keywords
        else:
            results, title = google.search(keywords, site, maximum=nums, faceMode=False, siteMode=False)
            results = url_link_list | results
    else:
        keywords = keyword
        results, title = google.search(keywords, site, maximum=nums, faceMode=faceMode, siteMode=siteMode, twitterMode=twitterMode)
        for sub_keyword in sub_keywords:
            googleLocal = GoogleSearch.GoogleSearch()
            plus_keyword = keyword + " " + sub_keyword
            url_link_list, _ = googleLocal.search(plus_keyword, site, maximum=nums, faceMode=faceMode, siteMode=siteMode, twitterMode=twitterMode)
            results = results | url_link_list
            del googleLocal

    logger.info(f"-> Found {str(len(results))} images")

    if len(results) == 0:
        return user_list

    os.makedirs(os.path.join(directory, title), exist_ok=True)

    url_image_list = []
    url_movie_list = []
    for i, url in enumerate(results):
        sub_dir = title
        if twitterMode and url[1] != 'jpg' and url[1] != 'mp4':
            imageUrl = url[0]
            user_id = url[1]
        else:
            imageUrl = url[0] + url[1]
            
        filename = list(reversed(imageUrl.split('/')))[0]

        if len(filename) > 128:
            filename = os.path.splitext(filename)
            filename = str(i).zfill(4) + filename[1]

        imgFile = os.path.join(*[directory, sub_dir, filename])
        logger.info(f"imageUrl: {imageUrl}")
        logger.info(f"imgFile: {imgFile}")

        logger.debug(f"imageUrl: {imageUrl}")
        if "pbs.twimg.com" in urlparse(imageUrl).hostname:
            if os.path.isfile(imgFile):
                continue
            url_image_list.append([imageUrl, imgFile])

        elif "twitter.com" in urlparse(imageUrl).hostname:
            info = youtube.twitterMovieGetTitle(imageUrl, "")
            logger.info("info", info)
            if len(info) == 0:
                continue
            if info.get('uploader_id'):
                movie_title = "mv - " + info['uploader_id'] + "-" + info['id'] + ".mp4"
            else:
                movie_title = info['id'] + ".mp4"
            imgFile = os.path.join(directory, sub_dir, movie_title)
            logger.info(f"imgFile: {imgFile}")

            if info.get('title'):
                movie_title = info['title'] + " - "  + info['id'] + ".mp4"
                dl_filename = os.path.join(directory, sub_dir, movie_title)
                if os.path.isfile(dl_filename):
                    os.rename(dl_filename, imgFile)
                    continue

            movie_title = info['id'] + ".mp4"
            dl_filename = os.path.join(directory, sub_dir, movie_title)
            if os.path.isfile(dl_filename):
                if dl_filename != imgFile:
                    os.rename(dl_filename, imgFile)
                continue
            
            url_movie_list.append([imageUrl, imgFile])

        else:
            if os.path.isfile(imgFile):
                filename = os.path.splitext(filename)
                imgFile = os.path.join(*[directory, sub_dir, filename[0] + "_" + str(i).zfill(4) + filename[1]])
            url_image_list.append([imageUrl, imgFile])


    # download
    logger.info(f"Begining downloading {keyword}")

    logger.info(f"-> Dowload {str(len(url_image_list))} images")
    download_errors = imageDownload.imageDownloads(url_image_list, site, min_size)

    logger.info(f"-> Dowload {str(len(url_movie_list))} movies")
    download_movie_errors = movieDownloads(url_movie_list)

    delete_image_list = []
    delete_duplicate_list = []
    new_image_list = []
    for img in url_image_list:
        if os.path.isfile(img[1]) == False:
            #logger.info(f"File Not Found: {img[1]}")
            continue

        filename = list(reversed(os.path.splitext(img[1])))[0]

        if filename != '.mp4' and myImages.is_jpg(img[1]) == False:
            logger.info(f"File not Image: {img[1]}")
            delete_image_list.append(img[1])
            continue
        new_image_list.append(img[1])

    for delete in delete_image_list:
        os.remove(delete)

    addImage_errors = []
    if ISIOS:
        logger.info(f"check imageFile {len(new_image_list)}")
        new_image_list = myImages.duplicateImageList(new_image_list, delete_duplicate_list)
        for delete in delete_duplicate_list:
            os.remove(delete)

        album = myPhotos.makeAlbum(keywords)
        for img in new_image_list:
            if myPhotos.addImage(album, img) == False:
                addImage_errors.append(img)
                continue

        myPhotos.deleteImagesFromAlbum(album, keywords)

    myImages.getCalcHistDirList(os.path.join(directory, title))

    logger.info("-" * 50)
    logger.info("Complete downloaded")
    if twitterMode and not siteMode:
        logger.info(f"{keywords},{name},{len(new_image_list)}, {len(url_movie_list)}")
    else:
        logger.info(f"├─ Successful downloaded {len(results) - (len(download_errors) + len(addImage_errors))} images")
        logger.info(f"└─ Failed to download {len(download_errors)}")
        logger.info(f"└─ Failed to addImage {len(addImage_errors)}")
        logger.info(f"└─ delete notImageFile {len(delete_image_list)}")
        logger.info(f"└─ delete duplicateFile {len(delete_duplicate_list)}")
        logger.info(f"└─ saved imageFile {len(new_image_list)}")

    if removeMode:
        #mainCascade(base_directory, os.path.join(directory, title), "person", mode_rename=True)
        mainDuplicateDelete(directory, title=title, removeMode=True, reverse=True)

    logger.info(f"retweet user count: {len(user_list)}")
    return user_list
    

def mainSearchLinks(keywords, site, directory, siteMode=False, limit=1, threadCount=5):
    logger.info("")

    logger.info(f"Begining searching {keywords}")
    keywords = keywords.split(' ')
    # search images
    url_link_list = [site]
    google.linkSearch(site, url_link_list, keyword=keywords[0], limit=limit)
    url_link_list = set(url_link_list)

    logger.info(f"-> Found {str(len(url_link_list))} links")
    logger.debug(f"link: {url_link_list}")

    new_url_link_list = []
    for keyword in keywords:
        new_url_link_list += [link for link in url_link_list if keyword in link]

    for link in new_url_link_list:
        try:
            mainSearch(1, "", link, directory, threadCount=threadCount, siteMode=siteMode)
            time.sleep(0.005)
        except Exception as e:
            logger.warning(e)
            continue


def mainMinSizeDelete(targetDirectory, removeMode=False, minSize=900):
    logger.info('mainMinSizeDelete')
    logger.info(f"target: {targetDirectory}")

    myImages.setCV(False)
    targetDirectory = str((pathlib.Path(targetDirectory)).resolve())
    sub_dirs = [name for name in os.listdir(targetDirectory) if os.path.isdir(os.path.join(targetDirectory, name))  and name != ".DS_Store" and name != "_min"]
    logger.info("list count: {}".format(len(sub_dirs)))
    if len(sub_dirs) == 0:
        sub_dir = os.path.basename(targetDirectory)
        targetDirectory = os.path.dirname(targetDirectory)
        sub_dirs.append(sub_dir)

    all_moved_count = 0
    for sub_dir in sub_dirs:
        logger.info(os.path.join(targetDirectory, sub_dir))
        images = sorted([os.path.join(targetDirectory, sub_dir, img) for img in os.listdir(os.path.join(targetDirectory, sub_dir)) if os.path.splitext(img)[1] == '.png' or os.path.splitext(img)[1] =='.jpeg' or os.path.splitext(img)[1] =='.jpg' or os.path.splitext(img)[1] =='.gif'])
        logger.info(f"images: {len(images)}")
        if len(images) ==0:
            logger.info("not images")
            continue

        results = myImages.getMinSizeList(images)
        logger.info(f"results: {len(results)}")

        # ファイル移動
        export_dir = os.path.join(targetDirectory, "_min", sub_dir)
        os.makedirs(export_dir, exist_ok=True)

        moved_count = 0
        for image, size in results.items():
            if size >= minSize:
                logger.debug(f"filesize ok: {size}, {image}")
            else:
                logger.debug(f"filesize little: {size}, {image}")
                moved_count += 1
                all_moved_count += 1
                if removeMode:
                    srcFile = image
                    basename = os.path.basename(image)
                    dstFile = os.path.join(export_dir, basename) 
                    logger.debug(f"srcFile: {srcFile}")
                    logger.debug(f"dstFile: {dstFile}")
                    os.rename(srcFile, dstFile)
        logger.info(f"moved: {sub_dir}, {moved_count}")
    logger.info(f"moved End: {targetDirectory}, {all_moved_count}")


def mainDuplicateDelete(directory, title="", removeMode=False, reverse=True, sub_dir_check=True, add_mode=False, delete_mode=False):
    if ISIOS:
        if title == '':
            imgs = myPhotos.selectAllImages()
        else:
            album = myPhotos.makeAlbum(title)
            logger.info(album.title)
            imgs = myPhotos.selectImagesFromAlbum(album, title)
        logger.info(f"duplicate check file : {len(imgs)}")

        delete_duplicate_list = myImages.duplicateImages(imgs)

        if removeMode == False:
            logger.info("check Only")
            return

        myPhotos.deleteImages(delete_duplicate_list)
        logger.info(f"duplicate delete file : {len(delete_duplicate_list)}")
    else:
        #Windows
        if len(title) != 0:
            directory = os.path.join(directory, title)
            logger.info(f"target Dir: {directory}")
            delete_duplicate_list = myImages.getDuplicateDirList(directory, sub_dir_check=False, reverse=reverse, add_mode=add_mode, delete_mode=delete_mode)
        elif sub_dir_check:
            sub_dirs = sorted([name for name in os.listdir(directory) if name != ".DS_Store" and os.path.isdir(os.path.join(directory, name))])
            logger.info(f"target dirs: {len(sub_dirs)}")

            executor = ThreadPoolExecutor(max_workers=20)
            futures = []
            for sub_dir in sub_dirs:
                image_dir = os.path.join(directory, sub_dir)
                image_dir = str((pathlib.Path(image_dir)).resolve())
                future = executor.submit(myImages.getDuplicateDirList, image_dir, sub_dir_check=False, reverse=reverse, add_mode=add_mode, delete_mode=delete_mode)
                futures.append(future)
                time.sleep(0.001)

            for future in futures:
                delete_duplicate_list = future.result()
                if delete_mode:
                    logger.info(f"deleted")
                elif removeMode:
                    for delete in delete_duplicate_list:
                        os.remove(delete)
                else:
                    logger.info(f"check Only")
                time.sleep(0.001)
                
            executor.shutdown()
            logger.info("remove end")
            return
        else:
            logger.info(f"target Dir: {directory}")
            delete_duplicate_list = myImages.getDuplicateDirList(directory, sub_dir_check=True, reverse=reverse, add_mode=add_mode, delete_mode=delete_mode)

        logger.info(f"duplicate imageFile: {len(delete_duplicate_list)}")

        if delete_mode:
            logger.info("deleted")
            return

        if removeMode == False:
            logger.info("check Only")
            return

        for delete in delete_duplicate_list:
            os.remove(delete)

    logger.info("remove end")


def mainDuplicateDeleteAllList(org, target, removeMode=False, sub_dir_mode=False, add_mode=False):
    logger.info('mainDuplicateDeleteAllList')
    org = str((pathlib.Path(org)).resolve())
    target = str((pathlib.Path(target)).resolve())
    if os.path.isdir(org) == False or os.path.isdir(target) == False:
        logger.info("no directory")
        return
    
    if org == target:
        logger.info("same directory")
        return

    if sub_dir_mode:
        delete_duplicate_list = []
        sub_dirs = sorted([name for name in os.listdir(org) if name != ".DS_Store" and os.path.isdir(os.path.join(org, name))])
        for sub_dir in sub_dirs:
            sub_dir = os.path.join(org, sub_dir)
            delete_duplicate_list += myImages.getDuplicateDirAllList(sub_dir, target, removeMode=removeMode, sub_dir_check=False, add_mode=add_mode)    
            time.sleep(0.001)
    elif add_mode:
        delete_duplicate_list = myImages.getDuplicateDirAllList(org, target, removeMode=removeMode, sub_dir_check=False, add_mode=add_mode)
    else:
        delete_duplicate_list = myImages.getDuplicateDirAllList(org, target, removeMode=removeMode, add_mode=add_mode)
    logger.info(f"delete_duplicate_list: {len(delete_duplicate_list)}")


def mainDuplicateDeleteList(org, target, removeMode=False, number=5, add_mode=False):
    logger.info('mainDuplicateDeleteList')
    org_directory = str((pathlib.Path(org)).resolve())
    target_directory = str((pathlib.Path(target)).resolve())
    if os.path.isdir(org_directory) == False or os.path.isdir(target_directory) == False:
        logger.info("no directory")
        return

    sub_dirs = sorted([name for name in os.listdir(target_directory) if name != ".DS_Store" and os.path.isdir(os.path.join(target_directory, name))])
    logger.info(f"target dirs: {len(sub_dirs)}")

    delete_duplicate_list = myImages.getDuplicateDirDirList(sub_dirs, org_directory, target_directory, removeMode, add_mode=add_mode)
    logger.info(f"delete_duplicate_list: {len(delete_duplicate_list)}")


def mainTargetDelete(keyword, targetDirectory):
    logger.info(f"mainTargetDelete[target, keyword]: [{targetDirectory}, {keyword}]")
    image_dir = str((pathlib.Path(targetDirectory)).resolve())
    if os.path.isdir(image_dir) == False:
        logger.info("no directory")
        return
    
    sub_dirs = [name for name in os.listdir(image_dir) if name != ".DS_Store" and os.path.isdir(os.path.join(image_dir, name))]    
    logger.info(f"sub_dir: {len(sub_dirs)}")
    target_list = []
    for sub_dir in sub_dirs:
        logger.info(f"target: {sub_dir}")
        path = pathlib.Path(os.path.join(image_dir, sub_dir))
        image_list = [f for f in sorted(path.glob(keyword)) if os.path.isfile(f)]
        if len(image_list) == 0:
            continue
        target_list += image_list
        logger.info(f"[total, now] --> [{len(target_list)}, {len(image_list)}]")
    logger.info(f"delete files: {len(target_list)}")
    for delete in target_list:
        os.remove(delete)


def mainEmptyDirectoryDelete(directory):
    logger.info(f"target: {directory}")
    image_dir = str((pathlib.Path(directory)).resolve())
    if os.path.isdir(image_dir) == False:
        logger.info("no directory")
        return

    sub_dirs = [name for name in os.listdir(image_dir) if name != ".DS_Store" and os.path.isdir(os.path.join(image_dir, name))]    
    logger.info(f"sub_dir: {len(sub_dirs)}")
    target_list = []
    for sub_dir in sub_dirs:
        image_dir = os.path.join(directory, sub_dir)
        image_list = sorted([img for img in os.listdir(image_dir) if os.path.splitext(img)[1] == '.png' or os.path.splitext(img)[1] =='.jpeg' or os.path.splitext(img)[1] =='.jpg' or os.path.splitext(img)[1] =='.gif'])
        movie_list = sorted([img for img in os.listdir(image_dir) if os.path.splitext(img)[1] == '.mp4'])
        dir_list = sorted([img for img in os.listdir(image_dir) if os.path.isdir(os.path.join(image_dir, img))])
        logger.info(f"[target, image, movie, dir]: [{sub_dir}, {len(image_list)}, {len(movie_list)}, {len(dir_list)}]")
        if len(image_list) == 0 and len(movie_list) == 0 and len(dir_list) == 0:
            target_list.append(image_dir)
            logger.info(f"empty: {image_dir}")
    logger.info(f"delete_target: {len(target_list)}")
    for delete in target_list:
        npz_list = sorted([img for img in os.listdir(delete) if os.path.splitext(img)[1] == '.npz'])
        for npz in npz_list:
            os.remove(os.path.join(delete, npz))

        try:
            os.rmdir(delete)
        except Exception as e:
            logger.warning(e)
            continue
        


def mainPredict(directory, epoch_size=50, batch_size=64, loadFile='', mode_add=False, imageSize=224, mode_rename=False, mode_bin=False):
    logger.info(f"mainPredict target: {directory}")
    image_dir = str((pathlib.Path(directory)).resolve())
    if os.path.isdir(image_dir) == False:
        logger.info("no directory")
        return

    tensowFlow = GoogleTensorFlow.GoogleTensorFlow(image_dir, file_name=loadFile, image_size=imageSize)
    sample_dir = 'sample'
    predict_dir = 'predict'
    export_dir = 'export'
    #画像分類用
    if len(loadFile) == 0:
        logger.info('saveModel')
        #tensowFlow.saveModel(sample_dir, batch_size=batch_size, epoch_size=epoch_size, mode_add=mode_add)
        tensowFlow.saveModelGenerator(sample_dir, sample_dir, batch_size=batch_size, epoch_size=epoch_size, mode_add=mode_add, mode_bin=mode_bin)

    predict_dir = os.path.join(image_dir, predict_dir)
    predict_dir = str((pathlib.Path(predict_dir)).resolve())
    file_list = getFileList(predict_dir)
    if mode_bin:
        predictions = tensowFlow.predictFromFilesBin(file_list)
        headers = ["カテゴリ", "ファイル名", "分類結果"]
        result = tabulate(predictions, headers, tablefmt="grid")
    else:
        predictions = tensowFlow.predictFromFiles(file_list)
        #predictions = tensowFlow.predictFromDirs(predict_dir)
        # 結果出力
        headers = ["カテゴリ", "ファイル名", "分類結果1", "分類結果2", "分類結果3", "予測値", "分類予測値"]
        result = tabulate(predictions, headers, tablefmt="grid")
    logger.info(result)


    del tensowFlow

    # ファイル移動
    if mode_rename:
        export_dir = os.path.join(image_dir, export_dir)
        export_dir = str((pathlib.Path(export_dir)).resolve())
        for prediction in predictions:
            srcFile = os.path.join(predict_dir, prediction[0], prediction[1])
            if mode_bin:
                if prediction[2] < 0.7:
                    os.makedirs(export_dir, exist_ok=True)
                    dstFile = os.path.join(export_dir, prediction[1])
                else:
                    continue
            else:
                os.makedirs(os.path.join(export_dir, prediction[2]), exist_ok=True)
                dstFile = os.path.join(export_dir, prediction[2], prediction[1])
            os.rename(srcFile, dstFile)


def mainPredictDir(directory, targetDirectory, loadFile='', imageSize=224, mode_rename=False, mode_bin=False):
    logger.info(f"mainPredict target: {targetDirectory}")
    directory = str((pathlib.Path(directory)).resolve())
    targetDirectory = str((pathlib.Path(targetDirectory)).resolve())
    export_dir = "_export"
    etc_dir = "_etc"
    if os.path.isdir(targetDirectory) == False or os.path.isdir(directory) == False:
        logger.info("no directory")
        return

    sub_dirs = [name for name in os.listdir(targetDirectory) if os.path.isdir(os.path.join(targetDirectory, name))  and name != ".DS_Store"]
    logger.info("list count: {}".format(len(sub_dirs)))
    if len(sub_dirs) == 0:
        sub_dir = os.path.basename(targetDirectory)
        targetDirectory = os.path.dirname(targetDirectory)
        sub_dirs.append(sub_dir)

    for sub_dir in sub_dirs:

        predict_dir = os.path.join(targetDirectory, sub_dir)

        logger.info(f"predict start: {sub_dir}")

        file_list = getFileList(predict_dir, sub_dir_check=False)

        logger.info(f"predict files: {sub_dir},  {len(file_list)}")
        if len(file_list) == 0:
            continue

        tensowFlow = GoogleTensorFlow.GoogleTensorFlow(directory, file_name=loadFile, image_size=imageSize)

        # 結果出力
        if mode_bin:
            predictions = tensowFlow.predictFromFilesBin(file_list)
            headers = ["カテゴリ", "ファイル名", "分類結果"]
            result = tabulate(predictions, headers, tablefmt="grid")
        else:
            predictions = tensowFlow.predictFromFiles(file_list)
            headers = ["カテゴリ", "ファイル名", "分類結果1", "分類結果2", "分類結果3", "予測値", "分類予測値"]
            result = tabulate(predictions, headers, tablefmt="grid")

        logger.info(f"predict predictions: {sub_dir},  {len(predictions)}")
        logger.debug(result)

        del tensowFlow

        # ファイル移動
        if mode_rename:
            export_dir = os.path.join(targetDirectory, export_dir)
            for prediction in predictions:
                srcFile = os.path.join(predict_dir, prediction[1])
                if mode_bin:
                    if prediction[2] < 0.7:
                        dstFile = os.path.join(export_dir, prediction[1])
                        os.makedirs(export_dir, exist_ok=True)
                    else:
                        continue
                elif prediction[6] == 1:
                    dstFile = os.path.join(export_dir, prediction[2], prediction[1])
                    os.makedirs(os.path.join(export_dir, prediction[2]), exist_ok=True)
                else:
                    dstFile = os.path.join(export_dir, etc_dir, prediction[1])
                    os.makedirs(os.path.join(export_dir, etc_dir), exist_ok=True)
                os.rename(srcFile, dstFile)


def mainReadTextFromImage(targetDirectory, mode_rename=False):
    logger.info(f"mainReadTextFromImage target: {targetDirectory}")
    directory = str((pathlib.Path(targetDirectory)).resolve())
    if os.path.isdir(directory) == False:
        logger.info("no directory")
        return

    sub_dirs = [name for name in os.listdir(directory) if os.path.isdir(os.path.join(directory, name)) and name != ".DS_Store"]

    logger.info("list count: {}".format(len(sub_dirs)))
    tesseractAPI = TesseractAPI.TesseractAPI()
    for sub_dir in sub_dirs:
        image_list = []
        image_dir = os.path.join(directory, sub_dir)
        path = pathlib.Path(image_dir)
        images = sorted(path.glob('*.jpg'))
        if len(images) == 0:
            continue
        
        name = sub_dir.split('@')
        name = name[1]
        logger.info("{}: {}".format(name, len(images)))
        same = 0
        n_same = 0
        for image in images:
            logger.debug("file: {}".format(os.path.basename(image)))
            sys.stdout.write("\rfile: {:<50}".format(os.path.basename(image)))
            sys.stdout.flush()
            result = tesseractAPI.get_account_from_image(image, lang="eng", searchText=name, rotate=1, add_reverse=2, debug_mode=False)
            if result:
                same += 1
            else:
                n_same += 1
                image_list.append([image, result])
            sys.stdout.write("result: {}".format(result))
            sys.stdout.flush()
        print("")
        logger.info("[same, n_same] => [{}, {}]".format(same, n_same))

        # ファイル移動
        if mode_rename:
            logger.info("move: {}".format(len(image_list)))
            export_dir = os.path.join(directory, "not")
            for image, not_move in image_list:
                if not_move:
                    continue
                srcFile = image
                sub_dir = os.path.basename(os.path.dirname(image))
                basename = os.path.basename(image)
                dstFile = os.path.join(export_dir, sub_dir, basename) 
                os.makedirs(os.path.dirname(dstFile), exist_ok=True)
                os.rename(srcFile, dstFile)


def mainCascade(directory, targetDirectory, keyword, mode_rename=False, batch_size=1, output_dir="", leg_mode=False, keyword_limit=2):
    logger.info('mainCascade')
    logger.info(f"target: {targetDirectory}")

    myImages.setCV(True)
    targetDirectory = str((pathlib.Path(targetDirectory)).resolve())
    sub_dirs = [name for name in os.listdir(targetDirectory) if os.path.isdir(os.path.join(targetDirectory, name))  and name != ".DS_Store"]
    logger.info("list count: {}".format(len(sub_dirs)))
    if len(sub_dirs) == 0:
        sub_dir = os.path.basename(targetDirectory)
        targetDirectory = os.path.dirname(targetDirectory)
        sub_dirs.append(sub_dir)

    for sub_dir in sub_dirs:
        logger.info(os.path.join(targetDirectory, sub_dir))
        images = sorted([os.path.join(targetDirectory, sub_dir, img) for img in os.listdir(os.path.join(targetDirectory, sub_dir)) if os.path.splitext(img)[1] == '.png' or os.path.splitext(img)[1] =='.jpeg' or os.path.splitext(img)[1] =='.jpg'])
        logger.info(f"images: {len(images)}")
        if len(images) ==0:
            logger.info("not images")
            continue
        if len(output_dir) > 0:
            output_dir = os.path.join(directory, output_dir)

        results = []
        set_count = 200
        detectedCount = 0
        while len(images) > detectedCount:
            detectedImages = images[detectedCount:detectedCount+set_count]

            myDetect = ObjectDetectionAPI.ObjectDetectionAPI(directory)
            results = myDetect.main(detectedImages, output_dir, keyword=keyword, keyword_limit=keyword_limit, batch_size=batch_size)
            del myDetect
            logger.info(f"results: {len(results)}, {detectedCount}")
            detectedCount = detectedCount + set_count

            if len(detectedImages) > len(results):
                logger.info(results)

            # ファイル移動
            if leg_mode:
                logger.info("leg_mode...")
                export_dir = os.path.join(targetDirectory, "_export")
                town_skin_dir = os.path.join(export_dir, "town_skin")
                town_noskin_dir = os.path.join(export_dir, "town_noskin")
                noramal_dir = os.path.join(export_dir, sub_dir)
                av_dir = os.path.join(export_dir, "av")
                not_dir = os.path.join(export_dir, "_not")
                moved_count = 0
                for image, not_move, objs in results:
                    srcFile = image
                    basename = os.path.basename(image)

                    if objs.count(keyword) == 0:
                        dest_dir = not_dir
                    elif objs.count(keyword) == 2:
                        if myImages.findRectOfTargetSkinColor(image, 2):
                            dest_dir = av_dir
                        else:
                            dest_dir = not_dir
                    elif objs.count(keyword) > 2:
                        if myImages.findRectOfTargetSkinColor(image, 8):
                            dest_dir = town_skin_dir
                        else:
                            dest_dir = town_noskin_dir
                    else:
                        dest_dir = noramal_dir

                    os.makedirs(dest_dir, exist_ok=True)
                    dstFile = os.path.join(dest_dir, basename) 
                    logger.debug(f"srcFile: {srcFile}")
                    logger.debug(f"dstFile: {dstFile}")

                    moved_count += 1
                    logger.debug("{0:20s} {1:s}".format("Objects Detected:", " ".join(objs)))
                    os.rename(srcFile, dstFile)
                logger.info(f"moved: {moved_count}")
            elif mode_rename:
                logger.info("noraml_mode...")
                export_dir = os.path.join(targetDirectory, "_export")
                noramal_dir = os.path.join(export_dir, sub_dir)
                not_dir = os.path.join(export_dir, "_not")
                moved_count = 0
                for image, not_move, objs in results:
                    srcFile = image
                    basename = os.path.basename(image)

                    if objs.count(keyword) == 0:
                        dest_dir = not_dir
                    elif objs.count(keyword) > keyword_limit:
                        if myImages.findRectOfTargetSkinColor(image, 8):
                            dest_dir = noramal_dir
                        else:
                            dest_dir = not_dir
                    else:
                        dest_dir = noramal_dir

                    os.makedirs(dest_dir, exist_ok=True)
                    dstFile = os.path.join(dest_dir, basename) 
                    logger.debug(f"srcFile: {srcFile}")
                    logger.debug(f"dstFile: {dstFile}")

                    moved_count += 1
                    logger.debug("{0:20s} {1:s}".format("Objects Detected:", " ".join(objs)))
                    os.rename(srcFile, dstFile)
                logger.info(f"moved: {moved_count}")


def mainColorCascade(targetDirectory, mode_rename=False, output_dir="", fileOnly=False):
    logger.info('mainColorCascade')
    logger.info(f"target: {targetDirectory}")

    targetDirectory = str((pathlib.Path(targetDirectory)).resolve())
    base_directory = os.path.dirname(targetDirectory)

    sub_dirs = [name for name in os.listdir(targetDirectory) if os.path.isdir(os.path.join(targetDirectory, name))  and name != ".DS_Store"]
    logger.info("list count: {}".format(len(sub_dirs)))

    if len(sub_dirs) == 0:
        sub_dir = os.path.basename(targetDirectory)
        targetDirectory = os.path.dirname(targetDirectory)
        base_directory = os.path.dirname(targetDirectory)
        sub_dirs.append(sub_dir)

    for sub_dir in sub_dirs:
        results = myImages.findRectOfTargetSkinColorList(os.path.join(targetDirectory, sub_dir))

        total_count = len(results)
        lists = list(results.values())
        not_image_count = lists.count(False)
        logger.info(f"results: {not_image_count} / {total_count}")


        # ファイル移動
        if mode_rename:
            if fileOnly:
                logger.info("rename...")
                export_dir = os.path.join(targetDirectory, "_not")
                moved_count = 0
                for image, not_move in results.items():
                    if not_move:
                        continue

                    moved_count += 1
                    srcFile = image
                    basename = os.path.basename(image)
                    dstFile = os.path.join(export_dir, sub_dir, basename) 
                    os.makedirs(os.path.dirname(dstFile), exist_ok=True)
                    logger.debug(f"srcFile: {srcFile}")
                    logger.debug(f"dstFile: {dstFile}")
                    os.rename(srcFile, dstFile)
                logger.info(f"moved: {moved_count}")

            else:
                if not_image_count < (total_count / 2):
                    continue
                dirFileMove(base_directory, os.path.basename(targetDirectory), output_dir, sub_dir.replace("twitter @", ""))


def mainPhotosUpload(baseDirectory, targetDirectory, image_type=2, keyword=''):
    logger.info('mainPhotosUpload')
    logger.info(f"target: {targetDirectory}")

    directory = targetDirectory if len(targetDirectory) > 0 else './data'
    directory = str((pathlib.Path(directory)).resolve())
    sub_dirs = sorted([name for name in os.listdir(directory) if name != ".DS_Store" and os.path.isdir(os.path.join(directory, name))])

    logger.info(f"target dirs: {len(sub_dirs)}")
    googlePhotos = GooglePhotos.GooglePhotos(baseDirectory)
    album_list = googlePhotos.get_album_list()
    for sub_dir in sub_dirs:
        image_dir = os.path.join(directory, sub_dir)
        images = getFileListDir(image_dir=image_dir, image_type=image_type)
        logger.info(images)
        images = [os.path.join(image_dir, img) for img in images]
        if len(images) == 0:
            continue
        logger.info(images)
        album_name = keyword + sub_dir
        logger.info(f"target album: {album_name}")
        logger.info(f"upload files: {len(images)}")
        # 作成したアルバじゃないと画像を追加できない 
        if album_name in album_list.keys():
            album_id = album_list[album_name]
            logger.info('album: {} exists'.format(album_name))
        else:
            album_id = googlePhotos.create_new_album(album_name)
            logger.info('album: {} created'.format(album_name))
        
        status = googlePhotos.upload_image_to_album(images, album_id)
        if type(status) == dict and status['message'] and status['message'] == 'Success':
            logger.debug('status: {status}')
        else:
            album_id = googlePhotos.create_new_album('_' + album_name)
            status = googlePhotos.upload_image_to_album(images, album_id)

        logger.info(f"status:{status}") 
    logger.info("Upload End")


def mainPhotosDownload(keyword, targetDirectory, directory):
    logger.info('mainPhotosDownload')
    logger.info(f"[keyword, target]: [{keyword}, {targetDirectory}]")

    directory = directory if len(directory) > 0 else './data'
    directory = str((pathlib.Path(directory)).resolve())

    googlePhotos = GooglePhotos.GooglePhotos(directory)

    targetDirectory = targetDirectory if len(targetDirectory) > 0 else './data'
    targetDirectory = str((pathlib.Path(targetDirectory)).resolve())


    album_list = googlePhotos.get_album_list()
    album_id_list = []
    for album_name in album_list.keys(): 
        if keyword in album_name:
            album_id = album_list[album_name]
            album_id_list.append([album_id, album_name])
            logger.info('[album_name, album_id]: [{}, {}]'.format(album_name, album_id))

    for album_id, album_name in album_id_list:
        target_name = os.path.join(targetDirectory, album_name)
        photo_list = googlePhotos.get_photo_list_from_album(album_id)
        logger.info('[album_name, album_id, count]: [{}, {}, {}]'.format(album_name, album_id, len(photo_list)))
        if len(photo_list) == 0:
            logger.info('none [album_name, album_id, count]: [{}, {}, {}]'.format(album_name, album_id, 0))
            continue
        elif getFileListDirCount(target_name) == len(photo_list):
            logger.info('copied [album_name, album_id, count]: [{}, {}, {}]'.format(album_name, album_id, len(photo_list)))
            continue

        os.makedirs(target_name, exist_ok=True)

        for i, photo_info in enumerate(photo_list):
            logger.debug("Download {}/{}".format(i + 1, len(photo_list)))
            googlePhotos.download_photo(targetDirectory, photo_info.get("id"), album_name=album_name, overwrite=False)
            time.sleep(googlePhotos.sleep_time)
    logger.info('Download End')


def mainAutoBrowser(site, keyword, directory):
    logger.info('mainAutoBrowser')
    directory = str((pathlib.Path(directory)).resolve())

    loginUrl = "https://mobile.twitter.com/login"
    browser = MechanizeDriver.MechanizeDriver()
    browser.twitteReqestlogin("user@gmail.com", "pass")

    #linkUrl = f"https://mobile.twitter.com/search?q={keyword}&src=typed_query"
    twiiterUrl = f"https://mobile.twitter.com/{keyword}/"
    #html = browser.getSouce(twiiterUrl)
    query_url, user_info, url_link_list, user_new_list = browser.twitteSearch(keyword)
    #logger.info(html)

    results = url_link_list

    url_image_list = []
    for i, url in enumerate(results):
        imageUrl = url[0]
        user_id = url[1]
        if keyword.startswith("#"):
            sub_dir = "twitter " + keyword
        else:
            sub_dir = "twitter @" + keyword

        os.makedirs(os.path.join(directory, sub_dir), exist_ok=True)
            
        imgFile = os.path.join(*[directory, sub_dir, str(i).zfill(4) + '.jpg'])
        site = query_url

        url_image_list.append([imageUrl, imgFile])

    # download
    logger.info(f"Begining downloading {keyword}")

    logger.info(f"-> Dowload {str(len(url_image_list))} images")
    #download_errors = imageDownload.imageDownloads(url_image_list, site)


def mainLoopSearch(args):
    base_directory = args.targetDirectory if len(args.targetDirectory) > 0 else './data'
    base_directory = str((pathlib.Path(base_directory)).resolve())
    logger.info(f"mainLoopSearch: {base_directory}")
    myImages.setCV(False)

    readed_users = {}
    if args.useDbOption:
        mySqlite = SqliteAPI.SqliteAPI(base_directory)
        accountTypeInfo, downloadDirectoryInfo = mySqlite.getAccountTypeInfo()
        account_type_word = mySqlite.getAccountTypeWords()
        account_type_user = mySqlite.getAccountTypeUsers(check_type='user')
        account_type_name = mySqlite.getAccountTypeUsers(check_type='name')
        db_users = mySqlite.userSearch()
        logger.info(f"users: {len(db_users)}")
        for userInfo in db_users:
            readed_users[userInfo['id']] = userInfo
            #logger.info(f"user, image_count, movie_count: {userInfo['id']}, {userInfo['name']}, {userInfo['image_count']}, {userInfo['movie_count'] }")
    else:
        accountTypeInfo = {}
        downloadDirectoryInfo = {}
        account_type_word = {}
        account_type_user = {}
        account_type_name = {}
        result_file = os.path.join(base_directory, "result.txt")
        read_users = readUserList(result_file)
        for id, val in read_users.items():
            userInfo = {}
            userInfo['id'] = id
            userInfo['name'] = val[1]
            userInfo['account_type'] = val[2]
            userInfo['image_count'] = val[3]
            userInfo['movie_count'] = val[4]
            userInfo['detail'] = val[len(val)-1]
            readed_users[id] = userInfo
            logger.info(f"user, image_count, movie_count: {userInfo['id']}, {userInfo['name']}, {userInfo['image_count']}, {userInfo['movie_count'] }")

    myAcccountType.setAccountType(accountTypeInfo, downloadDirectoryInfo, account_type_word, account_type_user, account_type_name)
    if len(downloadDirectoryInfo) == 0:
        downloadDirectoryInfo = myAcccountType.account_type_ok_class

    if len(accountTypeInfo) == 0:
        accountTypeInfo = myAcccountType.account_type_class

    users = []
    base_dirs = ["dl_fav", "dl_close"]

    target_all_dirs = base_dirs
    if args.pageDownload:
        target_all_dirs += accountTypeInfo.values()
    else:
        target_all_dirs += downloadDirectoryInfo.values()

    if len(args.keyword) > 0:
        target_dirs = [accountTypeInfo[args.keyword]]
    else:
        target_dirs = target_all_dirs

    directory = os.path.join(base_directory, "dl_fav")
    #fav_users = sorted([name.replace("twitter @", "") for name in os.listdir(directory) if name != ".DS_Store" and os.path.isdir(os.path.join(directory, name))])

    for target in target_dirs:
        directory = os.path.join(base_directory, target)
        os.makedirs(directory, exist_ok=True)
        users += sorted([name.replace("twitter @", "") for name in os.listdir(directory) if name != ".DS_Store" and os.path.isdir(os.path.join(directory, name))])

    users = set(users)

    total_count = len(users)
    logger.info(f"users: {total_count}")
    retweet_user_list = set()
    for count, user in enumerate(users):
        logger.info(f"user({count+1}/{total_count}): {user}")
        time.sleep(1)
        n_dl_count = 300
        l_dl_count = 100

        if readed_users.get(user):
            n_dl_count = 1
            l_dl_count = 0
            account_type = readed_users[user]['account_type']
            name = readed_users[user]['name']
            account_type = account_type if len(account_type) > 0 else "glayuser"
            if account_type in downloadDirectoryInfo.keys():
                dl_count = getFileListDirCount(os.path.join(base_directory, accountTypeInfo[account_type], "twitter @" + user))
                if dl_count < 20:
                    n_dl_count = 300
                name, account_type, detail = google.get_twitter_name(user)
            elif args.addOption or args.pageDownload:
                name, account_type, detail = google.get_twitter_name(user)
            else:
                detail = readed_users[user]['detail']

        else:
            name, account_type, detail = google.get_twitter_name(user)

        logger.info(f"[user, name, type] ---> [{user}, {name}, {account_type}]")

        for account_dir in accountTypeInfo.values():
            dirFileMove(base_directory, account_dir, accountTypeInfo[account_type], user)

        if args.addOption:
            if account_type in downloadDirectoryInfo.keys():
                retweet_user_list = retweet_user_list | mainSearch(n_dl_count, user, "", os.path.join(base_directory, accountTypeInfo[account_type]), threadCount=5, faceMode=args.faceMode, siteMode=False, twitterMode=True, removeMode=args.renameMode, base_directory=base_directory)
            else:
                mainSearch(l_dl_count, user, "", os.path.join(base_directory, accountTypeInfo[account_type]), threadCount=5, faceMode=False, siteMode=True, twitterMode=True, removeMode=args.renameMode, base_directory=base_directory)

        image_count = 0
        movie_count = 0
        for target in target_all_dirs:
            image_count += getFileListDirCount(os.path.join(base_directory, target, "twitter @" + user), image_type=0)
            movie_count += getFileListDirCount(os.path.join(base_directory, target, "twitter @" + user), image_type=1)

        userInfo = {}
        userInfo['id'] = user
        userInfo['name'] = name
        userInfo['account_type'] = account_type
        userInfo['image_count'] = image_count
        userInfo['movie_count'] = movie_count
        userInfo['detail'] = detail
        readed_users[user] = userInfo 

        if args.useDbOption:
            mySqlite.writeUserInfo(userInfo['id'], userInfo)

    logger.info("Loop End")

    if args.useDbOption == False:
        writeUserList(result_file, readed_users)

    retweet_user_list = set(retweet_user_list)
    logger.info(f"retweet_user: {len(retweet_user_list)}")
    retweet_user_list = retweet_user_list - users
    total_count = len(retweet_user_list)
    logger.info(f"retweet_user: {total_count}")
    for count, user in enumerate(retweet_user_list):
        logger.info(f"retweet_user {user}: {count+1}/{total_count}")
        mainSearch(1, user, "", os.path.join(base_directory, "dl_retweet"), threadCount=5, faceMode=False, siteMode=False, twitterMode=True, removeMode=args.renameMode, base_directory=base_directory)
  
  
def readUserList(result_file):
    readed_users = {}
    if os.path.isfile(result_file):
        with open(result_file, encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                time.sleep(0.001)
                readed_users[row[0]] = row
                #logger.info(','.join(row))

        logger.info(F"read user: {len(readed_users)}")
    
    return readed_users


def writeUserList(result_file, readed_users):
    if os.path.isfile(result_file):
        os.remove(result_file)
    with open(result_file, 'a', encoding='utf-8') as f:
        for line in readed_users.values():
            if isinstance(line, list):
                line = ','.join(line)
            elif isinstance(line, dict):
                line['image_count'] = str(line['image_count'])
                line['movie_count'] = str(line['movie_count'])
                line = list(line.values())
                logger.info(line)
                line = ','.join(line)
                
            logger.info(line)
            f.writelines(f"{line}\n")


def dirFileMove(base_directory, src_dir, dest_dir, user):
    if src_dir == dest_dir:
        return

    directory = os.path.join(base_directory, src_dir, "twitter @" + user)
    directory = str((pathlib.Path(directory)).resolve())
    dest_directory = os.path.join(base_directory, dest_dir, "twitter @" + user)
    dest_directory = str((pathlib.Path(dest_directory)).resolve())

    if os.path.isdir(directory):
        image_list = sorted([img for img in os.listdir(directory) if os.path.splitext(img)[1] == '.png' or os.path.splitext(img)[1] =='.jpeg' or os.path.splitext(img)[1] =='.jpg' or os.path.splitext(img)[1] =='.mp4'])
        os.makedirs(dest_directory, exist_ok=True)

        for image in image_list:
            time.sleep(0.001)
            src  = os.path.join(directory, image)
            dst = os.path.join(dest_directory, image)
            os.rename(src, dst)

        image_list = sorted([img for img in os.listdir(directory) if os.path.splitext(img)[1] == '.npz'])
        for image in image_list:
            src  = os.path.join(directory, image)
            os.remove(src)
        os.removedirs(directory)


def mainUpdateTwitterDir(args):
    logger.info("mainUpdateTwitterDir")
    base_directory = args.targetDirectory
    directory = str((pathlib.Path(base_directory)).resolve())
    users = []
    users += sorted([name.replace("twitter @", "") for name in os.listdir(directory) if name != ".DS_Store" and os.path.isdir(os.path.join(directory, name))])
    users = set(users)

    logger.info(f"users: {len(users)}")
    for user in users:
        time.sleep(1)
        logger.info(f"user: {user}")
        name, account_type, detail = google.get_twitter_name(user)
        logger.info(f"[user, name, type] ---> [{user}, {name}, {account_type}]")
    myImages.setCV(False)
    myImages.getCalcHistDirSearchList(directory, sub_dir_check=True)


def mainTwitterSearch(args):
    logger.info("mainTwitterSearch")
    base_directory = str((pathlib.Path(args.directory)).resolve())
    target_directory = args.targetDirectory
    mySqlite = SqliteAPI.SqliteAPI(base_directory)
    accountTypeInfo, downloadDirectoryInfo = mySqlite.getAccountTypeInfo()
    account_type_word = mySqlite.getAccountTypeWords()
    account_type_user = mySqlite.getAccountTypeUsers(check_type='user')
    account_type_name = mySqlite.getAccountTypeUsers(check_type='name')
    google.setAccountType(accountTypeInfo, downloadDirectoryInfo, account_type_word, account_type_user, account_type_name)
    #mySudachi = SudachiAPI.SudachiAPI()

    result_file = os.path.join(base_directory, "result.txt")
    readed_users = readUserList(result_file)
    db_users = mySqlite.userSearch()
    logger.info(f"db_users: {len(db_users)}")

    users = google.get_twitter_user_search(args.keyword, page=args.number)
    logger.info(f"users: {len(users)}")

    users = set(users)
    target_users = []
    for user in users:
        time.sleep(1)
        if readed_users.get(user):
            logger.info(readed_users[user])
            continue

        name, account_type, detail = google.get_twitter_name(user)
        logger.info(f"[user, name, type] ---> [{user}, {name}, {account_type}]")

        #words = mySudachi.getTokenizeSplit(detail, '名詞')
        #logger.info(words)

        if account_type in downloadDirectoryInfo.keys():
            target_users.append([user, name, account_type])
        elif args.keyword in name:
            if readed_users.get(user):
                logger.info(readed_users[user])
            else:
                target_users.append([user, name, account_type])
    
    logger.info(f"target users {len(target_users)}")
    retweet_user_list = set()
    for user, name, account_type in target_users:
        logger.info(f"[user, name, type] ---> [{user}, {name}, {account_type}]")
        retweet_user_list = retweet_user_list | mainSearch(1, user, "", os.path.join(base_directory, target_directory), threadCount=5, faceMode=args.faceMode, siteMode=False, twitterMode=True, removeMode=args.renameMode, base_directory=base_directory)

    retweet_user_list = retweet_user_list - users
    retweet_user_list = retweet_user_list - set(readed_users.keys())
    total_count = len(retweet_user_list)
    logger.info(f"retweet_user: {total_count}")
    for count, user in enumerate(retweet_user_list):
        logger.info(f"retweet_user {user}: {count+1}/{total_count}")
        mainSearch(1, user, "", os.path.join(base_directory, target_directory), threadCount=5, faceMode=False, siteMode=False, twitterMode=True, removeMode=args.renameMode, base_directory=base_directory)


def mainDbUserImport(args):
    base_directory = args.targetDirectory
    base_directory = str((pathlib.Path(base_directory)).resolve())
    logger.info(f"test: {base_directory}")
    result_file = os.path.join(base_directory, "result.txt")
    mySqlite = SqliteAPI.SqliteAPI(base_directory)

    directoryInfo = mySqlite.getDirectoryInfo()
    accountTypeInfo, downloadDirectoryInfo = mySqlite.getAccountTypeInfo()

    readed_users = readUserList(result_file)

    for user, val in readed_users.items():
        userInfo = {}
        userInfo['id'] = user
        userInfo['name'] = val[1]
        userInfo['account_type'] = val[2]
        userInfo['detail'] = val[len(val)-1]
        userInfo['image_count'] = 0
        userInfo['movie_count'] = 0
        for account_type, sub_dir in accountTypeInfo.items(): 
            image_dir = os.path.join(base_directory, sub_dir, "twitter @" + user)
            image_count = len(getFileListDir(image_dir, 0))
            movie_count = len(getFileListDir(image_dir, 1))
            userInfo['image_count'] = userInfo['image_count'] + image_count
            userInfo['movie_count'] = userInfo['movie_count'] + movie_count
            #logger.info(f"user, image_dir, image_count, movie_count: {user}, {sub_dir}, {image_count}, {movie_count}")
        #logger.info(f"user, image_count, movie_count: {user}, {userInfo['image_count']}, {userInfo['movie_count']}")
        mySqlite.writeUserInfo(user, userInfo)

    logger.info("insert end")
    users = mySqlite.userSearch()
    logger.info(f"users: {len(users)}")
    for userInfo in users:
        logger.info(f"user: {userInfo['id']}, {userInfo['name']}, {userInfo['account_type']}, {userInfo['image_count']}, {userInfo['movie_count'] }")


def mainLoopDuplicateDeleteList(args):
    base_directory = args.targetDirectory
    account_type_class = myAcccountType.account_type_class.values()
    base_dirs = ["dl_fav", "dl_close"]
    for base_dir in base_dirs:
        targetDirectory = str((pathlib.Path(os.path.join(base_directory, base_dir))).resolve())
        for dir in account_type_class:
            orgDirectory = str((pathlib.Path(os.path.join(base_directory, dir))).resolve())
            mainDuplicateDeleteList(orgDirectory, targetDirectory, removeMode=args.renameMode, number=args.number, add_mode=args.addOption)


def mainInitDbTable(args):
    base_directory = args.targetDirectory
    base_directory = str((pathlib.Path(base_directory)).resolve())
    logger.info(f"test: {base_directory}")
    mySqlite = SqliteAPI.SqliteAPI(base_directory)

    # テーブルの再作成
    if len(args.keyword) > 0:
        mySqlite.dropObject(args.keyword)
        mySqlite.createObject()

    # キーワードの再登録
    mySqlite.insertDefaultWord()

    # ユーザー初期化
    if args.addOption:
        mySqlite.deleteUsers()

    account_type_word = mySqlite.getAccountTypeWords()
    print(account_type_word)
    account_type_users = mySqlite.getAccountTypeUsers(check_type='user')
    print(account_type_users)
    account_type_names = mySqlite.getAccountTypeUsers(check_type='name')
    print(account_type_names)


def mainTestInsta(args):
    base_directory = args.directory
    base_directory = str((pathlib.Path(base_directory)).resolve())
    logger.info(f"test: {base_directory}")

    mySqlite = SqliteAPI.SqliteAPI(base_directory)
    accountTypeInfo, downloadDirectoryInfo = mySqlite.getAccountTypeInfo()
    account_type_word = mySqlite.getAccountTypeWords()
    account_type_user = mySqlite.getAccountTypeUsers(check_type='user')
    account_type_name = mySqlite.getAccountTypeUsers(check_type='name')
    google.setAccountType(accountTypeInfo, downloadDirectoryInfo, account_type_word, account_type_user, account_type_name)

    keyword = args.keyword
    title = keyword
    directory = args.targetDirectory
    directory = str((pathlib.Path(directory)).resolve())
    logger.info(f"test: {directory}")
    query_url, user_info, url_link_list, user_new_list = google.get_instagram_image(keyword=keyword, page=args.number)

    results = url_link_list

    url_image_list = []
    url_movie_list = []
    for i, url in enumerate(results):
        imageUrl = url[0]
        user_id = url[1]
        if keyword.startswith("#"):
            sub_dir = "instagram " + title
        else:
            sub_dir = "instagram @" + user_id

        os.makedirs(os.path.join(directory, sub_dir), exist_ok=True)
            
        #filename = list(reversed(imageUrl.split('/')))[0]
        #filename = list(filename.split('?'))[0]
        #imgFile = os.path.join(*[directory, sub_dir, filename])
        imgFile = os.path.join(*[directory, sub_dir, str(i).zfill(4) + '.jpg'])
        site = query_url

        if "scontent-nrt1-1.cdninstagram.com" in urlparse(imageUrl).hostname:
            if os.path.isfile(imgFile):
                continue
            url_image_list.append([imageUrl, imgFile])

    # download
    logger.info(f"Begining downloading {keyword}")

    logger.info(f"-> Dowload {str(len(url_image_list))} images")
    download_errors = imageDownload.imageDownloads(url_image_list, site)


def mainTest(args):
    base_directory = args.directory
    base_directory = str((pathlib.Path(base_directory)).resolve())
    logger.info(f"test: {base_directory}")
    sub_dirs = sorted([name for name in os.listdir(base_directory) if name != ".DS_Store" and os.path.isdir(os.path.join(base_directory, name))])
    for sub_dir in sub_dirs:
        sub_dir = os.path.join(base_directory, sub_dir)
        image_list = sorted([img for img in os.listdir(sub_dir) if os.path.splitext(img)[1] == '.png' or os.path.splitext(img)[1] =='.jpeg' or os.path.splitext(img)[1] =='.jpg'])
        number = 0
        for img in image_list:
            if "%" in img:
                img2 = img
                img3 = urllib.parse.unquote(img2)
            elif img.startswith("_"):
                img2 = img.replace("_", "%")
                img3 = urllib.parse.unquote(img2)
                img3 = img3.replace("%", "_")
            else:
                continue

            if img != img3:
                ext = os.path.splitext(img)[1]
                number = number + 1

                logger.info(f"encode: {img}")
                logger.info(f"decode: {img3}")

                destFile = os.path.join(sub_dir, str(number).zfill(4) + ext)
                while 1 == 1:
                    if not os.path.isfile(destFile):
                        break
                    number = number + 1
                    destFile = os.path.join(sub_dir, str(number).zfill(4) + ext)
                
                srcFile = os.path.join(sub_dir, img)
                logger.info(f"srcFile: {srcFile}")
                logger.info(f"destFile: {destFile}")
                os.rename(srcFile, destFile)

        logger.info(f"sub_dir end: {sub_dir}")
    logger.info(f"test end: {base_directory}")


def main():
    parser = argparse.ArgumentParser(prog='googleSearchLinkDL', formatter_class=argparse.RawTextHelpFormatter)    
    parser.add_argument(
        "-c", 
        "--command", 
        help='''command\n
            ms = movie search
            ys = youtube search
            sl = site link search
            cm = cascade check
            cc = color cascade check
            o  = ocr read Text
            p  = predict
            pp = predict dirs
            dd = duplicate
            dda = duplicate all list
            ddd = duplicate list
            lddd = loop duplicate list
            sd = keyword delete
            ed = empty directory delete
            md = mini size delete
            pd = photos download
            pu = photos upload
            ls = loop search
            tu = twitter update
            ts = twitter search
            dbi = database init
            ab = auto Browser
            test = test
            sa = search adult
            st = search talent
            sg = search gravure
            sja = search women anna
            se = search ero
            sml = search machi legs
            si = search insta

            ''', 
        type=str, 
        default='',
        choices=["ms", "ys", "sl", "cm", "cc", "o", "p", "pp", "dd", "ddd", "dda", "lddd", "sd", "ed", "md", "pd", "pu", "ls", "tu", "ts", "dbi", "ab", "test", "sja", "sa", "sg", "st", "se", "sml", "si"])
    parser.add_argument("-k", "--keyword", help="keyword", type=str, default="")
    parser.add_argument("-s", "--site", help="site", type=str, default="")
    parser.add_argument("-d", "--directory", help="base Directory", type=str, default="./data")
    parser.add_argument("-t", "--targetDirectory", help="target Directory", type=str, default="")
    parser.add_argument("-o", "--outputDirectory", help="output Directory", type=str, default="")

    parser.add_argument("-n", "--number", help="number of images", type=int, default=1)

    parser.add_argument("-r", "--renameMode", help="renameMode", action='store_true')
    parser.add_argument("-a", "--addOption", help="add Option add or twitter or cvOn", action='store_true')

    parser.add_argument("-f", "--faceMode", help="face download", action='store_true')
    parser.add_argument("-p", "--pageDownload", help="PageDownload", action='store_true')

    parser.add_argument("-l", "--loadFile", help="load model file", type=str, default='')
    parser.add_argument("-e", "--epoch", help="epoch size", type=int, default=50)
    parser.add_argument("-b", "--batch", help="batch size", type=int, default=1)
    parser.add_argument("-z", "--imageSize", help="image Size", type=int, default=224)
    parser.add_argument("-u", "--useDbOption", help="dbOption or addOption2", action='store_true')

    args = parser.parse_args()
    myImages.setCV(False)

    if args.command == 'test':
        mainTest(args)

    elif args.command == 'dbi':
        mainInitDbTable(args)

    elif args.command == 'tu':
        mainUpdateTwitterDir(args)

    elif args.command == 'ts':
        mainTwitterSearch(args)

    elif args.command == 'ls':
        mainLoopSearch(args)

    elif args.command == 'lddd':
        mainLoopDuplicateDeleteList(args)

    elif args.command == 'p':
        mainPredict(args.directory, epoch_size=args.epoch, batch_size=args.batch, loadFile=args.loadFile,
            mode_add=args.addOption, imageSize=args.imageSize, mode_rename=args.renameMode, mode_bin=args.faceMode)

    elif args.command == 'pp':
        mainPredictDir(args.directory, args.targetDirectory, loadFile=args.loadFile,
            imageSize=args.imageSize, mode_rename=args.renameMode, mode_bin=args.faceMode)

    elif args.command == 'o':
        mainReadTextFromImage(args.targetDirectory, mode_rename=args.renameMode)

    elif args.command == 'cm':
        mainCascade(args.directory, args.targetDirectory, args.keyword, mode_rename=args.renameMode, batch_size=args.batch, output_dir=args.outputDirectory, keyword_limit=args.number, leg_mode=args.addOption)

    elif args.command == 'cc':
        mainColorCascade(args.targetDirectory, mode_rename=args.renameMode, output_dir=args.outputDirectory, fileOnly=args.addOption)

    elif args.command == 'pu':
        mainPhotosUpload(args.directory, args.targetDirectory, args.number, args.keyword)

    elif args.command == 'pd':
        mainPhotosDownload(args.keyword, args.targetDirectory, args.directory)

    elif args.command == 'dd':
        myImages.setCV(False)
        mainDuplicateDelete(args.targetDirectory, args.keyword, removeMode=args.renameMode, sub_dir_check=args.addOption, add_mode=args.faceMode, delete_mode=args.useDbOption)

    elif args.command == 'dda':
        mainDuplicateDeleteAllList(args.directory, args.targetDirectory, removeMode=args.renameMode, sub_dir_mode=args.addOption, add_mode=args.faceMode)
    
    elif args.command == 'ddd':
        mainDuplicateDeleteList(args.directory, args.targetDirectory, removeMode=args.renameMode, number=args.number, add_mode=args.faceMode)
    
    elif args.command == 'sd':
        mainTargetDelete(args.keyword, args.targetDirectory)

    elif args.command == 'ed':
        mainEmptyDirectoryDelete(args.targetDirectory)

    elif args.command == 'md':
        mainMinSizeDelete(args.targetDirectory, removeMode=args.renameMode, minSize=args.imageSize)

    elif args.command == 'sl':
        mainSearchLinks(args.keyword, args.site, args.directory, siteMode=args.pageDownload, limit=args.number)

    elif args.command == 'ys':
        mainSearchMovie(args.number, args.keyword, args.site, args.directory, 1, searchYoutube=True, music=args.addOption)

    elif args.command == 'ms':
        mainSearchMovie(args.number, args.keyword, args.site, args.directory, 1, faceMode=args.faceMode, twitterMode=args.addOption)

    elif args.command == 'ab':
        mainAutoBrowser(args.site, args.keyword, args.targetDirectory)

    elif args.command == 'si':
        mainTestInsta(args)

    elif args.command == 'sja':
        keywords = SJA_KEYWORD
        mainSearch(args.number, args.keyword, args.site, args.targetDirectory, 20, faceMode=args.faceMode, siteMode=args.pageDownload, twitterMode=args.addOption, removeMode=args.renameMode, base_directory=args.directory, sub_keywords=keywords)
    elif args.command == 'sa':
        keywords = SA_KEYWORD
        mainSearch(args.number, args.keyword, args.site, args.targetDirectory, 20, faceMode=args.faceMode, siteMode=args.pageDownload, twitterMode=args.addOption, removeMode=args.renameMode, base_directory=args.directory, sub_keywords=keywords)
    elif args.command == 'sg':
        keywords = SG_KEYWORD
        mainSearch(args.number, args.keyword, args.site, args.targetDirectory, 20, faceMode=args.faceMode, siteMode=args.pageDownload, twitterMode=args.addOption, removeMode=args.renameMode, base_directory=args.directory, sub_keywords=keywords)
    elif args.command == 'st':
        keywords = ST_KEYWORD
        mainSearch(args.number, args.keyword, args.site, args.targetDirectory, 20, faceMode=args.faceMode, siteMode=args.pageDownload, twitterMode=args.addOption, removeMode=args.renameMode, base_directory=args.directory, sub_keywords=keywords)
    elif args.command == 'se':
        keywords = SE_KEYWORD
        mainSearch(args.number, args.keyword, args.site, args.targetDirectory, 20, faceMode=args.faceMode, siteMode=args.pageDownload, twitterMode=args.addOption, removeMode=args.renameMode, base_directory=args.directory, sub_keywords=keywords)
    elif args.command == 'sml':
        keywords = SML_KEYWORD
        mainSearch(args.number, args.keyword, args.site, args.targetDirectory, 20, faceMode=args.faceMode, siteMode=args.pageDownload, twitterMode=args.addOption, removeMode=args.renameMode, base_directory=args.directory, sub_keywords=keywords)
    else:
        mainSearch(args.number, args.keyword, args.site, args.targetDirectory, 20, faceMode=args.faceMode, siteMode=args.pageDownload, twitterMode=args.addOption, removeMode=args.renameMode, base_directory=args.directory, min_size=args.imageSize)

def click(sender):
    log = sender.superview['textlog']
    number = sender.superview['number']
    number = number.text
    keywords = sender.superview['keywords']
    keywords = keywords.text
    site = sender.superview['site']
    site = site.text
    directory = sender.superview['directory']
    directory = directory.text
    directory = directory if len(directory) > 0 else './data'

    mainSearch(int(number), keywords, site, directory, 1)
    log.text = 'Done!!'

def duplicateDelete(sender):
    log = sender.superview['textlog']
    directory = sender.superview['directory']
    directory = directory.text
    keywords = sender.superview['keywords']
    keywords = keywords.text

    mainDuplicateDelete(directory, keywords)

    log.text = 'Done!!'
    
def movieSearch(sender):
    log = sender.superview['textlog']
    number = sender.superview['number']
    number = number.text
    keywords = sender.superview['keywords']
    keywords = keywords.text
    site = sender.superview['site']
    site = site.text
    directory = sender.superview['directory']
    directory = directory.text
    directory = directory if len(directory) > 0 else './data'
    
    global isys
    if isys:
        mainSearchMovie(number, keywords, site, directory, 1, searchYoutube=True)
    else:
        mainSearchMovie(number, keywords, site, directory, 1)
    log.text = 'Done!!'

def youtubeSearchOn(sender):
    global isys
    isys = not isys
    
        
    
#v = ui.load_view()
#v.present('sheet')


if __name__ == "__main__":
    main()
