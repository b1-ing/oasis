import json
import pandas as pd
import numpy as np
import nltk
import torch
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import LatentDirichletAllocation
from transformers import pipeline
from collections import Counter

nltk.download("punkt")

# ---- Load Data ----
def load_posts(filepath):
    if filepath.endswith(".json"):
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        return pd.DataFrame(data)
    else:
        return pd.read_csv(filepath)

# ---- Split Viral vs Non-Viral ----
def split_by_viral_threshold(df, score_column="score", quantile=0.9):
    threshold = df[score_column].quantile(quantile)
    viral = df[df[score_column] >= threshold].copy()
    non_viral = df[df[score_column] < threshold].copy()
    print(f"💥 Viral threshold score: {threshold:.2f}")
    return viral, non_viral, threshold

# ---- Topic Modeling ----
def extract_topics(posts, n_topics=5):
    vectorizer = TfidfVectorizer(max_df=0.95, min_df=2, stop_words='english')
    X = vectorizer.fit_transform(posts)
    lda = LatentDirichletAllocation(n_components=n_topics, random_state=42)
    lda.fit(X)
    terms = vectorizer.get_feature_names_out()
    topic_keywords = []
    for topic in lda.components_:
        top_keywords = [terms[i] for i in topic.argsort()[:-6:-1]]
        topic_keywords.append(top_keywords)
    return topic_keywords

# ---- Sentiment and Emotion ----
def analyze_sentiment(posts):
    classifier = pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english")
    return classifier(posts)

def analyze_emotion(posts):
    emotion_classifier = pipeline("text-classification", model="j-hartmann/emotion-english-distilroberta-base", top_k=1)
    return emotion_classifier(posts)

# ---- Controversy Estimator ----
def estimate_controversy(posts):
    # Simple proxy: measure polarity spread from sentiment
    sentiments = analyze_sentiment(posts)
    controversial = [abs(1 - s['score']) for s in sentiments]  # closer to 0.5 = more controversial
    return controversial

# ---- Analyze Group ----
def analyze_group(name, df):
    print(f"\n📊 Analyzing {name} ({len(df)} posts)")
    posts = df["text"].astype(str).tolist()

    topics = extract_topics(posts)
    sentiments = analyze_sentiment(posts)
    emotions = analyze_emotion(posts)
    controversy_scores = estimate_controversy(posts)

    sentiment_counts = Counter([s["label"] for s in sentiments])
    emotion_counts = Counter([e[0]["label"] for e in emotions])
    avg_controversy = np.mean(controversy_scores)

    print(f"🗂 Topics:")
    for i, topic in enumerate(topics):
        print(f"  - Topic {i+1}: {', '.join(topic)}")

    print(f"😊 Sentiments: {dict(sentiment_counts)}")
    print(f"😲 Emotions: {dict(emotion_counts)}")
    print(f"🔥 Average Controversy Score: {avg_controversy:.3f}")

# ---- Main ----
def main(filepath):
    df = load_posts(filepath)
    if "text" not in df.columns or "score" not in df.columns:
        raise ValueError("CSV/JSON must include 'text' and 'score' columns")

    viral, non_viral, threshold = split_by_viral_threshold(df)

    analyze_group("Viral Posts", viral)
    analyze_group("Non-Viral Posts", non_viral)

if __name__ == "__main__":
    main("reddit_structured_posts_security.json")  # or replace with "posts.csv"
