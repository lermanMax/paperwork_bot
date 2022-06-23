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

got_customer_name_text = """Записано"""


def get_text_for_payment(
        service_name: str, payment_amount: int, payment_details: str):
    text = (
        'Вы собиратесь оплатить услугу:\n'
        f'{service_name}\n'
        f'Сумма к оплате: {payment_amount} USDT\n'
        f'Реквизиты для оплаты:\n'
        f'{payment_details}\n'
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
pasport_getting_text = 'Паспорт получен'
