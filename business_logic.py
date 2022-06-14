from __future__ import annotations
from collections import defaultdict
import datetime
import logging
from typing import Any
from enum import Enum
from datetime import date

from db_managing import OperatorData, SupportBotData,\
    TgUserData, UserNotFound


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

    def is_banned(self) -> bool:
        return self.tg_data.is_banned()


class Section(Enum):
    PAYMENT_CONTROL = 'PAYMENT_CONTROL'
    BANK_CARD = 'BANK_CARD'
    DRIVER_LICENSE = 'DRIVER_LICENSE'


class Operator(CacheMixin):
    @classmethod
    def new(tg_id: int, section: Section, name: str) -> Operator:
        operator_id = OperatorData.add_operator(
            tg_id=tg_id, section=section, name=name
        )
        return Operator(operator_id)

    @classmethod
    def delete(operator_id: int) -> None:
        OperatorData.delete(operator_id=operator_id)

    @classmethod
    def get_operator_list(section: Section) -> tuple[Operator]:
        operators_id = [1, 2, 3]
        return (Operator.get(operator_id) for operator_id in operators_id)

    def __init__(self, operator_id: int):
        super(Operator, self).__init__(key=operator_id)

        self.operator_data = OperatorData(operator_id)

    def get_tg_id(self) -> int:
        return self.operator_data.get_tg_id()

    def execute_service(self, service: Service):
        pass


class Service(CacheMixin):
    @classmethod
    def new(tg_id: int, customer_name: str, request_date: date) -> Service:
        service_id = 1
        return Service.get(service_id)

    def __init__(self, service_id: int):
        super(Service, self).__init__(key=service_id)
        self.service_id = service_id

    def put_payment_photo(self, payment_photo: str) -> None:
        log.info(f'new payment photo for service: {self.service_id}')
        print(f'new payment: {payment_photo}')

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


class PlaceType(Enum):
    TRAFFIC_POLICE = 'TRAFFIC_POLICE'
    BANK = 'BANK'


class Place:
    def __init__(
            self,
            place_type: PlaceType,
            name: str,
            address: str,
            google_map_link: str) -> Place:

        self.place_type = place_type
        self.name = name
        self.address = address
        self.google_map_link = google_map_link


class BankCardService(Service, Meeting):
    @classmethod
    def new() -> BankCardService:
        pass

    def __init__(self):
        self.bank_card_service_data = 0

    def new_data_for_field(self, name_field_in_db: str, value: Any) -> None:
        print(f'{name_field_in_db}: {value}')

    def change_form_status(self, is_complete: bool) -> None:
        log.info(f'form status: {is_complete}')

    def new_pasport(self, pasport: str) -> None:
        log.info(f'new_pasport for bankcard service: {pasport}')

    def change_pasport_status(self, is_complete: bool) -> None:
        log.info(f'pasport status: {is_complete}')


class DriveLicenseService(Service, Meeting):
    @classmethod
    def new() -> DriveLicenseService:
        pass

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
