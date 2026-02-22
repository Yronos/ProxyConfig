#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
filter_facebook.py
从源规则文件中过滤/添加规则，生成精简版规则文件
只进行本地文件处理
"""

import os
import re
from datetime import datetime

# ============================================================
# 用户配置区域
# ============================================================

# 输出文件名（不含路径，自动放到 ./rules/lite/ 下）
OUTPUT_FILENAME = "Meta.list"

# 源文件路径
SOURCE_FILE = "./rules/surge/Facebook.list"

# 输出目录
OUTPUT_DIR = "./rules/lite"

# ---------- 删除规则列表 ----------
# 格式与规则文件一致，脚本会从源文件中剔除这些规则
# 匹配时忽略大小写、忽略行尾空白
RULES_TO_REMOVE = [
    # "DOMAIN,aboutfacebook.com",
    # "DOMAIN-SUFFIX,aboutfacebook.com",
    # "DOMAIN-KEYWORD,facebook",
    # "IP-CIDR,108.168.176.192/26,no-resolve",
    # "IP-ASN,32934,no-resolve",
    # "IP-CIDR6,2c0f:f248::/32,no-resolve",
    "DOMAIN-SUFFIX,acebooik.com",
    "DOMAIN-SUFFIX,acebook.com",
    "DOMAIN-SUFFIX,www-facebook.com",
    "DOMAIN-SUFFIX,wwwfacebok.com",
    "DOMAIN-SUFFIX,wwwfacebook.com",
    "DOMAIN-SUFFIX,wwwinstagram.com",
    "DOMAIN-SUFFIX,wwwmfacebook.com",
    "DOMAIN-SUFFIX,intgram.com",
    "DOMAIN-SUFFIX,intagrm.com",
    "DOMAIN-SUFFIX,intagram.com",
    "DOMAIN-SUFFIX,instagran.com",
    "DOMAIN-SUFFIX,instagranm.com",
    "DOMAIN-SUFFIX,instagrem.com",
    "DOMAIN-SUFFIX,instagrm.com",
    "DOMAIN-SUFFIX,instagtram.com",
    "DOMAIN-SUFFIX,instagy.com",
    "DOMAIN-SUFFIX,instamgram.com",
    "DOMAIN-SUFFIX,instangram.com",
    "DOMAIN-SUFFIX,faacebok.com",
    "DOMAIN-SUFFIX,faacebook.com",
    "DOMAIN-SUFFIX,faasbook.com",
    "DOMAIN-SUFFIX,facbebook.com",
    "DOMAIN-SUFFIX,facbeok.com",
    "DOMAIN-SUFFIX,facboo.com",
    "DOMAIN-SUFFIX,facbook.com",
    "DOMAIN-SUFFIX,facbool.com",
    "DOMAIN-SUFFIX,facboox.com",
    "DOMAIN-SUFFIX,faccebook.com",
    "DOMAIN-SUFFIX,faccebookk.com",
    "DOMAIN-SUFFIX,facdbook.com",
    "DOMAIN-SUFFIX,facdebook.com",
    "DOMAIN-SUFFIX,face-book.com",
    "DOMAIN-SUFFIX,faceabook.com",
    "DOMAIN-SUFFIX,facebboc.com",
    "DOMAIN-SUFFIX,facebbook.com",
    "DOMAIN-SUFFIX,facebboook.com",
    "DOMAIN-SUFFIX,facebcook.com",
    "DOMAIN-SUFFIX,facebdok.com",
    "DOMAIN-SUFFIX,facebgook.com",
    "DOMAIN-SUFFIX,facebhook.com",
    "DOMAIN-SUFFIX,facebkkk.com",
    "DOMAIN-SUFFIX,facebo-ok.com",
    "DOMAIN-SUFFIX,faceboak.com",
    "DOMAIN-SUFFIX,facebock.com",
    "DOMAIN-SUFFIX,facebocke.com",
    "DOMAIN-SUFFIX,facebof.com",
    "DOMAIN-SUFFIX,faceboik.com",
    "DOMAIN-SUFFIX,facebok.com",
    "DOMAIN-SUFFIX,facebokbook.com",
    "DOMAIN-SUFFIX,facebokc.com",
    "DOMAIN-SUFFIX,facebokk.com",
    "DOMAIN-SUFFIX,facebokok.com",
    "DOMAIN-SUFFIX,faceboks.com",
    "DOMAIN-SUFFIX,facebol.com",
    "DOMAIN-SUFFIX,facebolk.com",
    "DOMAIN-SUFFIX,facebomok.com",
    "DOMAIN-SUFFIX,faceboo.com",
    "DOMAIN-SUFFIX,facebooa.com",
    "DOMAIN-SUFFIX,faceboob.com",
    "DOMAIN-SUFFIX,faceboobok.com",
    "DOMAIN-SUFFIX,facebooc.com",
    "DOMAIN-SUFFIX,faceboock.com",
    "DOMAIN-SUFFIX,facebood.com",
    "DOMAIN-SUFFIX,facebooe.com",
    "DOMAIN-SUFFIX,faceboof.com",
    "DOMAIN-SUFFIX,facebooi.com",
    "DOMAIN-SUFFIX,facebooik.com",
    "DOMAIN-SUFFIX,facebooik.org",
    "DOMAIN-SUFFIX,facebooj.com",
    "DOMAIN-SUFFIX,faacebok.com",
    "DOMAIN-SUFFIX,faacebook.com",
    "DOMAIN-SUFFIX,faasbook.com",
    "DOMAIN-SUFFIX,facbebook.com",
    "DOMAIN-SUFFIX,facbeok.com",
    "DOMAIN-SUFFIX,facboo.com",
    "DOMAIN-SUFFIX,facbook.com",
    "DOMAIN-SUFFIX,facbool.com",
    "DOMAIN-SUFFIX,facboox.com",
    "DOMAIN-SUFFIX,faccebook.com",
    "DOMAIN-SUFFIX,faccebookk.com",
    "DOMAIN-SUFFIX,facdbook.com",
    "DOMAIN-SUFFIX,facdebook.com",
    "DOMAIN-SUFFIX,face-book.com",
    "DOMAIN-SUFFIX,faceabook.com",
    "DOMAIN-SUFFIX,facebboc.com",
    "DOMAIN-SUFFIX,facebbook.com",
    "DOMAIN-SUFFIX,facebboook.com",
    "DOMAIN-SUFFIX,facebcook.com",
    "DOMAIN-SUFFIX,facebdok.com",
    "DOMAIN-SUFFIX,facebgook.com",
    "DOMAIN-SUFFIX,facebhook.com",
    "DOMAIN-SUFFIX,facebkkk.com",
    "DOMAIN-SUFFIX,facebo-ok.com",
    "DOMAIN-SUFFIX,faceboak.com",
    "DOMAIN-SUFFIX,facebock.com",
    "DOMAIN-SUFFIX,facebocke.com",
    "DOMAIN-SUFFIX,facebof.com",
    "DOMAIN-SUFFIX,faceboik.com",
    "DOMAIN-SUFFIX,facebok.com",
    "DOMAIN-SUFFIX,facebokbook.com",
    "DOMAIN-SUFFIX,facebokc.com",
    "DOMAIN-SUFFIX,facebokk.com",
    "DOMAIN-SUFFIX,facebokok.com",
    "DOMAIN-SUFFIX,faceboks.com",
    "DOMAIN-SUFFIX,facebol.com",
    "DOMAIN-SUFFIX,facebolk.com",
    "DOMAIN-SUFFIX,facebomok.com",
    "DOMAIN-SUFFIX,faceboo.com",
    "DOMAIN-SUFFIX,facebooa.com",
    "DOMAIN-SUFFIX,faceboob.com",
    "DOMAIN-SUFFIX,faceboobok.com",
    "DOMAIN-SUFFIX,facebooc.com",
    "DOMAIN-SUFFIX,faceboock.com",
    "DOMAIN-SUFFIX,facebood.com",
    "DOMAIN-SUFFIX,facebooe.com",
    "DOMAIN-SUFFIX,faceboof.com",
    "DOMAIN-SUFFIX,facebooi.com",
    "DOMAIN-SUFFIX,facebooik.com",
    "DOMAIN-SUFFIX,facebooik.org",
    "DOMAIN-SUFFIX,facebooj.com",
    "DOMAIN-SUFFIX,facebool.com",
    "DOMAIN-SUFFIX,facebool.info",
    "DOMAIN-SUFFIX,facebooll.com",
    "DOMAIN-SUFFIX,faceboom.com",
    "DOMAIN-SUFFIX,faceboon.com",
    "DOMAIN-SUFFIX,faceboonk.com",
    "DOMAIN-SUFFIX,faceboooik.com",
    "DOMAIN-SUFFIX,faceboook.com",
    "DOMAIN-SUFFIX,faceboop.com",
    "DOMAIN-SUFFIX,faceboot.com",
    "DOMAIN-SUFFIX,faceboox.com",
    "DOMAIN-SUFFIX,facebopk.com",
    "DOMAIN-SUFFIX,facebpook.com",
    "DOMAIN-SUFFIX,facebuk.com",
    "DOMAIN-SUFFIX,facebuok.com",
    "DOMAIN-SUFFIX,facebvook.com",
    "DOMAIN-SUFFIX,facebyook.com",
    "DOMAIN-SUFFIX,facebzook.com",
    "DOMAIN-SUFFIX,facecbgook.com",
    "DOMAIN-SUFFIX,facecbook.com",
    "DOMAIN-SUFFIX,facecbook.org",
    "DOMAIN-SUFFIX,facecook.com",
    "DOMAIN-SUFFIX,facecook.org",
    "DOMAIN-SUFFIX,facedbook.com",
    "DOMAIN-SUFFIX,faceebok.com",
    "DOMAIN-SUFFIX,faceebook.com",
    "DOMAIN-SUFFIX,faceebot.com",
    "DOMAIN-SUFFIX,facegbok.com",
    "DOMAIN-SUFFIX,facegbook.com",
    "DOMAIN-SUFFIX,faceobk.com",
    "DOMAIN-SUFFIX,faceobok.com",
    "DOMAIN-SUFFIX,faceobook.com",
    "DOMAIN-SUFFIX,faceook.com",
    "DOMAIN-SUFFIX,facerbooik.com",
    "DOMAIN-SUFFIX,facerbook.com",
    "DOMAIN-SUFFIX,facesbooc.com",
    "DOMAIN-SUFFIX,facesounds.com",
    "DOMAIN-SUFFIX,facetook.com",
    "DOMAIN-SUFFIX,facevbook.com",
    "DOMAIN-SUFFIX,facewbook.co",
    "DOMAIN-SUFFIX,facewook.com",
    "DOMAIN-SUFFIX,facfacebook.com",
    "DOMAIN-SUFFIX,facfebook.com",
    "DOMAIN-SUFFIX,faciometrics.com",
    "DOMAIN-SUFFIX,fackebook.com",
    "DOMAIN-SUFFIX,facnbook.com",
    "DOMAIN-SUFFIX,facrbook.com",
    "DOMAIN-SUFFIX,facvebook.com",
    "DOMAIN-SUFFIX,facwebook.com",
    "DOMAIN-SUFFIX,facxebook.com",
    "DOMAIN-SUFFIX,fadebook.com",
    "DOMAIN-SUFFIX,faebok.com",
    "DOMAIN-SUFFIX,faebook.com",
    "DOMAIN-SUFFIX,faebookc.com",
    "DOMAIN-SUFFIX,faeboook.com",
    "DOMAIN-SUFFIX,faecebok.com",
    "DOMAIN-SUFFIX,faesebook.com",
    "DOMAIN-SUFFIX,fafacebook.com",
    "DOMAIN-SUFFIX,faicbooc.com",
    "DOMAIN-SUFFIX,fasebokk.com",
    "DOMAIN-SUFFIX,fasebook.com",
    "DOMAIN-SUFFIX,faseboox.com",
    "DOMAIN-SUFFIX,fasttext.cc",
    "DOMAIN-SUFFIX,favebook.com",
    "DOMAIN-SUFFIX,faycbok.com",
    "DOMAIN-SUFFIX,fbacebook.com",
    "DOMAIN-SUFFIX,gacebook.com",
    "DOMAIN-SUFFIX,gfacecbook.com",
    "DOMAIN-SUFFIX,fcacebook.com",
    "DOMAIN-SUFFIX,fcaebook.com",
    "DOMAIN-SUFFIX,fcebook.com",
    "DOMAIN-SUFFIX,fcebookk.com",
    "DOMAIN-SUFFIX,fcfacebook.com",
    "DOMAIN-SUFFIX,fdacebook.info",
    "DOMAIN-SUFFIX,feacboo.com",
    "DOMAIN-SUFFIX,feacbook.com",
    "DOMAIN-SUFFIX,feacbooke.com",
    "DOMAIN-SUFFIX,feacebook.com",
    "DOMAIN-SUFFIX,fecbbok.com",
    "DOMAIN-SUFFIX,fecbooc.com",
    "DOMAIN-SUFFIX,fecbook.com",
    "DOMAIN-SUFFIX,feceboock.com",
    "DOMAIN-SUFFIX,fecebook.net",
    "DOMAIN-SUFFIX,feceboox.com",
    "DOMAIN-SUFFIX,fececbook.com",
    "DOMAIN-SUFFIX,feook.com",
    "DOMAIN-SUFFIX,ferabook.com",
    "DOMAIN-SUFFIX,fescebook.com",
    "DOMAIN-SUFFIX,fesebook.com",
    "DOMAIN-SUFFIX,ffacebook.com",
    "DOMAIN-SUFFIX,fgacebook.com",
    "DOMAIN-SUFFIX,ficeboock.com",
    "DOMAIN-SUFFIX,fmcebook.com",
    "DOMAIN-SUFFIX,fnacebook.com",
    "DOMAIN-SUFFIX,fosebook.com",
    "DOMAIN-SUFFIX,fpacebook.com",
    "DOMAIN-SUFFIX,fqcebook.com",
    "DOMAIN-SUFFIX,fracebook.com",
    "DOMAIN-SUFFIX,fsacebok.com",
    "DOMAIN-SUFFIX,fscebook.com",
    "DOMAIN-SUFFIX,httpfacebook.com",
    "DOMAIN-SUFFIX,httpsfacebook.com",
    "DOMAIN-SUFFIX,httpwwwfacebook.com",
    "DOMAIN-SUFFIX,imstagram.com",
    "DOMAIN-SUFFIX,imtagram.com",
    # CDN
    "DOMAIN-SUFFIX,cdninstagram.com",
    "DOMAIN-SUFFIX,fbcdn.net",
    "DOMAIN-SUFFIX,fbcdn.com",
    "DOMAIN-SUFFIX,fbsbx.com",
    # domain-keyword
    "DOMAIN-KEYWORD,facebook",
    "DOMAIN-KEYWORD,fbcdn",
    #
    "DOMAIN-SUFFIX,aboutfacebook.com",
    "DOMAIN-SUFFIX,accessfacebookfromschool.com",
    "DOMAIN-SUFFIX,askfacebook.net",
    "DOMAIN-SUFFIX,askfacebook.org",
    "DOMAIN-SUFFIX,bookstagram.com",
    "DOMAIN-SUFFIX,buyingfacebooklikes.com",
    "DOMAIN-SUFFIX,chickstagram.com",
    "DOMAIN-SUFFIX,china-facebook.com",
    "DOMAIN-SUFFIX,como-hackearfacebook.com",
    "DOMAIN-SUFFIX,dlfacebook.com",
    "DOMAIN-SUFFIX,dotfacebook.com",
    "DOMAIN-SUFFIX,dotfacebook.net",
    "DOMAIN-SUFFIX,facebook-corp.com",
    "DOMAIN-SUFFIX,facebook-covid-19.com",
    "DOMAIN-SUFFIX,facebook-ebook.com",
    "DOMAIN-SUFFIX,facebook-forum.com",
    "DOMAIN-SUFFIX,facebook-hardware.com",
    "DOMAIN-SUFFIX,facebook-inc.com",
    "DOMAIN-SUFFIX,facebook-login.com",
    "DOMAIN-SUFFIX,facebook-newsroom.com",
    "DOMAIN-SUFFIX,facebook-newsroom.org",
    "DOMAIN-SUFFIX,facebook-pmdcenter.com",
    "DOMAIN-SUFFIX,facebook-pmdcenter.net",
    "DOMAIN-SUFFIX,facebook-pmdcenter.org",
    "DOMAIN-SUFFIX,facebook-privacy.com",
    "DOMAIN-SUFFIX,facebook-program.com",
    "DOMAIN-SUFFIX,facebook-studio.com",
    "DOMAIN-SUFFIX,facebook-support.org",
    "DOMAIN-SUFFIX,facebook-texas-holdem.com",
    "DOMAIN-SUFFIX,facebook-texas-holdem.net",
    "DOMAIN-SUFFIX,facebook.wang",
    "DOMAIN-SUFFIX,facebook123.org",
    "DOMAIN-SUFFIX,facebook30.com",
    "DOMAIN-SUFFIX,facebook30.net",
    "DOMAIN-SUFFIX,facebook30.org",
    "DOMAIN-SUFFIX,facebook4business.com",
    "DOMAIN-SUFFIX,facebookads.com",
    "DOMAIN-SUFFIX,facebookadvertisingsecrets.com",
    "DOMAIN-SUFFIX,facebookappcenter.info",
    "DOMAIN-SUFFIX,facebookappcenter.net",
    "DOMAIN-SUFFIX,facebookappcenter.org",
    "DOMAIN-SUFFIX,facebookatschool.com",
    "DOMAIN-SUFFIX,facebookawards.com",
    "DOMAIN-SUFFIX,facebookblueprint.net",
    "DOMAIN-SUFFIX,facebookbrand.com",
    "DOMAIN-SUFFIX,facebookbrand.net",
    "DOMAIN-SUFFIX,facebookcanadianelectionintegrityinitiative.com",
    "DOMAIN-SUFFIX,facebookcareer.com",
    "DOMAIN-SUFFIX,facebookcheats.com",
    "DOMAIN-SUFFIX,facebookck.com",
    "DOMAIN-SUFFIX,facebookclub.com",
    "DOMAIN-SUFFIX,facebookcom.com",
    "DOMAIN-SUFFIX,facebookconnect.com",
    "DOMAIN-SUFFIX,facebookconsultant.org",
    "DOMAIN-SUFFIX,facebookcoronavirus.com",
    "DOMAIN-SUFFIX,facebookcovers.org",
    "DOMAIN-SUFFIX,facebookcredits.info",
    "DOMAIN-SUFFIX,facebookdating.net",
    "DOMAIN-SUFFIX,facebookdevelopergarage.com",
    "DOMAIN-SUFFIX,facebookdusexe.org",
    "DOMAIN-SUFFIX,facebookemail.com",
    "DOMAIN-SUFFIX,facebookenespanol.com",
    "DOMAIN-SUFFIX,facebookexchange.com",
    "DOMAIN-SUFFIX,facebookexchange.net",
    "DOMAIN-SUFFIX,facebookfacebook.com",
    "DOMAIN-SUFFIX,facebookflow.com",
    "DOMAIN-SUFFIX,facebookgames.com",
    "DOMAIN-SUFFIX,facebookgraphsearch.com",
    "DOMAIN-SUFFIX,facebookgraphsearch.info",
    "DOMAIN-SUFFIX,facebookgroups.com",
    "DOMAIN-SUFFIX,facebookhome.cc",
    "DOMAIN-SUFFIX,facebookhome.com",
    "DOMAIN-SUFFIX,facebookhome.info",
    "DOMAIN-SUFFIX,facebookhub.com",
    "DOMAIN-SUFFIX,facebooki.com",
    "DOMAIN-SUFFIX,facebookinc.com",
    "DOMAIN-SUFFIX,facebookland.com",
    "DOMAIN-SUFFIX,facebooklikeexchange.com",
    "DOMAIN-SUFFIX,facebooklive.com",
    "DOMAIN-SUFFIX,facebooklivestaging.net",
    "DOMAIN-SUFFIX,facebooklivestaging.org",
    "DOMAIN-SUFFIX,facebooklogin.com",
    "DOMAIN-SUFFIX,facebooklogin.info",
    "DOMAIN-SUFFIX,facebookloginhelp.net",
    "DOMAIN-SUFFIX,facebooklogs.com",
    "DOMAIN-SUFFIX,facebookmail.com",
    "DOMAIN-SUFFIX,facebookmail.tv",
    "DOMAIN-SUFFIX,facebookmanager.info",
    "DOMAIN-SUFFIX,facebookmarketing.info",
    "DOMAIN-SUFFIX,facebookmarketingpartner.com",
    "DOMAIN-SUFFIX,facebookmarketingpartners.com",
    "DOMAIN-SUFFIX,facebookmobile.com",
    "DOMAIN-SUFFIX,facebookmsn.com",
    "DOMAIN-SUFFIX,facebooknews.com",
    "DOMAIN-SUFFIX,facebooknfl.com",
    "DOMAIN-SUFFIX,facebooknude.com",
    "DOMAIN-SUFFIX,facebookofsex.com",
    "DOMAIN-SUFFIX,facebookook.com",
    "DOMAIN-SUFFIX,facebookpaper.com",
    "DOMAIN-SUFFIX,facebookpay.com",
    "DOMAIN-SUFFIX,facebookphonenumber.net",
    "DOMAIN-SUFFIX,facebookphoto.com",
    "DOMAIN-SUFFIX,facebookphotos.com",
    "DOMAIN-SUFFIX,facebookpmdcenter.com",
    "DOMAIN-SUFFIX,facebookpoke.net",
    "DOMAIN-SUFFIX,facebookpoke.org",
    "DOMAIN-SUFFIX,facebookpoker.info",
    "DOMAIN-SUFFIX,facebookpokerchips.info",
    "DOMAIN-SUFFIX,facebookporn.net",
    "DOMAIN-SUFFIX,facebookporn.org",
    "DOMAIN-SUFFIX,facebookporno.net",
    "DOMAIN-SUFFIX,facebookportal.com",
    "DOMAIN-SUFFIX,facebookquotes4u.com",
    "DOMAIN-SUFFIX,facebooks.com",
    "DOMAIN-SUFFIX,facebooksafety.com",
    "DOMAIN-SUFFIX,facebooksecurity.net",
    "DOMAIN-SUFFIX,facebookshop.com",
    "DOMAIN-SUFFIX,facebooksignup.net",
    "DOMAIN-SUFFIX,facebooksite.net",
    "DOMAIN-SUFFIX,facebookstories.com",
    "DOMAIN-SUFFIX,facebookstudios.net",
    "DOMAIN-SUFFIX,facebookstudios.org",
    "DOMAIN-SUFFIX,facebooksupplier.com",
    "DOMAIN-SUFFIX,facebooksuppliers.com",
    "DOMAIN-SUFFIX,facebookswagemea.com",
    "DOMAIN-SUFFIX,facebookswagstore.com",
    "DOMAIN-SUFFIX,facebooksz.com",
    "DOMAIN-SUFFIX,facebookthreads.net",
    "DOMAIN-SUFFIX,facebooktv.net",
    "DOMAIN-SUFFIX,facebooktv.org",
    "DOMAIN-SUFFIX,facebookvacation.com",
    "DOMAIN-SUFFIX,facebookw.com",
    "DOMAIN-SUFFIX,facebookwork.com",
    "DOMAIN-SUFFIX,facebookworld.com",
    "DOMAIN-SUFFIX,freefacebook.com",
    "DOMAIN-SUFFIX,freefacebook.net",
    "DOMAIN-SUFFIX,freefacebookads.net",
    "DOMAIN-SUFFIX,fundraisingwithfacebook.com",
    "DOMAIN-SUFFIX,funnyfacebook.org",
    "DOMAIN-SUFFIX,hackerfacebook.com",
    "DOMAIN-SUFFIX,hackfacebook.com",
    "DOMAIN-SUFFIX,hackfacebookid.com",
    "DOMAIN-SUFFIX,hifacebook.info",
    "DOMAIN-SUFFIX,howtohackfacebook-account.com",
    "DOMAIN-SUFFIX,hsfacebook.com",
    "DOMAIN-SUFFIX,mobilefacebook.com",
    "DOMAIN-SUFFIX,moneywithfacebook.com",
    "DOMAIN-SUFFIX,reachtheworldonfacebook.com",
    "DOMAIN-SUFFIX,shopfacebook.com",
    "DOMAIN-SUFFIX,sportsfacebook.com",
    "DOMAIN-SUFFIX,supportfacebook.com",
    "DOMAIN-SUFFIX,thefacebook.com",
    "DOMAIN-SUFFIX,thefacebook.net",
    "DOMAIN-SUFFIX,viewpointsfromfacebook.com",
    "DOMAIN-SUFFIX,whyfacebook.com",
    "DOMAIN-SUFFIX,achat-followers-instagram.com",
    "DOMAIN-SUFFIX,acheter-followers-instagram.com",
    "DOMAIN-SUFFIX,acheterdesfollowersinstagram.com",
    "DOMAIN-SUFFIX,acheterfollowersinstagram.com",
    "DOMAIN-SUFFIX,instagramci.com",
    "DOMAIN-SUFFIX,instagramcn.com",
    "DOMAIN-SUFFIX,instagramdi.com",
    "DOMAIN-SUFFIX,instagramhashtags.net",
    "DOMAIN-SUFFIX,instagramhilecim.com",
    "DOMAIN-SUFFIX,instagramhilesi.org",
    "DOMAIN-SUFFIX,instagramium.com",
    "DOMAIN-SUFFIX,instagramizlenme.com",
    "DOMAIN-SUFFIX,instagramkusu.com",
    "DOMAIN-SUFFIX,instagramlogin.com",
    "DOMAIN-SUFFIX,instagramm.com",
    "DOMAIN-SUFFIX,instagramn.com",
    "DOMAIN-SUFFIX,instagrampartners.com",
    "DOMAIN-SUFFIX,instagramphoto.com",
    "DOMAIN-SUFFIX,instagramq.com",
    "DOMAIN-SUFFIX,instagramsepeti.com",
    "DOMAIN-SUFFIX,instagramtakipcisatinal.net",
    "DOMAIN-SUFFIX,instagramtakiphilesi.com",
    "DOMAIN-SUFFIX,instagramtips.com",
    "DOMAIN-SUFFIX,instagramtr.com",
    "DOMAIN-SUFFIX,instagram-brand.com",
    "DOMAIN-SUFFIX,instagram-engineering.com",
    "DOMAIN-SUFFIX,instagram-help.com",
    "DOMAIN-SUFFIX,instagram-press.com",
    "DOMAIN-SUFFIX,instagram-press.net",
    "DOMAIN-SUFFIX,instaadder.com",
    "DOMAIN-SUFFIX,instachecker.com",
    "DOMAIN-SUFFIX,instafallow.com",
    "DOMAIN-SUFFIX,instafollower.com",
    "DOMAIN-SUFFIX,instagainer.com",
    "DOMAIN-SUFFIX,instagda.com",
    "DOMAIN-SUFFIX,instagify.com",
    "DOMAIN-SUFFIX,instagmania.com",
    "DOMAIN-SUFFIX,instagor.com",
    "DOMAIN-SUFFIX,instanttelegram.com",
    "DOMAIN-SUFFIX,instaplayer.net",
    "DOMAIN-SUFFIX,instastyle.tv",
    "DOMAIN-SUFFIX,instgram.com",
    "DOMAIN-SUFFIX,lnstagram-help.com",
    "DOMAIN-SUFFIX,oninstagram.com",
    "DOMAIN-SUFFIX,online-instagram.com",
    "DOMAIN-SUFFIX,onlineinstagram.com",
    "DOMAIN-SUFFIX,theinstagramhack.com",
    "DOMAIN-SUFFIX,web-instagram.net",
    "DOMAIN-SUFFIX,whatsapp-plus.info",
    "DOMAIN-SUFFIX,whatsapp-plus.me",
    "DOMAIN-SUFFIX,whatsapp-plus.net",
    "DOMAIN-SUFFIX,whatsapp.biz",
    "DOMAIN-SUFFIX,whatsapp.info",
    "DOMAIN-SUFFIX,whatsapp.tv",
    "DOMAIN-SUFFIX,whatsappbrand.com",
]

# ---------- 添加规则列表 ----------
# 这些规则会追加到输出文件末尾（自动去重）
RULES_TO_ADD = [
    # "DOMAIN,example.com",
    # "DOMAIN-SUFFIX,example.com",
    # "DOMAIN-KEYWORD,example",
    # "IP-CIDR,1.2.3.4/24,no-resolve",
    # "IP-ASN,12345,no-resolve",
    # "IP-CIDR6,2001:db8::/32,no-resolve",
    "DOMAIN-SUFFIX,threads.com",
    "DOMAIN-SUFFIX,threads.net",
]

# ============================================================
# 支持的规则类型（用于校验/解析）
# ============================================================
VALID_RULE_TYPES = {
    "DOMAIN",
    "DOMAIN-SUFFIX",
    "DOMAIN-KEYWORD",
    "DOMAIN-WILDCARD",
    "IP-CIDR",
    "IP-CIDR6",
    "IP-ASN",
    "GEOIP",
    "USER-AGENT",
    "URL-REGEX",
    "PROCESS-NAME",
}


# ============================================================
# 核心逻辑
# ============================================================


def normalize_rule(line: str) -> str:
    """去除注释、首尾空白，统一大写类型前缀，便于比较"""
    line = line.strip()
    if not line or line.startswith("#"):
        return ""
    # 去除行内注释（# 后内容）
    line = re.sub(r"\s*#.*$", "", line).strip()
    # 将规则类型部分统一大写
    parts = line.split(",")
    if parts and parts[0].upper() in VALID_RULE_TYPES:
        parts[0] = parts[0].upper()
    return ",".join(parts)


def build_remove_set(rules: list) -> set:
    """将 RULES_TO_REMOVE 列表构建为规范化 set"""
    return {normalize_rule(r) for r in rules if normalize_rule(r)}


def is_rule_line(line: str) -> bool:
    """判断是否为有效规则行（非注释、非空）"""
    stripped = line.strip()
    return bool(stripped) and not stripped.startswith("#")


def read_source(path: str) -> list:
    """读取源文件，返回原始行列表"""
    if not os.path.exists(path):
        raise FileNotFoundError(f"源文件不存在: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return f.readlines()


def process_rules(source_lines: list, remove_set: set, rules_to_add: list) -> tuple:
    """
    处理规则：
    - 过滤掉 remove_set 中的规则
    - 追加 rules_to_add 中的规则（去重）
    返回 (处理后的行列表, 统计信息 dict)
    """
    result_lines = []
    removed_count = 0
    seen_rules = set()  # 用于全局去重

    for raw_line in source_lines:
        normalized = normalize_rule(raw_line)

        # 保留注释行和空行（原样输出）
        if not normalized:
            # result_lines.append(raw_line.rstrip("\n"))
            continue

        # 检查是否需要删除
        if normalized in remove_set:
            removed_count += 1
            continue

        # 去重处理（源文件本身可能有重复）
        if normalized in seen_rules:
            continue
        seen_rules.add(normalized)

        result_lines.append(raw_line.rstrip("\n"))

    # 追加新增规则
    added_count = 0
    add_section = []
    for rule in rules_to_add:
        normalized = normalize_rule(rule)
        if not normalized:
            continue
        if normalized not in seen_rules:
            add_section.append(normalized)
            seen_rules.add(normalized)
            added_count += 1

    stats = {
        "source_total": sum(1 for l in source_lines if is_rule_line(l)),
        "removed": removed_count,
        "added": added_count,
        "output_total": sum(1 for l in result_lines if is_rule_line(l)) + added_count,
    }

    return result_lines, add_section, stats


def write_output(
    output_path: str, lines: list, add_section: list, stats: dict, source_path: str
):
    """写入输出文件，包含文件头注释"""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    header = [
        f"# Generated by filter_facebook.py",
        f"# Date     : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"# Source   : {source_path}",
        f"# Rules    : {stats['output_total']} "
        f"(source {stats['source_total']}, "
        f"-{stats['removed']} removed, "
        f"+{stats['added']} added)",
        "################################################################################",
    ]

    with open(output_path, "w", encoding="utf-8") as f:
        # 写入文件头
        f.write("\n".join(header) + "\n")

        # 写入处理后的规则
        for line in lines:
            f.write(line + "\n")

        # 写入新增规则段
        if add_section:
            f.write("\n# --- Custom Added Rules ---\n")
            for rule in add_section:
                f.write(rule + "\n")


def main():
    print(f"[*] 源文件  : {SOURCE_FILE}")

    output_path = os.path.join(OUTPUT_DIR, OUTPUT_FILENAME)
    print(f"[*] 输出文件: {output_path}")

    # 读取源文件
    source_lines = read_source(SOURCE_FILE)
    print(f"[*] 源文件共 {len(source_lines)} 行")

    # 构建删除集合
    remove_set = build_remove_set(RULES_TO_REMOVE)
    if remove_set:
        print(f"[*] 待删除规则: {len(remove_set)} 条")
        for r in sorted(remove_set):
            print(f"    - {r}")

    if RULES_TO_ADD:
        print(f"[*] 待添加规则: {len(RULES_TO_ADD)} 条")
        for r in RULES_TO_ADD:
            print(f"    + {r}")

    # 处理规则
    result_lines, add_section, stats = process_rules(
        source_lines, remove_set, RULES_TO_ADD
    )

    # 写入输出
    write_output(output_path, result_lines, add_section, stats, SOURCE_FILE)

    print(f"\n[✓] 处理完成")
    print(f"    源规则数  : {stats['source_total']}")
    print(f"    删除规则  : {stats['removed']}")
    print(f"    新增规则  : {stats['added']}")
    print(f"    输出规则数: {stats['output_total']}")
    print(f"    输出路径  : {output_path}")


if __name__ == "__main__":
    main()
