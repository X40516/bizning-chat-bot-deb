"""
FSM (Finite State Machine) holatlari.
"""
from aiogram.fsm.state import State, StatesGroup


class ConnectStates(StatesGroup):
    waiting_username = State()


class ChatStates(StatesGroup):
    active = State()


class AdminContentStates(StatesGroup):
    waiting_file = State()
    waiting_title = State()
    waiting_description = State()
    waiting_artist = State()
    waiting_genre = State()
    waiting_edit_value = State()
