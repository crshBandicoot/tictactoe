from aiogram import Bot
from aiogram.types import ReplyKeyboardRemove
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher import Dispatcher
from aiogram.utils import executor
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from keyboards import init_keyboard, get_keyboard_for_session
from time import time_ns
from db import Match, create_session, get_session, update_session, delete_session
from funcs import row, turn
import os

token = os.getenv('TOKEN')
bot = Bot(token)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)


class MatchState(StatesGroup):
    wait_for_id = State()
    match_circle = State()
    match_cross = State()


async def init(message, state):
    await state.finish()
    await bot.send_message(message['from']['id'], 'Для игры с оппонентом создайте сессию или присоединитесь к уже существующей', reply_markup=init_keyboard)


async def create(message, state):
    match_id = int(str(message['from']['id'])[:5] + str(time_ns())[-5:])
    async with state.proxy() as memory:
        memory['match_id'] = match_id
    create_session(match_id)
    await bot.send_message(message['from']['id'], f'Сессия создана, отправьте оппоненту id матча: **`{match_id}`**.\n Вы играете за нолики.', parse_mode='Markdown', reply_markup=get_keyboard_for_session(match_id))
    await MatchState.match_circle.set()


async def wait_for_id(message, state):
    await bot.send_message(message['from']['id'], 'Пришлите id матча.', reply_markup=ReplyKeyboardRemove())
    await MatchState.wait_for_id.set()


async def join(message, state):
    match_id = int(message['text'])
    match = get_session(match_id)
    if match:
        async with state.proxy() as memory:
            memory['match_id'] = match_id
        await bot.send_message(message['from']['id'], 'Игра началась, вы играете за крестики.', reply_markup=get_keyboard_for_session(match_id))
        await MatchState.match_cross.set()
    else:
        await bot.send_message(message['from']['id'], 'Такой игры нет.', reply_markup=init_keyboard)
        await state.finish()


async def match(message, state):
    async with state.proxy() as memory:

        if row(memory['match_id']):
            winner = ''
            if row(memory['match_id']) == 'circles':
                winner = 'нолики'
            else:
                winner = 'крестики'
            await bot.send_message(message['from']['id'], f'Победили {winner}', reply_markup=init_keyboard)
            await state.finish()
            return None
        if message['text'] == 'Обновить поле':
            await bot.send_message(message['from']['id'], 'Обновлено', reply_markup=get_keyboard_for_session(
                memory['match_id']))
            return None
        if memory.state == 'MatchState:match_circle':
            if turn(memory['match_id']) == 'circle':
                match = get_session(memory['match_id'])
                cell = int(message['text'][-2]) - 1
                match match[cell]:
                    case 0:
                        match[cell] = 1
                        update_session(memory['match_id'], match)
                        if row(memory['match_id']):
                            winner = ''
                            if row(memory['match_id']) == 'circles':
                                winner = 'нолики'
                            else:
                                winner = 'крестики'
                            await bot.send_message(message['from']['id'], f'Победили {winner}', reply_markup=init_keyboard)
                            await state.finish()
                            return None
                        await bot.send_message(message['from']['id'], 'Ход сделан, ждите оппонента.',
                                               reply_markup=get_keyboard_for_session(memory['match_id']))
                    case _:
                        await bot.send_message(message['from']['id'], 'Эта клетка уже заполнена, выберите другую.',
                                               reply_markup=get_keyboard_for_session(memory['match_id']))

            else:
                await bot.send_message(message['from']['id'], 'Ждите своего хода.',
                                       reply_markup=get_keyboard_for_session(memory['match_id']))
        elif memory.state == 'MatchState:match_cross':
            if turn(memory['match_id']) == 'cross':
                match = get_session(memory['match_id'])
                cell = int(message['text'][-2]) - 1
                match match[cell]:
                    case 0:
                        match[cell] = 2
                        update_session(memory['match_id'], match)
                        if row(memory['match_id']):
                            winner = ''
                            if row(memory['match_id']) == 'circles':
                                winner = 'нолики'
                            else:
                                winner = 'крестики'
                            await bot.send_message(message['from']['id'], f'Победили {winner}', reply_markup=init_keyboard)
                            await state.finish()
                            return None
                        await bot.send_message(message['from']['id'], 'Ход сделан, ждите оппонента.',
                                               reply_markup=get_keyboard_for_session(memory['match_id']))
                    case _:
                        await bot.send_message(message['from']['id'], 'Эта клетка уже заполнена, выберите другую.',
                                               reply_markup=get_keyboard_for_session(memory['match_id']))

            else:
                await bot.send_message(message['from']['id'], 'Ждите своего хода.',
                                       reply_markup=get_keyboard_for_session(memory['match_id']))


async def register_handlers(dp):
    dp.register_message_handler(init, commands=['start'], state='*')
    dp.register_message_handler(create, Text(
        equals='Start session'), state=None)
    dp.register_message_handler(wait_for_id, Text(
        equals='Join session'), state=None)
    dp.register_message_handler(join, state=MatchState.wait_for_id)
    dp.register_message_handler(match, state=MatchState.match_circle)
    dp.register_message_handler(match, state=MatchState.match_cross)


executor.start_polling(dp, skip_updates=True,
                       on_startup=register_handlers)
