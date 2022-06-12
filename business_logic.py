from __future__ import annotations
from collections import defaultdict
import logging
from typing import Any

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


class PaperworkBot():
    def __init__(self):
        self.paperwork_bot_data = SupportBotData()

    def add_tg_user(self, tg_id: int, tg_username: int) -> None:
        self.paperwork_bot_data.add_tg_user(
          tg_id=tg_id,
          tg_username=tg_username
        )

    def add_operator(self, tg_id: int):
        self.paperwork_bot_data.add_operator(
          tg_id=tg_id
        )

    def add_textmessage(self, tg_id: int, support_chat_message_id: int):
        self.paperwork_bot_data.add_message(
            tg_id=tg_id,
            support_chat_message_id=support_chat_message_id
        )

    def get_tg_users(self) -> list:
        """Returning not customers tg ids"""
        not_customers_tg_id = self.paperwork_bot_data.get_tg_users()
        return not_customers_tg_id


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


class Operator(TgUser):
    def __init__(self, tg_id: int):
        super(Operator, self).__init__(tg_id=tg_id)

        self.operator_data = OperatorData()

    def get_tg_id(self):
        return self.operator_data.get_tg_id()

    @staticmethod
    def ban(tg_id: int) -> None:
        try:
            OperatorData.ban(tg_id)
            log.info(f'tg_user going to the ban: {tg_id}')
        except UserNotFound:
            log.error(f'tg_user_not_found: {tg_id}')

    @staticmethod
    def unban(tg_id: int) -> None:
        try:
            OperatorData.unban(tg_id)
            log.info(f'tg_user was unbaned: {tg_id}')
        except UserNotFound:
            log.error(f'tg_user_not_found: {tg_id}')


class BankCardService():
    @classmethod
    def new() -> BankCardService:
        pass

    def __init__(self, bcs_id: int):

        self.bank_card_service_data = 0

    def new_payment_foto(foto_tg_id: str) -> None:
        pass

    def new_data_for_field(name_field_in_db: str, value: Any) -> None:
        print(f'{name_field_in_db}: {value}')
