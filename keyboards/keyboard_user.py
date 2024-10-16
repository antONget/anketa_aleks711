from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from database.models import User
import logging


def keyboard_action() -> InlineKeyboardMarkup:
    logging.info("keyboard_action")
    button_1 = InlineKeyboardButton(text='Продать', callback_data=f'action_sell')
    button_2 = InlineKeyboardButton(text='Купить', callback_data=f'action_bay')
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[button_1], [button_2]],)
    return keyboard


def keyboards_get_contact() -> ReplyKeyboardMarkup:
    logging.info("keyboards_get_contact")
    button_1 = KeyboardButton(text='Отправить свой контакт ☎️',
                              request_contact=True)
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[button_1]],
        resize_keyboard=True
    )
    return keyboard


def keyboard_send() -> InlineKeyboardMarkup:
    logging.info("keyboard_send")
    button_1 = InlineKeyboardButton(text='Отправить', callback_data=f'send_content')
    button_2 = InlineKeyboardButton(text='Добавить', callback_data=f'add_content')
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[button_2], [button_1]],)
    return keyboard