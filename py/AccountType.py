import logging
from requests.sessions import default_headers

logger = logging.getLogger(__name__)

class AccountType(object):
    SJA_KEYWORD = ["女子アナ グラビア", "女子アナ お宝", "女子アナ ヌード", "女子アナ 写真集", "女子アナ 盗撮", "女子アナ 美脚", "女子アナ twitter", "女子アナ insta", "女子アナ 流出"]
    SA_KEYWORD = ["美脚", "美巨乳", "腹筋 美巨乳", "スレンダー 美巨乳", "くびれ 美巨乳", "おっぱい",  "グラビア", "無修正", "AV", "緊縛", "パイパン", "ヌード", "おまんこ", "フェラ",  "手コキ", "カリビアン", "一本道", "Heyzo"]
    SG_KEYWORD = ["グラビア", "お宝", "ヌード", "写真集", "着エロ", "流出", "盗撮", "美脚", "twitter", "insta", "コスプレ"]
    ST_KEYWORD = ["アイコラ", "グラビア", "お宝", "濡れ場", "ヌード", "写真集", "流出", "盗撮", "美脚", "twitter", "insta"]
    SE_KEYWORD = ["色白", "自撮り", "twitter", "腹筋", "tiktok", "投稿", "彼氏", "彼女", "人妻", "寝取り", "女子大生", "寝取られ", "掲示板", "流出"]
    SML_KEYWORD = ["街角", "街撮り", "素人 街角", "素人 街撮り", "素人 盗撮", "素人 盗撮 街角", "素人 盗撮 街撮り"]
    SF_KEYWORD = ["nude", "leak", "sex", "aznude", "legs", "voyuer"]

    default_account_type = 'uraaka'

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

    account_type_uraaka_name = ("しゆ", "紫音", "えの", "たそ", "汐", "前科", "バール", "むぎ", "ことり", "あー", "性欲", "裏垢女子")
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

    account_type_user = {
        'fav_uraaka': account_type_uraaka_fav,
        'fav_eroaka': account_type_eroaka_fav,
        'fav_cosplayer': account_type_cosplayer_fav,
        'fav_couple': account_type_couple_fav,
        'uraaka': account_type_uraaka_user,
        'eroaka': account_type_eroaka_user,
        'cosplayer': account_type_cosplayer_user,
        'couple': account_type_couple_user,
        'idol': account_type_idol_user,
        'leg': account_type_leg_user,
        'photographer': account_type_photographer_user,
        'face': account_type_face_user,
    }

    account_type_name = {
        'uraaka': account_type_uraaka_name,
    }

    account_type_niji_mix_word = ("18禁", "描いて")
    account_type_word = {
        0: {
            'account_type': 'otheruser', 
            'words': ('高学歴', '子育て', '運用', 'カメコ', '活動範囲', '成人済みの男', '相談', 'bot', 'お誘い', '鍵盤', 'メルマガ', 'ピアノ', 'ガンダム', 'バイク', 'つくる', '独身男性', '動画編集', 'スタッフ', 'ライブレポ', '商用利用', 'ニュースサイト', '営業時間', '開催', '研究所', 'サラリーマン', '印刷所')
        }, 
        1: {
            'account_type': 'joso', 
            'words': ('女装', 'ニューハーフ', 'ﾆｭｰﾊｰﾌ')
        }, 
        2: {
            'account_type': 'pocha', 
            'words': ('でぶ', 'デブ', 'ぽちゃ', 'ポチャ', 'ぽっちゃり')
        }, 
        3: {
            'account_type': 'cosplayer', 
            'words': ('コスプレ', 'ｺｽﾌﾟﾚ', 'レイヤ', 'ﾚｲﾔ')
        }, 
        4: {
            'account_type': 'out', 
            'words': ('露出', 'ﾛｼｭﾂ')
        }, 
        5: {
            'account_type': 'couple', 
            'words': ('夫婦', 'スワップ', 'スワッピング', '寝取られ', 'NTR', 'ntr', 'カップル', '調教', '共有', '共同', 'ご主人', '主人公認')
        }, 
        6: {
            'account_type': 'leg', 
            'words': ('脚フェチ', '足フェチ', '美脚')
        }, 
        7: {
            'account_type': 'feti', 
            'words': ('ふぇち', 'フェチ', 'SM', '緊縛', '縛り', 'フィスト', '異物挿入', 'ポルチオ', '風俗', '倶楽部')
        }, 
        8: {
            'account_type': 'av', 
            'words': ('AV女優', '女優')
        }, 
        9: {
            'account_type': 'idol', 
            'words': ('アイドル', 'ｱｲﾄﾞﾙ', 'AV', '撮影会', 'モデル', 'グラドル', 'グラビア', '写真集', 'お仕事')
        }, 
        10: {
            'account_type': 'paipan', 
            'words': ('パイパン', 'ﾊﾟｲﾊﾟﾝ')
        }, 
        11: {
            'account_type': 'uraaka', 
            'words': ('J○', 'J〇', '女子大生', 'OL', '看護', 'ガイド', 'ｶﾞｲﾄﾞ', '人妻', 'ひとづま', 'JD', 'JK', 'ｼﾞｮｼﾀﾞｲｾｲ', '処女')
        }, 
        12: {
            'account_type': 'uraaka', 
            'words': ('半裸', 'むちむち', '尻', 'おしり', '脚', 'cup', 'かっぷ', 'カップ', '乳', 'おっぱい', 'ちっぱい', '胸', 'せんち', 'センチ', 'cm')
        }, 
        13: {
            'account_type': 'uraaka', 
            'words': ('fantia', 'booth')
        }, 
        14: {
            'account_type': 'uraaka', 
            'words': ('鍵', '退避', '避難', '凍結', 'サブ', 'sub', 'SUB', 'ツイ消し', '保存')
        }, 
        15: {
            'account_type': 'otheruser', 
            'words': ('発売', '男子', 'タダマン', 'スーツ', '紳士')
        }, 
        16: {
            'account_type': 'uraaka', 
            'words': ('質問', '自己満', '見られ', '自撮り', '承認欲求', 'センシティブ', '性癖', '惚気', '性欲', '旦那', 'しゃい')
        }, 
        17: {
            'account_type': 'otheruser', 
            'words': ('撮る', '趣味垢', '雑多垢', 'ゲーム', '実況', '募集中', '公式', '通販', 'YouTube')
        }, 
        18: {
            'account_type': 'niji', 
            'words': ('書く', '同人誌', '描い', 'イラスト', '漫画', 'まんが', '描く', 'かき', '落書き')
        }, 
        19: {
            'account_type': 'couple', 
            'words': ('オフパコ', 'ｵﾌﾊﾟｺ', 'はめ撮り', 'ハメ撮り')
        }, 
        20: {
            'account_type': 'feti', 
            'words': ('手こき', '手コキ', '回春', '責め', 'マッサージ', 'はめ撮り', 'ハメ撮り')
        }, 
        21: {
            'account_type': 'uraaka', 
            'words': ('amazon', '転載', '現実逃避', '直し', '変態', '愛して', 'エッチ', 'えっち', '女子', '美女', '本垢', '裏垢', '裏赤', 'ません', 'DM', 'ＤＭ', '腹筋', 'オナニ', 'ｵﾅﾆ')
        }
    }

    def __init__(self, account_type_class={}, account_type_ok_class={}, account_type_word={}, account_type_user={}, account_type_name={}):
        self.setAccountType(account_type_class, account_type_ok_class, account_type_word, account_type_user, account_type_name)


    def setAccountType(self, account_type_class={}, account_type_ok_class={}, account_type_word={}, account_type_user={}, account_type_name={}):
        if len(account_type_class) == 0:
            self.account_type_class = AccountType.account_type_class
        else:
            self.account_type_class = account_type_class

        if len(account_type_ok_class) == 0:
            self.account_type_ok_class = dict(self.account_type_class.items() - AccountType.account_type_no_class.items())
        else:
            self.account_type_ok_class = account_type_ok_class

        if len(account_type_word) == 0:
            self.account_type_word = AccountType.account_type_word
        else:
            self.account_type_word = account_type_word

        if len(account_type_user) == 0:
            self.account_type_user = AccountType.account_type_user
        else:
            self.account_type_user = account_type_user

        if len(account_type_name) == 0:
            self.account_type_name = AccountType.account_type_name
        else:
            self.account_type_name = account_type_name


    def get_account_type(self, name, keyword, detail, html):
        if name == None:
            # 凍結
            if 'アカウントは凍結' in html or 'account has been suspended' in html:
                name = keyword
                account_type = "lockuser"
            # NO USER
            else:
                name = ""
                account_type = "nouser"

            return name, account_type, detail

        # 非公開
        if 'imgsprite_protected_lock_gif' in html:
            account_type = "privateuser"
        else:
            account_type = "glayuser"
            if detail != None:
                detail = detail.text.strip()
                detail = detail.replace(' ', '')
                detail = detail.replace('\n', ' ')
                detail = detail.replace(',', ' ')
                logger.info(detail)

                for key, val in self.account_type_user.items():
                    if any(map(keyword.__contains__, val)):
                        account_type = key
                        break

                if account_type == "glayuser": 
                    if all(map(detail.__contains__, AccountType.account_type_niji_mix_word)):
                        account_type = "niji"
                    else:
                        for i in range(len(self.account_type_word)):
                            if any(map(detail.__contains__, self.account_type_word.get(i)['words'])):
                                account_type = self.account_type_word.get(i)['account_type']
                                break

        name = name.text.strip()
        name = name.replace(",", " ")
        if  account_type == "glayuser":
            for key, val in self.account_type_name.items():
                if any(map(name.__contains__, val)):
                    account_type = key
                    break

        return name, account_type, detail


    def check_account_type(self, account_type):
        if account_type == AccountType.account_type_class.get("uraaka") \
            or (account_type > AccountType.account_type_class.get("glayuser") \
                and account_type < AccountType.account_type_class.get("niji")):
            return True
        else:
            return False
