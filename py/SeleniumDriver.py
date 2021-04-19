import logging
import time
from selenium import webdriver
from selenium.webdriver.common.keys import Keys as keys

class SeleniumDriver(object):
    def __init__(self):
        self.WAIT_TIME = 1
        self.browser = webdriver.Chrome()

    def reqestUrl(self, url):
        try:
            self.browser.get(url)
            self.browser.implicitly_wait(5)
        except Exception as e:
            logging.error(f"File Not load: {url}")
            logging.error(e)


    def closeBrowser(self):
        try:
            self.browser.close()
        except Exception as e:
            logging.error(e)


    def getSouce(self):
        try:
            return self.browser.page_source
        except Exception as e:
            logging.error("Get Source")
            logging.error(e)


    def getScreenShot(self, fileName):
        try:
            self.browser.save_screenshot(fileName)
        except Exception as e:
            logging.error(f"Not shot: {fileName}")
            logging.error(e)


    def getScreenShotAction(self, url, fileName, sleeping=0):
        try:
            self.browser.get(url)
            self.browser.save_screenshot(fileName)
            time.sleep(sleeping)

            self.browser.close()
        except Exception as e:
            logging.error(f"FNot shot: {url}")
            logging.error(e)


    def reqestlogin(self, url, loginC, passwordC, login, password, buttunC, rememberMeC="remember_me"):
        try:
            self.reqestUrl(url)
            elm = self.browser.find_element_by_name(loginC)
            elm.send_keys(login)
            time.sleep(self.WAIT_TIME)            
            elm = self.browser.find_element_by_name(passwordC)
            elm.send_keys(passwordC)
            time.sleep(self.WAIT_TIME)            
            elm = self.browser.find_element_by_name(rememberMeC)
            elm.click()
            time.sleep(self.WAIT_TIME)            
            elm = self.browser.find_element_by_id(buttunC)
            elm.click()
            time.sleep(self.WAIT_TIME)            
        except Exception as e:
            logging.error(f"File Not load: {url}")
            logging.error(e)


    def twitterReqestlogin(self, url, login, password):
        try:
            self.reqestUrl(url)
            username = self.browser.find_element_by_css_selector('#page-container &gt; div &gt; div.signin-wrapper &gt; form &gt; fieldset &gt; div:nth-child(2) &gt; input')
            password = self.browser.find_element_by_css_selector('#page-container &gt; div &gt; div.signin-wrapper &gt; form &gt; fieldset &gt; div:nth-child(3) &gt; input')
            username.send_keys(login)
            password.send_keys(password)
            password.send_keys(keys.ENTER)
            time.sleep(self.WAIT_TIME)            
        except Exception as e:
            logging.error(f"File Not load: {url}")
            logging.error(e)

