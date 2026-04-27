from sklearn.cluster import AgglomerativeClustering
import numpy as np


def cluster_students(results_store):
    """
    Clusters students based on their evaluation scores.
    Returns cluster labels aligned with results_store.
    """

    # Extract scores safely
    scores = [r.get("score", 0) for r in results_store]

    # 🔴 FIX 1: need at least 2 data points
    if len(scores) < 2:
        return [0 for _ in scores]

    # Convert to numpy 2D array (IMPORTANT for sklearn)
    X = np.array(scores, dtype=float).reshape(-1, 1)

    # 🔴 FIX 2: avoid n_clusters > number of samples
    n_clusters = min(3, len(scores))

    model = AgglomerativeClustering(
        n_clusters=n_clusters,
        linkage="ward"
    )

    labels = model.fit_predict(X)

    return labels.tolist()