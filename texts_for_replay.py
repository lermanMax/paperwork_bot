help_text = 'хелп'
help_for_admin_text = """
/operator - запрос на доступ для оператора

/all_operators - посмотреть всех операторов
"""

start_cmnd_text = """
Добро пожаловать!

Используйте кнопки внизу экрана, чтобы ознакомиться с нашими услугами
"""

reply_on_random_message = """
Извините, не могу это обработать.

Если вы что-то заполняли, попробуйте начать с начала.

Используте /help если у вас остались вопросы.
"""

waiting_customer_name_text = """Пришлите имя на кого вы оформляете услугу"""
customer_name_exist_text = """
\n(если вы уже начинали оформлять услугу, выберете имя из списка, чтобы продолжить)
"""


got_customer_name_text = """Принято"""


def get_text_for_payment(
        service_name: str, payment_amount: int, payment_details: str):
    text = (
        'Оплата услуги:\n'
        f'<b>{service_name}</b>\n'
        f'Сумма к оплате: <b>{payment_amount}</b> \n'
        f'Реквизиты для оплаты:\n'
        f'<code>{payment_details}</code>\n'
        f'\nИнструкция:\n'
        f'1. Выполните перевод\n'
        f'2. Пришлите скриншот перевода\n'
        f'3. Когда администратор проверит ваш перевод, вам придет подтверждение\n'
        f'\n(сейчас можно кинуть просто рандомную фотку)'
    )
    return text


got_payment_screenshot_text = """
Скриншот отправлен администратору. Когда он будет проверен, вам придет подтверждение.
"""


def get_text_for_payment_control(
        product_name: str, payment_amount: int, from_customer: str):
    text = (
        'Новая оплата на услугу:\n'
        f'<b>{product_name}</b>\n'
        f'Сумма к оплате: {payment_amount} \n'
        f'Клиент:{from_customer}\n'
    )
    return text


def get_confirm_payment_text():
    return 'Администратор подтвердил платеж'


def get_cancel_payment_text():
    return 'Администратор не принял платеж'


start_form_filling_text = 'Начинаем заполнять анкету'
form_is_end_text = 'Анкета заполнена'


def get_text_for_form_field(
      field_name: str, field_type_discription: str):
    text = (
      f'Напишите <b>{field_name}</b> \n'
      f'({ field_type_discription })'
    )
    return text


waiting_pasport_text = 'Пришлите фото паспорта. (любое фото)'
pasport_getting_text = 'Паспорт принят'

waiting_evisa_text = 'Пришлите электронную визу. (любое фото)'
evisa_getting_text = 'Электронная виза принята'

answer_shoud_be_bool = 'Ответ должен быть Да или Нет'
documents_is_ready_text = """
Вы прислали все, что было необходимо. Ваша заявка на услугу отправлена иполнителю. Когда исполнитель назначит день встречи, вам придет уведомление.
"""


def get_text_for_new_service(
        product_name: str,
        customer_name: str,
        operator_name: str,
        place_name: str = None,
        date_time: str = None
        ):
    if place_name:
        place_text = f'Место: {place_name} \n'
        date_text = f'Дата и время: --- {date_time[11:]}\n'
    else:
        place_text = ''
        date_text = ''
    text = (
        '<b>ЗАКАЗ</b>\n\n'
        f'Услуга: {product_name}\n'
        f'Клиент: {customer_name}\n'
        f'Исполнитель: {operator_name}\n'
        f'{place_text}'
        f'{date_text}'

    )
    return text


def get_form_text(title: str, form_dict: dict):
    text = f'<b>{title}</b>\n\n'
    for key, value in form_dict.items():
        text += f'{key}: {value}\n'
    return text


def get_meeting_text(
        product_name: str,
        customer_name: str,
        operator_name: str,
        place_name: str,
        data_time: str,
        place_link: str = None
        ):
    if place_link:
        place_text = f'Место: <a href="{place_link}">{place_name}</a> \n'
    else:
        place_text = f'Место: {place_name}\n'
    text = (
        '<b>ВСТРЕЧА</b>\n\n'
        f'Услуга: {product_name}\n'
        f'Клиент: {customer_name}\n'
        f'Исполнитель: {operator_name}\n'
        f'{place_text}'
        f'Дата и время: {data_time}\n'
    )
    return text


chose_meeting_place = """\n\n<b>Выберете, какое место встречи?</b>"""
chose_meeting_time = """\n\n<b>Выберете, какое время встречи?</b>"""
chose_meeting_date = """\n\n<b>Выберете, дату встречи?</b>"""
meeting_date_chosing_operator = """
\n\n<b>Дату встречи выберет исполнитель</b>"""
