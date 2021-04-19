import logging
import sqlite3
import datetime
import json
import os
import time
import GoogleSearch

logger = logging.getLogger(__name__)

class SqliteAPI(object):
    sql_create_object = {
        "users": "CREATE TABLE IF NOT EXISTS users (id TEXT PRIMARY KEY, name TEXT, account_type TEXT, detail TEXT, image_count INTEGER, movie_count INTEGER)",
        "users_dl_info": "CREATE TABLE IF NOT EXISTS users_dl_info (id TEXT PRIMARY KEY, directory INTEGER, image_count INTEGER, movie_count INTEGER)",
        "account_type": "CREATE TABLE IF NOT EXISTS account_type (id INTEGER PRIMARY KEY, name TEXT, directory TEXT, download INTEGER)",
        "directory_info": "CREATE TABLE IF NOT EXISTS directory_info (id INTEGER PRIMARY KEY, directory TEXT)",
        "account_type_word": "CREATE TABLE IF NOT EXISTS account_type_word (id INTEGER PRIMARY KEY, account_type TEXT, check_type TEXT, priority INTEGER, word TEXT)",
    }

    sql_drop_object = {
        "users": "DROP TABLE users",
        "users_dl_info": "DROP TABLE users_dl_info",
        "account_type": "DROP TABLE account_type",
        "directory_info": "DROP TABLE directory_info",
        "account_type_word": "DROP TABLE account_type_word",
    }

    sql_users = {
        "select_where_id": "SELECT * FROM users WHERE id = ? and movie_count > ?",
        "select_all": "SELECT * FROM users WHERE movie_count > ? ORDER BY id ASC",
        "search_where_name": "SELECT * FROM users WHERE name = ? and movie_count > ?",
        "search_where_type": "SELECT * FROM users WHERE type = ? and movie_count > ? ORDER BY id ASC",
        "insert": "INSERT INTO users VALUES(?, ?, ?, ?, ?, ?)",
        "update_user_info": "UPDATE users SET name = ?, account_type = ?, detail = ? WHERE id = ?",
        "update_user_count": "UPDATE users SET image_count = ?, movie_count = ? WHERE id = ?",
        "delete": "DELETE FROM users where id = ?",
        "delete_all": "DELETE FROM users",
    }

    sql_users_dl_info = {
        "select_where_id": "SELECT * FROM users_dl_info WHERE id = ? ORDER BY directory ASC",
        "insert": "INSERT INTO users_dl_info VALUES(?, ?, ?, ?)",
        "update": "UPDATE users_dl_info SET image_count = ?, movie_count = ? WHERE id = ? AND directory = ?",
        "delete": "DELETE users_dl_info WHERE id = ? AND directory = ?",
    }

    sql_directory_info = {
        "delete": "DELETE FROM directory_info",
        "insert": "INSERT INTO directory_info VALUES (?, ?)",
        "select": "SELECT * FROM directory_info ORDER BY id ASC",
        "select_where_id": "SELECT * FROM directory_info WHERE id = ?",
    }

    sql_account_type_info = {
        "delete": "DELETE FROM account_type",
        "insert": "INSERT INTO account_type(name, directory, download) VALUES (?, ?, ?)",
        "select": "SELECT * FROM account_type ORDER BY id ASC",
        "select_where_dl": "SELECT * FROM account_type WHERE download = 1 ORDER BY id ASC",
        "select_where_id": "SELECT * FROM account_type WHERE id = ?",
        "select_where_name": "SELECT * FROM account_type WHERE name = ?",
    }

    sql_account_type_word = {
        "insert": "INSERT INTO account_type_word (account_type, check_type, priority, word) VALUES(?, ?, ?, ?)",
        "select_all": "SELECT * FROM account_type_word ORDER BY priority ASC, id ASC",
        "select_where_check_type": "SELECT * FROM account_type_word WHERE check_type = ? ORDER BY priority ASC, id ASC",
        "select_where_priority": "SELECT * FROM account_type_word WHERE priority = ? ORDER BY priority ASC, id ASC",
        "select_where_account_type": "SELECT * FROM account_type_word WHERE account_type = ? ORDER BY priority ASC, id ASC",
        "delete_all": "DELETE FROM account_type_word",
        "update_where_word": "UPDATE account_type_word SET account_type = ?, check_type = ?, priority = ? WHERE word = ?",
    }

    account_type_class = {
        'uraaka': 'dl_normal', 
        'nouser': 'dl_nouser', 
        'lockuser': 'dl_stopuser', 
        'privateuser': 'dl_stopuser', 
        'glayuser': 'dl_glayuser', 
        'couple': 'dl_couple', 
        'cosplayer': 'dl_cos', 
        'out': 'dl_out', 
        'idol': 'dl_idol', 
        'joso': 'dl_joso', 
        'face': 'dl_face', 
        'leg': 'dl_leg', 
        'av': 'dl_av', 
        'niji': 'dl_niji', 
        'paipan': 'dl_paipan', 
        'feti': 'dl_feti', 
        'eroaka': 'dl_eroaka', 
        'pocha': 'dl_pocha', 
        'otheruser': 'dl_otheruser',
        'photographer': 'dl_photographer',
        'fav_uraaka': 'fav_normal', 
        'fav_eroaka': 'fav_eroaka', 
        'fav_cosplayer': 'fav_cos', 
        'fav_couple': 'fav_couple', 
        'temp': 'dl_temp', 
        'no_dl': 'no_dl', 
    }

    account_type_no_class = {
        'nouser': 'dl_nouser', 
        'lockuser': 'dl_stopuser', 
        'privateuser': 'dl_stopuser', 
        'glayuser': 'dl_glayuser', 
        'otheruser': 'dl_otheruser',
        'no_dl': 'no_dl', 
    }


    def __init__(self, base_directory="", db_name="twitter.db"):
        if len(base_directory) == 0:
            self.DRIVE_PATH = "/content/drive/My Drive/Colab Notebooks/"
        else:
            self.DRIVE_PATH = base_directory

        self.DB_NAME = db_name
        self.conn = sqlite3.connect(os.path.join(self.DRIVE_PATH, self.DB_NAME))
        self.conn.row_factory = sqlite3.Row
        self.createObject()
        self.accountTypeInfo, self.downloadDirectoryInfo = self.getAccountTypeInfo()

        if len(self.accountTypeInfo) == 0:
            self.insertInformation()
            self.accountTypeInfo, self.downloadDirectoryInfo = self.getAccountTypeInfo()


    def __del__(self):
        self.conn.close()


    def createObject(self):
        cur = self.conn.cursor()
        for sql in SqliteAPI.sql_create_object.values():
            cur.execute(sql, [])
        
        self.conn.commit()
        cur.close()


    def dropObject(self, targetObject):
        logger.info(f"target: {targetObject}")
        if targetObject in SqliteAPI.sql_drop_object.keys():
            cur = self.conn.cursor()
            cur.execute(SqliteAPI.sql_drop_object.get(targetObject), [])
            self.conn.commit()
            cur.close()


    def executeSelect(self, sql, values=[], all=False):
        cur = self.conn.cursor()
        
        try:
            cur.execute(sql, values)
            if all:
                result = cur.fetchall()
            else:
                result = cur.fetchone()
            cur.close()
            return result
        except sqlite3.Error as e:
            logger.error(e)
            logger.error(f"sql: {sql}")
            logger.error(f"values: {values}")
            if all:
                return []
            else:
                return ""


    def executeSql(self, sql, values=[]):
        cur = self.conn.cursor()
        
        try:
            if len(values) > 0:
                cur.executemany(sql, values)
            elif len(values) == 0:
                cur.execute(sql)
            else:
                cur.execute(sql, values[0])
            self.conn.commit()
            cur.close()
            return True
        except sqlite3.Error as e:
            logger.error(e)
            logger.error(f"sql: {sql}")
            logger.error(f"values: {values}")
            return False


    def getDirectoryInfo(self):
        directoryInfo = {}
        results = self.executeSelect(SqliteAPI.sql_directory_info.get("select"), [], True)
        for info in results:
            directoryInfo[info[0]] = info[1]
        return directoryInfo


    def getAccountTypeInfo(self):
        accountTypeInfo = {}
        downloadDirectoryInfo = {}
        results = self.executeSelect(SqliteAPI.sql_account_type_info.get("select"), [], True)
        for info in results:
            accountTypeInfo[info[1]] = info[2]

        results = self.executeSelect(SqliteAPI.sql_account_type_info.get("select_where_dl"), [], True)
        for info in results:
            downloadDirectoryInfo[info[1]] = info[2]
        return accountTypeInfo, downloadDirectoryInfo


    def userSearch(self, id="", name="", type="", movie=False):
        sql = ""
        key = ""
        movie_count = 0 if movie else -1
        if len(id) > 0:
            sql = SqliteAPI.sql_users.get("select_where_id")
            key = id
        elif len(name) > 0:
            sql = SqliteAPI.sql_users.get("select_where_name")
            key = name
        elif len(type) > 0:
            sql = SqliteAPI.sql_users.get("select_where_type")
            key = type
        else:
            sql = SqliteAPI.sql_users.get("select_all")
            return self.executeSelect(sql, [movie_count], all=True)

        users = self.executeSelect(sql, [key, movie_count])
        return users


    def getUserInfo(self, id):
        if len(id) == 0:
            return {}

        return self.executeSelect(SqliteAPI.sql_users.get("select_where_id"), [(id)])


    def updateUserInfo(self, userInfo):
        if len(id) == 0:
            return False

        return self.executeSql(
            SqliteAPI.sql_users.get('update_user_info'), 
                [(
                    userInfo['name'], 
                    userInfo['account_type'], 
                    userInfo['detail'],
                    userInfo['id'])])


    def updateUserCount(self, userInfo):
        if len(id) == 0:
            return False

        return self.executeSql(
            SqliteAPI.sql_users.get('update_user_count'), 
                [(
                    userInfo['image_count'], 
                    userInfo['movie_count'],
                    userInfo['id'])])


    def updateUser(self, userInfo):
        if len(userInfo) == 0:
            return False

        result = self.executeSql(
            SqliteAPI.sql_users.get('update_user_info'), 
                [(
                    userInfo['name'], 
                    userInfo['account_type'], 
                    userInfo['detail'],
                    userInfo['id'])])
        if result:
            return self.executeSql(
                SqliteAPI.sql_users.get('update_user_count'), 
                    [(
                        userInfo['image_count'], 
                        userInfo['movie_count'],
                        userInfo['id'])])
        else:
            return False


    def insertUserInfo(self, userInfo):
        if len(userInfo) == 0:
            return False

        return self.executeSql(
            SqliteAPI.sql_users.get('insert'), 
                [(
                    str(userInfo['id']), 
                    userInfo['name'], 
                    userInfo['account_type'], 
                    str(userInfo['detail']),
                    str(userInfo['image_count']), 
                    str(userInfo['movie_count']))])


    def writeUserInfo(self, id, userInfo):
        if self.userSearch(id=id):
            logger.debug(f"updateUser:{id}")
            return self.updateUser(userInfo)
        else:
            logger.debug(f"insertUser:{id}")
            return self.insertUserInfo(userInfo)


    def insertWord(self, account_type, check_type, priority, words):
        values = []
        for word in words:
            values.append((account_type, check_type, priority, word))

        self.executeSql(SqliteAPI.sql_account_type_word.get("insert"), values)


    def selectWord(self, account_type="", check_type="", priority=""):
        sql = ""
        key = ""
        if len(account_type) > 0:
            sql = SqliteAPI.sql_account_type_word.get("select_where_account_type")
            key = account_type
        elif len(check_type) > 0:
            sql = SqliteAPI.sql_account_type_word.get("select_where_check_type")
            key = check_type
        elif len(priority) > 0:
            sql = SqliteAPI.sql_account_type_word.get("select_where_priority")
            key = priority
        else:
            sql = SqliteAPI.sql_account_type_word.get("select_all")
            return self.executeSelect(sql, [], all=True)

        words = self.executeSelect(sql, [key], all=True)
        return words


    def getAccountTypeWords(self):
        results = self.selectWord(check_type="word")
        account_type_words = {}
        for row in results:
            word = row['word']
            account_type = row['account_type']
            priority = row['priority']
            if account_type_words.get(priority):
                words = account_type_words[priority]['words']
            else:
                words = []
            words.append(word)

            account_type_word = {}
            account_type_word['account_type'] = account_type
            account_type_word['words'] = words        

            account_type_words[priority] = account_type_word

        results = {}
        for key, val in account_type_words.items():
            account_type_word = {}
            account_type_word['account_type'] = val['account_type']
            account_type_word['words'] = tuple(val['words'])
            results[key] = account_type_word

        return results


    def getAccountTypeUsers(self, check_type):
        results = self.selectWord(check_type=check_type)
        account_type_users = {}
        for row in results:
            word = row['word']
            account_type = row['account_type']
            if account_type_users.get(account_type):
                words = account_type_users[account_type]
            else:
                words = []
            words.append(word)
            account_type_users[account_type] = words

        results = {}
        for key, val in account_type_users.items():
            results[key] = tuple(val)

        return results


    def insertInformation(self):
        cur = self.conn.cursor()
        account_type_class = SqliteAPI.account_type_class
        values = []
        for key, val in account_type_class.items():
            if key in SqliteAPI.account_type_no_class.keys():
                download = 0
            else:
                download = 1
            values.append((key, val, download))
        
        self.executeSql(SqliteAPI.sql_account_type_info.get("delete"), [])
        self.executeSql(SqliteAPI.sql_account_type_info.get("insert"), values)

        self.conn.commit()
        cur.close()


    def insertDefaultWord(self):
        values = []
        cur = self.conn.cursor()
        cur.execute(SqliteAPI.sql_account_type_word.get("delete_all"), [])
        self.conn.commit()

        words =["高学歴", "子育て", "運用", "カメコ", "活動範囲", "成人済みの男", "相談", "bot", "お誘い", "鍵盤", "メルマガ", "ピアノ", "ガンダム", "バイク", "つくる", "独身男性", "動画編集", "スタッフ", "ライブレポ", "商用利用", "ニュースサイト", "営業時間", "開催", "研究所", "サラリーマン", "印刷所"]
        for word in words:
            values.append(("otheruser", "word", 0, word))
        words = ["女装", "ニューハーフ", "ﾆｭｰﾊｰﾌ"]
        for word in words:
            values.append(("joso", "word", 1, word))
        words = ["でぶ", "デブ", "ぽちゃ", "ポチャ", "ぽっちゃり"]
        for word in words:
            values.append(("pocha", "word", 2, word))
        words = ["コスプレ", "ｺｽﾌﾟﾚ", "レイヤ", "ﾚｲﾔ"]
        for word in words:
            values.append(("cosplayer", "word", 3, word))
        words = ["露出", "ﾛｼｭﾂ"]
        for word in words:
            values.append(("out", "word", 4, word))
        words = ["夫婦", "スワップ", "スワッピング", "寝取られ", "NTR", "ntr", "カップル", "調教", "共有", "共同", "ご主人", "主人公認"]
        for word in words:
            values.append(("couple", "word", 5, word))
        words = ["脚フェチ", "足フェチ", "美脚"]
        for word in words:
            values.append(("leg", "word", 6, word))
        words = ["ふぇち", "フェチ", "SM", "緊縛", "縛り", "フィスト", "異物挿入", "ポルチオ", "風俗", "倶楽部"]
        for word in words:
            values.append(("feti", "word", 7, word))
        words = ["AV女優", "女優"]
        for word in words:
            values.append(("av", "word", 8, word))
        words = ["アイドル", "ｱｲﾄﾞﾙ", "AV", "撮影会", "モデル", "グラドル", "グラビア", "写真集", "お仕事"]
        for word in words:
            values.append(("idol", "word", 9, word))
        words = ["パイパン", "ﾊﾟｲﾊﾟﾝ"]
        for word in words:
            values.append(("paipan", "word", 10, word))
                        # 裏垢
        words = ["J○", "J〇", "女子大生", "OL", "看護", "ガイド", "ｶﾞｲﾄﾞ", "人妻", "ひとづま", "JD", "JK", "ｼﾞｮｼﾀﾞｲｾｲ", "処女"]
        for word in words:
            values.append(("uraaka", "word", 11, word))
        words = ["半裸", "むちむち", "尻", "おしり", "脚", "cup", "かっぷ", "カップ", "乳", "おっぱい", "ちっぱい", "胸" , "せんち", "センチ", "cm"]
        for word in words:
            values.append(("uraaka", "word", 12, word))
        words = ["fantia", "booth"]
        for word in words:
            values.append(("uraaka", "word", 13, word))
        words = ["鍵", "退避", "避難", "凍結", "サブ", "sub", "SUB", "ツイ消し", "保存"]
        for word in words:
            values.append(("uraaka", "word", 14, word))
        words = ["発売", "男子", "タダマン", "スーツ", "紳士"]
        for word in words:
            values.append(("otheruser", "word", 15, word))
        words = ["質問", "自己満", "見られ", "自撮り", "承認欲求", "センシティブ", "性癖", "惚気", "性欲", "旦那", "しゃい"]
        for word in words:
            values.append(("uraaka", "word", 16, word))
        words = ["撮る", "趣味垢", "雑多垢", "ゲーム", "実況", "募集中", "公式", "通販", "YouTube"]
        for word in words:
            values.append(("otheruser", "word", 17, word))
                        # niji
        words = ["書く", "同人誌", "描い", "イラスト", "漫画", "まんが", "描く", "かき", "落書き"]
        for word in words:
            values.append(("niji", "word", 18, word))
        words = ["オフパコ", "ｵﾌﾊﾟｺ", "はめ撮り", "ハメ撮り"]
        for word in words:
            values.append(("couple", "word", 19, word))
        words = ["手こき", "手コキ", "回春", "責め", "マッサージ", "はめ撮り", "ハメ撮り"]
        for word in words:
            values.append(("feti", "word", 20, word))
        words = ["amazon", "転載", "現実逃避", "直し", "変態", "愛して", "エッチ", "えっち", "女子", "美女", "本垢", "裏垢", "裏赤", "ません", "DM", "ＤＭ", "腹筋", "オナニ", "ｵﾅﾆ"]
        for word in words:
            values.append(("uraaka", "word", 21, word))

        #user
        account_type_uraaka_fav = ("sena__cas__", "als__kono", "leyleyo0", "___00or", 
            "kom_inu_AB", "o__ililu_o", "sumire1544", "yb_huku", "sena_0oxx", "_oOS2_", "memmimu", "ohayoo_bomb", 
            "________io___", "HOL59918201", "ma__yu00", "maimai_22120", "chaco__g", "Re_mules", "33____chan", 
            "chikuwaaaan_88", "kom_inu", "310mint___", "aika_memories03", 
            "_____0X0XO", "_tofumyon", "147cmworld", "620_KaRen", )
        account_type_uraaka_user =("__miic__", "__no_w_here__", "7z7zzzz", "8_muu_8", "chiiconyan", "A_________xxxX", )
        account_type_eroaka_fav = ("eno_mm6", "eno_mm4", "chi____puri", "anzu_uX", "ai_xxi5", "sn0wsheep", "otama_geco", )
        account_type_eroaka_user = ("00fin16", )
        account_type_couple_fav = ("mochikichi16", "aki_takkun2", )
        account_type_couple_user = ("8mm_kuzira", )
        account_type_idol_user = ("airishimizu", "omotemaru", "enako_cos")
        account_type_face_user = ("LczLst", "5roume", )
        account_type_cosplayer_fav = ("amimutam", )
        account_type_cosplayer_user = ("_m_a_f_o_i_", )
        account_type_leg_user = ("aya__1110", )
        account_type_photographer_user = ("AzusaTsuki", "TheGoddessBound", )
        account_type_nodl_user = ()

        for user in account_type_uraaka_fav:
            values.append(("fav_uraaka", "user", 0, user))

        for user in account_type_uraaka_user:
            values.append(("uraaka", "user", 0, user))

        for user in account_type_eroaka_fav:
            values.append(("fav_eroaka", "user", 0, user))

        for user in account_type_eroaka_user:
            values.append(("eroaka", "user", 0, user))

        for user in account_type_couple_fav:
            values.append(("fav_couple", "user", 0, user))

        for user in account_type_couple_user:
            values.append(("couple", "user", 0, user))

        for user in account_type_idol_user:
            values.append(("idol", "user", 0, user))

        for user in account_type_face_user:
            values.append(("face", "user", 0, user))

        for user in account_type_cosplayer_fav:
            values.append(("fav_cosplayer", "user", 0, user))

        for user in account_type_cosplayer_user:
            values.append(("cosplayer", "user", 0, user))

        for user in account_type_photographer_user:
            values.append(("photographer", "user", 0, user))

        for user in account_type_leg_user:
            values.append(("leg", "user", 0, user))

        for user in account_type_nodl_user:
            values.append(("no_dl", "user", 0, user))

        cur.executemany(SqliteAPI.sql_account_type_word.get("insert"), values)
        self.conn.commit()
        cur.close()


    def deleteUsers(self):
        cur = self.conn.cursor()
        cur.execute(SqliteAPI.sql_users.get("delete_all"), [])
        self.conn.commit()
        cur.close()
