# -*- coding: utf-8 -*-
import requests
from pyquery import PyQuery as pq
import pymongo as pm
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import threading
import queue
import logging
import os,sys
from datetime import datetime
import traceback
import time

try:
    from docs.conf import *
    # log_file = os.path.join(os.getcwd(), 'tmp/log/log_'+datetime.now().strftime('%Y-%m-%dT%H:%M:%S')+'.txt')
    log_file = os.path.join(os.getcwd(), 'tmp/log/log_spider.txt')
    craw_page = os.path.join(os.getcwd(), 'tmp/craw_page.txt')
except:
    parentdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0,parentdir)
    from docs.conf import *
    # log_file = os.path.join(parentdir, 'tmp/log/log_'+datetime.now().strftime('%Y-%m-%dT%H:%M:%S')+'.txt')
    log_file = os.path.join(parentdir, 'tmp/log/log_spider.txt')
    craw_page = os.path.join(parentdir, 'tmp/craw_page.txt')

logging.basicConfig(filename=log_file, filemode='w', level = logging.INFO, format = '%(asctime)s %(filename)s %(funcName)s %(lineno)d  - %(levelname)s: %(message)s')

execute_url = queue.Queue()
operate_url_q = queue.Queue()
rlock = threading.RLock()


class  Spider(object):
    def __init__(self):
        try:
            self.login_page = CHINA_SCOPE_LOGIN_PAGE
            self.login_user = PHANTOM_LOGIN
            self.phantomjs_path = PHANTOMJS_PATH
            self.init_session()
            self.init_db()
        except Exception as e:
            traceback.print_exc()
            logging.error('init session error:' + str(e))
            sys.exit(0)

    def init_session(self,):
        a = requests.adapters.HTTPAdapter(max_retries=10)
        b = requests.adapters.HTTPAdapter(max_retries=10)
        self.header = CHINA_SCOPE_HEADER
        self.query_session = requests.Session()
        self.query_session.mount('http://', a)
        self.query_session.mount('https://', b)
        for k in self.header:
            self.query_session.headers.update({k: self.header[k]})
        cookie = self.login()
        # 初始化代理

    def init_db(self):
        self.db = pm.MongoClient(MONGO_URL)['china_scope']

    def save_current_page(self, page):
        # todo save current scraping page
        self.page_f.seek(0, 0)
        self.page_f.truncate()
        self.page_f.write(str(page))
        pass

    def load_current_page(self, ):
        # todo load from last failed page from file
        if os.path.isfile(craw_page):
            self.page_f = open(craw_page, 'r+')
            try:
                self.page = int(self.page_f.readline())
                logging.info('init page success')
            except Exception as ex:
                logging.error('load page error %s ' % ex)
                self.page = 1
        else:
            self.page_f = open(craw_page, 'w+')
            self.page = 1
        pass

    def login(self):
        while True:
            self.init_phantomjs()
            try:
                logging.info('phantomjs loging %s' % self.driver.current_url)
                self.driver.get("about:blank")
                self.driver.get(self.login_page)
                WebDriverWait(self.driver, 60).until(EC.presence_of_element_located((By.TAG_NAME, "input")))
                self.driver.find_element_by_name("username").send_keys(self.login_user['name'])
                self.driver.find_element_by_id("passwd").send_keys(self.login_user['pwd'])
                self.driver.find_element_by_css_selector(".js-login").click()
                logging.info('phantomjs login success ')
            except Exception as e:
                logging.error('login error : %s' % e)
                logging.info('current url %s ' % (self.driver.current_url))
                if 'username' in str(e):
                    logging.error('bad happend ')
                    self.db.chinascopes_finance.remove({'stockid':self.current_stockid})
                    sys.exit(0)
                continue

            time.sleep(5)
            cookies = self.driver.get_cookies()
            cookies.reverse()
            Cookie = ''.join(map(lambda x:x['name']+"="+x['value']+";", cookies))
            self.query_session.headers.update({'Cookie': Cookie})
            return

    def init_phantomjs(self):
        #todo proxy&timeout close if it exists
        try:
            self.driver.delete_all_cookies()
            self.driver.close()
            self.driver.quit()
            os.system("ps aux|grep phantomjs | awk '{print $2}'|xargs kill -9")
        except Exception as e:
            logging.error('close driver error '+str(e))
        finally:
            logging.info('init driver')
            self.driver = webdriver.PhantomJS(executable_path=self.phantomjs_path)
            #self.driver.get("about:blank")
            # self.driver.implicitly_wait(5*60)
            self.driver.set_page_load_timeout(5*60)

    def get_commpany_list(self):
        self.query_session.headers.update({'X-Requested-With': 'XMLHttpRequest'})
        payload = CHINA_SCOPE_SEARCH_FORM_DATA
        payload['page'] = self.page
        while True:
            try:
                re = self.query_session.post(url=CHINA_SCOPE_SEARCH, data=payload, timeout=5)
                json_data = re.json()
                #todo reconstructor into multiprocess
                self.get_commpany_detail(json_data)
            except Exception as e:
                logging.error(e)
                self.init_session()
                continue

            if int(json_data['page']) > int(json_data['total']):
                self.save_current_page(1)
                break
            #todo reconstructor random page_number
            logging.info('page %s' % json_data['page'])
            payload['page'] = int(json_data['page'])+1
            self.save_current_page(payload['page'])
        # close file
        self.page_f.close()
        pass

    def search_cpny_by_name(self, cpnyname):
        self.query_session.headers.update({'X-Requested-With': 'XMLHttpRequest'})
        payload = CHINA_SCOPE_SEARCH_FORM_DATA
        payload['market'] = ''
        payload['q'] = cpnyname.strip()
        try:
            re = self.query_session.post(url=CHINA_SCOPE_SEARCH, data=payload, timeout=5)
            json_data = re.json()
            return json_data
            #self.get_commpany_detail(json_data)
        except Exception as e:
            logging.error(e)
            self.init_session()

    def get_commpany_detail(self, company_data):

        def company_basic_info():
            #pdb.set_trace()
            data = []
            info = pq_tag(".cp_info td")
            i = 1
            while True:
                try:
                    if info[i+1].find('a') is not None:
                        v = info[i+1].find('a').text
                    else:
                        v = info[i+1].text
                    data.append((info[i].text.strip(),v))
                    i += 3
                except Exception as e:
                    break

            data.append(('公司简介',  pq_tag(".com_sum_txt").text()))
            return data

        def company_stock():
            info =  pq_tag(".seinfo").text().split(' ')
            data =  list(zip(info[::2], info[1::2]))
            return data

        def company_business_catgory():
            i = 1
            data = []
            while True:
                cat_name = pq_tag("[href='#tabs-%s']" % i).text()
                cat_val = pq_tag("#tabs-%s" % i).text()
                if cat_name:
                    if i==1:
                        cat_name = cat_name.split(' ')[0]
                    data.append((cat_name, cat_val))
                else:
                    break
                i += 1
            return data

        def company_executives():
            return pq_tag("td [class='tcenter']").text()

        def company_stockhoder():
            return list(zip(pq_tag(".shinfo_holder").text().split(" "),
                            pq_tag(".s_ration").text().split(' ')))

        def company_finance(sid):
            stock_url = CHINA_SCOPE_FINANCE_URL % sid
            while True:
                try:
                    return self.query_session.get(stock_url, timeout=5).json()
                except Exception as e:
                    logging.error(str(e) + ' company_finance_error: ' + sid)
                    self.init_session()
                    continue

        def nav_url(stockid):
            #todo 先处理金融报表 其余的下周再处理
            title = pq_tag("#horizontal ul").text().split(" ")
            for k, e in enumerate(pq_tag("#horizontal .hor_text")):
                for n in e.findall("a"):
                    if 'executive' in n.attrib['href']:
                        execute_url.put({'title': title[k] + '#' + n.text, 'url': n.attrib['href'], 'stockid': stockid})
                        logging.info('put %s execuete in queue' % stockid)
                    elif 'business/operating' in n.attrib['href']:
                        operate_url_q.put({'title': title[k] + '#' + n.text, 'url': n.attrib['href'], 'stockid': stockid})
                        logging.info('put %s operate in queue' % stockid)
                    # elif 'shinfo' in n.attrib['href']:
                    #     shinfo_url_q.put({'title': title[k] + '#' + n.text, 'url': n.attrib['href'], 'stockid': stockid})
                    #     logging.info('put %s shinfo in queue' % stockid)

        for e in company_data['rows']:
            data = e
            url = e['link']
            try:
                while True:
                    try:
                        url_content = self.query_session.get(url, timeout=5)
                        if url_content.status_code != 200: raise Exception(url_content.status_code, 'HTTP status code error '+url_content.status_code)
                    except Exception as ex:
                        logging.error(str(ex) + ' company_basic_info_url:' + url)
                        self.init_session()
                        continue
                    break

                url_content.encoding = 'utf-8'
                pq_tag = pq(url_content.text)
                data['company_basic_info'] = company_basic_info()
                data['company_stock'] = company_stock()
                data['company_business_catgory'] = company_business_catgory()
                data['company_executives'] = company_executives()
                data['company_stockhoder'] = company_stockhoder()
                data['company_finance'] = company_finance(e['stockid'])
            except Exception as e:
                logging.error(e)

            self.save_data(data)
            nav_url(e['stockid'])
            #time.sleep(random.uniform(0.1, 1))

    def save_data(self, data_dict):
        data_dict['updated_at'] =  datetime.now()
        logging.info('get data %s ' % data_dict['stockid'])
        try:
            self.db.chinascopes.update_one({'stockid': data_dict['stockid']}, {'$set': data_dict}, upsert=True)
        except Exception as e:
            logging.error(e)

    def executive_info(self, url_info=None):
            logging.info('init execute thread success')
            # 董事信息
            while True:
                try:
                    url_info = execute_url.get()
                    # logging.info('get execute info %s ' % url_info)
                    # pdb.set_trace()
                except:
                    logging.info('empty return')
                    return

                data_to_db = []
                url = url_info['url']
                while True:
                    try:
                        if rlock.acquire():
                            page_data = self.query_session.get(url)
                            rlock.release()
                    except Exception as ex:
                        rlock.release()
                        logging.error('get execute info error %s' % ex)
                        self.init_session()
                        continue
                    break
                pqa_data = pq(page_data.content)

                for e in pqa_data(".def_table tr:gt(0) td a"):
                    while True:
                        try:
                            if rlock.acquire():
                                exec_data = self.query_session.get(e.attrib['href'])
                                exec_data_pq = pq(exec_data.content)
                                rlock.release()
                        except Exception as ex:
                            rlock.release()
                            logging.error('get execute detail error %s' % ex)
                            self.init_session()
                            continue
                        break
                    exec_brief = exec_data_pq(".resume_div_txt").text()
                    data_to_db.append(('个人简介', exec_brief))
                    tmp = []
                    for key, val in enumerate(exec_data_pq(".rs_left_box table tr td")):
                        if key % 2 == 0:
                            tmp.append(val.text)
                        else:
                            tmp.append(val.find_class("blk")[0].text)
                            data_to_db.append(tmp)
                            tmp = []
                self.db.chinascopes.update_one({'stockid': url_info['stockid']}, {'$set': {url_info['title']: data_to_db}}, upsert=True)
                logging.info('get execute info %s' % url_info['stockid'])
            pass

    def operate_info(self, url_info=None):
        # 运营信息 单独的线程
        logging.info('init operate info')

        #todo 先访问页面内容 获取开始时间和结束时间
        while True:
            #pdb.set_trace()
            try:
                url_info = operate_url_q.get()
            except:
                logging.info('opeate_url thread empty return')
                return

            url = url_info['url']
            while True:
                try:
                    if rlock.acquire():
                        page_data = self.query_session.get(url)
                        rlock.release()
                except Exception as ex:
                    rlock.release()
                    logging.error('get execute info error %s' % ex)
                    self.init_session()
                    continue
                break
            pqa_data = pq(page_data.content)

            d_start = pqa_data('#d_start').val()
            d_end = pqa_data('#d_end').val()
            secu = pqa_data(".qsdiv td:eq(0) span").text()
            json_url = 'http://fin.chinascopefinancial.com/business/getOptData'
            pay_load = {
                'sid': url_info['stockid'],
                'ystart': d_start,
                'yend': d_end,
                'freq': 'S',
                'ytd': 'N',
                'mode': 'metr',
                'contrast': 1,
                'request': 'J',
                'style': 'web',
                'secu': secu,
                'acl_export': ''
            }
            while True:
                try:
                    if rlock.acquire():
                        json_data = self.query_session.post(json_url, data=pay_load, timeout=20)
                        rlock.release()
                except:
                    self.init_session()
                    continue
                break

            self.db.chinascopes.update_one({'stockid': url_info['stockid']}, {'$set': {url_info['title']: json_data.json()}}, upsert=True)
            logging.info('get operate info %s' % url_info['stockid'])

if __name__ == "__main__":
    try:
        args = str(sys.argv[1])
        if args == 'production':
            from docs.production import *
    except:
        pass

    spider = Spider()
    th1 = threading.Thread(target=spider.executive_info)
    th2 = threading.Thread(target=spider.operate_info)
    th1.start()
    th2.start()
    spider.get_commpany_list()
    th1.join()
    th2.join()
    pass

