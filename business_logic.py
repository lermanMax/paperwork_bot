from __future__ import annotations
from collections import defaultdict
import logging
from typing import Any, NamedTuple, Tuple, List
from enum import Enum
from datetime import date, datetime

from db_managing import OperatorData, ServiceData, TgUserData


# Configure logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger('busines_logic')


# Exeptions

# Class
class CacheMixin(object):
    __all_objects = defaultdict(dict)

    def __init__(self, key):
        self.__all_objects[self.__class__][key] = self

    @classmethod
    def get(cls, key):
        if key in cls.__all_objects[cls]:
            object_ = cls.__all_objects[cls][key]
            if object_ is not None:
                return object_
        return cls(key)


class TgUser(CacheMixin):
    @classmethod
    def new(cls, tg_id: int, tg_username: str) -> TgUser:
        log.info(f'new TgUser: {tg_id}')
        if not TgUserData.does_tg_user_exist(tg_id):
            TgUserData.new_tg_user(tg_id, tg_username)
        return TgUser(tg_id)

    def __init__(self, tg_id: int):
        super(TgUser, self).__init__(key=tg_id)
        self.tg_id = tg_id
        self.tg_data = TgUserData(tg_id)

    def get_tg_id(self) -> int:
        return self.tg_id

    def get_username(self) -> str:
        username = self.tg_data.get_tg_username()
        if not username:
            return self.get_tg_id()
        else:
            return username


class Section(Enum):
    PAYMENT_CONTROL = 'PAYMENT_CONTROL'
    BANK_CARD = 'BANK_CARD'
    DRIVER_LICENSE = 'DRIVER_LICENSE'


class Operator(CacheMixin):
    @classmethod
    def new(cls, tg_id: int, section: Section, name: str) -> Operator:
        operator_id = OperatorData.new_operator(
            tg_id=tg_id, section=section.value, name=name
        )
        return Operator(operator_id)

    @classmethod
    def delete(cls, operator_id: int) -> None:
        OperatorData.delete_operator(operator_id=operator_id)

    @classmethod
    def get_operator_list(cls, section: Section = None) -> tuple[Operator]:
        if section:
            section = section.value
        operators_id = OperatorData.get_operator_id_list(section)
        return (Operator.get(operator_id) for operator_id in operators_id)

    def __init__(self, operator_id: int):
        super(Operator, self).__init__(key=operator_id)
        self.operator_data = OperatorData(operator_id)

    def get_tg_id(self) -> int:
        return self.operator_data.get_tg_id()

    def get_name(self) -> int:
        return self.operator_data.get_name()

    def get_operator_id(self) -> int:
        return self.operator_data.get_operator_id()

    def get_section(self) -> Section:
        section_name = self.operator_data.get_section()
        return Section(section_name)

    def execute_service(self, service: Service):
        pass


class Service(CacheMixin):
    @classmethod
    def new(cls,
            tg_id: int,
            customer_name: str,
            request_date: date) -> Service:
        service_id = 1
        return Service.get(service_id)

    def __init__(self, service_id: int):
        super(Service, self).__init__(key=service_id)
        self.service_id = service_id
        self.service_data = ServiceData(service_id)

    def get_tg_id(self) -> int:
        return self.service_data.get_user_tg_id()

    def get_payment_photo_id(self) -> str:
        return self.service_data.get_payment_photo()

    def put_payment_photo(self, payment_photo: str) -> None:
        log.info((
            'new payment photo for service: '
            f'{self.service_id} {payment_photo}'
            ))
        self.service_data.update_payment_photo(payment_photo)

    def confirm_payment(self) -> None:
        log.info(f'confirm_payment for service: {self.service_id}')

    def change_executor(self, new_executor: Operator) -> None:
        log.info(f'new operator for service: {self.service_id}')


class Meeting():
    def set_time(time_for_meeting: datetime):
        log.info(f'set_time: {time_for_meeting}')

    def set_place(place: Place):
        log.info(f'set_place: {place.name}')

    def get_time_slots():
        pass


class Place:
    def __init__(
            self,
            name: str,
            address: str,
            google_map_link: str) -> Place:

        self.name = name
        self.address = address
        self.google_map_link = google_map_link


# -------------------------------------------------------------- PRODUCT STAFF
def get_next_enum(enum_member: Enum):
    enum_list = list(enum_member.__class__)
    next_member_index = enum_list.index(enum_member) + 1
    if next_member_index < len(enum_list):
        return enum_list[next_member_index]
    else:
        return None


class FieldType(Enum):
    TEXT = "текст"
    EN_TEXT = "текст на английском"
    RU_TEXT = "текст на русском"
    COUNT = "целое число"
    PHONE = "номер телефона"
    EMAIL = "email адрес"
    DATE = "дата (дд.мм.гггг)"


class Form(NamedTuple):
    name_table_in_db: str


class FormField(NamedTuple):
    form: Form
    field_type: FieldType
    name_in_db: str
    name_for_human: str


class ProductNotFound(Exception):
    """Product do not exist or uniq_key is wrong"""


class Document:
    def __init__(self, document_name: str) -> None:
        self.document_name = document_name


class Product:
    _all_products = {}

    @classmethod
    def get_product(cls, uniq_key: str) -> Product:
        if uniq_key in cls._all_products:
            return cls._all_products[uniq_key]
        else:
            raise ProductNotFound

    @classmethod
    def get_all_products(cls) -> List[Product]:
        return [product for key, product in cls._all_products.items()]

    @classmethod
    def get_all_product_keys(cls) -> List[str]:
        return [key for key, product in cls._all_products.items()]

    @classmethod
    def get_all_product_names(cls) -> List[str]:
        return [
            product.product_name
            for key, product in cls._all_products.items()
        ]

    @classmethod
    def get_product_by_name(cls, product_name: str) -> Product:
        for key, product in cls._all_products.items():
            if product.product_name == product_name:
                return product
        raise ProductNotFound

    def __init__(
            self,
            product_name: str,
            uniq_key: str,
            payment_amount: str,
            terms_description: str,
            list_of_documents: List[Document],
            preparation_description: str,
            list_of_places: List[Place],
            service_class) -> Product:

        self.product_name = product_name
        self.uniq_key = uniq_key
        self.payment_amount = payment_amount

        self.terms_description = terms_description
        self.list_of_documents = list_of_documents
        self.preparation_description = preparation_description

        self.list_of_places = list_of_places
        self.service_class = service_class
        self._all_products[uniq_key] = self

    def get_document_names(self) -> List[str]:
        return [doc.document_name for doc in self.list_of_documents]
