import json
import pandas as pd
import spacy
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from sklearn.feature_extraction.text import CountVectorizer
# Load posts

subreddit="NationalServiceSG"
with open(f"processed_{subreddit}_posts.json", "r", encoding="utf-8") as f:
    posts = json.load(f)

# Initialize sentiment analyzer and spaCy NLP
analyzer = SentimentIntensityAnalyzer()
nlp = spacy.load("en_core_web_sm")

# Trigger keywords that often appear in viral posts
def post_text(p):
    return ((p.get('title') or '') + ' ' + (p.get('post_text') or '')).lower()

texts = [post_text(p) for p in posts]
virality_metric = [(p['score'] + 0.5 * p['num_comments']) for p in posts]

# Top X% are viral
df = pd.DataFrame({'text': texts, 'virality': virality_metric})
threshold = df['virality'].quantile(0.90)
viral_texts = df[df['virality'] >= threshold]['text']
nonviral_texts = df[df['virality'] < threshold]['text']

# ----------------------------
# STEP 2: Extract common discriminative keywords
# ----------------------------
vectorizer = CountVectorizer(stop_words='english', max_features=3000)
X_viral = vectorizer.fit_transform(viral_texts)
X_nonviral = vectorizer.transform(nonviral_texts)

viral_freq = X_viral.sum(axis=0).A1
nonviral_freq = X_nonviral.sum(axis=0).A1
vocab = vectorizer.get_feature_names_out()

# Compute "viral bias score" for each keyword
keyword_scores = [(vocab[i], viral_freq[i] - nonviral_freq[i]) for i in range(len(vocab))]
keyword_scores.sort(key=lambda x: -x[1])

# Pick top 15 viral keywords
trigger_keywords = [kw for kw, score in keyword_scores[:15]]
print("Auto-generated trigger keywords:", trigger_keywords)
# Detect if a sentence is a question using NLP
def is_question_nlp(text):
    if not text:
        return False

    doc = nlp(text.lower())
    for token in doc:
        if token.tag_ in ("WDT", "WP", "WP$", "WRB"):  # WH-words
            return True
        if token.dep_ == "aux" and token.head.pos_ == "VERB":
            return True

    common_starts = ["anyone know", "can someone", "need help", "is it possible", "how do i", "looking for", "where can i", "what do i"]
    return any(text.lower().startswith(p) for p in common_starts)

# Compute features
def compute_features(post):
    title = post.get('title', '') or ''
    text = post.get('post_text', '') or ''
    combined = f"{title} {text}".lower()

    sentiment = analyzer.polarity_scores(combined)
    compound = sentiment['compound']
    num_keywords = sum(kw in combined for kw in trigger_keywords)
    has_question = is_question_nlp(title) or is_question_nlp(text)
    word_count = len(combined.split())

    # Simple rule-based virality score
    score = (
        compound * 2 +
        num_keywords * 1.5 +
        has_question * 2 +
        (word_count > 50) * 1.0
    )

    return {
        "id": post["id"],
        "title": post["title"],
        "score": post["score"],
        "num_comments": post["num_comments"],
        "compound": compound,
        "num_keywords": num_keywords,
        "has_question": has_question,
        "computed_virality_score": round(score, 3)
    }

# Apply to all posts
features_df = pd.DataFrame([compute_features(p) for p in posts])

# Rank by predicted virality
top_predicted = features_df.sort_values(by="computed_virality_score", ascending=False)

# Save output
features_df.to_csv(f"analyzed_posts_{subreddit}_2.csv", index=False)

# Preview top 10
print(top_predicted.head(10))
