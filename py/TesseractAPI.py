from PIL import Image, ImageOps, ImageEnhance
import re
import numpy as np
import sys
import os
import pyocr
import pyocr.builders
import logging

logger = logging.getLogger(__name__)

def filter_normal(col):
    if col >= 10:
        return 255
    else:
        return 0

def filter_reverse(col):
    if col >= 245:
        return 0
    else:
        return 255

class TesseractAPI:
    rotation_map = {
        "3": [0, 5, 10, 15, 30, 45, -5, -10, -15, -30, -45],
        "2": [0, 5, 10, -5, -10],
        "1": [0, 5, -5],
        "0": [0]
    }

    color_map = {
        "1": [1, 2, 0, 3, 4],
        "2": [1, 2, 0, 3, 4, 5, 6],
        "0": [1, 2, 0],
    }

    def __init__(self):
        tools = pyocr.get_available_tools()
        if len(tools) == 0:
            logger.error("No OCR tool found")
            sys.exit(1)
        self.tool = tools[0]
 
    def get_account_from_image(self, filename, lang="jpn", searchText="", rotate=0, add_reverse=0, debug_mode=False):
        logger.debug("[file, lang, name]->[{}, {}, {}]".format(os.path.basename(filename), lang, searchText))
        tesseract_layout = 6
        searchText = searchText.lower()
        rotations = TesseractAPI.rotation_map.get(str(rotate))
        reverses = TesseractAPI.color_map.get(str(add_reverse))

        with Image.open(filename) as img:
            base_img = img.convert('L')
        #base_img = base_img.resize((round(base_img.width*0.75), round(base_img.height*0.75)))

        gray_images = []
        for reverse in reverses:
            if reverse == 1:
                gray_img = base_img.point(filter_reverse)
            elif reverse == 2:
                gray_img = base_img.point(filter_normal)
            elif reverse == 3:
                gray_img = base_img.point(lambda x: 0 if x > 240 else 255)
            elif reverse == 4:
                gray_img = base_img.point(lambda x: 0 if x < 15 else 255)
            elif reverse == 5:
                gray_img = base_img.point(lambda x: 0 if x > 235 else 255)
            elif reverse == 6:
                gray_img = base_img.point(lambda x: 0 if x < 20 else 255)
            else:
                base_img = ImageEnhance.Contrast(base_img)
                base_img = base_img.enhance(2.0)
                base_img = base_img.quantize(64)
                #gray_img.save(os.path.join(os.path.dirname(filename), '__' + str(reverse) + '_' + os.path.basename(filename)))
                base_img = base_img.convert('L')
                gray_img = base_img.point(lambda x: 0 if x < 150 else 255)
            gray_images.append(gray_img)
            #gray_img.save(os.path.join(os.path.dirname(filename), '_' + str(reverse) + '_' + os.path.basename(filename)))
            for rotation in rotations:
                logger.debug("[reverse, rotation]: {}, {}".format(reverse, rotation))
                if rotation != 0:
                    rotate_img = gray_img.rotate(rotation)
                    readText = self.tool.image_to_string(
                        rotate_img,
                        lang=lang,
                        builder=pyocr.builders.TextBuilder(tesseract_layout=tesseract_layout)
                    )
                else:
                    readText = self.tool.image_to_string(
                        gray_img,
                        lang=lang,
                        builder=pyocr.builders.TextBuilder(tesseract_layout=tesseract_layout)
                    )

                readText = readText.lower()
                readText = re.sub(r"\r\n", ' ', readText)
                readText = re.sub(r"\n", ' ', readText)
                readTexts = [word for word in readText.split(' ') if len(word) >= len(searchText)]
                readTexts = ' '.join(readTexts)
                logger.debug("getText:[{}]".format(readTexts))

                if searchText in readText:
                    return True
                
                searchText = re.sub(r"[\d]+", '', searchText)
                if searchText in readTexts:
                    return True

                searchText = re.sub('＿', '_', searchText)
                names = [name for name in searchText.split('_') if len(name) > 0]
                if len(names) == 1 and len(names[0]) > 3:
                    names.append((names[0])[:3])
                    names.append((names[0])[-3:])
                logger.debug(names)

                for name in names:
                    if len(name) == 0:
                        continue
                    logger.debug("split_name: {}".format(name))
                    readTexts = [word for word in readText.split(' ') if len(word) >= len(name)]
                    logger.debug("readTexts:[{}]".format(readTexts))
                    if name in readTexts:
                        return True
        if debug_mode:
            for i, reverse in enumerate(reverses):
                gray_images[i].save(os.path.join(os.path.dirname(filename), '_' + str(reverse) + '_' + os.path.basename(filename)))

        return False

