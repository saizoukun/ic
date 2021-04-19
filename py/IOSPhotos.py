import platform
import logging
from PIL import Image

if 'iPhone' in platform.platform() or 'iPad' in platform.platform():
    import photos

class IOSPhotos(object):
    def __init__(self):
        self.ISIOS = self.isIOS()

    def isIOS(self):
        if 'iPhone' in platform.platform() or 'iPad' in platform.platform():
            return True
        else:
            return False

    def makeAlbum(self, title, already=True):
        if not self.ISIOS:
            return None

        try:
            for album in photos.get_albums():
                if album.title == title:
                    return album if already else None

            return photos.create_album(title)
        except Exception as e:
            logging.error(f"could not add album: {title}")
            logging.error(e)
            return None

    def getAlbum(self, title, create=False):
        if not self.ISIOS:
            return None

        try:
            for album in photos.get_smart_albums():
                if album.title == title:
                    return album
            return photos.create_album(title) if create else None
        except Exception as e:
            logging.error(f"get not album: {title}")
            logging.error(e)
            return None

    def addImage(self, album, imgFile):
        if not self.ISIOS:
            return True

        try:
            imgs = [photos.create_image_asset(imgFile)]
            if album is not None and album.can_add_assets:
                album.add_assets(imgs)
            return True
        except Exception as e:
            logging.error(f"could not add roll: {imgFile}")
            logging.error(e)
            return False

    def deleteImagesFromAlbum(self, album, title):
        if not self.ISIOS:
            return True

        try:
            assets = photos.pick_asset(album, title, True)
            photos.batch_delete(assets)
            return True
        except Exception as e:
            logging.error("could not delete")
            logging.error(e)
            return False

    def selectImagesFromAlbum(self, album, title):
        if not self.ISIOS:
            return True

        try:
            assets = photos.pick_asset(album, title, True)
            imgs = []
            for asset in assets:
                img = asset.get_image(True)
                imgs.append(asset, img.histogram())
            return imgs

        except Exception as e:
            logging.error("could not pic")
            logging.error(e)
            return False

    def selectAllImages(self):
        if not self.ISIOS:
            return None

        try:
            assets = photos.get_assets()
            imgs = []
            logging.info(len(assets))
            for asset in assets:
                img = asset.get_image(True)
                hist = img.histogram()
                imgs.append([asset, hist])
            return imgs

        except Exception as e:
            logging.error("could not pic")
            logging.error(e)
            return None

    def deleteImages(self, delete_list):
        if not self.ISIOS:
            return True

        try:
            photos.batch_delete(delete_list)
            return True
            
        except Exception as e:
            logging.error("could not delete")
            logging.error(e)
            return False
