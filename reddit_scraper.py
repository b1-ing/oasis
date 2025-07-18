from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import json
import time

def scrape_structured(subreddit, num_scrolls=3):
    chrome_options = Options()
    # chrome_options.add_argument("--headless")  # Enable headless if needed
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("user-agent=Mozilla/5.0")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

    driver.get(f"https://www.reddit.com/r/{subreddit}/new/")
    WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, 'article'))
    )

    for _ in range(num_scrolls):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)

    posts = driver.find_elements(By.CSS_SELECTOR, 'article')

    results = []
    for post in posts:
        try:
            # Title and link
            title_elem = post.find_element(By.CSS_SELECTOR, 'a[slot="title"]')
            title = title_elem.text.strip()
            url = "https://www.reddit.com" + title_elem.get_attribute("href")

            # Author
            author_elem = post.find_element(By.CSS_SELECTOR, 'a[href^="/user/"]')
            author = author_elem.text.strip()

            # Timestamp
            time_elem = post.find_element(By.CSS_SELECTOR, 'time')
            timestamp = time_elem.get_attribute("datetime")

            # Flair (optional)
            try:
                flair_elem = post.find_element(By.CSS_SELECTOR, '.flair-content')
                flair = flair_elem.text.strip()
            except:
                flair = None

            # Body preview (optional)
            try:
                body_elem = post.find_element(By.CSS_SELECTOR, '.feed-card-text-preview')
                post_text = body_elem.text.strip()
            except:
                post_text = None

            # Score (upvotes)
            try:
                score_el = post.find_element(By.TAG_NAME, "faceplate-number")
                score = int(score_el.text.strip())
                print(score)
                if score == 'Vote':  # sometimes it shows placeholder text
                    score = None
                else:
                    score = int(score.replace('k', '000').replace('.', ''))
            except:
                score = None

            # Comment count
            try:
                comment_elem = post.find_element(By.XPATH, ".//span[contains(text(),'comment')]")
                comment_text = comment_elem.text.strip().split()[0]
                if 'k' in comment_text:
                    comments_count = int(float(comment_text.replace('k', '')) * 1000)
                else:
                    comments_count = int(comment_text)
            except:
                comments_count = None

            results.append({
                "title": title,
                "url": url,
                "author": author,
                "timestamp": timestamp,
                "flair": flair,
                "post_text": post_text,
                "score": score,
                "comments_count": comments_count
            })
        except Exception as e:
            continue

    driver.quit()
    return results


def save_to_json(data, filename="reddit_structured_posts_new.json"):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    subreddit = "SecurityCamera"
    structured_posts = scrape_structured(subreddit, num_scrolls=2)
    save_to_json(structured_posts, filename="reddit_structured_posts_new.json")
    print(f"✅ Extracted {len(structured_posts)} structured posts from r/{subreddit}")
