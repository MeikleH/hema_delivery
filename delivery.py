import os
import csv
import time
import random
import atexit
import requests

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
# from selenium.common.exceptions import NoSuchElementException as nsee

url_prefix = 'https://api2.pushdeer.com/message/push?pushkey=<your pushkey>&text='
url_time_prefix = 'https://api2.pushdeer.com/message/push?pushkey=<your pushkey>&text=' + \
    time.strftime("%H:%M", time.localtime()) + ' '
# 请在pushkey处填入自己的pushkey，如有疑问可以先了解一下pushdeer这个项目
# 当然不需要推送的话直接把所有requests全删掉也行


# 程序退出前执行
@atexit.register
def notice():
    write_csv('error', time.strftime(
        "%y-%m-%d %H:%M:%S", time.localtime()), '异常退出')

    print(time.strftime("%y-%m-%d %H:%M:%S", time.localtime()) + ' 异常退出')

    push_url_atexit = url_prefix + ' ' + \
        time.strftime("%m-%d %H:%M:%S", time.localtime()) + ' 盒马下单监控异常退出'
    requests.get(push_url_atexit)


# 写csv
def write_csv(document, date, availability):
    if document == 'delivery':
        path = "./hema_delivery.csv"
    else:
        path = "./error.csv"
    with open(path, 'a+', newline='', encoding='utf-8-sig') as f:
        csv_write = csv.writer(f)
        data_row = [date, availability]
        csv_write.writerow(data_row)


# 判断是否有运力
def hema_selenium_delivery():
    # 反爬虫，移除 window.navigator.webdriver，添加参数
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('log-level=3')
    # chrome_options.add_argument('--headless')  # 隐藏显示
    chrome_options.add_argument('--incognito')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--start-maximized')
    chrome_options.add_argument('--disable-extensions')
    chrome_options.add_argument('--profile-directory=Default')
    chrome_options.add_argument('--disable-plugins-discovery')
    chrome_options.add_argument('blink-settings=imagesEnabled=false')
    driver = webdriver.Chrome(chrome_options=chrome_options)
    driver.delete_all_cookies()
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": """
        Object.defineProperty(navigator, 'webdriver', {
        get: () => undefined
        })
        """
    })

    # 访问网址
    driver.get(
        'https://hema.taobao.com/s/itemdetail?shopid=401583233&serviceid=645944692876')
    # 用需要监控运力的盒马店铺的有货商品链接，这里用的是绿地新都汇店面粉的链接
    # 所以监控的就是绿地新都会店的运力情况
    n = 0
    if not os.path.exists('./delivery'):
        os.makedirs('./delivery')
    if not os.path.exists('./delivery/mhtml'):
        os.makedirs('./delivery/mhtml')

    while(1):
        n = n + 1
        url_time_prefix = 'https://api2.pushdeer.com/message/push?pushkey=PDU82ThbUhK6lnrCX7bY3Q6ZYj21w3OFHiW7kl&text=' + \
            time.strftime("%H:%M", time.localtime()) + ' '
        try:
            driver.refresh()
            time.sleep(1)

            # 404异常处理
            message_404 = str(driver.find_element(
                by=By.XPATH, value='/html/body/h1').get_attribute('innerText'))
            if '404' in (message_404):
                # 写csv
                write_csv('error', time.strftime(
                    "%y-%m-%d %H:%M:%S", time.localtime()), '404 error')

                print(time.strftime(
                    "%y-%m-%d %H:%M:%S", time.localtime()) + ' 404 error')

                # 保存mhtml供排查错误
                error_mhtml = driver.execute_cdp_cmd(
                    'Page.captureSnapshot', {})
                if not os.path.exists('./delivery/mhtml'):
                    os.makedirs('./delivery/mhtml')
                error_mhtml_filename = './delivery/mhtml/delivery_404_error_inCycle' + str(n) + '_' + \
                    str(time.strftime("%H%M", time.localtime())) + '.mhtml'
                with open(error_mhtml_filename, 'w', newline='') as f:
                    f.write(error_mhtml['data'])

                push_url_404 = url_time_prefix + '404 error'
                requests.get(push_url_404)

                continue

        except Exception as e1:
            if 'no such element' in str(e1):
                continue
            else:
                # 保存mhtml供排查错误
                error_mhtml = driver.execute_cdp_cmd(
                    'Page.captureSnapshot', {})
                if not os.path.exists('./delivery/mhtml'):
                    os.makedirs('./delivery/mhtml')
                error_mhtml_filename = './delivery/mhtml/delivery_other_error_inCycle' + str(n) + '_' + \
                    str(time.strftime("%H%M", time.localtime())) + '.mhtml'
                with open(error_mhtml_filename, 'w', newline='') as f:
                    f.write(error_mhtml['data'])

                # 输出错误详情
                print(e1)
                continue

        finally:
            try:
                message_404
                continue
            except:
                pass
            # 获取运力状态
            try:
                # 拼接推送网址
                # push_url_full = url_time_prefix + '盒马绿地新都汇店运力状态：' + delivery_status
                push_url_empty = url_time_prefix + '盒马绿地新都汇店运力状态：可下单'
                # 等待某个class加载完
                WebDriverWait(driver, 5).until(ec.presence_of_element_located(
                    (By.CLASS_NAME, "item-detail-bottom-ability")))
                delivery_status = driver.find_element(
                    by=By.XPATH,
                    value='//*[@id="root"]/div/div/div[1]/div[3]/div[1]'
                ).get_attribute('innerText')

            except Exception as e2:
                if 'no such element' in str(e2):
                    write_csv('delivery', time.strftime(
                        "%y-%m-%d %H:%M:%S", time.localtime()), '有运力')
                    print(time.strftime(
                        "%y-%m-%d %H:%M:%S", time.localtime()) + ' 有运力')
                    requests.get(push_url_empty)

            finally:
                if "满" in delivery_status:
                    write_csv('delivery', time.strftime(
                        "%y-%m-%d %H:%M:%S", time.localtime()), '无运力')
                    print(time.strftime(
                        "%y-%m-%d %H:%M:%S", time.localtime()) + ' 无运力')
                    # requests.get(push_url_full)
                else:
                    # 保存mhtml供排查错误
                    error_mhtml = driver.execute_cdp_cmd(
                        'Page.captureSnapshot', {})
                    if not os.path.exists('./delivery/mhtml'):
                        os.makedirs('./delivery/mhtml')
                    error_mhtml_filename = './delivery/mhtml/delivery_Unknown_error_inCycle' + str(n) + '_' + \
                        str(time.strftime("%H%M", time.localtime())) + '.mhtml'
                    with open(error_mhtml_filename, 'w', newline='') as f:
                        f.write(error_mhtml['data'])

                    write_csv('delivery', time.strftime(
                        "%y-%m-%d %H:%M:%S", time.localtime()), '未知情况')
                    print(time.strftime(
                        "%y-%m-%d %H:%M:%S", time.localtime()) + ' 未知情况')
                    push_url_unknown = url_time_prefix + '未知情况'
                    requests.get(push_url_unknown)

                # 保存截图
                filename = './delivery/delivery_screenshot_incycle' + str(n) + '_' + \
                    str(time.strftime("%H%M", time.localtime())) + '.png'
                driver.save_screenshot(str(filename))

                service_status = url_time_prefix + '盒马下单监控正在运行'
                if (n % 30) == 0:
                    requests.get(service_status)

                # 等待一分钟左右，带点儿随机，再开始下一次循环
                time.sleep(50 + random.randint(0, 20))


def main():
    hema_selenium_delivery()


if __name__ == "__main__":
    main()
