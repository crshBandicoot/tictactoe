from db import get_session, get_session_complete, session_complete, delete_session
from vosk import Model, KaldiRecognizer
import wave
import os

model = Model('vosk_model')


def turn(match_id):
    circles = 0
    crosses = 0
    for cell in get_session(match_id):
        match cell:
            case 1:
                circles += 1
            case 2:
                crosses += 1
            case _:
                pass
    if circles == crosses:
        return 'circle'
    else:
        return 'cross'


def row(match_id):
    match = get_session(match_id)
    if match[0] == match[1] == match[2] == 1 or match[3] == match[4] == match[5] == 1 or match[6] == match[7] == match[8] == 1 or match[0] == match[3] == match[6] == 1 or match[1] == match[4] == match[7] == 1 or match[2] == match[5] == match[8] == 1 or match[0] == match[4] == match[8] == 1 or match[2] == match[4] == match[6] == 1:
        return 'circles'
    if match[0] == match[1] == match[2] == 2 or match[3] == match[4] == match[5] == 2 or match[6] == match[7] == match[8] == 2 or match[0] == match[3] == match[6] == 2 or match[1] == match[4] == match[7] == 2 or match[2] == match[5] == match[8] == 2 or match[0] == match[4] == match[8] == 2 or match[2] == match[4] == match[6] == 2:
        return 'crosses'


async def winner(state, match_id, bot, user, reply_markup):
    if row(match_id):
        winner = ''
        if row(match_id) == 'circles':
            winner = 'нолики'
        else:
            winner = 'крестики'
        await bot.send_message(user, f'Победили {winner}', reply_markup=reply_markup)
        await state.finish()
        if get_session_complete(match_id):
            delete_session(match_id)
            for file in os.listdir('voices'):
                if file.split('_')[0] == str(match_id):
                    os.remove(os.path.join('voices', file))
        else:
            session_complete(match_id)
        return True


def vosk_recognition(path):
    with wave.open(path, 'rb') as audio:
        recognizer = KaldiRecognizer(model, audio.getframerate())
        while True:
            data = audio.readframes(4000)
            if len(data) == 0:
                break
            recognizer.AcceptWaveform(data)

        return recognizer.FinalResult().split('"')[-2]
