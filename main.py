import time
import csv
import re
import os
import pickle
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class Data_Mining():
    def __init__(self):
        self.path = r"C:\Users\Elyar\Desktop\test"  # مسیر ذخیره فایل و chromedriver
        self.driver_path = os.path.join(self.path, "chromedriver.exe")
        self.cookies_path = os.path.join(self.path, "cookies.pkl")
        self.driver = None

    def setup_driver(self):
        if not os.path.exists(self.driver_path):
            raise FileNotFoundError(f"chromedriver پیدا نشد در: {self.driver_path}")

        chrome_options = Options()
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("--disable-infobars")
        chrome_options.add_argument("--disable-extensions")

        self.driver = webdriver.Chrome(service=Service(self.driver_path), options=chrome_options)

    def login(self):
        self.driver.get("https://www.linkedin.com/")

        if os.path.exists(self.cookies_path):
            print("🔁 بارگذاری کوکی‌های ذخیره شده...")
            with open(self.cookies_path, "rb") as cookies_file:
                cookies = pickle.load(cookies_file)
                for cookie in cookies:
                    if 'expiry' in cookie:
                        del cookie['expiry']
                    self.driver.add_cookie(cookie)

            self.driver.get("https://www.linkedin.com/feed/")
            time.sleep(3)

            if "feed" in self.driver.current_url:
                print("✅ لاگین با کوکی‌ها موفق بود.")
                return
            else:
                print("⚠️ کوکی‌ها معتبر نیستند یا منقضی شده‌اند. نیاز به لاگین دستی.")

        self.driver.get("https://www.linkedin.com/login/")
        print("🔑 لطفاً ایمیل و رمز عبور خود را وارد کنید و لاگین شوید (و کپچا را حل کنید اگر نمایش داده شد)...")

        try:
            WebDriverWait(self.driver, 180).until(
                EC.presence_of_element_located((By.ID, "global-nav-search"))
            )
            print("✅ ورود با موفقیت انجام شد.")

            cookies = self.driver.get_cookies()
            with open(self.cookies_path, "wb") as cookies_file:
                pickle.dump(cookies, cookies_file)
            print("💾 کوکی‌ها ذخیره شدند.")

        except:
            print("⛔ زمان ورود تمام شد یا ورود ناموفق بود.")
            self.driver.quit()
            exit()

    def jobs(self, job_name: str, location: str):
        self.driver.get("https://www.linkedin.com/jobs/")
        time.sleep(5)

        job_name_input = self.driver.find_element(By.CSS_SELECTOR, 'input[aria-label="Search by title, skill, or company"]')
        job_name_input.clear()
        job_name_input.send_keys(job_name)
        time.sleep(1)

        location_input = self.driver.find_element(By.CSS_SELECTOR, 'input[aria-label="City, state, or zip code"]')
        location_input.clear()
        location_input.send_keys(location)
        time.sleep(1)
        location_input.send_keys(Keys.RETURN)
        time.sleep(5)

    def job_scraper(self, counts: int):
        def loop_count(counts: int):
            return (counts // 25) + (1 if counts % 25 != 0 else 0)

        def clean_salary(text: str):
            match = re.search(r"\$[\d.,K]+/?[a-zA-Z]*(?:\s*-\s*\$[\d.,K]+/?[a-zA-Z]*)?", text)
            return match.group() if match else "None"

        job_data = []

        for _ in range(loop_count(counts)):
            time.sleep(2)
            jobs = self.driver.find_elements(By.XPATH, "//li[@data-occludable-job-id]")

            for job in jobs:
                self.driver.execute_script("arguments[0].scrollIntoView();", job)
                try:
                    job_id = job.get_attribute("data-occludable-job-id")

                    job_title_element = job.find_element(By.XPATH, ".//a[contains(@class, 'job-card-container__link')]")
                    job_title = job_title_element.text.strip()

                    company_element = job.find_element(By.XPATH, ".//div[contains(@class, 'artdeco-entity-lockup__subtitle')]")
                    company_name = company_element.text.strip()

                    location = "None"
                    try:
                        location_element = job.find_element(By.XPATH, ".//div[contains(@class, 'artdeco-entity-lockup__caption')]//li")
                        location = location_element.text.strip()
                    except:
                        pass

                    salary = "None"
                    try:
                        salary_element = job.find_element(By.XPATH, ".//div[contains(@class, 'artdeco-entity-lockup__metadata')]//li")
                        salary = clean_salary(salary_element.text.strip())
                    except:
                        pass

                    job_data.append({
                        'ID': job_id,
                        'Link': f"https://www.linkedin.com/jobs/view/{job_id}/",
                        'Title': job_title,
                        'Company': company_name,
                        'Location': location,
                        'Salary': salary
                    })
                except Exception as e:
                    print(f"⚠️ خطا در استخراج اطلاعات شغل: {e}")
                    continue

            try:
                next_button_element = self.driver.find_element(By.XPATH, "//button[@aria-label='View next page']")
                if next_button_element.is_enabled():
                    next_button_element.click()
                else:
                    print("🔚 دکمه بعدی غیرفعال است. توقف.")
                    break
            except Exception as e:
                print(f"⛔ نتوانست دکمه بعدی را پیدا کند یا کلیک کند: {e}")
                break

        job_data_path = os.path.join(self.path, "job_data.csv")
        with open(job_data_path, "w", newline='', encoding='utf-8') as jobs_data:
            writer = csv.DictWriter(jobs_data, fieldnames=["ID", "Link", "Title", "Company", "Location", "Salary"])
            writer.writeheader()
            writer.writerows(job_data)

        print(f"✅ استخراج {len(job_data)} شغل کامل شد. فایل ذخیره شد در: {job_data_path}")


if __name__ == "__main__":
    data = Data_Mining()
    data.setup_driver()
    data.login()
    data.jobs('java', 'germany')
    data.job_scraper(50)