from typing import NamedTuple
from enum import Enum


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


def get_next_enum(enum_member: Enum):
    enum_list = list(enum_member.__class__)
    next_member_index = enum_list.index(enum_member) + 1
    if next_member_index < len(enum_list):
        return enum_list[next_member_index]
    else:
        return None


class FormField(NamedTuple):
    form: Form
    field_type: FieldType
    name_in_db: str
    name_for_human: str


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
        bank_form, FieldType.EN_TEXT,
        'indonesian_phone_number', 'indonesian phone number')
    overseas_phone_number = FormField(
        bank_form, FieldType.EN_TEXT,
        'overseas_phone_number', 'overseas phone number')
    indonesian_adress = FormField(
        bank_form, FieldType.EN_TEXT,
        'indonesian_adress', 'indonesian adress')
    overseas_address = FormField(
        bank_form, FieldType.EN_TEXT, 'overseas_address', 'overseas_address')
    address_email = FormField(
        bank_form, FieldType.EN_TEXT, 'address_email', 'address email')
    occupation = FormField(
        bank_form, FieldType.EN_TEXT, 'occupation', 'occupation')
    company_name = FormField(
        bank_form, FieldType.EN_TEXT, 'company_name', 'company name')
    business_type_company = FormField(
        bank_form, FieldType.EN_TEXT,
        'business_type_company', 'business type company')
    address_company = FormField(
        bank_form, FieldType.EN_TEXT, 'address_company', 'address company')
