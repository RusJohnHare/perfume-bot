from aiogram.fsm.state import State, StatesGroup


class NoteSelection(StatesGroup):
    choosing_categories = State()
    choosing_notes = State()
    viewing_results = State()


class FavoritesMenu(StatesGroup):
    viewing_list = State()
