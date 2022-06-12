import logging
import typing

from aiogram import Bot, Dispatcher, executor
from aiogram.types import Message, \
    ReplyKeyboardMarkup, ReplyKeyboardRemove, KeyboardButton, \
    InlineKeyboardMarkup, InlineKeyboardButton, \
    CallbackQuery
from aiogram.utils import callback_data, exceptions
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.types.message import ContentType
from enum import Enum

# Import modules of this project
from config import API_TOKEN, PAYMENT_DETAILS
from business_logic import PaperworkBot
from texts_for_replay import start_cmnd_text, help_text, \
    bank_card_terms_text, driver_license_terms_text, reply_on_random_message, \
    get_text_for_payment, got_payment_screenshot_text, \
    bank_card_preparation_text, get_text_for_form_field

# Configure logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger('paperwork_bot')

# Initialize bot and dispatcher
bot = Bot(token=API_TOKEN, parse_mode="HTML")
dp = Dispatcher(bot, storage=MemoryStorage())

# Sructure of callback buttons
button_cb = callback_data.CallbackData(
    'btn', 'question', 'answer', 'data')

# Initialize business logic
paperwork_bot = PaperworkBot()


#  ------------------------------------------------------------ ВСПОМОГАТЕЛЬНОЕ
def get_empty_keyboard() -> ReplyKeyboardMarkup:
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    return keyboard


def make_inline_keyboard(
        question: str,
        answers: list,
        data=0) -> InlineKeyboardMarkup:
    """Возвращает клавиатуру для сообщений

    Args:
        question (str): Под каким сообщение кнопка
        answers (list): список кнопок
        data (int, optional): Дополнительные данные. Defaults to 0.

    Returns:
        InlineKeyboardMarkup
    """
    if not answers:
        return None

    keyboard = InlineKeyboardMarkup()
    row = []
    for answer in answers:  # make a botton for every answer
        cb_data = button_cb.new(
            question=question,
            answer=answer,
            data=data)
        row.append(InlineKeyboardButton(
            answer, callback_data=cb_data)
        )
    if len(row) <= 2:
        keyboard.row(*row)
    else:
        for button in row:
            keyboard.row(button)

    return keyboard


def is_message_private(message: Message) -> bool:
    """Сообщение из личного чата с ботом?"""
    if message.chat.type == 'private':
        return True
    else:
        return False


#  -------------------------------------------------------------- ВХОД ТГ ЮЗЕРА
class Services(Enum):
    bank_card = 'Оформление карты Permata'
    driver_license = 'Оформление водительских прав'


def get_keyboard_services() -> ReplyKeyboardMarkup:
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    for button in Services:
        keyboard.add(KeyboardButton(button.value))
    return keyboard


@dp.message_handler(
    lambda message: is_message_private(message),
    commands=['start'], state="*")
async def start_command(message: Message, state: FSMContext):
    log.info('start command from: %r', message.from_user.id)

    paperwork_bot.add_tg_user(
        tg_id=message.from_user.id,
        tg_username=message.from_user.username
    )
    await message.answer(
        text=start_cmnd_text,
        reply_markup=get_keyboard_services())


@dp.message_handler(
    lambda message: is_message_private(message),
    commands=['help'], state="*")
async def send_help(message: Message, state: FSMContext):
    log.info('help command from: %r', message.from_user.id)
    await message.answer(
        text=help_text,
        reply_markup=get_keyboard_services()
    )


#  ----------------------------------------------------------- ОФОРМЛЕНИЕ УСЛУГ
class CustomerState(StatesGroup):
    waiting_for_payment_photo = State()


start_service_button = 'Начать оформление'

form_for_bank_card = 'Анкета для Банка'
pasport_for_bank_card = 'Фото паспорта'


async def send_reply_for_bank_card_button(
        message: Message, state: FSMContext):
    log.info('send_reply_for_bank_card_button')
    keyboard = make_inline_keyboard(
        question=Services.bank_card.name,
        answers=[start_service_button, ]
    )
    await message.answer(
        text=bank_card_terms_text,
        reply_markup=keyboard
    )


async def send_reply_for_driver_license_button(
        message: Message, state: FSMContext):
    log.info('send_reply_for_driver_license_button')
    await message.answer(
        text=driver_license_terms_text,
        reply_markup=get_keyboard_services()
    )


def is_message_service_button(message: Message) -> bool:
    """Сообщение это кнопка из клавиатуры сервисов"""
    if message.text in [button.value for button in Services]:
        return True
    else:
        return False


@dp.message_handler(
    lambda message: is_message_private(message),
    lambda message: is_message_service_button(message),
    content_types=[ContentType.TEXT],
    state='*')
async def new_text_message(message: Message, state: FSMContext):
    log.info('new_text_message from: %r', message.from_user.id)

    if message.text in [button.value for button in Services]:
        if message.text == Services.bank_card.value:
            await send_reply_for_bank_card_button(message, state)
        elif message.text == Services.driver_license.value:
            await send_reply_for_driver_license_button(message, state)


@dp.callback_query_handler(
    button_cb.filter(
        question=[button.name for button in Services],
        answer=[start_service_button, ]
    ),
    state='*')
async def start_service_callback_button(
        query: CallbackQuery,
        callback_data: typing.Dict[str, str],
        state: FSMContext):
    log.info('Got this callback data: %r', callback_data)

    await query.message.edit_reply_markup()  # delete inline button

    if callback_data['question'] == Services.bank_card.name:
        await send_form_for_pay(
            tg_id=query.from_user.id,
            service_name=Services.bank_card.value,
            payment_amount=140,
            state=state
        )
    elif callback_data['question'] == Services.driver_license.name:
        await send_form_for_pay(
            tg_id=query.from_user.id,
            service_name=Services.driver_license.value,
            payment_amount=140,
            state=state
        )

    await query.answer()  # stop circle on button


async def send_form_for_pay(
        tg_id: int,
        service_name: str,
        payment_amount: int,
        state: FSMContext):
    log.info('send_form_for_pay')
    await bot.send_message(
        chat_id=tg_id,
        text=get_text_for_payment(
            service_name=service_name,
            payment_amount=payment_amount,
            payment_details=PAYMENT_DETAILS
        )
    )
    await CustomerState.waiting_for_payment_photo.set()
    await state.update_data(service_name=service_name)


@dp.message_handler(
    content_types=ContentType.PHOTO,
    state=CustomerState.waiting_for_payment_photo)
async def new_payment_photo(message: Message, state: FSMContext):
    log.info(f'new_payment_photo from: { message.from_user.id }')
    await message.reply(got_payment_screenshot_text)

    state_data = await state.get_data()
    service_name = state_data['service_name']
    if service_name == Services.bank_card.value:
        await send_actions_for_bank_card(message, state)
    else:
        log.error(f'lost state_data from: { message.from_user.id }')
        await message.answer(reply_on_random_message)


#  ------------------------------------------------------------ ФОРМА ДЛЯ БАНКА
class BankFormState(StatesGroup):
    waiting_full_name = State()
    waiting_mother_name = State()
    waiting_marital_status = State()


class BankPasportState(StatesGroup):
    waiting_pasport = State()


state_and_fields = {
    BankFormState.waiting_full_name.state: BankCardForm.full_name,
    BankFormState.waiting_mother_name.state: BankCardForm.mother_name,
    BankFormState.waiting_marital_status.state: BankCardForm.marital_status
}


#  ------------------------------------------------ ОФОРМЛЕНИЕ БАНКОВСКОЙ КАРТЫ
async def send_actions_for_bank_card(
        message: Message, state: FSMContext):
    """Отправляет кнопки - какие действия нужно совершить для оформления"""
    log.info('send_reply_for_bank_card_button')
    keyboard = make_inline_keyboard(
        question=Services.bank_card.name,
        answers=[form_for_bank_card, pasport_for_bank_card]
    )
    await message.answer(
        text=bank_card_preparation_text,
        reply_markup=keyboard
    )


@dp.callback_query_handler(
    button_cb.filter(
        question=Services.bank_card.name,
        answer=[form_for_bank_card, pasport_for_bank_card]
    ),
    state='*')
async def callback_button_bank_card(
        query: CallbackQuery,
        callback_data: typing.Dict[str, str],
        state: FSMContext):
    log.info('Got this callback data: %r', callback_data)

    if callback_data['answer'] == form_for_bank_card:
        await start_form_filling(query.message, state)
    elif callback_data['answer'] == pasport_for_bank_card:
        await start_pasport_getting(query.message, state)

    await query.answer()  # stop circle on button


async def start_form_filling(message: Message, state: FSMContext):
    log.info('start_form_filling from: %r', message.from_user.id)
    await BankFormState.waiting_full_name.set()
    await message.answer(
        text='Начинаем заполнять анкету'
    )
    field = state_and_fields[await state.get_state()].value
    await message.answer(
        text=get_text_for_form_field(
            field_name=field.name_for_human,
            field_type_discription=field.field_type.value
        )
    )


@dp.message_handler(
    lambda message: is_message_private(message),
    content_types=[ContentType.TEXT],
    state=[st for st in BankFormState.all_states])
async def form_filling(message: Message, state: FSMContext):
    log.info('form_filling from: %r', message.from_user.id)

    field = state_and_fields[await state.get_state()].value
    print(f'{field.name_in_db}: {message.text}')

    if await state.get_state() == BankFormState.waiting_marital_status.state:
        await message.answer(
            text='Анкета заполнена'
        )
        await state.finish()
        return

    await BankFormState.next()

    field = state_and_fields[await state.get_state()].value
    await message.answer(
        text=get_text_for_form_field(
            field_name=field.name_for_human,
            field_type_discription=field.field_type.value
        )
    )


async def start_pasport_getting(message: Message, state: FSMContext):
    log.info('start_pasport_getting from: %r', message.from_user.id)
    await BankFormState.waiting_pasport.set()
    await message.answer(
        text='Пришлите фото паспорта. (любое фото)'
    )


@dp.message_handler(
    lambda message: is_message_private(message),
    content_types=[ContentType.PHOTO],
    state=BankFormState.waiting_pasport)
async def pasport_getting(message: Message, state: FSMContext):
    log.info('form_filling from: %r', message.from_user.id)
    await message.answer(
        text='Паспорт получен'
    )


#  ---------------------------------------------------------- ОБРАБОТКА ДРУГОГО
@dp.message_handler(
    lambda message: is_message_private(message),
    content_types=[ContentType.ANY],
    state='*')
async def random_message(message: Message, state: FSMContext):
    log.info('random_message from: %r', message.from_user.id)
    await message.reply(
            text=reply_on_random_message,
            reply_markup=get_keyboard_services()
        )


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=False)
