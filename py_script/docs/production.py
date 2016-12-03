# -*- coding: utf-8 -*-
CHINA_SCOPE_DOMIAN = "http://www.chinascopefinancial.com/"
CHINA_SCOPE_LOGIN  = "http://ada.account.chinascope.com/user/dologin"
CHINA_SCOPE_LOGIN_PAGE = "https://account.chinascope.com/index/account/login?forward=http%3A%2F%2Ffinance.chinascope.com%2F"
CHINA_SCOPE_SEARCH = "http://fin.chinascope.com/company/doSearch"
CHINA_SCOPE_HEADER = {
                      'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.103 Safari/537.36',
                      'Connection': "keep-alive",
                      }

CHINA_SCOPE_USERNAME = ''
CHINA_SCOPE_PWD      = ''
CHINA_SCOPE_SEARCH_FORM_DATA = {
        'q':'',
        'indt': 'csf',
        'indtc': '',
        'area': '',
        'market': "1001,1054,1002,1055,1003,1012,1006,1007,1045,1042,1082,1029,1017,1018,1021,1022,1023,1024,1034,1035,1066,1071,1074,1078,1008,1005,1058,1059,1060,1062,1063,1064,1065,1079,1056,1080,1057",
        'page': 1,
        'limit':25
        }

MONGO_URL = "mongodb://localhost:26534"
CHINA_SCOPE_FINANCE_URL = "http://fin.chinascopefinancial.com/listed/ajaxProfileFH?sid=%s"

#PROXY = {
#    "http":  "http://user:pass@proxy.abuyun.com:9010/",
#    "https": "http://user:pass@proxy.abuyun.com:9010/",
#}

PROXY = [{'user':'name', 'pass':'pass', 'domain': 'domain'}]

PHANTOMJS_PATH = '/home/deploy/spider/china-scope-python-spider/py_script/phantomjs/bin/phantomjs'

PHANTOM_LOGIN = {
   'name': '',
   'pwd': ''
}

SHINFO_LOGIN = {
    'name': '@gmail.com',
    'pwd': ''
}

CS_BASIC  = 'chinascopes'
CS_FINANCE = 'chinascopes_finance'
CS_SHINFO = 'chinascopes_shinfo'

