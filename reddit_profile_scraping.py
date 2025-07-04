from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import json
from bs4 import BeautifulSoup



def scrape_first_n_users(subreddit, n=50, num_scrolls=15):
    chrome_options = Options()
    # chrome_options.add_argument("--headless")  # Uncomment for no browser window
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("user-agent=Mozilla/5.0")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    driver.get(f"https://www.reddit.com/r/{subreddit}/new/")

    WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, 'article'))
    )

    unique_users = set()
    scroll_count = 0

    while len(unique_users) < n and scroll_count < num_scrolls:
        posts = driver.find_elements(By.CSS_SELECTOR, 'article')
        for post in posts:
            try:
                author_elem = post.find_element(By.CSS_SELECTOR, 'a[href^="/user/"]')
                username = author_elem.text.strip()
                if username and username not in unique_users:
                    unique_users.add(username)
                    if len(unique_users) >= n:
                        break
            except:
                continue

        if len(unique_users) >= n:
            break

        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        scroll_count += 1

    driver.quit()
    return list(unique_users)

def scrape_user_profile(username):
    chrome_options = Options()
    # chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("user-agent=Mozilla/5.0")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    url = f"https://www.reddit.com/user/{username.lstrip('u/')}"
    driver.get(url)
    time.sleep(3)

    profile_data = {"username": username}

    # Get full HTML to parse with BeautifulSoup
    html = driver.page_source
    soup = BeautifulSoup(html, "html.parser")

    # Bio
    try:
        about_elem = soup.find('div', {'data-testid': 'profile--bio'})
        profile_data["bio"] = about_elem.text.strip() if about_elem else None
    except:
        profile_data["bio"] = None

    # Karma values
    karma_spans = soup.find_all('span', {'data-testid': 'karma-number'})
    if len(karma_spans) >= 2:
        profile_data["post_karma"] = karma_spans[0].text.strip()
        profile_data["comment_karma"] = karma_spans[1].text.strip()
    else:
        profile_data["post_karma"] = None
        profile_data["comment_karma"] = None

    # Cake day
    cake_day_tag = soup.find('time', {'data-testid': 'cake-day'})
    profile_data["cake_day"] = cake_day_tag.get('datetime') if cake_day_tag else None

    driver.quit()
    return profile_data

def save_to_json(data, filename="reddit_users_profiles.json"):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    subreddit = "NationalServiceSG"
    print(f"Scraping first 50 unique users from r/{subreddit}...")
    users = scrape_first_n_users(subreddit, n=1)

    print(f"Scraping profiles for {len(users)} users...")
    profiles = []
    for i, user in enumerate(users, 1):
        print(f"[{i}/{len(users)}] Scraping profile: {user}")
        profile_data = scrape_user_profile(user)
        profiles.append(profile_data)

    save_to_json(profiles)
    print(f"✅ Saved {len(profiles)} user profiles to reddit_users_profiles.json")
