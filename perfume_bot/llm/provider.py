from dataclasses import dataclass


@dataclass
class PerfumeInfo:
    name: str
    brand: str
    description: str | None
    notes: list[str]
    price_rub: str | None
    shop_url: str | None


class LLMProvider:
    """
    Абстракция над LLM для формирования текстов карточек парфюмов.
    MVP использует шаблоны; для подключения Claude API заменить _format_with_llm.
    """

    def format_recommendation(self, perfume: PerfumeInfo) -> str:
        notes_str = ", ".join(perfume.notes[:5]) if perfume.notes else "—"
        price_str = f"{perfume.price_rub} ₽" if perfume.price_rub else "цена уточняется"
        description = perfume.description or "Классический парфюм."

        return (
            f"🌸 <b>{perfume.name}</b> — {perfume.brand}\n"
            f"{description}\n\n"
            f"🎵 Ноты: {notes_str}\n"
            f"💰 {price_str}"
        )
