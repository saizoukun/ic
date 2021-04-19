from googleapiclient.discovery import build
from httplib2 import Http
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage
from pathlib import Path
import requests
import logging
import argparse
import sys
import time

API_TRY_MAX = 2
SCOPES = ['https://www.googleapis.com/auth/photoslibrary']
API_SERVICE_NAME = 'photoslibrary'
API_VERSION = 'v1'
CLIENT_SECRETS_FILE = '/content/drive/My Drive/py/google_photos_client_secrets.json'
TOKEN_FILE = '/content/drive/My Drive/py/google_photos_token.json'
# client_secrets.json の内容は以下の形式
# {
# "installed": {
#    "client_id": ".....",
#    "project_id": ".....",
#    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
#    "token_uri": "https://www.googleapis.com/oauth2/v3/token",
#    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
#    "client_secret": ".....",
#    "redirect_uris": [
#      "urn:ietf:wg:oauth:2.0:oob",
#      "http://localhost"
#    ]
#  }
# }


def get_authenticated_service(args):
    """
    Google Account を認証し service object を返す
    初回（TOKEN_FILE が存在しない）はブラウザを起動されるので、認証を行う
    次回以降は TOKEN_FILE に保存された access_token を使用
    access_token の有効期限が切れた場合は refresh_token を使用して access_token の再取得が自動で行われる
    """
    store = Storage(TOKEN_FILE)
    creds = store.get()
    if not creds or creds.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRETS_FILE, SCOPES)
        creds = tools.run_flow(flow, store, args)

    return build(API_SERVICE_NAME, API_VERSION, http=creds.authorize(Http()))


def execute_service_api(service_api, service_name):
    # 時々、エラーが発生することがあるのでリトライを行う
    # リトライ実績
    # <HttpError 500 when requesting https://photoslibrary.googleapis.com/v1/mediaItems:batchCreate?alt=json returned "Internal error encountered.">
    # <HttpError 503 when requesting https://photoslibrary.googleapis.com/v1/mediaItems:batchCreate?alt=json returned "The service is currently unavailable.">
    # <HttpError 400 when requesting https://photoslibrary.googleapis.com/v1/mediaItems:batchCreate?alt=json returned "Request must contain a valid upload token.">
    # <HttpError 400 when requesting https://photoslibrary.googleapis.com/v1/mediaItems:batchCreate?alt=json returned "Invalid album ID."
    # <HttpError 500 when requesting https://photoslibrary.googleapis.com/v1/albums?alt=json&pageSize=50&pageToken= returned "Internal error encountered.">
    # <HttpError 503 when requesting https://photoslibrary.googleapis.com/v1/albums?alt=json&pageSize=50&pageToken= returned "The service is currently unavailable.">
    # <HttpError 500 when requesting https://photoslibrary.googleapis.com/v1/albums?alt=json&pageToken=.....&pageSize=50 returned "Internal error encountered.">
    # <HttpError 503 when requesting https://photoslibrary.googleapis.com/v1/albums?alt=json&pageSize=50&pageToken=..... returned "The service is currently unavailable.">
    # リトライアウト実績
    # ERROR:__main__:HTTPSConnectionPool(host='photoslibrary.googleapis.com', port=443): Max retries exceeded with url: /v1/uploads (Caused by SSLError(SSLError("bad handshake: SysCallError(104, 'ECONNRESET')",),))
    # ERROR:__main__:service.mediaItems().batchCreate().execute() retry out
    # ERROR:__main__:service.albums().list().execute() retry out

    for i in range(API_TRY_MAX):
        try:
            response = service_api.execute()
            return response
        except Exception as e:
            logger.error(e)
            if i < (API_TRY_MAX - 1):
                time.sleep(3)
    else:
        logger.error('{} retry out'.format(service_name))
        # エラーでリトライアウトした場合は終了
        sys.exit(1)


def get_album_id_list(service):
    """
    アルバム名および対応する album id の一覧を返す
    """
    nextPageToken = ''
    album_id_list = {}
    while True:
        album_list = execute_service_api(
            service.albums().list(
                pageSize=50,
                pageToken=nextPageToken),
            'service.albums().list().execute()')
        if not album_list['albums']:
            break;

        for album in album_list['albums']:
            # 各アルバムの名前と ID を保存
            album_id_list[album['title']] = album['id']
            mediaItemsCount = 0
            if 'mediaItemsCount' in album:
                mediaItemsCount = int(album['mediaItemsCount'])
            logger.debug('{:20} {:3d}'.format(album['title'], mediaItemsCount))
        # nextPageToken が無ければ、取得完了
        if 'nextPageToken' not in album_list:
            break
        nextPageToken = album_list['nextPageToken']
    return album_id_list


def create_new_album(album_name):
    """
    新規アルバムを作成し album id を返す
    """
    logger.debug('create album: {}'.format(album_name))
    # アルバム作成は同名のアルバムが存在しても、同名の別アルバムが作成されるので
    # ここでのリトライは行わない
    new_album = {'album': {'title': album_name}}
    response = service.albums().create(body=new_album).execute()
    logger.debug('id: {}, title: {}'.format(response['id'], response['title']))
    return response['id']


def get_media_list(service, album_id):
    """
    指定されたアルバムに含まれる画像のファイル名一覧を返す
    """
    album_media_set = set()
    nextPageToken = ''
    while True:
        search = {'albumId': album_id,
                  'pageSize': 100,
                  'pageToken': nextPageToken}
        media_list = execute_service_api(
            service.mediaItems().search(body=search),
            'service.mediaItems().search().execute()')
        # album が空の場合は mediaItems 無し
        if 'mediaItems' not in media_list:
            break
        # ファイル名をリストに追加
        for media in media_list['mediaItems']:
            album_media_set.add(media['filename'])
        # nextPageToken が無い場合は、取得終了
        if 'nextPageToken' not in media_list:
            break
        nextPageToken = media_list['nextPageToken']
    return album_media_set


def upload_image(service, image_file, album_id):
    """
    画像をアップロードし、アルバムに追加する
    """
    for i in range(API_TRY_MAX):
        try:
            # service object がアップロードに対応していないので、
            # ここでは requests を使用
            with open(str(image_file), 'rb') as image_data:
                url = 'https://photoslibrary.googleapis.com/v1/uploads'
                headers = {
                    'Authorization': "Bearer " + service._http.request.credentials.access_token,
                    'Content-Type': 'application/octet-stream',
                    'X-Goog-Upload-File-Name': image_file.name,
                    'X-Goog-Upload-Protocol': "raw",
                }
                response = requests.post(url, data=image_data, headers=headers)
            # アップロードの応答で upload token が返る
            upload_token = response.content.decode('utf-8')
            break
        except Exception as e:
            logger.error(e)
            if i < (API_TRY_MAX - 1):
                time.sleep(3)
    else:
        logger.error('upload retry out')
        # エラーでリトライアウトした場合は終了
        sys.exit(1)

    new_item = {'albumId': album_id,
                'newMediaItems': [{'simpleMediaItem': {'uploadToken': upload_token}}]}
    response = execute_service_api(
        service.mediaItems().batchCreate(body=new_item),
        'service.mediaItems().batchCreate().execute()')
    status = response['newMediaItemResults'][0]['status']
    logger.debug('batchCreate status: {}'.format(status))
    return status


parser = argparse.ArgumentParser(
    description='Google Photos Uploader',
    parents=[tools.argparser])
parser.add_argument('image_dirs', nargs='+',
                    help='image directories for upload')
args = parser.parse_args()

logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
# logger.setLevel(logging.INFO)

# Google アカウントの認証を行い API 呼び出し用の service object を取得する
service = get_authenticated_service(args)

# 作成するアルバムが既に存在するかどうかを確認するためアルバムの一覧を取得する
# （アルバム名を指定して存在有無を確認する手段が無いため、最初に一覧を取得
# 　している。アルバム数が多いと時間がかかるのが難点）
album_id_list = get_album_id_list(service)

# コマンドパラメータで指定されたディレクトリ毎に、配下に画像ファイル（JPG）が
# あればディレクトリ名でアルバムを作成し、画像ファイルをアップロードしてアルバムに
# 追加する
for image_dir in args.image_dirs:
    path = Path(image_dir)
    if path.is_dir():
        images = sorted(path.glob('*.jpg'))
        if len(images) > 0:
            album_name = path.name
            # 最初に取得したアルバム一覧に存在すれば、そのアルバムに追加する
            # 存在しなければ新規アルバムを作成
            new_album = False
            if album_name in album_id_list:
                logger.info('album: {} exists'.format(album_name))
                album_id = album_id_list[album_name]
            else:
                logger.info('album: {} not exists'.format(album_name))
                album_id = create_new_album(album_name)
                new_album = True
                logger.info('album: {} created'.format(album_name))

            # アルバムが存在していた場合は、途中でエラー等により処理が中断した可能性があるため、
            # アルバム内の画像を一覧として取得し、追加対象の画像の存在有無の判定に使用する
            album_media_set = set()
            if not new_album:
                album_media_set = get_media_list(service, album_id)
                # エラーでリトライアウトした場合は終了
                if album_media_set is None:
                    sys.exit(1)

                logger.info('album: {} {} images'.format(
                    album_name, len(album_media_set)))

            album_media_count = 0
            for image_file in images:
                album_media_count += 1
                # 追加対象の画像がアルバムに存在しなければ、アップロードしアルバムに追加する
                if image_file.name not in album_media_set:
                    logger.debug('{:3d} {} uploading... '.format(
                        album_media_count, image_file.name))
                    # 画像をアップロードしアルバムに追加
                    status = upload_image(service, image_file, album_id)
                else:
                    logger.debug('{:3d} {} exists'.format(
                        album_media_count, image_file.name))
