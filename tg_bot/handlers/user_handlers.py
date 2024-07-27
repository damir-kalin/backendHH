import os
import json
from datetime import datetime
from copy import deepcopy
import logging

import requests
from aiogram import Router, F
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, CallbackQuery
from aiogram.filters.callback_data import CallbackData
from aiogram_calendar import SimpleCalendar, SimpleCalendarCallback

from keyboards.inline_kb import create_inline_keyboard
from lexicon.lexicon import LEXICON
from database.database import user_dict_template, user_db
from database.methods import get_metrica


router = Router()

logger = logging.getLogger(__name__)

API_HOST = os.getenv('API_HOST')
API_PORT = os.getenv('API_PORT')

@router.message(CommandStart())
async def process_start_command(message: Message):
    calendar = SimpleCalendar()
    calendar.set_dates_range(datetime(2024,6,1), datetime.now())

    user_db[message.from_user.id] = deepcopy(user_dict_template)

    await message.answer(
        text=LEXICON[message.text],
        reply_markup= await calendar.start_calendar(year=2024, month=6),

    )

@router.callback_query(F.data == 'yes')
async def process_start_dashbord(callback_query: CallbackQuery):
    url_req = f"http://{API_HOST}:{API_PORT}/metrics"
    logger.info(str([user_db[callback_query.from_user.id]['city'],
                user_db[callback_query.from_user.id]['profession'],
                user_db[callback_query.from_user.id]['start_date'].strftime('%Y-%m-%d'),
                user_db[callback_query.from_user.id]['end_date'].strftime('%Y-%m-%d')]))
    parameters = {'city':'Санкт-Петербург', 'profession':'Data engineer', 'date_from':'2024-05-14', 'date_to':'2024-07-26'}
    req_metric = requests.get(url=url_req, params=parameters)
    value = json.loads(req_metric.content.decode(encoding='utf-8'))
    await callback_query.message.edit_text(text=str(value))

@router.callback_query(F.data == 'no')
async def process_start_dashbord(callback_query: CallbackQuery):
    await callback_query.message.edit_text(text='Не лови!')


@router.callback_query(F.data.in_(['Data engineer', 'Data analyst']))
async def process_add_profession(callback_query: CallbackQuery):
    user_db[callback_query.from_user.id]['profession'] = callback_query.data
    await callback_query.message.edit_text(text=LEXICON['correct_profession'],
                                           reply_markup=create_inline_keyboard(
                                               'moscow',
                                               'saint_petersburg'
                                           ))

@router.callback_query(F.data.in_(['moscow', 'saint_petersburg']))
async def process_add_city(callback_query: CallbackQuery):
    user_db[callback_query.from_user.id]['city'] = LEXICON[callback_query.data]
    await callback_query.message.edit_text(text=LEXICON['correct_city'],
                                           reply_markup=create_inline_keyboard('yes', 'no'))



@router.callback_query(SimpleCalendarCallback.filter())
async def process_simple_calendar(callback_query: CallbackQuery, callback_data: CallbackData):
    calendar = SimpleCalendar()
    calendar.set_dates_range(datetime(2024, 6, 1), datetime.now())
    selected, date = await calendar.process_selection(callback_query, callback_data)
    if selected:
        if user_db[callback_query.from_user.id]['start_date'] is None and type(date)==datetime:
            user_db[callback_query.from_user.id]['start_date'] = date
            await callback_query.message.edit_text(text=LEXICON['correct_start_date'],
                                                   reply_markup= await calendar.start_calendar(
                                                       year=datetime.now().year,
                                                       month=datetime.now().month))
        elif user_db[callback_query.from_user.id]['end_date'] is None and date > user_db[callback_query.from_user.id]['start_date'] and type(date)==datetime:
            user_db[callback_query.from_user.id]['end_date'] = date
            await callback_query.message.edit_text(text=LEXICON['correct_end_date'],
                                                   reply_markup= create_inline_keyboard(
                                                                    'Data engineer',
                                                                    'Data analyst'
                                                                ))
        else:
            await callback_query.message.edit_text(
            text=LEXICON['incorrect_date']
            )
        print(user_db)
