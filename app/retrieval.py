from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sqlmodel import Session
from app.models import Incident, Officer
from app.security import authorized_chunks

def hybrid_search(session: Session, question: str, officer: Officer, days: int, limit: int = 6):
    # SQL restricts parish and date before vector ranking.
    chunks = authorized_chunks(session, officer, days)
    if not chunks:
        return []
    texts = [c.text for c in chunks]
    vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
    try:
        matrix = vectorizer.fit_transform(texts + [question])
        scores = cosine_similarity(matrix[-1], matrix[:-1]).flatten()
    except ValueError:
        return []
    ranked = sorted(zip(chunks, scores), key=lambda pair: float(pair[1]), reverse=True)
    results = []
    for chunk, score in ranked[:limit]:
        incident = session.get(Incident, chunk.incident_id)
        if incident and incident.parish == officer.parish and float(score) > 0:
            results.append((incident, chunk.text, float(score)))
    return results
