#region imports
import configparser
from time                           import sleep
from time                           import time
from sys                            import exit
from colorama                       import Back
from selenium                       import webdriver
from selenium                       import webdriver
from selenium.webdriver.common.by   import By
from selenium.webdriver.support.ui  import WebDriverWait
from selenium.webdriver.support     import expected_conditions as EC
from selenium.webdriver.support.ui  import Select
from selenium.common.exceptions     import NoSuchElementException
from selenium.webdriver.common.keys import Keys

import logging
URL = r"https://utah.atriumcampus.com"
MAX_RETRYS = 3

config = configparser.ConfigParser()
config.read("configurations.ini")
SleepTime = int(config["Script Information"]["Sleep"])
WaitTime = int(config["Script Information"]["Wait"])
ErrorTime = int(config["Script Information"]["Error"])

logging.basicConfig(filename = "AtriumOptLogger.txt", filemode='w', format='%(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)
#endregion

class color:
    red = Back.RED
    blue = Back.BLUE
    green = Back.GREEN
    grey = Back.LIGHTBLACK_EX
    default = Back.RESET

class AtriumCrawler:

    def __init__(self, username, password, card_list, new_access_list):
        print("Initiating Constructor")
        self.username = username
        self.password = password
        self.card_list = card_list
        self.new_access_list = new_access_list
        self.pages_accessed = []
        self.driver = None
        self.main_page = None

    def __enter__(self):
        print("Initiating Driver")
        self.driver = webdriver.Safari()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        print("Initiating Exit")
        if self.driver:
            self.driver.quit()

    def login(self):        
        print("Initiating Login")
        self.driver.get(URL)
        self.driver.maximize_window()
        element = WebDriverWait(self.driver, WaitTime).until(EC.element_to_be_clickable((By.XPATH, "//div[@role='button' and text()='SSO Login']")))        
        self.driver.execute_script("arguments[0].click();", element)
        retry_count = 0
        sleep(int(SleepTime))
        while retry_count < MAX_RETRYS:
            try:
                username_element = self.driver.find_element(By.ID, 'username')
                username_element.send_keys(self.username)

                password_element = self.driver.find_element(By.ID, 'password')
                password_element.send_keys(self.password)
                element = WebDriverWait(self.driver, WaitTime).until(EC.element_to_be_clickable((By.NAME, "submit")))
                print("Element: " + str(element))
                sleep(SleepTime)
                self.driver.execute_script("arguments[0].click();", element)        

                try:
                    # Check if the element is present
                    element_present = EC.presence_of_element_located((By.XPATH, "Check for a Duo Push"))
                    WebDriverWait(self.driver, WaitTime).until(element_present)
                    print("Element is present on the page.")

                    # Wait for the element to disappear
                    element_disappeared = EC.invisibility_of_element_located((By.ID, 'element_id'))
                    WebDriverWait(self.driver, WaitTime).until(element_disappeared)
                    print("Element has disappeared from the page.")
                except Exception as e:
                    print("Element was not found within the timeout period, or it did not disappear within the timeout period.\n\t %(e)s")
                    sleep(ErrorTime)


                element = WebDriverWait(self.driver, WaitTime).until(EC.element_to_be_clickable((By.ID, "dont-trust-browser-button")))
                print("Element: " + str(element))
                sleep(SleepTime)
                self.driver.execute_script("arguments[0].click();", element)        
                sleep(SleepTime)
                print("Element Clicked")
                self.main_page = self.driver.current_window_handle
                WebDriverWait(self.driver, WaitTime).until(EC.element_to_be_clickable((By.XPATH, "//*[contains(text(), 'People')]"))).click()
                break
            except Exception as e:
                retry_count += 1
                print("Failure while trying to log in\nRestarting Operation (#%i)\nError Source: %s" % (retry_count, e))
                sleep(ErrorTime)
                if self.check_login_error():
                    print("Username or Password information incorrect\nClosing operation")
                    self.driver.close()
                    exit()
                continue
        return self
    
    def check_login_error(self):
        print("Initiating Check Login Error")
        try:
            self.driver.find_element(By.XPATH, "//div[@id='notice' and contains(text(), 'information')]")
        except NoSuchElementException:
            return False
        return True

    def access_search_bar(self):
        print("Initiating Access Search Bar")
        sleep(SleepTime)
        retry_count = 0
        while retry_count < MAX_RETRYS:
            try:
                items = Select(self.driver.find_element(By.NAME, 'search_par[]'))
                items.select_by_value('card_number')
                break
            except Exception as e:
                retry_count += 1
                print("Trouble when accesing and choosing ID in drop-down search bar\nRestarting operation (#%i)\nError source: %s" % (retry_count, e))
                sleep(ErrorTime)
                continue
        if (retry_count == MAX_RETRYS):
            print("Operation failed, exit code: -1\nExiting system")
            self.driver.close()
            exit()
    
    def open_card(self, card_number):
        print("Initiating Open Card")
        retry_count = 0
        while retry_count < MAX_RETRYS:
            try:
                username_field = self.driver.find_element(By.NAME, 'value_box[]')
                username_field.clear()
                username_field.send_keys(card_number)
                sleep(SleepTime)
                username_field.send_keys(u'\ue007')
                sleep(SleepTime)
                WebDriverWait(self.driver, WaitTime).until(EC.element_to_be_clickable((By.XPATH,"//span[@class='name' and contains(text(), 'CONFERENCE')]"))).click()
                break

            except Exception as e:
                retry_count += 1
                print("Error finding and/or clicking on chosen card\nRestarting operation (#%i)\nError source: %s" %(retry_count, e))
                sleep(ErrorTime)
                continue

        if (retry_count == MAX_RETRYS):
            print("Operation failed, exit code: 0\nSkipping current card (%i)" % (card_number))
            return

    def find_access(self, card):
        print("Initiating Find Access")
        tabs = self.driver.window_handles

        print("Current Card: %s%s%s" % (color.red, str(card), color.default))

        for i in range(len(tabs)):
            self.driver.switch_to.window(tabs[i])

            if tabs[i] == self.main_page:
                continue
            if tabs[i] in self.pages_accessed:
                continue

            try:
                access_div = WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//div[@id='access_groups']")))
                access_ul = access_div.find_element(By.TAG_NAME, "ul")
                access_li = access_ul.find_elements(By.TAG_NAME, "li")
                print("Tab: %s%s%s" % (color.green, tabs[i], color.default))
                print("Access: ")
                for access in access_li:
                    print("\t%s%s%s" % (color.blue, access.text, color.default))
                self.pages_accessed.append(tabs[i])
                break

            except Exception as e:   
                try:
                    self.driver.find_element(By.XPATH, "//div[@id='access_groups']/p[@class='none_assigned']")
                    print("Tab: %s%s%s" % (color.green, tabs[i], color.default))
                    print("%sNo Access%s" % (color.blue, color.default))
                    self.open_edit()
                except NoSuchElementException:
                    return False
                continue

    def open_edit(self):
        print("Initiating Open Edit")
        try:
            self.driver.execute_script("arguments[0].click();", WebDriverWait(self.driver, WaitTime).until(EC.element_to_be_clickable((By.ID,"edit_icon_body")))) 
            WebDriverWait(self.driver, WaitTime).until(EC.element_to_be_clickable((By.ID,"edit_icon_body"))).click()
            sleep(SleepTime)
            accordion_buttons = self.driver.find_elements(By.CLASS_NAME, "accordion-button")
            print(accordion_buttons)
            accordion_buttons[3].click()
        except:
            pass

    def change_access(self):   
        print("Initiating Change Access") 
        parent_div = WebDriverWait(self.driver, WaitTime).until(
            EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'lft_rgt_opts') and contains(@class, 'bulk_move')]"))
        )
        rgt_opt_button = parent_div.find_element(By.XPATH, ".//button[contains(@class, 'rgt_opt')]")
        self.driver.execute_script("arguments[0].click();", rgt_opt_button)    
        print(len(new_access_list))    
        if (len(new_access_list) == 0 or new_access_list[0] == "None"):
            WebDriverWait(self.driver, WaitTime).until(EC.element_to_be_clickable((By.XPATH,'//input[@value="Save"]'))).click()
            return
        for new_access in self.new_access_list:
            print("New Access")
            access_input = self.driver.find_element(By.XPATH,'//input[@placeholder="Filter Groups"]')
            access_input.clear()
            access_input.send_keys(new_access)
            options = self.driver.find_elements(By.XPATH,"//li[@role='option']")
            for option in options:
                if new_access in option.text:
                    option.click()
        WebDriverWait(self.driver, WaitTime).until(EC.element_to_be_clickable((By.XPATH,'//input[@value="Save"]'))).click()

    def atrium_homepage(self): 
        self.driver.switch_to.window(self.main_page)

    def run(self):
        print("Initiating Run")
        start_session = time()
        for card in self.card_list:
            start_card = time()
            self.access_search_bar()
            sleep(SleepTime)
            self.open_card(card)
            sleep(SleepTime)
            self.find_access(card)
            sleep(SleepTime)
            self.open_edit()
            sleep(SleepTime)
            self.change_access()
            sleep(SleepTime)
            self.atrium_homepage()
            print("%sCard took %.2f seconds%s" % (color.grey, time() - start_card, color.default))
        print("%sSession took %.2f seconds%s" % (color.grey, time() - start_session, color.default))

if __name__ == "__main__":
    card_list = (input("Card numbers: ")).split(", ")
    new_access_list = (input("New card access: ")).split(", ")    
    new_access_list = [item.strip() for item in new_access_list if item.strip()]
    username = input("Username: ")
    password = input("Password: ")
    # card_list = ["527166", "496287"]
    # new_access_list = ["CONF MHC", "CONF 821"]
    
    try:
        with AtriumCrawler(username, password, card_list, new_access_list) as crawler:
            crawler.login()
            print("Logging In succesful")
            sleep(SleepTime)
            print("Running")
            crawler.run()
    except Exception as e:
        print("There was a problem in the operation")