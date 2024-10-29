from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from aiogram.filters import CommandStart, StateFilter, or_f
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from config_data.config import Config, load_config
import database.requests as rq
import keyboards.keyboard_user as kb
from filter.filter import validate_russian_phone_number

import logging
import asyncio
import random

router = Router()
config: Config = load_config()


class User(StatesGroup):
    name = State()
    phone = State()
    request_user = State()
    content_state  = State()


@router.message(CommandStart())
async def process_start_command(message: Message, state: FSMContext, bot: Bot) -> None:
    """
    Запуск бота - нажата кнопка "Начать" или введена команда "/start"
    :param message:
    :param state:
    :param bot:
    :return:
    """
    logging.info(f"process_start_command {message.chat.id}")
    await state.set_state(state=None)
    if message.from_user.username == None:
        username = 'None'
    else:
        username = message.from_user.username
    await rq.add_user(tg_id=message.chat.id,
                      data={"tg_id": message.chat.id, "username": username})
    await message.answer(text=f'🤖 Добрый день, мы рады вас видеть.\n'
                              f'Хотите продать или купить автомобиль?',
                         reply_markup=kb.keyboard_action())


@router.callback_query(F.data.startswith('action'))
async def process_registration(callback: CallbackQuery, state: FSMContext):
    """
    Выбор действия пользователем
    :param callback:
    :param state:
    :param bot:
    :return:
    """
    logging.info(f"process_registration {callback.message.chat.id}")
    answer = callback.data.split('_')[1]
    await state.update_data(action=answer)
    if answer == 'sell':
        await callback.message.edit_text(text="🤖 Хорошо, сейчас оценим, а пока давайте познакомимся.\n"
                                              "Как вас зовут?",
                                         reply_markup=None)
        await state.set_state(User.name)
    elif answer == "bay":
        await callback.message.edit_text(text="🤖 Хорошо. Давайте познакомимся.\n"
                                              "Как вас зовут?",
                                         reply_markup=None)
        await state.set_state(User.name)
    await callback.answer()


@router.message(F.text, StateFilter(User.name))
async def get_name(message: Message, state: FSMContext, bot: Bot) -> None:
    """
    Получаем от пользователя имя
    :param message:
    :param state:
    :param bot:
    :return:
    """
    logging.info(f'get_name {message.chat.id}')
    await state.update_data(name=message.text)
    await message.answer(text='Укажите ваш номер телефона или нажмите внизу 👇\n'
                              '"Отправить свой контакт ☎️"',
                         reply_markup=kb.keyboards_get_contact())
    await state.set_state(User.phone)


@router.message(StateFilter(User.phone))
async def get_phone_user(message: Message, state: FSMContext) -> None:
    """
    Получаем номер телефона проверяем его на валидность и заносим его в БД
    :param message:
    :param state:
    :return:
    """
    logging.info(f'get_phone_user: {message.chat.id}')
    # если номер телефона отправлен через кнопку "Поделится"
    if message.contact:
        phone = str(message.contact.phone_number)
    # если введен в поле ввода
    else:
        phone = message.text
        # проверка валидности отправленного номера телефона, если не валиден просим ввести его повторно
        if not validate_russian_phone_number(phone):
            await message.answer(text="Неверный формат номера, повторите ввод.")
            return
    # обновляем поле номера телефона
    await state.update_data(phone=phone)
    data = await state.get_data()
    action = data['action']
    if action == 'bay':
        await message.answer(text=f'🤖 Очень приятно, {data["name"]}. '
                                  f'Опишите параметры интересующего автомобиля - марка, модель, бюджет.',
                             reply_markup=ReplyKeyboardRemove())
    elif action == 'sell':
        await message.answer(text=f'🤖 Очень приятно, {data["name"]}. '
                                  f'Какой у вас автомобиль? Марка, год, пробег, пожелание по цене',
                             reply_markup=ReplyKeyboardRemove())
    await state.set_state(User.request_user)


@router.message(F.text, StateFilter(User.request_user))
async def get_request_user(message: Message, state: FSMContext, bot: Bot) -> None:
    """
    Получаем запрос пользователя
    :param message:
    :param state:
    :param bot:
    :return:
    """
    logging.info(f'get_request_user {message.chat.id}')
    await message.answer(text='📎 Прикрепите фото (можно несколько), видео или документ.')
    await state.set_state(User.content_state)
    await state.update_data(content=[])
    await state.update_data(count=[])
    await state.update_data(request_user=message.text)


@router.message(StateFilter(User.content_state), or_f(F.document, F.photo, F.video))
async def request_content_photo_text(message: Message, state: FSMContext):
    """
    Получаем от пользователя контент для публикации
    :param message:
    :param state:
    :return:
    """
    logging.info(f'request_content_photo_text {message.chat.id}')
    await asyncio.sleep(random.random())
    data = await state.get_data()
    list_content = data.get('content', [])
    count = data.get('count', [])
    if message.text:
        await message.answer(text=f'📎 Прикрепите фото (можно несколько), видео или документ.')
        return
    elif message.photo:
        content = message.photo[-1].file_id
        if message.caption:
            caption = message.caption
        else:
            caption = 'None'
        await state.update_data(caption=caption)

    elif message.video:
        content = message.video.file_id
        if message.caption:
            caption = message.caption
        else:
            caption = 'None'
        await state.update_data(caption=caption)

    elif message.document:
        content = message.document.file_id
        if message.caption:
            caption = message.caption
        else:
            caption = 'None'
        await state.update_data(caption=caption)

    list_content.append(content)
    count.append(content)
    await state.update_data(content=list_content)
    await state.update_data(count=count)
    await state.set_state(state=None)
    if len(count) == 1:
        await message.answer(text='Добавить еще материал или отправить?',
                             reply_markup=kb.keyboard_send())


@router.callback_query(F.data.endswith('content'))
async def send_add_content(callback: CallbackQuery, state: FSMContext, bot: Bot):
    logging.info(f'send_add_content {callback.message.chat.id}')
    answer = callback.data.split('_')[0]
    if answer == 'add':
        await state.set_state(User.content_state)
        await state.update_data(count=[])
        await callback.message.edit_text(text='📎 Прикрепите фото (можно несколько), видео или документ.')
    else:
        await callback.message.edit_text(text='Материалы от вас переданы\n\n'
                                              'Спасибо! С вами свяжутся',
                                         reply_markup=None)

        data = await state.get_data()
        request_user = data['request_user']
        content = data['content']
        action = data['action']
        first_text = ''
        if action == 'sell':
            await callback.message.edit_text(text=f'🤖 Благодарю, специалист свяжется с вами в ближайшее время и озвучит сумму,'
                                                  f' за которую мы готовы купить ваш автомобиль, а пока вступайте в наш канал,'
                                                  f' чтобы познакомиться поближе\n\n'
                                                  f'https://t.me/kirianov_al',
                                             reply_markup=None)
            first_text = f'Пользователь @{callback.from_user.username} оставил запрос на продажу автомобиля'
        elif action == 'bay':
            await callback.message.edit_text(text=f'🤖 Благодарю за обращение, мы свяжемся с вами для консультации в ближайшее время,'
                                                  f' а пока вступайте в наш канал, чтобы познакомиться поближе\n\n'
                                                  f'https://t.me/kirianov_al',
                                             reply_markup=None)
            first_text = f'Пользователь @{callback.from_user.username} оставил запрос на покупку автомобиля'
        for admin in config.tg_bot.admin_ids.split(','):
            try:
                for item in content:
                    try:
                        await bot.send_photo(chat_id=admin,
                                             photo=item)
                    except:
                        try:
                            await bot.send_video(chat_id=admin,
                                                 video=item)
                        except:
                            await bot.send_document(chat_id=admin,
                                                    document=item)
            except:
                await bot.send_message(chat_id=admin,
                                       text='Не удалось отправить контент')
            try:
                await bot.send_message(chat_id=admin,
                                       text=f'<b>{first_text}:</b>\n\n'
                                            f'<b>Имя:</b> {data["name"]}\n'
                                            f'<b>Телефон:</b> {data["phone"]}\n'
                                            f'<b>Запрос от пользователя:</b> {request_user}\n')

            except:
                pass
        await state.set_state(state=None)
