from pathlib import Path
from requests_oauthlib import OAuth2Session
import json
import logging
import time
import os
import re
from datetime import datetime, timedelta
 
logger = logging.getLogger(__name__)
 
class GooglePhotos:
    # APIのURLやスコープ
    api_url = {
        "test": "https://photoslibrary.googleapis.com/v1/mediaItems",
        "searchItems": "https://photoslibrary.googleapis.com/v1/mediaItems:search",
        "mediaItem": "https://photoslibrary.googleapis.com/v1/mediaItems/{}",
        "albums": "https://photoslibrary.googleapis.com/v1/albums",
        "upload": "https://photoslibrary.googleapis.com/v1/uploads",
        "batchCreate": "https://photoslibrary.googleapis.com/v1/mediaItems:batchCreate",
        "addMediaToAlbum": "https://photoslibrary.googleapis.com/v1/albums/{}:batchAddMediaItems",
        "removeMediaFromAlbum": "https://photoslibrary.googleapis.com/v1/albums/{}:batchRemoveMediaItems"
    }
    scope = ["https://www.googleapis.com/auth/photoslibrary"]
    sleep_time = 1
    photo_size_format = "{base}=w{width}-h{height}"
 
    def __init__(self, directory, token_path="token.json", credential_path="credentials.json"):
        self.BASE_DIRECTORY = directory
        self.API_TRY_MAX = 3
        self.token_path = os.path.join(directory, token_path)
        self.credential_path = os.path.join(directory, credential_path)
        self.google_session, logged_in = self.login()
        # ログイン処理が行われていたらトークンを保存
        # 本来自動保存だが動かないので追加
        if logged_in:
            self.save_token()
        # 有効期限の過ぎたトークンをリフレッシュ
        self.token_expires_at = datetime.fromtimestamp(self.google_session.token.get("expires_at"))
        self.check_and_refresh_token()
 
    # ログイン後に取得したトークンをtoken.jsonに保存
    def save_token(self):
        logger.debug("トークンを保存しています")
        Path(self.token_path).write_text(json.dumps(self.google_session.token))
 
    # token.jsonが存在したら読み込み
    def load_token(self):
        # 存在しない場合は期限切れのダミーを返す
        token = {
            "access_token": "",
            "refresh_token": "",
            "token_type": "",
            "expires_in": "-30",
            "expires_at": (datetime.now() - timedelta(hours=2)).timestamp()
        }
        path = Path(self.token_path)
        if path.exists():
            logger.debug("トークンをファイルから読み込んでいます")
            token = json.loads(path.read_text())
        return token
 
    def check_and_refresh_token(self):
        if datetime.now() + timedelta(minutes=10) > self.token_expires_at:
            logger.debug("トークンの期限切れが近いため、更新を行います")
            new_token = self.google_session.refresh_token(
                self.google_session.auto_refresh_url,
                **self.google_session.auto_refresh_kwargs
            )
            self.google_session.token = new_token
            self.token_expires_at = datetime.fromtimestamp(self.google_session.token.get("expires_at"))
 
    def get(self, *args, **kwargs):
        self.check_and_refresh_token()
        response = self.google_session.get(*args, **kwargs)
        if response.status_code != 200:
            logger.error("response error")
            logger.error(response)
            raise Exception("response error", response.json())

        return response
 
    def post(self, *args, **kwargs):
        self.check_and_refresh_token()
        response = self.google_session.post(*args, **kwargs)
        if response.status_code != 200:
            logger.error("response error")
            logger.error(response)
            logger.error(response.json())
            raise Exception("response error", response.json())

        return response
 
    # ログインしてセッションオブジェクトを返す
    def login(self):
        # 認証情報を読み込み
        auth_info = json.loads(Path(self.credential_path).read_text()).get("installed", None)
        assert auth_info is not None
        # トークン読み込み
        token = self.load_token()
        # トークン更新用の認証情報
        extras = {
            "client_id": auth_info.get("client_id"),
            "client_secret": auth_info.get("client_secret"),
        }
        # セッションオブジェクトを作成
        # TODO: token_updaterの引数がたぶん合わない
        google_session = OAuth2Session(
            auth_info.get("client_id"),
            scope=GooglePhotos.scope,
            token=token,
            auto_refresh_kwargs=extras,
            token_updater=self.save_token,
            auto_refresh_url=auth_info.get("token_uri"),
            redirect_uri=auth_info.get("redirect_uris")[0]
        )
        # ログインしていない場合ログインを行う
        logged_in = False
        if not google_session.authorized:
            logger.debug("ログインを行います")
            authorization_url, state = google_session.authorization_url(
                auth_info.get("auth_uri"),
                access_type="offline",
                prompt="select_account"
            )
            # 認証URLにアクセスしてコードをペースト
            logger.info("Access {} and paste code.".format(authorization_url))
            access_code = input(">>> ")
            google_session.fetch_token(
                auth_info.get("token_uri"),
                client_secret=auth_info.get("client_secret"),
                code=access_code
            )
            assert google_session.authorized
            logged_in = True
        return google_session, logged_in
 
    def duplicate_rename(self, filename, count=1):
        if os.path.exists(filename):
            ftitle, fext = os.path.splitext(filename)
            match_ = re.findall(r'(.+)\((\d{3})\)$', ftitle)
            if len(match_) == 1:
                logger.debug(match_)
                match_ = match_[0]
                ftitle = match_[0]
                count = int(match_[1]) + 1

            addPara = '(' + '{:0=3}'.format(count) + ')'
            fpath = os.path.join(ftitle + addPara + fext)
            logger.debug('Rename: %s' % fpath)
            return (self.duplicate_rename(fpath, count + 1))
        else:
            return filename
            
    def getPhotoList(self, page_num=10, page_size="100"):
        photo_list = []
        params = {
            "pageSize": str(page_size)
        }
        # リクエストボディ
        query_filter = {
            "filters": {
                "mediaTypeFilter": {
                    "mediaTypes": [
                        "PHOTO"
                    ]
                }
            }
        }
        for page_index in range(page_num):
            logger.debug("{}番目のページを取得します".format(page_index))
            # リクエスト送信
            api_url = GooglePhotos.api_url.get("searchItems")
            response = self.post(api_url, params=params, data=json.dumps(query_filter))
            assert response.status_code == 200, "Response is not 200"
            res_json = response.json()
            # 画像情報だけ抜き出し
            media_items = res_json.get("mediaItems")
            if media_items is None:
                break
            photo_list.extend(media_items)
            # 次ページのトークンを取得・設定
            if "nextPageToken" in res_json:
                params["pageToken"] = res_json.get("nextPageToken")
            else:
                break
            # 過負荷を避けるため間隔を開けてAPIを叩く
            time.sleep(GooglePhotos.sleep_time)
        return photo_list

    # ファイルのダウンロード
    def download_photo(self, directory, photo_id, album_name="default", add_datetime_header=False, overwrite=False):
        logger.debug("Downloading: {}".format(photo_id))
        for i in range(self.API_TRY_MAX):
            try:
                response = self.get(GooglePhotos.api_url.get("mediaItem").format(photo_id))
                break
            except Exception as e:
                logger.error(e)
                if i < (self.API_TRY_MAX - 1):
                    time.sleep(GooglePhotos.sleep_time)
                    
        media_item_latest = response.json()
        # MediaItemから各種情報を取得
        base_url = media_item_latest.get("baseUrl")
        metadata = media_item_latest.get("mediaMetadata")
        filename = media_item_latest.get("filename")
        # ダウンロードURLを構成
        download_url = GooglePhotos.photo_size_format.format(
            base=base_url,
            width=metadata["width"],
            height=metadata["height"]
        )
        # 保存ファイルの作成
        if add_datetime_header:
            creation_time = datetime.strptime(metadata.get("creationTime"), "%Y-%m-%dT%H:%M:%SZ")
            header = creation_time.strftime("%Y%m%d_%H%M%S_")
            filename = header + filename.lower()

        for i in range(self.API_TRY_MAX):
            try:
                response = self.get(download_url)
                break
            except Exception as e:
                logger.error(e)
                if i < (self.API_TRY_MAX - 1):
                    time.sleep(GooglePhotos.sleep_time)

        image_file = os.path.join(directory, album_name, filename.lower())
        if overwrite == False:
            image_file = self.duplicate_rename(image_file)
        # 保存
        logger.debug("Saving to {}".format(image_file))
        with open(image_file, 'wb') as f:
            f.write(response.content)

    # albunリスト取得
    def get_album_list(self, page_size=50):
        album_id_list = {}
        nextPageToken = ''
        api_url = GooglePhotos.api_url.get("albums")

        while True:
            params = {
                "pageSize": str(page_size),
                "pageToken": nextPageToken
            }
            response = self.get(api_url, params=params)
            res_json = response.json()

            # nextPageToken が入ってくるようになったため、取得したデータがなくなったら終了
            if len(res_json) == 0:
                break

            if not 'albums' in res_json:
                break;

            for album in res_json['albums']:
                # 各アルバムの名前と ID を保存
                album_id_list[album['title']] = album['id']
                mediaItemsCount = 0
                if 'mediaItemsCount' in album:
                    mediaItemsCount = int(album['mediaItemsCount'])
                logger.debug('{:20} {:4d}'.format(album['title'], mediaItemsCount))
            # nextPageToken が無ければ、取得完了
            if 'nextPageToken' not in res_json:
                break
            nextPageToken = res_json['nextPageToken']
        
        logger.info('album_count:{}'.format(len(album_id_list)))
        return album_id_list

    # Album内の画像を取得
    def get_photo_list_from_album(self, album_id="", page_size="100"):
        photo_list = []
        nextPageToken = ''
        api_url = GooglePhotos.api_url.get("searchItems")

        while True:
            condition = {
                "albumId": album_id,
                "pageSize": str(page_size),
                "pageToken": nextPageToken,
            }
            response = self.post(api_url, data=json.dumps(condition))
            res_json = response.json()
            # 画像情報だけ抜き出し
            media_items = res_json.get("mediaItems")
            if media_items is None:
                break
            photo_list.extend(media_items)
            # nextPageToken が無ければ、取得完了
            if 'nextPageToken' not in res_json:
                break
            nextPageToken = res_json['nextPageToken']
            # 過負荷を避けるため間隔を開けてAPIを叩く
            time.sleep(GooglePhotos.sleep_time)

        logger.debug('photo_count:{}'.format(len(photo_list)))
        return photo_list

    #新規アルバムを作成し album id を返す
    def create_new_album(self, album_name):
        api_url = GooglePhotos.api_url.get("albums")
        new_album = {
            "album": {"title": album_name}
        }
        response = self.post(api_url, data=json.dumps(new_album))
        res_json = response.json()
        logger.info('id: {}, title: {}'.format(res_json['id'], res_json['title']))
        return res_json['id']

    # 画像をアップロード
    def upload_image(self, image_file):
        api_url = GooglePhotos.api_url.get("upload")
        for i in range(self.API_TRY_MAX):
            try:
                # service object がアップロードに対応していないので、
                # ここでは requests を使用
                with open(str(image_file), 'rb') as image_data:
                    headers = {
                        'Content-Type': 'application/octet-stream',
                        'X-Goog-Upload-File-Name': os.path.basename(image_file),
                        'X-Goog-Upload-Protocol': "raw",
                    }
                    response = self.post(api_url, data=image_data, headers=headers)
                # アップロードの応答で upload token が返る
                upload_token = response.content.decode('utf-8')
                return upload_token
            except Exception as e:
                logger.error(e)
                if i < (self.API_TRY_MAX - 1):
                    time.sleep(GooglePhotos.sleep_time)
                else:
                    logger.error(f'upload retry out:{image_file}')

    # 画像をアップロードし、アルバムに追加する
    def upload_image_to_album(self, image_files, album_id):
        logger.info(f'Upload to {album_id}: {len(image_files)}')
        upload_tokens = []
        for image_file in image_files:
            #logger.info("image: {}".format(image_file))
            image_size = os.path.getsize(image_file)
            #logger.info("image size: {}".format(image_file))
            if image_size == 0:
                continue

            upload_token = self.upload_image(image_file)
            item = {
                    'description':'',
                    'simpleMediaItem': {
                        'uploadToken': upload_token,
                        'fileName': os.path.basename(image_file)
                        }
                    }
            #logger.info("item:", item)
            upload_tokens.append(item)
            time.sleep(GooglePhotos.sleep_time)

        logger.info(f'Uploaded: {len(image_files)}')

        api_url = GooglePhotos.api_url.get("batchCreate")
        image_file_count = len(image_files)
        uploaded_count = 0
        upload_count = 0

        while uploaded_count < image_file_count:
            upload_count = uploaded_count + 50
            new_items = {'albumId': album_id,
                        'newMediaItems': upload_tokens[uploaded_count:upload_count]}
            try:
                response = self.post(api_url, data=json.dumps(new_items))
            except Exception as err:
                logger.error(err)
                return err;
            res_json = response.json()
            status = res_json['newMediaItemResults'][0]['status']
            logger.debug('batchCreate status: {}'.format(status))
            uploaded_count = upload_count
            time.sleep(GooglePhotos.sleep_time)

        logger.info(f'Uploaded to {album_id}: {len(image_files)}')
        return status


    # 画像をアップロードし、アルバムに追加する
    def upload_image_to_album2(self, image_files, album_id):
        image_file_count = len(image_files)
        logger.info(f'Upload to {album_id}: {image_file_count}')
        upload_tokens = []
        for image_file in image_files:
            upload_token = self.upload_image(image_file)
            upload_tokens.append(upload_token)

        logger.info(f'Uploaded: {image_file_count}')

        api_url = GooglePhotos.api_url.get("addMediaToAlbum").format(album_id)
        uploaded_count = 0
        upload_count = 0

        while uploaded_count < image_file_count:
            upload_count = uploaded_count + 50
            new_items = {'mediaItemIds': upload_tokens[uploaded_count:upload_count]}
            logger.debug(json.dumps(new_items))
            response = self.post(api_url, data=json.dumps(new_items))
            res_json = response.json()
            status = not res_json
            uploaded_count = upload_count
            time.sleep(GooglePhotos.sleep_time)

        logger.info(f'Uploaded to {album_id}: {len(image_files)}')
        return status


    # アルバムから画像を削除する
    def delete_image_from_album(self, media_items, album_id):
        api_url = GooglePhotos.api_url.get("batchRemove").format(album_id)
        media_items_ids = [x.get('id') for x in media_items if x.get('id')]
        image_file_count = len(media_items_ids)
        uploaded_count = 0
        upload_count = 0

        while uploaded_count < image_file_count:
            upload_count = uploaded_count + 50
            new_items = {'mediaItemIds': media_items_ids[uploaded_count:upload_count]}
            logger.debug(json.dumps(new_items))
            response = self.post(api_url, data=json.dumps(new_items))
            res_json = response.json()
            status = not res_json
            uploaded_count = upload_count
            time.sleep(GooglePhotos.sleep_time)
        return status
