from aiogram import Bot
from aiogram.types import ReplyKeyboardRemove, ContentType
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher import Dispatcher
from aiogram.utils import executor
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from keyboards import init_keyboard, get_keyboard_for_session
from time import time_ns
from db import create_session, get_session, update_session
from funcs import winner, turn, vosk_recognition
import os
from pydub import AudioSegment

token = os.getenv('TOKEN')
bot = Bot(token)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

moves = {'circle': 1, 'cross': 2}


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
        if await winner(state, memory['match_id'], bot, message['from']['id'], init_keyboard):
            return True
        id = memory['match_id']
        player = memory.state.split('_')[-1]
        if message['text']:
            if message['text'] == 'Обновить поле':
                await bot.send_message(message['from']['id'], 'Обновлено', reply_markup=get_keyboard_for_session(
                    memory['match_id']))
                return True
            if message['text'][-2].isdigit():
                cell = int(message['text'][-2]) - 1
            else:
                await bot.send_message(message['from']['id'], 'Неверный формат ввода',
                                       reply_markup=get_keyboard_for_session(memory['match_id']))
                return False

        elif message['voice']:
            await bot.download_file_by_id(message['voice']['file_id'], os.path.join('voices', str(id) + '_' + player + '.ogg'))
            audio = AudioSegment.from_ogg(os.path.join(
                'voices', str(id) + '_' + player + '.ogg'))
            audio.set_sample_width(2).export(os.path.join(
                'voices', str(id) + '_' + player + '.wav'), format='wav')
            text = vosk_recognition(os.path.join(
                'voices', str(id) + '_' + player + '.wav'))
            match text:
                case 'один':
                    cell = 0
                case 'два':
                    cell = 1
                case 'три':
                    cell = 2
                case 'четыре':
                    cell = 3
                case 'пять':
                    cell = 4
                case 'шесть':
                    cell = 5
                case 'семь':
                    cell = 6
                case 'восемь':
                    cell = 7
                case 'девять':
                    cell = 8
                case 'обновить поле':
                    await bot.send_message(message['from']['id'], 'Обновлено', reply_markup=get_keyboard_for_session(
                        memory['match_id']))
                    return True
                case _:
                    await message.reply(f'Неизвестная команда:\n{text}')
                    return False
            await message.reply(text.capitalize())

        if turn(id) == player:
            match = get_session(id)
            match match[cell]:
                case 0:
                    match[cell] = moves[player]
                    update_session(id, match)
                    if await winner(state, id, bot, message['from']['id'], init_keyboard):
                        return None
                    await bot.send_message(message['from']['id'], 'Ход сделан, ждите оппонента.',
                                           reply_markup=get_keyboard_for_session(id))
                case _:
                    await bot.send_message(message['from']['id'], 'Эта клетка уже заполнена, выберите другую.',
                                           reply_markup=get_keyboard_for_session(id))

        else:
            await bot.send_message(message['from']['id'], 'Ждите своего хода.',
                                   reply_markup=get_keyboard_for_session(id))


async def register_handlers(dp):
    dp.register_message_handler(init, commands=['start'], state='*')
    dp.register_message_handler(create, Text(
        equals='Start session'), state=None)
    dp.register_message_handler(wait_for_id, Text(
        equals='Join session'), state=None)
    dp.register_message_handler(join, state=MatchState.wait_for_id)
    dp.register_message_handler(
        match, state=MatchState.match_circle, content_types=[ContentType.TEXT, ContentType.VOICE])
    dp.register_message_handler(
        match, state=MatchState.match_cross, content_types=[ContentType.TEXT, ContentType.VOICE])

executor.start_polling(dp, skip_updates=True,
                       on_startup=register_handlers)
