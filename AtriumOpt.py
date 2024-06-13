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

config      = configparser.ConfigParser()
config.read("configurations.ini")
SleepTime   = int(config["Script Information"]["Sleep"])
WaitTime    = int(config["Script Information"]["Wait"])
ErrorTime   = int(config["Script Information"]["Error"])

logging.basicConfig(filename = "AtriumOptLogger.txt", filemode='w', format='%(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)
#endregion

class color:
    red         = Back.RED
    blue        = Back.BLUE
    green       = Back.GREEN
    grey        = Back.LIGHTBLACK_EX
    default     = Back.RESET

class AtriumCrawler:

    def __init__(self, username, password):
        print("Initiating Constructor")
        self.username = username
        self.password = password
        self.pages_accessed = []
        self.driver = webdriver.Safari()
        self.main_page = None
        self.login()
        self.open_people_tab()

    def __enter__(self):
        print("Initiating Driver")
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
        sleep(SleepTime)
        while retry_count < MAX_RETRYS:
            try:
                username_element = self.driver.find_element(By.ID, 'username')
                username_element.send_keys(self.username)

                password_element = self.driver.find_element(By.ID, 'password')
                password_element.send_keys(self.password)
                element = WebDriverWait(self.driver, WaitTime).until(EC.element_to_be_clickable((By.NAME, "submit")))
                sleep(SleepTime)
                self.driver.execute_script("arguments[0].click();", element)        

                try_count = 0
                while try_count < MAX_RETRYS:
                    try:
                        # Check if the element is present
                        element_present = EC.presence_of_element_located((By.ID, "header-text"))
                        WebDriverWait(self.driver, WaitTime).until(element_present)
                        print("Element is present on the page.")

                        # Wait for the element to disappear
                        element_disappeared = EC.invisibility_of_element_located((By.ID, 'header-text'))
                        WebDriverWait(self.driver, WaitTime).until(element_disappeared)
                        print("Element has disappeared from the page.")
                        break
                    except Exception as e:
                        print(f"Element was not found within the timeout period, or it did not disappear within the timeout period.\n\t {e}")
                        sleep(ErrorTime)
                        try_count+=1
                        continue

                element = WebDriverWait(self.driver, WaitTime).until(EC.element_to_be_clickable((By.ID, "dont-trust-browser-button")))
                sleep(SleepTime)
                self.driver.execute_script("arguments[0].click();", element)        
                sleep(SleepTime)
                break

            except Exception as e:
                retry_count += 1
                print(f"Failure while trying to log in\nRestarting Operation ({retry_count})\nError Source: {e}")
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

    def open_people_tab(self):
        print("Finding people")
        self.main_page = self.driver.current_window_handle
        print("A")
        element = WebDriverWait(self.driver, WaitTime).until(EC.element_to_be_clickable((By.XPATH, "//*[contains(text(), 'People')]")))
        self.driver.execute_script("arguments[0].click();", element)
        # element.click()
        print("B")

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
                print(f"Trouble when accesing and choosing ID in drop-down search bar\nRestarting operation ({retry_count})\nError source: {e}")
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

                element = WebDriverWait(self.driver, WaitTime).until(EC.element_to_be_clickable((By.XPATH,"//span[@class='name' and contains(text(), 'CONFERENCE')]")))
                self.driver.execute_script("arguments[0].click();", element)

                break

            except Exception as e:
                retry_count += 1
                print(f"Error finding and/or clicking on chosen card\nRestarting operation ({retry_count})\nError source: {e}")
                sleep(ErrorTime)
                continue

        if (retry_count == MAX_RETRYS):
            print(f"Operation failed, exit code: 0\nSkipping current card ({card_number})")
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
                return set([x.text for x in access_li])

            except Exception as e:   
                try:
                    self.driver.find_element(By.XPATH, "//div[@id='access_groups']/p[@class='none_assigned']")
                    print("Tab: %s%s%s" % (color.green, tabs[i], color.default))
                    print("%sNo Access%s" % (color.blue, color.default))
                except NoSuchElementException:
                    return False
                continue

    def open_edit(self):
        print("Initiating Open Edit")
        self.driver.execute_script("arguments[0].click();", WebDriverWait(self.driver, WaitTime).until(EC.element_to_be_clickable((By.ID,"edit_icon_body")))) 
        sleep(SleepTime)

        accordion_buttons = self.driver.find_elements(By.CLASS_NAME, "accordion-button")
        print(accordion_buttons[3])
        accordion_buttons[3].click()

    def change_access(self):
        print("Initiating Change Access") 
        parent_div = WebDriverWait(self.driver, 2).until(
            EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'lft_rgt_opts') and contains(@class, 'bulk_move')]"))
        )
        rgt_opt_button = parent_div.find_element(By.XPATH, ".//button[contains(@class, 'rgt_opt')]")
        self.driver.execute_script("arguments[0].click();", rgt_opt_button) 
        if (len(self.new_access_list) == 0 or self.new_access_list[0] == "None"):
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

    def run(self, card_list, new_access_list):
        print("Initiating Run")
        self.card_list = card_list
        self.new_access_list = new_access_list
        start_session = time()
        for card in self.card_list:
            start_card = time()
            self.access_search_bar()
            sleep(SleepTime)
            self.open_card(card)
            sleep(SleepTime)
            access = self.find_access(card)
            if (access == set(new_access_list)):
                self.atrium_homepage()
                continue
            sleep(SleepTime)
            self.open_edit()
            sleep(SleepTime)
            self.change_access()
            sleep(SleepTime)
            self.atrium_homepage()

            print("%sCard took %.2f seconds%s" % (color.grey, time() - start_card, color.default))
        print("%sSession took %.2f seconds%s" % (color.grey, time() - start_session, color.default))

if __name__ == "__main__":
    # card_list = (input("Card numbers: ")).split(", ")
    # new_access_list = (input("New card access: ")).split(", ")    
    # new_access_list = [item.strip() for item in new_access_list if item.strip()]
    # username = input("Username: ")
    # password = input("Password: ")
    username = "01443182"
    password = "Bgp1112@U"
    card_list = ["529062", "528608", "527922", "527096", "527760", "465054", "529043", "527115", "528607", "496185", "528588", "529078", "527106", "528605", "529177", "528606", "530519", "529053", "528595", "529067", "529061", "529058", "528613", "529798", "528633", "529783", "529799", "529070", "529066", "529046", "495494", "529034"]
    new_access_list = ["CONF KAHLERT 3RD FLOOR 3301-3364"]

    # SQLHandler.create_server_connection()
    # SQLHandler.change_card(card_list[0], new_access_list, username)

    try:
        with AtriumCrawler(username, password) as crawler:
            # crawler.login()
            print(new_access_list)
            print("Logging In succesful")
            sleep(SleepTime)
            print("Running")
            crawler.run(card_list, new_access_list)
    except Exception as e:
        print("There was a problem in the operation")