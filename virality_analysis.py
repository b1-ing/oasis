import json
import pandas as pd
import spacy
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from sklearn.feature_extraction.text import CountVectorizer
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import torch

# Load posts
subreddit = "SecurityCamera"
with open(f"processed_{subreddit}_posts.json", "r", encoding="utf-8") as f:
    posts = json.load(f)

# Initialize sentiment analyzer and spaCy NLP
analyzer = SentimentIntensityAnalyzer()
nlp = spacy.load("en_core_web_sm")

# Initialize tag generation model
tag_tokenizer = AutoTokenizer.from_pretrained("fabiochiu/t5-base-tag-generation")
tag_model = AutoModelForSeq2SeqLM.from_pretrained("fabiochiu/t5-base-tag-generation")

# Function to generate tags for text
def generate_tags(text, max_tags=5):
    if not text or len(text.strip()) < 10:
        return []

    input_ids = tag_tokenizer(f"Generate tags for this text: {text}",
                              return_tensors="pt", truncation=True, max_length=512).input_ids

    with torch.no_grad():
        outputs = tag_model.generate(input_ids, max_length=64, num_beams=4,
                                     do_sample=False, num_return_sequences=1)

    tags_text = tag_tokenizer.decode(outputs[0], skip_special_tokens=True)
    tags = [tag.strip() for tag in tags_text.split(",") if tag.strip()]
    print(tags)
    return tags[:max_tags]

# Get post text
def post_text(p):
    return ((p.get('title') or '') + ' ' + (p.get('post_text') or '')).lower()

texts = [post_text(p) for p in posts]
virality_metric = [(p['score'] + 0.5 * p['num_comments']) for p in posts]

# Create DataFrame
df = pd.DataFrame({'text': texts, 'virality': virality_metric})
print(df)
threshold = df['virality'].quantile(0.90)
viral_texts = df[df['virality'] >= threshold]['text']
nonviral_texts = df[df['virality'] < threshold]['text']

# ----------------------------
# STEP 2: Generate tags for viral vs non-viral posts
# ----------------------------
print("Generating tags for viral posts...")
viral_tags = []
for text in viral_texts:
    if text and len(text) > 10:  # Skip very short texts
        tags = generate_tags(text)
        viral_tags.extend(tags)

print("Generating tags for non-viral posts...")
nonviral_tags = []
for text in nonviral_texts:
    if text and len(text) > 10:
        tags = generate_tags(text)
        nonviral_tags.extend(tags)

# Count tag frequencies
from collections import Counter
viral_tag_counts = Counter(viral_tags)
nonviral_tag_counts = Counter(nonviral_tags)

# Compute "viral bias score" for each tag
all_tags = set(list(viral_tag_counts.keys()) + list(nonviral_tag_counts.keys()))
tag_scores = []
for tag in all_tags:
    viral_freq = viral_tag_counts.get(tag, 0)
    nonviral_freq = nonviral_tags.count(tag)  # More accurate count
    bias_score = viral_freq - nonviral_freq
    tag_scores.append((tag, bias_score))

tag_scores.sort(key=lambda x: -x[1])

# Pick top 15 viral tags as trigger keywords
trigger_keywords = [tag for tag, score in tag_scores[:15] if len(tag) > 2 and tag.isalpha()]
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
        "computed_virality_score": round(score, 3),
        "trigger_keywords_found": [kw for kw in trigger_keywords if kw in combined]
    }

# Apply to all posts
print("Computing features for all posts...")
features_df = pd.DataFrame([compute_features(p) for p in posts])

# Rank by predicted virality
top_predicted = features_df.sort_values(by="computed_virality_score", ascending=False)

# Save output
features_df.to_csv(f"analyzed_posts_{subreddit}_2.csv", index=False)

# Preview top 10
print("Top 10 predicted viral posts:")
print(top_predicted[['title', 'computed_virality_score', 'trigger_keywords_found']].head(10))

# Show tag analysis summary
print(f"\nTag Analysis Summary:")
print(f"Total viral posts analyzed: {len(viral_texts)}")
print(f"Total non-viral posts analyzed: {len(nonviral_texts)}")
print(f"Top 10 viral-biased tags: {[tag for tag, score in tag_scores[:10]]}")