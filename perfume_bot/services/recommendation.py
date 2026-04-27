from dataclasses import dataclass

import numpy as np
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from perfume_bot.models.perfume import Perfume, PerfumeNote, FragranceNote


@dataclass
class RecommendationResult:
    perfume: Perfume
    score: float
    is_exact: bool


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))


def build_note_vector(all_note_ids: list[int], selected_ids: set[int]) -> np.ndarray:
    return np.array([1.0 if nid in selected_ids else 0.0 for nid in all_note_ids])


class RecommendationService:

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_recommendations(
        self,
        selected_note_ids: list[int],
        top_n: int = 5,
    ) -> list[RecommendationResult]:
        # 1. Загрузить все ноты (для построения пространства векторов)
        all_notes_result = await self._session.execute(
            select(FragranceNote.id).order_by(FragranceNote.id)
        )
        all_note_ids: list[int] = list(all_notes_result.scalars().all())
        if not all_note_ids:
            return []

        user_vec = build_note_vector(all_note_ids, set(selected_note_ids))

        # 2. Загрузить все парфюмы с нотами
        perfumes_result = await self._session.execute(
            select(Perfume).options(selectinload(Perfume.perfume_notes))
        )
        perfumes = list(perfumes_result.scalars().all())
        if not perfumes:
            return []

        # 3. Вычислить схожесть
        scored: list[RecommendationResult] = []
        for perfume in perfumes:
            note_ids = {pn.note_id for pn in perfume.perfume_notes}
            perfume_vec = build_note_vector(all_note_ids, note_ids)
            score = cosine_similarity(user_vec, perfume_vec)
            is_exact = note_ids.issuperset(set(selected_note_ids))
            scored.append(RecommendationResult(perfume=perfume, score=score, is_exact=is_exact))

        scored.sort(key=lambda r: (r.is_exact, r.score), reverse=True)
        return scored[:max(top_n, len(scored))] if len(scored) < top_n else scored[:top_n]
