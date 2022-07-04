from typing import Any, List
from enum import Enum
from datetime import date

from business_logic import Section, Service, Meeting, FormField, Product,\
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
    """Продуктовый сервис для Банковской карты"""
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
        Place('Банк 1', 'address 1', 'https://goo.gl/maps/JCfYWKhpRfFeShY48'),
        Place('Банк 2', 'address 2', 'https://goo.gl/maps/JCfYWKhpRfFeShY48'),
        Place('Bank 3', 'address 3', 'https://goo.gl/maps/JCfYWKhpRfFeShY48')
    ],
    service_class=BankCardService,
    operator_section=Section.BANK_CARD
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
4. Нужно выбрать место и время встречи

Выберете, что вы хотите сделать:
"""


class DriveLicenseService(Service, Meeting):
    """Продуктовый сервис для Прав"""
    product = None  # Product()

    @classmethod
    def new(cls, tg_id: int, customer_name: str, request_data: date):
        log.info(f'new DriveLicenseService from: {tg_id}')
        service_id = DriverLicenseServiceData.new_service(
            tg_id=tg_id,
            customer_name=customer_name,
            request_date=request_data
        )
        return DriveLicenseService(service_id)

    @classmethod
    def does_service_exist(cls, service_id: int) -> bool:
        driver_data = DriverLicenseServiceData
        return driver_data.does_driver_license_service_exist(service_id)

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
        self.driver_license_data = DriverLicenseServiceData(service_id)

    def is_service_ready(self) -> bool:
        if (self.driver_license_data.is_paid()
                and self.driver_license_data.is_form_complete()
                and self.driver_license_data.is_passport_complete()
                and self.driver_license_data.is_visa_complete()
                and self.did_customer_chose_meeting()):
            return True
        else:
            return False

    def put_data_to_field(self, name_field_in_db: str, value: Any) -> None:
        log.info(f'{name_field_in_db}: {value}')
        self.driver_license_data.put_data_to_field(
            field_name=name_field_in_db,
            value=value
        )

    def form_complete(self) -> None:
        log.info(f'form_complete: {self.service_id}')
        self.driver_license_data.form_complete()

    def form_incomplete(self) -> None:
        log.info(f'form_complete: {self.service_id}')
        self.driver_license_data.form_incomplete()

    def get_form(self) -> dict:
        return self.driver_license_data.get_form()

    def new_pasport(self, pasport: str) -> None:
        log.info(f'new_pasport for driver_license service: {pasport}')
        self.driver_license_data.change_passport(pasport)

    def passport_complete(self) -> None:
        log.info(f'passport_complete: {self.service_id}')
        self.driver_license_data.passport_complete()

    def passport_incomplete(self) -> None:
        log.info(f'passport_complete: {self.service_id}')
        self.driver_license_data.passport_incomplete()

    def get_passport(self) -> str:
        return self.driver_license_data.get_passport()

    def new_evisa(self, e_visa: str) -> None:
        log.info(f'new_evisa for bankcard service: {e_visa}')
        self.driver_license_data.change_e_visa(e_visa)

    def evisa_complete(self) -> None:
        log.info(f'evisa_complete: {self.service_id}')
        self.driver_license_data.visa_complete()

    def evisa_incomplete(self) -> None:
        log.info(f'evisa_incomplete: {self.service_id}')
        self.driver_license_data.visa_incomplete()

    def get_evisa(self) -> str:
        return self.driver_license_data.get_e_visa()

    def did_customer_chose_meeting(self) -> bool:
        if self.get_place_address():
            if self.get_time():
                return True
        return False


driver_license_product = Product(
    product_name='Оформление водительских прав',
    uniq_key='driver_license',
    payment_amount='140$',
    terms_description=driver_license_terms_text,
    list_of_documents=[
        Document('Анкета'),
        Document('Фото паспорта'),
        Document('Электронная виза'),
        Document('Место встречи')],
    preparation_description=driver_license_preparation_text,
    list_of_places=[
        Place(
            'Восток Бали',
            'Jl. Bhayangkara, Polres Karangasem',
            'https://maps.app.goo.gl/r3cFvoZdzhy3VX9B7'),
        Place(
            'Денпасар',
            'Jl. Gunung Sanghyang No.110, Padangsambian, Kec. Denpasar Bar.',
            'https://goo.gl/maps/nk7Km8AsXmucHrJv9')
    ],
    service_class=DriveLicenseService,
    operator_section=Section.DRIVER_LICENSE
)

drive_form = Form('bank_card_service_data')


class DriverLicenseForm(Enum):
    blood_type = FormField(
        drive_form, FieldType.EN_TEXT, 'blood_type', 'группу крови')
    height_cm = FormField(
        drive_form, FieldType.COUNT, 'height_cm', 'рост (cm)')
    category_a = FormField(
        drive_form, FieldType.YES_NO, 'category_a',
        ', вам нужна категория А?')
    category_b = FormField(
        drive_form, FieldType.YES_NO, 'category_b',
        'вам нужна категория B?')
    international = FormField(
        drive_form, FieldType.YES_NO, 'international',
        ', вам нужны международные права?')
