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

from datetime import datetime, timedelta, date
from pytz import timezone
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger

# Import modules of this project
from config import ADMINS_TG, API_TOKEN, CLIENT_TIMEZONE_NAME, PAYMENT_DETAILS
from business_logic import Operator, Service, TgUser, get_next_enum, Section
from products import BankCardForm, DriveLicenseService, Product, \
    bank_card_product, driver_license_product, \
    BankCardService
from texts_for_replay import get_cancel_payment_text, \
    get_confirm_payment_text, get_form_text, get_meeting_text, \
    get_text_for_bank_card_operator, get_text_for_payment_control, \
    start_cmnd_text, help_text, \
    help_for_admin_text, \
    reply_on_random_message, waiting_customer_name_text,\
    customer_name_exist_text, \
    get_text_for_payment, got_payment_screenshot_text, got_customer_name_text,\
    get_text_for_form_field, waiting_pasport_text, pasport_getting_text,\
    start_form_filling_text, form_is_end_text, chose_meeting_place, \
    chose_meeting_time

# Configure logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger('paperwork_bot')

# Initialize bot and dispatcher
bot = Bot(token=API_TOKEN, parse_mode="HTML")
dp = Dispatcher(bot, storage=MemoryStorage())

# Initialize scheduler
scheduler = AsyncIOScheduler()
scheduler.start()

# Sructure of callback buttons
button_cb = callback_data.CallbackData(
    'btn', 'question', 'answer', 'data')


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


#  ------------------------------------------------------ НАЗНАЧЕНИЕ ОПЕРАТОРОВ
made_operator = 'made_operator'
ignor_button = 'IGNOR'
buttons_for_made_operator = [ignor_button, ] \
    + [section_member.value for section_member in list(Section)]


def get_keyboard_for_made_operator(tg_id: int) -> InlineKeyboardMarkup:
    keyboard = make_inline_keyboard(
        question=made_operator,
        answers=buttons_for_made_operator,
        data=tg_id
    )
    return keyboard


@dp.message_handler(
    lambda message: is_message_private(message),
    commands=['operator'], state="*")
async def operator_command(message: Message, state: FSMContext):
    log.info('operator_command from: %r', message.from_user.id)
    await message.reply(
        text='Запрос отправлен',
        reply_markup=ReplyKeyboardRemove()
    )
    for admin_id in ADMINS_TG:
        await bot.send_message(
            chat_id=admin_id,
            text=message.from_user.full_name,
            reply_markup=get_keyboard_for_made_operator(
                message.from_user.id
            )
        )


@dp.callback_query_handler(
    button_cb.filter(
        question=made_operator,
        answer=buttons_for_made_operator
    ),
    state='*')
async def made_operator_callback_button(
        query: CallbackQuery,
        callback_data: typing.Dict[str, str],
        state: FSMContext):
    log.info('Got this callback data: %r', callback_data)
    section_for_operator = callback_data['answer']
    if section_for_operator == ignor_button:
        await query.message.delete()
        return

    operator_tg_id = callback_data['data']
    try:
        Operator.new(
            tg_id=operator_tg_id,
            section=Section[section_for_operator],
            name=query.message.text
        )
    except Exception:
        await query.message.answer('ошибка при назначение')
        return

    await query.message.edit_text((
            query.message.text
            + ' \n'
            + section_for_operator)
        )


def is_message_from_admin(message: Message):
    return message.from_user.id in ADMINS_TG


@dp.message_handler(
    lambda message: is_message_private(message),
    lambda message: is_message_from_admin(message),
    commands=['help'], state="*")
async def send_help_for_admin(message: Message, state: FSMContext):
    log.info('send_help_for_admin from: %r', message.from_user.id)
    await message.answer(
        text=help_for_admin_text
    )

delete_button = 'Удалить'


def get_keyboard_for_operator(operator_id: int) -> InlineKeyboardMarkup:
    keyboard = make_inline_keyboard(
        question=made_operator,
        answers=[delete_button, ],
        data=operator_id
    )
    return keyboard


@dp.message_handler(
    lambda message: is_message_private(message),
    lambda message: is_message_from_admin(message),
    commands=['all_operators'], state="*")
async def send_all_operators(message: Message, state: FSMContext):
    log.info('send_all_operators from: %r', message.from_user.id)
    for operator in Operator.get_operator_list():
        await message.answer(
            text=(
                operator.get_name()
                + ' - '
                + operator.get_section().value),
            reply_markup=get_keyboard_for_operator(operator.get_operator_id())
        )


@dp.callback_query_handler(
    button_cb.filter(
        question=made_operator,
        answer=[delete_button, ]),
    state='*')
async def delete_operator_callback_button(
        query: CallbackQuery,
        callback_data: typing.Dict[str, str],
        state: FSMContext):
    log.info('Got this callback data: %r', callback_data)
    operator_id = callback_data['data']
    Operator.delete(operator_id)
    await query.message.delete()


#  -------------------------------------------------------------- ВХОД ТГ ЮЗЕРА
def get_keyboard_services() -> ReplyKeyboardMarkup:
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    for product_name in Product.get_all_product_names()[0:1]:  # SHIT !!!!!!!!!
        keyboard.add(KeyboardButton(text=product_name))
    return keyboard


@dp.message_handler(
    lambda message: is_message_private(message),
    commands=['start'], state="*")
async def start_command(message: Message, state: FSMContext):
    log.info('start command from: %r', message.from_user.id)

    TgUser.new(
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
    waiting_for_customer_name = State()
    waiting_for_payment_photo = State()


start_service_button = 'Начать оформление'


def is_message_product_button(message: Message) -> bool:
    """Сообщение это кнопка из клавиатуры сервисов?"""
    if message.text in Product.get_all_product_names():
        return True
    else:
        return False


@dp.message_handler(
    lambda message: is_message_private(message),
    lambda message: is_message_product_button(message),
    content_types=[ContentType.TEXT],
    state='*')
async def replay_for_product_button(message: Message, state: FSMContext):
    log.info('new_text_message from: %r', message.from_user.id)

    product = Product.get_product_by_name(message.text)
    keyboard = make_inline_keyboard(
        question=product.uniq_key,
        answers=[start_service_button, ]
    )
    await message.answer(
        text=product.terms_description,
        reply_markup=keyboard
    )


def get_keyboard_exist_customer_name(
        product: Product, tg_id: int) -> ReplyKeyboardMarkup:
    service_class = product.service_class
    services = service_class.get_uncompleted_services(tg_id)
    if not services:
        return None

    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    for service in services:
        keyboard.add(KeyboardButton(text=service.get_customer_name()))
    return keyboard


@dp.callback_query_handler(
    button_cb.filter(
        question=Product.get_all_product_keys(),
        answer=[start_service_button, ]
    ),
    state='*')
async def start_service_callback_button(
        query: CallbackQuery,
        callback_data: typing.Dict[str, str],
        state: FSMContext):
    log.info('Got this callback data: %r', callback_data)

    await query.message.edit_reply_markup()  # delete inline button

    product_key = callback_data['question']
    product = Product.get_product(product_key)

    await CustomerState.waiting_for_customer_name.set()
    await state.update_data(product_name=product.product_name)

    keyboard = get_keyboard_exist_customer_name(
        product=product,
        tg_id=query.from_user.id
    )
    text = waiting_customer_name_text
    if keyboard:
        text += customer_name_exist_text
    await query.message.answer(
        text=text,
        reply_markup=keyboard)

    await query.answer()  # stop circle on button


@dp.message_handler(
    content_types=ContentType.TEXT,
    state=CustomerState.waiting_for_customer_name)
async def new_customer_name(message: Message, state: FSMContext):
    log.info(f'new_customer_name from: { message.from_user.id }')
    await message.reply(
        text=got_customer_name_text,
        reply_markup=get_keyboard_services()
    )
    state_data = await state.get_data()
    product_name = state_data['product_name']
    product = Product.get_product_by_name(product_name)

    Service_Class = product.service_class
    service = Service_Class.get_service_by_customer_name(
        tg_id=message.from_user.id,
        customer_name=message.text,
        request_data=datetime.today().date()
    )
    await state.update_data(service=service)

    if service.is_paid():
        await send_actions_for_service(message, product)
    else:
        await send_form_for_pay(
            tg_id=message.from_user.id,
            product_name=product.product_name,
            payment_amount=product.payment_amount,
            state=state
        )


async def send_form_for_pay(
        tg_id: int,
        product_name: str,
        payment_amount: int,
        state: FSMContext):
    log.info('send_form_for_pay')
    await bot.send_message(
        chat_id=tg_id,
        text=get_text_for_payment(
            service_name=product_name,
            payment_amount=payment_amount,
            payment_details=PAYMENT_DETAILS
        )
    )
    await CustomerState.waiting_for_payment_photo.set()


@dp.message_handler(
    content_types=ContentType.PHOTO,
    state=CustomerState.waiting_for_payment_photo)
async def new_payment_photo(message: Message, state: FSMContext):
    log.info(f'new_payment_photo from: { message.from_user.id }')
    await message.reply(got_payment_screenshot_text)

    state_data = await state.get_data()
    product_name = state_data['product_name']
    product = Product.get_product_by_name(product_name)

    service = state_data['service']
    service.put_payment_photo(
        payment_photo=message.photo[0]['file_id']
    )
    await send_payment_to_control(service=service)
    await send_actions_for_service(message, product)


async def send_confirm_payment_notification(service: Service):
    await bot.send_message(
        chat_id=service.get_tg_user().get_tg_id(),
        text=get_confirm_payment_text()
    )


async def send_cancel_payment_notification(service: Service):
    await bot.send_message(
        chat_id=service.get_tg_user().get_tg_id(),
        text=get_cancel_payment_text()
    )


async def send_actions_for_service(
        message: Message, product: Product):
    """Отправляет кнопки - какие действия нужно совершить для оформления"""
    log.info('send_actions_for_service')
    keyboard = make_inline_keyboard(
        question=product.uniq_key,
        answers=product.get_document_names()
    )
    await message.answer(
        text=product.preparation_description,
        reply_markup=keyboard
    )


#  ------------------------------------------------ ОФОРМЛЕНИЕ БАНКОВСКОЙ КАРТЫ
class BankCardState(StatesGroup):
    waiting_form = State()
    waiting_pasport = State()


@dp.callback_query_handler(
    button_cb.filter(
        question=bank_card_product.uniq_key,
        answer=bank_card_product.get_document_names()),
    state='*')
async def callback_button_bank_card(
        query: CallbackQuery,
        callback_data: typing.Dict[str, str],
        state: FSMContext):
    log.info('Got this callback data: %r', callback_data)

    if callback_data['answer'] == 'Анкета для Банка':
        await start_form_filling(query.message, state)
    elif callback_data['answer'] == 'Фото паспорта':
        await start_pasport_getting(query.message, state)
    await query.answer()  # stop circle on button

    state_data = await state.get_data()
    product_name = state_data['product_name']
    product = Product.get_product_by_name(product_name)
    await query.message.edit_text(
        text=product.preparation_description,
    )


async def start_form_filling(message: Message, state: FSMContext):
    log.info('start_form_filling from: %r', message.from_user.id)
    await message.answer(
        text=start_form_filling_text
    )

    await BankCardState.waiting_form.set()
    field_enum = BankCardForm.full_name
    field = field_enum.value
    await state.update_data(field_enum=field_enum)
    await message.answer(
        text=get_text_for_form_field(
            field_name=field.name_for_human,
            field_type_discription=field.field_type.value
        )
    )


@dp.message_handler(
    lambda message: is_message_private(message),
    content_types=[ContentType.TEXT],
    state=BankCardState.waiting_form)
async def bankcard_form_filling(message: Message, state: FSMContext):
    log.info('form_filling from: %r', message.from_user.id)

    state_data = await state.get_data()
    field_enum = state_data['field_enum']
    service = state_data['service']

    field = field_enum.value
    print(f'{field.name_in_db}: {message.text}')
    service.put_data_to_field(
        name_field_in_db=field.name_in_db,
        value=message.text
    )

    if field_enum == BankCardForm.address_company:
        await message.answer(text=form_is_end_text)
        await state.reset_state(with_data=False)
        service.form_complete()
        await send_actions_for_service(message, bank_card_product)
        await check_readiness_and_do_next_step(service)
        return

    field_enum = get_next_enum(field_enum)
    field = field_enum.value
    await state.update_data(field_enum=field_enum)
    await message.answer(
        text=get_text_for_form_field(
            field_name=field.name_for_human,
            field_type_discription=field.field_type.value
        )
    )


async def start_pasport_getting(message: Message, state: FSMContext):
    log.info('start_pasport_getting from: %r', message.from_user.id)
    await BankCardState.waiting_pasport.set()
    await message.answer(
        text=waiting_pasport_text
    )


@dp.message_handler(
    lambda message: is_message_private(message),
    content_types=[ContentType.PHOTO],
    state=BankCardState.waiting_pasport)
async def pasport_getting(message: Message, state: FSMContext):
    log.info('form_filling from: %r', message.from_user.id)

    state_data = await state.get_data()
    service = state_data['service']
    service.new_pasport(
        pasport=message.photo[0]['file_id']
    )
    service.passport_complete()
    await check_readiness_and_do_next_step(service)
    await message.answer(
        text=pasport_getting_text
    )


#  ------------------------------------------------------------ PAYMENT CONTROL
confirm_payment = 'Подтвердить платеж'
cancel_payment = 'Платеж не верный'
payment_control_buttons = (confirm_payment, cancel_payment)


def payment_control_keyboard(service: Service):
    keyboard = make_inline_keyboard(
        question=Section.PAYMENT_CONTROL.name,
        answers=payment_control_buttons,
        data=service.get_service_id()
    )
    return keyboard


async def send_payment_to_control(service: Service):
    """Отправляет оплату на проверку"""
    log.info('send_payment_to_control')
    product = service.__class__.product
    tg_user = service.get_tg_user()
    text = get_text_for_payment_control(
        product_name=product.product_name,
        payment_amount=product.payment_amount,
        from_customer=(
            f'{service.get_customer_name()} @{tg_user.get_username()}'
        )
    )

    payment_operators = Operator.get_operator_list(Section.PAYMENT_CONTROL)
    for operator in payment_operators:
        await bot.send_photo(
            chat_id=operator.get_tg_id(),
            photo=service.get_payment_photo_id(),
            caption=text,
            reply_markup=payment_control_keyboard(service)
        )


@dp.callback_query_handler(
    button_cb.filter(
        question=Section.PAYMENT_CONTROL.name,
        answer=payment_control_buttons),
    state='*')
async def callback_button_payment_control(
        query: CallbackQuery,
        callback_data: typing.Dict[str, str],
        state: FSMContext):
    log.info('Got this callback data: %r', callback_data)
    if not Operator.is_user_operator(
            tg_id=query.from_user.id,
            section=Section.PAYMENT_CONTROL):
        log.warning('user is not payment_control_operator')
        return

    service_id = callback_data['data']
    service = Service(service_id)
    if callback_data['answer'] == confirm_payment:
        service.confirm_payment()
        await send_confirm_payment_notification(service)
        await query.message.edit_caption(
            caption=query.message.caption + '\nПОДТВЕРЖДЕН'
        )
        await check_readiness_and_do_next_step(service)
    elif callback_data['answer'] == cancel_payment:
        service.cancel_payment()
        await query.message.edit_caption(
            caption=query.message.caption + '\nОТМЕНА'
        )
        await send_cancel_payment_notification(service)


#  ---------------------------------------------------------- ВЫПОЛНЕНИЕ УСЛУГИ
async def check_readiness_and_do_next_step(service: Service):
    """Отправляет сервис на проверку готовности:
        Оплата, готовность документов
    Если все готов:
        отправляет исполнителю-оператору
    """
    log.info('check_readiness_bank_card_service')

    if BankCardService.does_service_exist(service.get_service_id()):
        service = BankCardService(service.get_service_id())
        if not service.is_service_ready():
            log.info('BankCardService is not ready')
            return
        log.info('BankCardService is ready')
        await send_service_to_bank_operator(service)
    elif DriveLicenseService.does_service_exist(service.get_service_id()):
        service = BankCardService(service.get_service_id())
        if not service.is_service_ready():
            print('drive')
            return


take_customer = 'Взять клиента'
refuse_customer = 'Отказаться'
bank_card_operator_buttons = (take_customer, refuse_customer)


def bank_card_operator_keyboard(service: Service):
    keyboard = make_inline_keyboard(
        question=Section.BANK_CARD.name,
        answers=bank_card_operator_buttons,
        data=service.get_service_id()
    )
    return keyboard


async def send_service_to_bank_operator(service: Service):
    """Отправляет исполнителю-оператору"""
    log.info('send_service_to_bank_operator')
    bank_operators = Operator.get_operator_list(Section.BANK_CARD)
    for operator in bank_operators:
        await bot.send_message(
            chat_id=operator.get_tg_id(),
            text=get_text_for_bank_card_operator(
                from_customer=service.get_customer_name(),
                operator=service.get_executor_name()
            ),
            reply_markup=bank_card_operator_keyboard(service)
        )


@dp.callback_query_handler(
    button_cb.filter(
        question=Section.BANK_CARD.name,
        answer=bank_card_operator_buttons),
    state='*')
async def callback_bank_card_operator(
        query: CallbackQuery,
        callback_data: typing.Dict[str, str],
        state: FSMContext):
    log.info('Got this callback data: %r', callback_data)
    if not Operator.is_user_operator(
            tg_id=query.from_user.id,
            section=Section.BANK_CARD):
        log.warning('user is not bank_card_operator')
        return

    service_id = callback_data['data']
    service = BankCardService(service_id)
    if callback_data['answer'] == take_customer:
        operator = Operator.get_operator(query.from_user.id, Section.BANK_CARD)
        service.change_executor(operator)
        await send_documents_for_bank_operator(service)
        await send_meeting_message(service)
    elif callback_data['answer'] == refuse_customer:
        pass

    await query.message.edit_text(
        text=get_text_for_bank_card_operator(
            from_customer=service.get_customer_name(),
            operator=service.get_executor_name()
        )
    )


async def send_documents_for_bank_operator(service: Service):
    """Отправляет документы исполнителю-оператору"""
    log.info('send_service_to_bank_operator')
    product = service.__class__.product
    operator = service.get_executor()

    await bot.send_message(
        chat_id=operator.get_tg_id(),
        text=get_form_text(
            title=product.list_of_documents[0].document_name,
            form_dict=service.get_form()
        )
    )
    await bot.send_photo(
        chat_id=operator.get_tg_id(),
        photo=service.get_passport(),
        caption=product.list_of_documents[1].document_name
    )

bank_place_name_buttons = [
    place.name for place in bank_card_product.list_of_places]


def bank_places_keyboard(service: Service):
    keyboard = make_inline_keyboard(
        question=Section.BANK_CARD.name,
        answers=bank_place_name_buttons,
        data=service.get_service_id()
    )
    return keyboard


async def send_meeting_message(service: Service):
    """Отправляет исполнителю-оператору сообщение
    для назначения времени/места встречи
    """
    log.info('send_meeting_message')
    operator = service.get_executor()
    product = service.__class__.product

    await bot.send_message(
        chat_id=operator.get_tg_id(),
        text=(
            get_meeting_text(
                product_name=product.product_name,
                customer_name=service.get_customer_name(),
                operator_name=service.get_executor_name(),
                place_name='---',
                data_time='--- | 7:40')
            + chose_meeting_place
        ),
        reply_markup=bank_places_keyboard(service)
    )


@dp.callback_query_handler(
    button_cb.filter(
        question=Section.BANK_CARD.name,
        answer=bank_place_name_buttons),
    state='*')
async def callback_meeting_message(
        query: CallbackQuery,
        callback_data: typing.Dict[str, str],
        state: FSMContext):
    log.info('Got this callback data: %r', callback_data)
    if not Operator.is_user_operator(
            tg_id=query.from_user.id,
            section=Section.BANK_CARD):
        log.warning('user is not bank_card_operator')
        return

    service_id = callback_data['data']
    service = BankCardService(service_id)
    product = service.__class__.product
    place_name = callback_data['answer']
    place = product.get_place_by_name(place_name)
    service.set_place(place)

    await query.message.edit_text(
        text=(
            get_meeting_text(
                product_name=product.product_name,
                customer_name=service.get_customer_name(),
                operator_name=service.get_executor_name(),
                place_name=service.get_place_address(),
                data_time='--- | 7:40')
            + chose_meeting_time
        ),
        reply_markup=bank_days_keyboard(service)
    )


bank_days_name_question = 'bank_days'


def bank_days_keyboard(service: Service):
    today = datetime.now(tz=timezone(CLIENT_TIMEZONE_NAME)).date()
    days = [str(today + timedelta(days=i)) for i in range(1, 4)]
    keyboard = make_inline_keyboard(
        question=bank_days_name_question,
        answers=days,
        data=service.get_service_id()
    )
    return keyboard


@dp.callback_query_handler(
    button_cb.filter(
        question=bank_days_name_question),
    state='*')
async def callback_time_meeting_message(
        query: CallbackQuery,
        callback_data: typing.Dict[str, str],
        state: FSMContext):
    log.info('Got this callback data: %r', callback_data)
    if not Operator.is_user_operator(
            tg_id=query.from_user.id,
            section=Section.BANK_CARD):
        log.warning('user is not bank_card_operator')
        return

    service_id = callback_data['data']
    service = BankCardService(service_id)
    product = service.__class__.product

    day_str = callback_data['answer']
    meeting_day = datetime(
        year=int(day_str[0:4]),
        month=int(day_str[5:7]),
        day=int(day_str[8:10]),
        hour=7,
        minute=40
    )
    meeting_day = timezone(CLIENT_TIMEZONE_NAME).localize(meeting_day)
    service.set_time(meeting_day)

    await query.message.edit_text(
        text=get_meeting_text(
            product_name=product.product_name,
            customer_name=service.get_customer_name(),
            operator_name=service.get_executor_name(),
            place_name=service.get_place_address(),
            data_time=service.get_time().strftime('%Y-%m-%d | %H:%M')
        )
    )
    await add_meeting_notification(service)
    await send_meeting_notification(service)


#  ----------------------------------------------------- ДЕЙСТВИЯ ПО РАСПИСАНИЮ
async def add_meeting_notification(service: Service):
    """Настраивает отложенное напоминание"""
    log.info('meeting_notification')

    meeting_time = service.get_time()
    time_for_notifi = (
        meeting_time - timedelta(days=1)
        ).replace(hour=21, minute=00)

    scheduler.add_job(
        func=send_meeting_notification,
        trigger=DateTrigger(
            run_date=time_for_notifi
        ),
        kwargs={'service': service}
    )


async def send_meeting_notification(service: Service):
    """Отправляет клиенту напоминание о встрече"""
    log.info('notification')
    product = service.__class__.product
    product = Product()
    place = product.find_place(place_address=service.get_place_address())
    await bot.send_message(
        chat_id=service.get_tg_user().get_tg_id(),
        text=get_meeting_text(
            product_name=product.product_name,
            customer_name=service.get_customer_name(),
            operator_name=service.get_executor_name(),
            place_name=place.address,
            place_link=place.google_map_link,
            data_time=service.get_time().strftime('%Y-%m-%d | %H:%M')
        )
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
