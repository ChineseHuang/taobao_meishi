import re
import pymongo
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from pyquery import PyQuery as pq
from taobao_meishi.config import *

client = pymongo.MongoClient(MONGO_URL, connect=False)
db = client[MONGO_DB]

# browser = webdriver.Firefox()
browser = webdriver.PhantomJS(service_args=SERVICE_ARGS)

wait = WebDriverWait(browser, 10)

# 设置PhantomJS的窗口大小
browser.set_window_size(1400, 900)

def search():
    """
    返回美食界面的页数
    :return:
    """
    print('正在搜索...')
    try:
        browser.get('https://www.taobao.com')

        # 第一种方法
        in_put = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#q")))
        in_put.send_keys(KEYWORD)
        submit = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, '#J_TSearchForm > div.search-button > button')))
        submit.click()

        # 第二种方法
        # in_put = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="q"]')))
        # in_put.send_keys('美食')
        # submit = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="J_TSearchForm"]/div[1]/button')))
        # submit.click()

        # 第三种方法
        # browser.find_element_by_xpath('//*[@id="q"]').clear()
        # browser.find_element_by_xpath('//*[@id="q"]').send_keys("美食")
        # browser.find_element_by_xpath('//*[@id="J_TSearchForm"]/div[1]/button').click()

        total = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '#mainsrp-pager > div > div > div > div.total')))
        get_products()
        return total.text
    except TimeoutException:
        return search()


def next_page(page_number):
    """
    实现自动翻页
    :param page_number:
    :return:
    """
    print('正在翻页：', page_number)
    try:
        in_put = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '#mainsrp-pager > div > div > div > div.form > input')))
        in_put.clear()
        in_put.send_keys(page_number)
        submit = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, '#mainsrp-pager > div > div > div > div.form > span.btn.J_Submit')))
        submit.click()
        wait.until(EC.text_to_be_present_in_element((By.CSS_SELECTOR, '#mainsrp-pager > div > div > div > ul > li.item.active > span'), str(page_number)))
        get_products()
    except TimeoutException:
        next_page(page_number)


def get_products():
    """
    获取页面内容
    :return:
    """
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '#mainsrp-itemlist .items .item')))
    html = browser.page_source
    doc = pq(html)
    items = doc('#mainsrp-itemlist .items .item').items()
    for item in items:
        product = {
            'image': item.find('.pic .img').attr('src'),
            'price': item.find('.price').text(),
            'deal': item.find('.deal-cnt').text()[:-3],
            'title': item.find('.title').text(),
            'shop': item.find('.shop').text(),
            'location': item.find('.location').text()
        }
        # print(product)
        save_to_mongo(product)


def save_to_mongo(result):
    """
    将数据存入MongoDB数据库
    :param result:
    :return:
    """
    try:
        if db[MONGO_TABLE].insert(result):
            print('存储到MongoDB成功', result)
            return True
        return False
    except Exception:
        print('存储到MongoDB失败', result)

def main():
    try:

        total = search()
        total = int(re.compile('(\d+)').search(total).group(1))
        # print(total)
        for i in range(2, total):
            next_page(i)
    except Exception:
        print('出错了！！！')
    finally:
        browser.close()

if __name__ == '__main__':
    main()
