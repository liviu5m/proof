from typing import Any

import numpy as np

from .embeddings import get_embedding_provider


async def score_semantic(
    expected: str,
    response: str,
) -> dict[str, Any]:
    """Score response against expected using semantic similarity.

    Returns dict with score (1-5), reason, and raw similarity value.
    """
    if not expected or not response:
        return {
            "score": 1.0,
            "reason": "Missing expected or response text",
            "similarity": 0.0,
        }

    provider = get_embedding_provider()
    embeddings = await provider.aembed([expected, response])

    a = np.array(embeddings[0])
    b = np.array(embeddings[1])
    similarity = float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

    # Map similarity to 1-5 scale
    if similarity >= 0.90:
        score = 5.0
    elif similarity >= 0.75:
        score = 4.0
    elif similarity >= 0.60:
        score = 3.0
    elif similarity >= 0.45:
        score = 2.0
    else:
        score = 1.0

    return {
        "score": score,
        "reason": f"Semantic similarity: {similarity:.2f}",
        "similarity": similarity,
    }


async def score_semantic_batch(
    pairs: list[tuple[str, str]],
) -> list[dict[str, Any]]:
    """Score multiple (expected, response) pairs efficiently in one batch."""
    if not pairs:
        return []

    provider = get_embedding_provider()

    # Flatten all texts for single batch embedding call
    all_texts = []
    for expected, response in pairs:
        all_texts.append(expected)
        all_texts.append(response)

    embeddings = await provider.aembed(all_texts)

    results = []
    for i, _pair in enumerate(pairs):
        a = np.array(embeddings[i * 2])
        b = np.array(embeddings[i * 2 + 1])
        similarity = float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

        if similarity >= 0.90:
            score = 5.0
        elif similarity >= 0.75:
            score = 4.0
        elif similarity >= 0.60:
            score = 3.0
        elif similarity >= 0.45:
            score = 2.0
        else:
            score = 1.0

        results.append(
            {
                "score": score,
                "reason": f"Semantic similarity: {similarity:.2f}",
                "similarity": similarity,
            }
        )

    return results
