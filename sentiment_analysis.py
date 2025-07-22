import json
import pandas as pd
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from bertopic import BERTopic
from transformers import pipeline
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS
from keybert import KeyBERT
from tqdm import tqdm
from transformers import pipeline
# ---------------- CONFIG ----------------
subreddit="NationalServiceSG"
VIRAL_SCORE_THRESHOLD = 100
VIRAL_COMMENT_THRESHOLD = 30

# ------------- LOAD POSTS ----------------
with open(f"processed_{subreddit}_posts.json", "r", encoding="utf-8") as f:
    data = json.load(f)

df = pd.DataFrame(data)

# # Remove missing or empty posts
# df = df[df["text"].notna() & (df["text"].str.strip() != "")]

# Fill missing numeric fields with 0
df["score"] = pd.to_numeric(df.get("score", 0), errors="coerce").fillna(0)
VIRAL_SCORE_THRESHOLD = df["score"].mean()
df["num_comments"] = pd.to_numeric(df.get("num_comments", 0), errors="coerce").fillna(0)
VIRAL_COMMENTS_THRESHOLD = df["num_comments"].mean()
# ----------- SPLIT VIRAL/NON-VIRAL --------
def is_viral(row):
    return (row["score"] >= VIRAL_SCORE_THRESHOLD) or (row["num_comments"] >= VIRAL_COMMENT_THRESHOLD)
sent_analyzer = SentimentIntensityAnalyzer()
emotion_model = pipeline("text-classification", model="j-hartmann/emotion-english-distilroberta-base", top_k=None)
# Remove missing or empty posts
df = df[df["post_text"].notna() & (df["post_text"].str.strip() != "")]

# Add this line after defining is_viral(row)
df["label"] = df.apply(lambda row: "viral" if is_viral(row) else "nonviral", axis=1)


# Combine title and post text if you want to include both
df["full_text"] = df["title"].fillna('') + ". " + df["post_text"].fillna('')

print(df["full_text"])
tqdm.pandas()
kw_model = KeyBERT()
def extract_top_keyword(text):
    if isinstance(text, str) and text.strip():
        try:
            keywords = kw_model.extract_keywords(text, keyphrase_ngram_range=(1, 1), stop_words='english', top_n=1)
            return keywords[0][0] if keywords else ""
        except Exception:
            return ""
    return ""

print("Extracting top keywords (gists)...")
df["keywords"] = df["full_text"].progress_apply(extract_top_keyword)

# Sentiment
print("Analyzing sentiment...")
df["sentiment"] = df["full_text"].apply(lambda x: sent_analyzer.polarity_scores(x)["compound"])

# Emotion
print("Detecting emotions...")

# Returns top emotion + full emotion probability distribution
def get_emotion_with_probs(text):
    try:
        result = emotion_model(text)
        if result and result[0]:
            emotion_scores = [(entry["label"], entry["score"]) for entry in result[0]]
            top_emotion = max(emotion_scores, key=lambda x: x[1])[0]
            return pd.Series([top_emotion, emotion_scores])
    except Exception:
        return pd.Series([None, None])

# Apply function and assign two new columns
df[["emotion", "emotion_probs"]] = df["full_text"].apply(get_emotion_with_probs)



# Topics


#summariser

summarizer = pipeline("summarization", model="facebook/bart-large-cnn")

def summarize_post(text):
    if isinstance(text, str) and text.strip():
        try:
            summary = summarizer(text, max_length=60, min_length=20, do_sample=False)
            return summary[0]['summary_text']
        except Exception:
            return None
    return None

df["summary"] = df["post_text"].apply(summarize_post)

# ------------- TOPICS ---------------------
print("Extracting topics with BERTopic...")
topic_model = BERTopic(min_topic_size=5)
def clean_text(text):
    return " ".join([word for word in text.split() if word.lower() not in ENGLISH_STOP_WORDS])

# Add a new column with cleaned post text
df["clean_text"] = df["full_text"].apply(clean_text)
topics, _ = topic_model.fit_transform(df["clean_text"].tolist())
df["topic"] = topics
topic_info = topic_model.get_topic_info().set_index("Topic")
df["topic_name"] = df["topic"].map(topic_info["Name"])

# ----------- CONTROVERSY ------------------
def controversy(row):
    if row["score"] <= 2:
        return "low"
    ratio = row["num_comments"] / (row["score"] + 1e-5)
    if ratio > 2:
        return "high"
    elif ratio > 1:
        return "medium"
    else:
        return "low"

df["controversy"] = df.apply(controversy, axis=1)

# ----------- ANALYSIS OUTPUT --------------
def summarize(sub_df, label):
    print(f"\n===== 📊 {label.upper()} POSTS =====")
    print("\n🔹 Top Topics:")
    print(sub_df["topic_name"].value_counts().head(5))
    print("\n🔹 Sentiment Stats:")
    print(sub_df["sentiment"].describe())
    print("\n🔹 Emotion Distribution:")
    print(sub_df["emotion"].value_counts(normalize=True))
    print("\n🔹 Controversy:")
    print(sub_df["controversy"].value_counts(normalize=True))

summarize(df[df["label"] == "viral"], "viral")
summarize(df[df["label"] == "nonviral"], "non-viral")
print(f"mean is {VIRAL_SCORE_THRESHOLD}, {VIRAL_COMMENT_THRESHOLD}")
# ------------ SAVE OUTPUT -----------------
df.to_csv(f"analyzed_posts_{subreddit}.csv", index=False)
