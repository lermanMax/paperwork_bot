from typing import Any, List
from enum import Enum
from datetime import date

from business_logic import Service, Meeting, FormField, Product,\
    Form, Document, Place, FieldType, log
from db_managing import BankCardServiceData, DriverLicenseServiceData


# -------------------------------------------------------------- BANK CARD
bank_card_terms_text = """
Условия открытия банковского счета Permata.

Стоимость: 2.000.000 IDR | 140$
Срок изготовления: 1 час на следующий день после оформления заявления официально в банке (исключения праздники и выходные)

Вид счета:
  1.Индонезийский счет: IDR
  2.Мультивалютный счет: EUR,USD,CNY (не снижаемый депозит в 1.000.000 IDR. При закрытии депозит возвращается)

Лимиты:
- Снятие наличных:
    до 5000$ без комиссии в месяц
    до 10.000.000 IDR в сутки
    (если больше, то 0,5% комиссия)
+ Пополнение:
    лимитов нет

Мобильный банк:
  + Работает по всему миру
  + Возможность пополнения через p2p
  + SWIFT

Как получить услугу?
  1. Нажмите [ Начать оформление ]
  2. Оплатите услугу
  3. Пришлите данные, которые попросит бот
  4. Приходите на встречу в назначенное время
"""

bank_card_preparation_text = """
Для оформления банковской карты нужна следующая информация:

1. Нужно заполнить анкету для Банка
2. Нужно прислать фото паспорта

Выберете, что вы хотите сделать сейчас:
"""


class BankCardService(Service, Meeting):
    product = None  # Product()

    @classmethod
    def new(cls, tg_id: int, customer_name: str, request_data: date):
        log.info(f'new BankCardService from: {tg_id}')
        service_id = BankCardServiceData.new_service(
            tg_id=tg_id,
            customer_name=customer_name,
            request_date=request_data
        )
        return BankCardService(service_id)

    @classmethod
    def does_service_exist(cls, service_id: int) -> bool:
        return BankCardServiceData.does_bank_card_service_exist(service_id)

    @classmethod
    def get_uncompleted_services(cls, tg_id: int) -> List:
        services = Service.get_service_list(tg_id)
        result_services = []
        for service in services:
            if cls.does_service_exist(service.get_service_id()):
                if not service.get_executor():
                    result_services.append(
                        cls(service_id=service.get_service_id())
                    )
        return result_services

    @classmethod
    def get_service_by_customer_name(
            cls, tg_id: int, customer_name: str, request_data: date = None):
        services = cls.get_uncompleted_services(tg_id)
        for service in services:
            if service.get_customer_name() == customer_name:
                return service
        return cls.new(tg_id, customer_name, request_data)

    def __init__(self, service_id: int):
        Service.__init__(self, service_id)
        Meeting.__init__(self, service_id)
        self.bank_card_service_data = BankCardServiceData(service_id)

    def is_service_ready(self) -> bool:
        if (self.bank_card_service_data.is_paid()
                and self.bank_card_service_data.is_form_complete()
                and self.bank_card_service_data.is_passport_complete()):
            return True
        else:
            return False

    def put_data_to_field(self, name_field_in_db: str, value: Any) -> None:
        log.info(f'{name_field_in_db}: {value}')
        self.bank_card_service_data.put_data_to_field(
            field_name=name_field_in_db,
            value=value
        )

    def form_complete(self) -> None:
        log.info(f'form_complete: {self.service_id}')
        self.bank_card_service_data.form_complete()

    def form_incomplete(self) -> None:
        log.info(f'form_complete: {self.service_id}')
        self.bank_card_service_data.form_incomplete()

    def get_form(self) -> dict:
        return self.bank_card_service_data.get_form()

    def new_pasport(self, pasport: str) -> None:
        log.info(f'new_pasport for bankcard service: {pasport}')
        self.bank_card_service_data.change_passport(pasport)

    def passport_complete(self) -> None:
        log.info(f'passport_complete: {self.service_id}')
        self.bank_card_service_data.passport_complete()

    def passport_incomplete(self) -> None:
        log.info(f'passport_complete: {self.service_id}')
        self.bank_card_service_data.passport_incomplete()

    def get_passport(self) -> str:
        return self.bank_card_service_data.get_passport()


bank_card_product = Product(
    product_name='Оформление карты Permata',
    uniq_key='bank_card',
    payment_amount='140$',
    terms_description=bank_card_terms_text,
    list_of_documents=[
        Document('Анкета для Банка'),
        Document('Фото паспорта')],
    preparation_description=bank_card_preparation_text,
    list_of_places=[
        Place('Банк 1', 'address 1', 'map link 1'),
        Place('Bank 2', 'address 2', 'map link 2')
    ],
    service_class=BankCardService
)

bank_form = Form('bank_card_service_data')


class BankCardForm(Enum):
    full_name = FormField(
        bank_form, FieldType.EN_TEXT, 'full_name', 'full name')
    mother_name = FormField(
        bank_form, FieldType.EN_TEXT, 'mother_name', 'mother name')
    marital_status = FormField(
        bank_form, FieldType.EN_TEXT, 'marital_status', 'marital status')
    last_education = FormField(
        bank_form, FieldType.EN_TEXT, 'last_education', 'last education')
    indonesian_phone_number = FormField(
        bank_form, FieldType.PHONE,
        'indonesian_phone_number', 'indonesian phone number')
    overseas_phone_number = FormField(
        bank_form, FieldType.PHONE,
        'overseas_phone_number', 'overseas phone number')
    indonesian_adress = FormField(
        bank_form, FieldType.EN_TEXT,
        'indonesian_address', 'indonesian address')
    overseas_address = FormField(
        bank_form, FieldType.EN_TEXT, 'overseas_address', 'overseas_address')
    address_email = FormField(
        bank_form, FieldType.EMAIL, 'address_email', 'address email')
    occupation = FormField(
        bank_form, FieldType.EN_TEXT, 'occupation', 'occupation')
    company_name = FormField(
        bank_form, FieldType.EN_TEXT, 'company_name', 'company name')
    business_type_company = FormField(
        bank_form, FieldType.EN_TEXT,
        'business_type_company', 'business type company')
    address_company = FormField(
        bank_form, FieldType.EN_TEXT, 'address_company', 'address company')


# -------------------------------------------------------------- DRIVER LICENSE
driver_license_terms_text = """
Условия оформления водительских прав в Индонезии:

◾ Водительское удостоверение в Индонезии представляет собой 1 документ на 1 категорию.
◾ Получение происходит официально в ГАИ при личном посещении.
◾ Действуют официально 2 года на территории Индонезии и Малайзии.
◾ Дополнительным преимуществом наличие местных водительских прав является:
    + получение скидок для посещения различных мероприятий
    + возможность верификаций на платежных и игровых системах

Как получить услугу?
  1. Нажмите [ Начать оформление ]
  2. Оплатите услугу
  3. Пришлите данные, которые попросит бот
  4. Приходите на встречу в назначенное время
"""

driver_license_preparation_text = """
Для оформления водительских прав нужна следующая информация:

1. Нужно заполнить анкету
2. Нужно прислать фото паспорта
3. Нужно прислать электронную визу

Выберете, что вы хотите сделать:
"""


class DriveLicenseService(Service, Meeting):
    product = None  # Product()

    @classmethod
    def new():
        pass

    @classmethod
    def does_service_exist(cls, service_id: int) -> bool:
        r = DriverLicenseServiceData.does_bank_card_service_exist(service_id)
        return r

    def __init__(self):
        self.drive_license_service_data = 0

    def new_data_for_field(self, name_field_in_db: str, value: Any) -> None:
        print(f'{name_field_in_db}: {value}')

    def change_form_status(self, is_complete: bool) -> None:
        log.info(f'form status: {is_complete}')

    def new_pasport(self, pasport: str) -> None:
        log.info(f'new_pasport for bankcard service: {pasport}')

    def change_pasport_status(self, is_complete: bool) -> None:
        log.info(f'pasport status: {is_complete}')

    def new_evisa(self, e_visa: str) -> None:
        log.info(f'new_evisa for bankcard service: {e_visa}')

    def change_evisa_status(self, is_complete: bool) -> None:
        log.info(f'evisa status: {is_complete}')


driver_license_product = Product(
    product_name='Оформление водительских прав',
    uniq_key='driver_license',
    payment_amount='140$',
    terms_description=driver_license_terms_text,
    list_of_documents=[
        Document('Анкета для '),
        Document('Фото паспорта'),
        Document('Электронная виза')],
    preparation_description=driver_license_preparation_text,
    list_of_places=[
        Place('Банк 1', 'address 1', 'map link 1'),
        Place('Bank 2', 'address 2', 'map link 2')
    ],
    service_class=DriveLicenseService
)
