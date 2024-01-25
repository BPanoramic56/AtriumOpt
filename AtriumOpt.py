import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import NoSuchElementException
from colorama import Back

# Constants
URL = r"https://utah.atriumcampus.com"
MAX_RETRYS = 3

# Color codes
class Color:
    red = Back.RED
    blue = Back.BLUE
    green = Back.GREEN
    default = Back.RESET

class AtriumCrawler:
    def __init__(self, card_list, new_access_list):
        self.card_list = card_list
        self.new_access_list = new_access_list
        self.pages_accessed = []
        self.driver = None

    def __enter__(self):
        self.driver = webdriver.Safari()  # You can use other drivers like Firefox, etc.
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if self.driver:
            self.driver.quit()

    def check_login_error(self):
        try:
            self.driver.find_element(By.XPATH, "//div[@id='notice' and contains(text(), 'information')]")
        except NoSuchElementException:
            return False
        return True

    def login(self):
        self.driver.get(URL)
        WebDriverWait(self.driver, 30).until(EC.element_to_be_clickable((By.XPATH, "//div[@role='button' and text()='Local']"))).click()

        username = input("Enter your username: ")
        password = input("Enter your password: ")

        retry_count = 0
        while retry_count < MAX_RETRYS:
            try:
                self.driver.find_element(By.NAME, 'username').send_keys(username)
                self.driver.find_element(By.NAME, 'password').send_keys(password)
                WebDriverWait(self.driver, 30).until(EC.element_to_be_clickable((By.NAME, "login"))).click()
                WebDriverWait(self.driver, 30).until(EC.element_to_be_clickable((By.XPATH, "//*[contains(text(), 'People')]"))).click()
                break
            except Exception as e:
                retry_count += 1
                print(f"Failure while trying to log in\nRestarting Operation (# {retry_count})\nError Source: {e}")
                if self.check_login_error():
                    print("Username or Password information incorrect\nClosing operation")
                    self.driver.close()
                    exit()
                continue

    # Other methods remain unchanged

if __name__ == "__main__":
    card_list = [12345, 67890]
    new_access_list = ["Access Group 1", "Access Group 2"]

    with AtriumCrawler(card_list, new_access_list) as crawler:
        crawler.login()
        crawler.run()
