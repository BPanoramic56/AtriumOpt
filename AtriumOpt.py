#region imports
from time       import sleep
from time       import time
from sys        import exit
from colorama   import Back
from selenium   import webdriver
from selenium.webdriver.common.by       import By
from selenium.webdriver.support.ui      import WebDriverWait
from selenium.webdriver.support         import expected_conditions as EC
from selenium.webdriver.support.ui      import Select
from selenium.common.exceptions         import NoSuchElementException
#endregion

#region constants
URL = r"https://utah.atriumcampus.com"
MAX_RETRYS = 3
#endregion

class color:
    red = Back.RED
    blue = Back.BLUE
    green = Back.GREEN
    grey = Back.LIGHTBLACK_EX
    default = Back.RESET

class AtriumCrawler:

    def __init__(self, username, password, card_list, new_access_list):
        self.username = username
        self.password = password
        self.card_list = card_list
        self.new_access_list = new_access_list
        self.pages_accessed = []
        self.driver = None
        self.main_page = None

    def __enter__(self):
        self.driver = webdriver.Safari()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if self.driver:
            self.driver.quit()

    def login(self):
        self.driver.get(URL)
        self.driver.maximize_window()
        WebDriverWait(self.driver, 30).until(EC.element_to_be_clickable((By.XPATH, "//div[@role='button' and text()='Local']"))).click()

        retry_count = 0
        while retry_count < MAX_RETRYS:
            try:
                self.driver.find_element(By.NAME, 'username').send_keys(self.username)
                self.driver.find_element(By.NAME, 'password').send_keys(self.password)
                WebDriverWait(self.driver, 30).until(EC.element_to_be_clickable((By.NAME, "login"))).click()                
                self.main_page = self.driver.current_window_handle
                WebDriverWait(self.driver, 30).until(EC.element_to_be_clickable((By.XPATH, "//*[contains(text(), 'People')]"))).click()
                break
            except Exception as e:
                retry_count += 1
                print("Failure while trying to log in\nRestarting Operation (#%i)\nError Source: %s" % (retry_count, e))
                if self.check_login_error():
                    print("Username or Password information incorrect\nClosing operation")
                    self.driver.close()
                    exit()
                continue
        return self
    
    def check_login_error(self):
        try:
            self.driver.find_element(By.XPATH, "//div[@id='notice' and contains(text(), 'information')]")
        except NoSuchElementException:
            return False
        return True

    def access_search_bar(self):
        sleep(1)
        retry_count = 0
        while retry_count < MAX_RETRYS:
            try:
                items = Select(self.driver.find_element(By.NAME, 'search_par[]'))
                items.select_by_value('card_number')
                break
            except Exception as e:
                retry_count += 1
                print("Trouble when accesing and choosing ID in drop-down search bar\nRestarting operation (#%i)\nError source: %s" % (retry_count, e))
                continue
        if (retry_count == MAX_RETRYS):
            print("Operation failed, exit code: -1\nExiting system")
            self.driver.close()
            exit()
    
    def open_card(self, card_number):
        retry_count = 0
        while retry_count < MAX_RETRYS:
            try:
                username_field = self.driver.find_element(By.NAME, 'value_box[]')
                username_field.clear()
                username_field.send_keys(card_number)
                sleep(2)
                username_field.send_keys(u'\ue007')
                sleep(2)
                WebDriverWait(self.driver, 30).until(EC.element_to_be_clickable((By.XPATH,"//span[@class='name' and contains(text(), 'CONFERENCE')]"))).click()
                break

            except Exception as e:
                retry_count += 1
                print("Error finding and/or clicking on chosen card\nRestarting operation (#%i)\nError source: %s" %(retry_count, e))
                continue

        if (retry_count == MAX_RETRYS):
            print("Operation failed, exit code: 0\nSkipping current card (%i)" % (card_number))
            return

    def find_access(self, card):
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
                # self.open_edit()
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
        try:
            WebDriverWait(self.driver, 30).until(EC.element_to_be_clickable((By.ID,"edit_icon_body"))).click()
            sleep(2)
            accordion_buttons = self.driver.find_elements(By.CLASS_NAME, "accordion-button")
            accordion_buttons[7].click()
            for i in range(2):
                self.driver.execute_script("window.scrollTo(100,document.body.scrollHeight);")
            self.change_access()
        except:
            pass

    def change_access(self):        
        WebDriverWait(self.driver, 30).until(EC.element_to_be_clickable((By.XPATH,"//button[@class='rgt_opt']"))).click()
        # for new_access in self.new_access_list:
        #     access_input = self.driver.find_element(By.XPATH,'//input[@placeholder="Filter Groups"]')
        #     access_input.clear()
        #     access_input.send_keys(new_access)
        #     options = self.driver.find_elements(By.XPATH,"//li[@role='option']")
        #     for option in options:
        #         if new_access in option.text:
        #             option.click()
        WebDriverWait(self.driver, 30).until(EC.element_to_be_clickable((By.XPATH,'//input[@value="Save"]'))).click()

    def atrium_homepage(self): 
        self.driver.switch_to.window(self.main_page)

    def run(self):
        start_session = time()
        for card in self.card_list:
            start_card = time()
            self.access_search_bar()
            self.open_card(card)
            self.find_access(card)
            self.atrium_homepage()
            print("%sCard took %.2f seconds%s" % (color.grey, time() - start_card, color.default))
        print("%sSession took %.2f seconds%s" % (color.grey, time() - start_session, color.default))

while True:
    if __name__ == "__main__":
        card_list = (input("Card numbers: ")).split(", ")
        new_access_list = (input("New card access: ")).split(", ")
        username = r"01443182"
        password = r"Bgp1112@Atrium"

        with AtriumCrawler(username, password, card_list, new_access_list) as crawler:
            crawler.login()
            crawler.run()
