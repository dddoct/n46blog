"""
乃木坂46成员汉英对照表
"""

# 成员名字映射：日文名 -> 英文名
MEMBER_NAME_MAP = {
    # 1期生
    "秋元真夏": "AkimotoManatsu",
    "生田絵梨花": "IkutaErika",
    "生駒里奈": "IkomaRina",
    "伊藤万理華": "ItoMarika",
    "井上小百合": "InoueSayuri",
    "衛藤美彩": "EtoMisa",
    "川村真洋": "KawamuraMahiro",
    "齋藤飛鳥": "SaitoAsuka",
    "斉藤優里": "SaitoYuri",
    "桜井玲香": "SakuraiReika",
    "白石麻衣": "ShiraishiMai",
    "高山一実": "TakayamaKazumi",
    "中田花奈": "NakadaKana",
    "中元日芽香": "NakamotoHimeka",
    "西野七瀬": "NishinoNanase",
    "橋本奈々未": "HashimotoNanami",
    "樋口日奈": "HiguchiHina",
    "深川麻衣": "FukagawaMai",
    "星野みなみ": "HoshinoMinami",
    "松村沙友理": "MatsumuraSayuri",
    "若月佑美": "WakatsukiYumi",
    "和田まあや": "WadaMaaya",
    
    # 2期生
    "伊藤純奈": "ItoJunna",
    "北野日奈子": "KitanoHinako",
    "相楽伊織": "SagaraIori",
    "佐々木琴子": "SasakiKotoko",
    "新内眞衣": "ShinuchiMai",
    "鈴木絢音": "SuzukiAyane",
    "寺田蘭世": "TeradaRanze",
    "堀未央奈": "HoriMiona",
    "山崎怜奈": "YamazakiRena",
    "渡辺みり愛": "WatanabeMiria",
    
    # 3期生
    "伊藤理々杏": "ItoRiria",
    "岩本蓮加": "IwamotoRenka",
    "梅澤美波": "UmezawaMinami",
    "大園桃子": "OzonoMomoko",
    "久保史緒里": "KuboShiori",
    "阪口珠美": "SakaguchiTamami",
    "佐藤楓": "SatoKaede",
    "中村麗乃": "NakamuraReno",
    "向井葉月": "MukaiHazuki",
    "山下美月": "YamashitaMizuki",
    "吉田綾乃クリスティー": "YoshidaAyanoChristie",
    "与田祐希": "YodaYuki",
    
    # 4期生
    "遠藤さくら": "EndoSakura",
    "賀喜遥香": "KakiHaruka",
    "掛橋沙耶香": "KakehashiSayaka",
    "金川紗耶": "KanagawaSaya",
    "北川悠理": "KitagawaYuri",
    "黒見明香": "KuromiHaruka",
    "佐藤璃果": "SatoRika",
    "柴田柚菜": "ShibataYuna",
    "清宮レイ": "SeimiyaRei",
    "田村真佑": "TamuraMayu",
    "筒井あやめ": "TsutsuiAyame",
    "早川聖来": "HayakawaSeira",
    "林瑠奈": "HayashiRuna",
    "松尾美佑": "MatsuoMiyu",
    "弓木奈於": "YumikiNao",
    
    # 5期生
    "五百城茉央": "IokiMao",
    "池田瑛紗": "IkedaTeresa",
    "一ノ瀬美空": "IchinoseMiku",
    "井上和": "InoueNagi",
    "岡本姫奈": "OkamotoHina",
    "小川彩": "OgawaAya",
    "奥田いろは": "OkudaIroha",
    "川崎桜": "KawasakiSakura",
    "菅原咲月": "SugawaraSatsuki",
    "冨里奈央": "TomisatoNao",
    "中西アルノ": "NakanishiAruno",
    
    # 6期生
    "愛宕心響": "AtagoKokoro",
    "大越ひなの": "OtsukiHinano",
    "小津玲奈": "OzuRena",
    "海邉朱莉": "KaibeAkari",
    "川端晃菜": "KawabataHikaru",
    "鈴木佑捺": "SuzukiYuuna",
    "長嶋凛桜": "NagashimaRio",
    "増田三莉音": "MasudaMarine",
    "森平麗心": "MorihiraReiko",
    "矢田萌華": "YadaMoka",
    
    # 其他成员
    "瀬戸口心月": "SetoguchiMitsuki",
    "川﨑桜": "KawasakiSakura",
    "長嶋 凛桜": "NagashimaRio",
    "長嶋 凛 桜": "NagashimaRio",
    "岡本 姫奈": "OkamotoHina",
    " 岡本 姫奈": "OkamotoHina",
}


def get_english_name(japanese_name):
    """
    获取成员的英文名
    如果没有找到对应关系，返回清理后的日文名
    """
    if not japanese_name:
        return "unknown"
    
    # 直接查找
    if japanese_name in MEMBER_NAME_MAP:
        return MEMBER_NAME_MAP[japanese_name]
    
    # 去除空格后查找
    name_no_space = japanese_name.replace(" ", "").replace("　", "")
    if name_no_space in MEMBER_NAME_MAP:
        return MEMBER_NAME_MAP[name_no_space]
    
    # 如果没有找到，返回清理后的原名（去除空格）
    return name_no_space


# 如果需要添加更多成员，可以在这里扩展
# 请提供汉英对照，我可以帮你添加到映射表中