from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from db import get_session
create = KeyboardButton('Start session')
join = KeyboardButton('Join session')

init_keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
init_keyboard.add(create).add(join)


def get_keyboard_for_session(id):
    session_keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    session = get_session(id)
    for i in range(9):
        match session[i]:
            case 1:
                icon = '⚪️'
            case 2:
                icon = '❌'
            case _:
                icon = '⬛️'
        if i % 3 == 0:
            session_keyboard.row(icon + f'   ({i+1})')
        else:
            session_keyboard.insert(icon + f'    ({i+1})')
    session_keyboard.row('Обновить поле')
    return session_keyboard
