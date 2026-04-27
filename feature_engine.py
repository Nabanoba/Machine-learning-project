

import re

# =========================
# CLEAN TEXT
# =========================
def clean_text(text):
    text = str(text).lower().strip()
    text = re.sub(r"[^a-zA-Z0-9\s/=.]", "", text)  # keep math symbols
    return text


# =========================
# FEATURE EXTRACTION
# =========================
def extract_features(text):

    text = clean_text(text)

    # =========================
    # BASIC STRUCTURE
    # =========================
    sentences = text.split(".") if text else []
    words = text.split() if text else []

    words = [w for w in words if w.strip() != ""]

    num_sentences = max(len(sentences), 1)
    num_words = max(len(words), 1)

    # =========================
    # FEATURES
    # =========================

    avg_sentence_length = num_words / num_sentences

    lexical_diversity = len(set(words)) / num_words

    # =========================
    # READABILITY (SAFE)
    # =========================
    try:
        if len(text) < 20:
            readability = 0  # too short for meaningful score
        else:
            readability = round(206.835 - (1.015 * avg_sentence_length), 2)
    except:
        readability = 0

    # =========================
    # RETURN
    # =========================
    return {
        "avg_sentence_length": round(avg_sentence_length, 2),
        "lexical_diversity": round(lexical_diversity, 2),
        "readability": round(readability, 2)
    }