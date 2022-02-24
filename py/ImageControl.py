import logging
import os
import time
import pathlib
import platform
import imghdr
from PIL import Image
import numpy as np
import threading
from concurrent.futures import ThreadPoolExecutor
import imagehash
import pickle

if 'iPhone' in platform.platform() or 'iPad' in platform.platform():
    logging.info('')
else:
    import cv2

logger = logging.getLogger(__name__)
header = {True: "cv_", False: "pil_"}

class ImageControl(object):
    def __init__(self, cvON=False, threadCount=10):
        self.ISIOS = self.isIOS()
        self.IMAGE_SIZE = (200, 200)
        self.CVON = cvON
        # 一般的なしきい値
        self.HSV_MIN = np.array([0, 30, 60])
        self.HSV_MAX = np.array([20, 150, 255])
        # 色白に対応したい
        #self.HSV_MIN = np.array([0, 1, 60])
        #self.HSV_MAX = np.array([50, 150, 255])
        # 4近傍の定義
        #self.neiborhood = np.array([[0, 1, 0], [1, 1, 1], [0, 1, 0]], np.uint8)
        # 8近傍の定義
        self.neiborhood = np.array([[1, 1, 1], [1, 1, 1], [1, 1, 1]], np.uint8)
        self.lock = threading.Lock()
        self.threadCount = threadCount
        self.executor = ThreadPoolExecutor(max_workers=self.threadCount)
        self.hist_file = "img_hist.npz"


    def __del__(self):
        self.executor.shutdown()


    def setCV(self, cvON):
        self.CVON = cvON


    def isIOS(self):
        if 'iPhone' in platform.platform() or 'iPad' in platform.platform():
            return True
        else:
            return False


    def is_jpg(self, img):
        if imghdr.what(img) != None:
            return True

        with open(img, 'rb') as myFile:
            byte = myFile.read(4)

        return byte[:2] == b'\xff\xd8'


    def getMinSize(self, imgFile):
        try:
            with Image.open(imgFile) as f:
                return min(f.width, f.height)

        except Exception:
            logger.error(f"image error: {imgFile}")
            if os.path.isfile(imgFile):
                os.remove(imgFile)
            return 0


    def getcalcHistCV(self, imgFile):
        img = cv2.imread(imgFile)
        img = cv2.resize(img, self.IMAGE_SIZE)
        return cv2.calcHist([img], [0], None, [256], [0, 256])


    def getHistgramPIL(self, imgFile):
        return Image.open(imgFile).histogram()


    def getHash(self, imgFile):
        try:
            return imagehash.average_hash(Image.open(imgFile))
        except Exception:
            logger.error(f"hash error: {imgFile}")
            if os.path.isfile(imgFile):
                os.remove(imgFile)
            return np.array([])


    def getcalcHistNoCV(self, imgFile):
        return self.getHash(imgFile)


    def getcalcHistImg(self, imgFile):
        return imagehash.average_hash(imgFile)


    def getcalcHist(self, imgFile):
        if self.CVON:
            self.lock.acquire()
            cwd = os.getcwd()
            os.chdir(os.path.dirname(imgFile))
            histogram = self.getcalcHistCV(os.path.basename(imgFile)) 
            os.chdir(cwd)
            self.lock.release()
        else:
            histogram = self.getcalcHistNoCV(imgFile)
        return histogram


    def compareHist(self, hist1, hist2):
        try:
            if self.CVON:
                ret = cv2.compareHist(hist1, hist2, 0)
                return ret == 1
            else:
                return np.array_equal(hist1, hist2)
        except Exception as e:
            logger.error("File Not compair")
            logger.error(e)
            return False


    def getMinSizeList(self, image_list):
        sizes = list(map(self.getMinSize, image_list))
        return dict(zip(image_list, sizes))


    def getCalcHistList(self, image_list):
        hists = list(map(self.getcalcHist, image_list))
        return dict(zip(image_list, hists))


    def getCalcHistDirList(self, directory, add_mode=False):
        logger.info(f"getCalcHistDirList {directory}")
        base_directory = directory
        if os.path.isdir(base_directory) == False:
            return {}
        
        base_name = os.path.basename(base_directory)

        npz_file = os.path.join(base_directory, header[self.CVON] + self.hist_file)
        image_list = sorted([img for img in os.listdir(base_directory) if os.path.splitext(img)[1] == '.png' or os.path.splitext(img)[1] =='.jpeg' or os.path.splitext(img)[1] =='.jpg' or os.path.splitext(img)[1] =='.gif'])

        if add_mode:
            logger.info(f"getCalcHistDirList: {directory}, add mode")
        elif len(image_list) == 0:
            if os.path.isfile(npz_file):
                os.remove(npz_file)
            npz_file = os.path.join(base_directory, header[not self.CVON] + self.hist_file)
            if os.path.isfile(npz_file):
                os.remove(npz_file)
            return {}

        logger.info(f"getCalcHistDirList: {directory}, {len(image_list)} Files")

        i_list = [os.path.join(base_directory, f) for f in image_list]

        logger.debug(f"getCalcHistDirList loading {directory}, {os.path.basename(npz_file)}")

        tmp_list = {}
        if os.path.isfile(npz_file):
            if self.CVON:
                tmp_list = dict(np.load(npz_file))
            else:
                with open(npz_file, 'rb') as f:
                    tmp_list = pickle.load(f)
                logger.debug(f"getCalcHistDirList loaded {directory}, {os.path.basename(npz_file)}")

                for temp_directory in tmp_list.keys():
                    temp_directory = os.path.dirname(temp_directory)
                    break
                tmp_list = {os.path.join(base_directory, os.path.basename(k)): v for k, v in tmp_list.items()} 

        if not add_mode:
            tmp_list = {k: v for k, v in tmp_list.items() if k in i_list} 

        logger.info(f"getCalcHistDirList tmp_list {directory}, {len(tmp_list)}")

        if len(tmp_list) != len(i_list) or temp_directory != base_directory:
            i_list = list(set(i_list) - set(tmp_list.keys()))

            logger.info(f"getCalcHistDirList makeHash {directory}, {len(i_list)}")
            if self.CVON:
                self.lock.acquire()
                cwd = os.getcwd()
                os.chdir(base_directory)
                image_list = [os.path.basename(f) for f in i_list]
                hists = list(map(self.getcalcHistCV, image_list))
                os.chdir(cwd)
                self.lock.release()
            else:
                hists = list(map(self.getcalcHistNoCV, i_list))

            new_list = dict(zip(i_list, hists))
            tmp_list.update(new_list)
            if self.CVON:
                np.savez(npz_file, **tmp_list)
            else:
                with open(npz_file, 'wb') as f:
                    pickle.dump(tmp_list, f)

        logger.info(f"getCalcHistDirList End {directory}, {len(tmp_list)}")

        return tmp_list


    def getCalcHistDirSearchList(self, directory, sub_dir_check=False, add_mode=False):
        base_directory = str((pathlib.Path(directory)).resolve())
        org_list = {}

        if sub_dir_check == False:
            sub_dir = os.path.basename(base_directory)
            org_list = self.getCalcHistDirList(base_directory, add_mode=add_mode)
        else:
            sub_dirs = sorted([name for name in os.listdir(directory) if name != ".DS_Store" and os.path.isdir(os.path.join(directory, name))])
            logger.info(f"org dirs: {len(sub_dirs)}")

            futures = []

            for sub_dir in sub_dirs:
                logger.info(f"target: {sub_dir}")
                image_dir = os.path.join(directory, sub_dir)
                future = self.executor.submit(self.getCalcHistDirList, image_dir, add_mode=add_mode)
                futures.append(future)

            for future in futures:
                target_list = future.result()
                org_list.update(target_list)

            logger.info(f"[dir, image] --> [{base_directory}, {len(org_list)}]")
        return org_list


    def duplicateImageList(self, image_list, delete_duplicate_list):
        logger.info("image_list read...")
        image_hist_list = self.getCalcHistList(image_list)
        new_image_list = {}
        duplicate_list = []
        for img, imgHist in image_hist_list.items():
            duplicate = False

            if self.CVON:
                for hist in new_image_list.values():
                    duplicate = self.compareHist(hist, imgHist)
                    if duplicate == True:
                        break
                    time.sleep(0.005)
            else:
                if imgHist in new_image_list.values():
                    duplicate = True

            time.sleep(0.005)

            if duplicate:
                duplicate_list.append(img)
                logger.info(f"duplicated file!: {img}")
            else:
                new_image_list[img] = imgHist

        delete_duplicate_list += duplicate_list
        return new_image_list.keys()


    def duplicateImageListList(self, org_list, new_list):
        logger.info("org_list read...")
        org_hist_list = self.getCalcHistList(org_list)
        logger.info("new_list read...")
        new_hist_list = self.getCalcHistList(new_list)
        res = []
        for img, imgHist in new_hist_list.items():
            duplicate = False

            if self.CVON:
                for hist in org_hist_list.values():
                    duplicate = self.compareHist(hist, imgHist)
                    if duplicate == True:
                        break
                    time.sleep(0.005)
            else:
                if imgHist in org_hist_list.values():
                    duplicate = True

            time.sleep(0.005)

            if duplicate:
                res.append(img)
                logger.info(f"duplicated file!: {img}")

        return res


    def duplicateImages(self, image_list):
        res = []
        new_image_list = []
        for img, imgHist in image_list:
            duplicate = False
            for new in new_image_list:
                duplicate = self.compareHist(new[1], imgHist)
                if duplicate == True:
                    break

                time.sleep(0.005)

            if duplicate:
                res.append(img)
                logger.info(f"duplicated file!: {img}")
            else:
                new_image_list.append([img, imgHist])

        return res


    def getDuplicateDirList(self, target_dir, sub_dir_check=False, reverse=True, add_mode=False, delete_mode=False):
        logger.info("getDuplicateDirList ")
        target_list = self.getCalcHistDirSearchList(target_dir, sub_dir_check=sub_dir_check, add_mode=add_mode)

        logger.info("Duplicate Check ")
        if self.CVON:

            new_list = {}
            duplicate_list = []
            new_file_list = []
            for img, imgHist in sorted(target_list.items(), key=lambda x:x[0], reverse=reverse):
                duplicate = False

                filename = os.path.basename(img)
                name = filename.split('.')[0]            
                if name.isdecimal() == False and filename in new_file_list:
                    logger.debug(f"samed file!: {img}")
                    duplicate_list.append(img)
                    continue

                for hist in new_list.values():
                    duplicate = self.compareHist(hist, imgHist)
                    if duplicate == True:
                        break
                    time.sleep(0.005)

                time.sleep(0.005)

                if duplicate:
                    logger.debug(f"duplicated file!: {img}")
                    org = {v: k for k, v in new_list.items() if v == imgHist}
                    logger.debug(f"duplicated original: {org[imgHist]}")
                    if delete_mode and os.path.isfile(img):
                        os.remove(img)
                        logger.debug(f"removed file!: {img}")
                    else:
                        duplicate_list.append(img)
                else:
                    new_list[img] = imgHist
                    new_file_list = [os.path.basename(f) for f in new_list.keys()]
                    new_file_list = set(new_file_list)

        else:
            new_list = set()
            duplicate_list = []
            for img, imgHist in sorted(target_list.items(), key=lambda x:x[0], reverse=reverse):
                if imgHist in new_list:
                    logger.debug(f"duplicated file!: {img}")
                    if delete_mode and os.path.isfile(img):
                        os.remove(img)
                        logger.debug(f"removed file!: {img}")
                    else:
                        duplicate_list.append(img)
                else:
                    new_list.add(imgHist)

                time.sleep(0.005)

        return duplicate_list        


    def getDuplicateDirAllList(self, org_dir, target_dir, nameOnly=True, removeMode=False, sub_dir_check=True, add_mode=False):
        logger.info(f"getDuplicateDirAllList: {org_dir}")
        org_list = self.getCalcHistDirSearchList(org_dir, sub_dir_check=sub_dir_check, add_mode=add_mode)
        org_file_list = [os.path.basename(f) for f in org_list.keys()]
        org_file_list = set(org_file_list)

        directory = str((pathlib.Path(target_dir)).resolve())
        sub_dirs = sorted([name for name in os.listdir(directory) if name != ".DS_Store" and os.path.isdir(os.path.join(directory, name))])
        logger.info(f"target dirs: {len(sub_dirs)}")

        res = []
        futures = []
        for sub_dir in sub_dirs:
            logger.info(f"target: {sub_dir}")
            image_dir = os.path.join(directory, sub_dir)
            future = self.executor.submit(self.execDuplicateDirAllList, org_list, org_file_list, image_dir, removeMode=removeMode)
            futures.append(future)
            time.sleep(0.001)

        for future in futures:
            res += future.result()
            time.sleep(0.001)
        return res  


    def execDuplicateDirAllList(self, org_list, org_file_list, image_dir, removeMode=False):
        delete_duplicate_list = []
        tmp_list = self.getCalcHistDirList(image_dir)
        #org_r_list = {v: k for k, v in org_list.items()}

        logger.info(f"check imageFile:{image_dir} ---> {len(org_list)}, {len(tmp_list)}")
        org_list_values = org_list.values()
        if self.CVON:
            for file, hist in tmp_list.items():
                filename = os.path.basename(file)
                name = filename.split('.')[0]
                if name.isdecimal() == False and filename in org_file_list:
                    logger.debug(f"same: {file}")
                    delete_duplicate_list.append(file)
                    continue

                for v in org_list_values:
                    if self.compareHist(hist, v):
                        logger.debug(f"duplicate: {file}")
                        delete_duplicate_list.append(file)
                        break

                    time.sleep(0.005)
        else:
            for file, hist in tmp_list.items():
                if hist in org_list_values:
                    logger.debug(f"duplicate: {file}")
                    #logger.info(f"duplicate original: {org_r_list[hist]}")
                    delete_duplicate_list.append(file)
                    continue
                time.sleep(0.005)

        if removeMode and len(delete_duplicate_list) > 0:
            logger.info(f"Delete File: {image_dir}, {len(delete_duplicate_list)}")
            for delete in delete_duplicate_list:
                os.remove(delete)
                del tmp_list[delete]
            npz_file = os.path.join(image_dir, header[self.CVON] + self.hist_file)

            if len(tmp_list) == 0:
                os.remove(npz_file)
                npz_file = os.path.join(image_dir, header[not self.CVON] + self.hist_file)
                if os.path.isfile(npz_file):
                    os.remove(npz_file)
            else:
                if self.CVON:
                    np.savez(npz_file, **tmp_list)
                else:
                    with open(npz_file, 'wb') as f:
                        pickle.dump(tmp_list, f)
        else:
            logger.info(f"Check Only:{image_dir} ---> {len(delete_duplicate_list)}")
        
        return delete_duplicate_list


    def getDuplicateDirDirList(self, sub_dirs, org_dir, target_dir, removeMode=False, add_mode=False):
        logger.info("getDuplicateDirDirList ")
        res = []
        futures = []
        for sub_dir in sub_dirs:
            future = self.executor.submit(self.execDuplicateDirList, sub_dir, org_dir, target_dir, removeMode=removeMode, add_mode=add_mode)
            futures.append(future)

        for future in futures:
            res += future.result()

        logger.info("getDuplicateDirDirList End")
        return res  


    def execDuplicateDirList(self, sub_dir, org_dir, target_dir, removeMode=False, add_mode=False):
        logger.info("execDuplicateDirList ")
        logger.info(f"target: {sub_dir}")

        delete_duplicate_list = []
        if org_dir == target_dir:
            return delete_duplicate_list
        elif os.path.isdir(os.path.join(org_dir, sub_dir)) == False:
            return delete_duplicate_list
            
        tmp_list = self.getCalcHistDirList(os.path.join(target_dir, sub_dir))
        org_list = self.getCalcHistDirList(os.path.join(org_dir, sub_dir), add_mode=add_mode)
        org_file_list = [os.path.basename(f) for f in org_list.keys()]
        org_file_list = set(org_file_list)

        logger.info(f"[dir, target_image, org_image] --> [{sub_dir}, {len(tmp_list)}, {len(org_list)}]")

        if self.CVON:
            for file, hist in tmp_list.items():
                time.sleep(0.001)                
                filename = os.path.basename(file)
                name = filename.split('.')[0]            
                if name.isdecimal() == False and filename in org_file_list:
                    logger.debug(f"same: {file}")
                    delete_duplicate_list.append(file)
                    continue
                
                for v in org_list.values():
                    if self.compareHist(hist, v):
                        logger.debug(f"duplicate: {file}")
                        delete_duplicate_list.append(file)
                        break

                    time.sleep(0.005)                

        else:
            for file, hist in tmp_list.items():
                time.sleep(0.001)                
                if hist in org_list.values():
                    logger.debug(f"duplicate: {file}")
                    delete_duplicate_list.append(file)
                    continue

        if removeMode and len(delete_duplicate_list) > 0:
            logger.info(f"Delete File: {sub_dir}, {len(delete_duplicate_list)}")
            for delete in delete_duplicate_list:
                os.remove(delete)
                del tmp_list[delete]
            npz_file = os.path.join(target_dir, sub_dir, header[self.CVON] + self.hist_file)
            if len(tmp_list) == 0:
                os.remove(npz_file)
                npz_file = os.path.join(target_dir, sub_dir, header[not self.CVON] + self.hist_file)
                if os.path.isfile(npz_file):
                    os.remove(npz_file)
            else:
                if self.CVON:
                    np.savez(npz_file, **tmp_list)
                else:
                    with open(npz_file, 'wb') as f:
                        pickle.dump(tmp_list, f)

        else:
            logger.info(f"Check Only: {len(delete_duplicate_list)}")

        if len(org_list) > 0 and len(tmp_list) > 0:
            for file in tmp_list.keys():
                base_file_name = os.path.basename(file)
                mvfile = os.path.join(org_dir, sub_dir, base_file_name)
                if not os.path.isfile(mvfile):
                    os.rename(file, mvfile)
                else:
                    log_number = 0
                    while os.path.isfile(mvfile):
                        log_number = log_number + 1
                        base_file_name = os.path.splitext(base_file_name)
                        mvfile = os.path.join(os.path.join(org_dir, sub_dir), base_file_name[0] + "_" + str(log_number).zfill(2) + base_file_name[1])
                    os.rename(file, mvfile)

        movie_list = sorted([img for img in os.listdir(os.path.join(target_dir, sub_dir)) if os.path.splitext(img)[1] == '.mp4'])
        for file in movie_list:
            base_file_name = file
            mvfile = os.path.join(org_dir, sub_dir, base_file_name)
            if not os.path.isfile(mvfile):
                os.rename(os.path.join(target_dir, sub_dir, base_file_name), mvfile)
            else:
                log_number = 0
                while os.path.isfile(mvfile):
                    log_number = log_number + 1
                    base_file_name = os.path.splitext(base_file_name)
                    mvfile = os.path.join(os.path.join(org_dir, sub_dir), base_file_name[0] + "_" + str(log_number).zfill(2) + base_file_name[1])
                os.rename(os.path.join(target_dir, sub_dir, base_file_name), mvfile)


        logger.info("checkDuplicateDirList End")
        return delete_duplicate_list


    def findRectOfTargetSkinColorSample(self, image):
        cwd = os.getcwd()
        os.chdir(os.path.dirname(image))
        img = cv2.imread(os.path.basename(image))
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV) #COLOR_BGR2HSV_FULL
        mask = cv2.inRange(hsv, self.HSV_MIN, self.HSV_MAX)
        h, w, c = img.shape
    
        # 近傍の定義
        neiborhood = np.array([[0, 1, 0], [1, 1, 1], [0, 1, 0]], np.uint8)
        # 収縮
        mask = cv2.dilate(mask, neiborhood, iterations=2)
        # 膨張
        mask = cv2.erode(mask, neiborhood, iterations=2)

        #cv2.imwrite("mask_" + os.path.basename(image), mask)

        contours, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        rects = []
        areas = []
        for contour in contours:
            approx = cv2.convexHull(contour)
            rect = cv2.boundingRect(approx)
            rects.append(np.array(rect))
            areas.append(cv2.contourArea(contour))

        print(max(areas))
        
        if len(rects) > 0:
            rect = max(rects, key=(lambda x: x[2] * x[3]))
            if rect[3] > 10:
                cv2.rectangle(img, tuple(rect[0:2]), tuple(rect[0:2] + rect[2:4]), (0, 255, 0), thickness=2)
                cv2.imwrite("rect_" + os.path.basename(image), img)

        os.chdir(cwd)

        return rect


    def findRectOfTargetSkinColor(self, image, size=64):
        try:
            img = cv2.imread(image)
            h, w, c = img.shape
            img = cv2.resize(img, (int(h/2), int(w/2)))
            h, w, c = img.shape
            hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV) #COLOR_BGR2HSV_FULL
            mask = cv2.inRange(hsv, self.HSV_MIN, self.HSV_MAX)
            org_area_size = h * w

            # 膨張
            mask = cv2.dilate(mask, self.neiborhood, iterations=2)
            contours, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
            areas = []
            for contour in contours:
                areas.append(cv2.contourArea(contour))

            if len(areas) == 0:
                logger.info("None")
                return False
            
            max_area_size = max(areas)
            if max_area_size > org_area_size / size:
                return True
            else:
                logger.info(max_area_size)
                return False
        except:
            return False


    def findRectOfTargetSkinColorList(self, directory):
        logger.info(f"findRectOfTargetSkinColorList {directory}")
        base_directory = directory
        if os.path.isdir(base_directory) == False:
            return {}

        image_list = sorted([img for img in os.listdir(base_directory) if os.path.splitext(img)[1] == '.png' or os.path.splitext(img)[1] =='.jpeg' or os.path.splitext(img)[1] =='.jpg' or os.path.splitext(img)[1] =='.gif'])

        if len(image_list) == 0:
            return {}

        i_list = [os.path.join(base_directory, f) for f in image_list]

        self.lock.acquire()
        cwd = os.getcwd()
        os.chdir(base_directory)
        results = list(map(self.findRectOfTargetSkinColor, image_list))
        os.chdir(cwd)
        self.lock.release()

        results = dict(zip(i_list, results))
        logger.info(f"findRectOfTargetSkinColorList End {directory}, {len(results)}")
        return results
