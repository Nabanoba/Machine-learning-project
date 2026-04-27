from sklearn.feature_extraction.text import CountVectorizer
from sklearn.decomposition import LatentDirichletAllocation
import numpy as np

def run_lda(texts):

    vectorizer = CountVectorizer(stop_words="english")
    X = vectorizer.fit_transform(texts)

    lda = LatentDirichletAllocation(n_components=3, random_state=42)
    lda_output = lda.fit_transform(X)

    return np.argmax(lda_output, axis=1)