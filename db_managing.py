from datetime import date, datetime
import psycopg2
from typing import List

from config import DB_HOST, DB_NAME, DB_USER, DB_PASS, DB_PORT

db_config = {'host': DB_HOST,
             'dbname': DB_NAME,
             'user': DB_USER,
             'password': DB_PASS,
             'port': DB_PORT}


class UserNotFound(Exception):
    pass


class OperatorAlreadySet(Exception):
    pass


class OperatorNotFound(Exception):
    pass


class FieldNotFound(Exception):
    pass


class TgUserData:
    def __init__(self, tg_id: int):
        self._tg_id = tg_id

        connection = psycopg2.connect(**db_config)
        with connection.cursor() as cursor:
            select_script = '''SELECT tg_username
                                FROM tg_user
                                WHERE tg_id = %s;'''
            cursor.execute(select_script, (tg_id,))
            select_username, = cursor.fetchone()
        connection.commit()
        connection.close()

        self._tg_username = select_username

    def get_tg_id(self) -> int:
        return self._tg_id

    def get_tg_username(self) -> str:
        return self._tg_username

    @staticmethod
    def new_tg_user(tg_id, tg_username) -> int:
        connection = psycopg2.connect(**db_config)
        with connection.cursor() as cursor:
            insert_values = (tg_id, tg_username)
            insert_script = '''
                INSERT INTO tg_user (tg_id, tg_username)
                VALUES (%s, %s)
                ON CONFLICT (tg_id)
                DO UPDATE
                SET tg_username = EXCLUDED.tg_username;'''
            cursor.execute(insert_script, insert_values)
        connection.commit()
        connection.close()
        return tg_id

    @staticmethod
    def does_tg_user_exist(tg_id) -> bool:
        connection = psycopg2.connect(**db_config)
        with connection.cursor() as cursor:
            select_script = '''
            SELECT exists(
                SELECT tg_id
                FROM tg_user
                WHERE tg_id = %s);'''
            cursor.execute(select_script, (tg_id,))
            exists, = cursor.fetchone()
        connection.commit()
        connection.close()
        return exists


class OperatorData:
    def __init__(self, operator_id: int):
        self._operator_id = operator_id

        connection = psycopg2.connect(**db_config)
        with connection.cursor() as cursor:
            select_script = '''SELECT tg_id, name, operation_section
                                FROM operator
                                WHERE operator_id = %s;'''
            cursor.execute(select_script, (operator_id,))
            tg_id, name, operation_section = cursor.fetchone()
        connection.commit()
        connection.close()

        self._tg_id = tg_id
        self._name = name
        self._section = operation_section

    def get_operator_id(self) -> int:
        return self._operator_id

    def get_tg_id(self) -> int:
        return self._tg_id

    def get_name(self) -> str:
        return self._name

    def get_section(self) -> str:
        return self._section

    @staticmethod
    def new_operator(tg_id: int, section: str, name: str) -> int:
        if TgUserData.does_tg_user_exist(tg_id):
            connection = psycopg2.connect(**db_config)
            with connection.cursor() as cursor:
                insert_values = (tg_id, section, name)
                insert_script = '''
                    INSERT INTO operator (tg_id, operation_section, name)
                    VALUES (%s, %s, %s)
                    RETURNING operator_id;'''
                try:
                    cursor.execute(insert_script, insert_values)
                    operator_id, = cursor.fetchone()
                except psycopg2.errors.UniqueViolation:
                    raise OperatorAlreadySet
            connection.commit()
            connection.close()
        else:
            raise UserNotFound
        return operator_id

    @staticmethod
    def does_operator_exist(operator_id) -> bool:
        connection = psycopg2.connect(**db_config)
        with connection.cursor() as cursor:
            select_script = '''
            SELECT exists(
                SELECT operator_id
                FROM operator
                WHERE operator_id = %s);'''
            cursor.execute(select_script, (operator_id,))
            exists, = cursor.fetchone()
        connection.commit()
        connection.close()
        return exists

    @staticmethod
    def delete_operator(operator_id: int) -> int:
        if OperatorData.does_operator_exist(operator_id):
            connection = psycopg2.connect(**db_config)
            with connection.cursor() as cursor:
                select_script = '''DELETE FROM operator
                                    WHERE operator_id = %s;'''
                cursor.execute(select_script, (operator_id,))
            connection.commit()
            connection.close()
        else:
            raise OperatorNotFound
        return operator_id

    @staticmethod
    def get_operator_id_list(section: str = None) -> List[int]:
        connection = psycopg2.connect(**db_config)
        with connection.cursor() as cursor:
            if section:
                select_script = '''SELECT operator_id FROM operator
                                    WHERE operation_section = %s;'''
                cursor.execute(select_script, (section,))
            else:
                select_script = '''SELECT operator_id FROM operator;'''
                cursor.execute(select_script)
            try:
                id_list = cursor.fetchall()
            except TypeError:
                id_list = []
        connection.commit()
        connection.close()
        return [id_tuple[0] for id_tuple in id_list]


class ServiceData:
    def __init__(self, service_id: int):
        self._service_id = service_id

        connection = psycopg2.connect(**db_config)
        with connection.cursor() as cursor:
            select_script = '''
                SELECT user_tg_id, request_date
                FROM service
                WHERE service_id = %s;'''
            cursor.execute(select_script, (service_id,))
            user_tg_id, request_date = cursor.fetchone()
        connection.commit()
        connection.close()

        self._user_tg_id = user_tg_id
        self._request_date = request_date

    def get_user_tg_id(self) -> int:
        return self._user_tg_id

    def get_customer_name(self) -> str:
        connection = psycopg2.connect(**db_config)
        with connection.cursor() as cursor:
            select_script = '''
                SELECT customer_name
                FROM service
                WHERE service_id = %s;'''
            cursor.execute(select_script, (self._service_id,))
            customer_name, = cursor.fetchone()
        connection.commit()
        connection.close()
        return customer_name

    def get_request_date(self) -> date:
        return self._request_date

    def get_payment_photo(self) -> str:
        connection = psycopg2.connect(**db_config)
        with connection.cursor() as cursor:
            select_script = '''SELECT payment_photo
                                FROM service
                                WHERE service_id = %s;'''
            cursor.execute(select_script, (self._service_id,))
            payment_photo, = cursor.fetchone()
        connection.commit()
        connection.close()
        return payment_photo

    def is_paid(self) -> bool:
        connection = psycopg2.connect(**db_config)
        with connection.cursor() as cursor:
            select_script = '''SELECT is_paid
                                FROM service
                                WHERE service_id = %s;'''
            cursor.execute(select_script, (self._service_id,))
            is_paid, = cursor.fetchone()
        connection.commit()
        connection.close()
        return is_paid

    def get_service_executor(self) -> int:
        connection = psycopg2.connect(**db_config)
        with connection.cursor() as cursor:
            select_script = '''SELECT service_executor
                                FROM service
                                WHERE service_id = %s;'''
            cursor.execute(select_script, (self._service_id,))
            service_executor, = cursor.fetchone()
        connection.commit()
        connection.close()
        return service_executor

    def update_payment_photo(self, new_payment_photo: str) -> None:
        connection = psycopg2.connect(**db_config)
        with connection.cursor() as cursor:
            update_script = '''UPDATE service
                                SET payment_photo = %s
                                WHERE service_id = %s;'''
            cursor.execute(update_script, (new_payment_photo,
                                           self._service_id,))
        connection.commit()
        connection.close()

    def change_customer_name(self, new_customer_name: str) -> None:
        connection = psycopg2.connect(**db_config)
        with connection.cursor() as cursor:
            update_script = '''
                UPDATE service
                SET customer_name = %s
                WHERE service_id = %s;'''
            cursor.execute(update_script, (new_customer_name,
                                           self._service_id,))
        connection.commit()
        connection.close()

    def mark_paid(self) -> None:
        connection = psycopg2.connect(**db_config)
        with connection.cursor() as cursor:
            update_script = '''UPDATE service
                                SET is_paid = TRUE
                                WHERE service_id = %s;'''
            cursor.execute(update_script, (self._service_id,))
        connection.commit()
        connection.close()

    def mark_unpaid(self) -> None:
        connection = psycopg2.connect(**db_config)
        with connection.cursor() as cursor:
            update_script = '''UPDATE service
                                SET is_paid = FALSE
                                WHERE service_id = %s;'''
            cursor.execute(update_script, (self._service_id,))
        connection.commit()
        connection.close()

    def change_service_executor(self, new_operator_id: int) -> None:
        if OperatorData.does_operator_exist(new_operator_id):
            connection = psycopg2.connect(**db_config)
            with connection.cursor() as cursor:
                update_script = '''
                    UPDATE service
                    SET service_executor = %s
                    WHERE service_id = %s;'''
                cursor.execute(update_script, (new_operator_id,
                                               self._service_id,))
            connection.commit()
            connection.close()
        else:
            raise OperatorNotFound

    @classmethod
    def new_service(cls, tg_id: int, customer_name: str,
                    request_date: date) -> int:
        if TgUserData.does_tg_user_exist(tg_id):
            connection = psycopg2.connect(**db_config)
            with connection.cursor() as cursor:
                insert_values = (tg_id, customer_name, request_date)
                insert_script = '''
                    INSERT INTO service (user_tg_id, customer_name, 
                        request_date)
                    VALUES (%s, %s, %s)
                    RETURNING service_id;'''
                cursor.execute(insert_script, insert_values)
                service_id, = cursor.fetchone()
            connection.commit()
            connection.close()
        else:
            raise UserNotFound
        return service_id


class MeetingData:
    def __init__(self, service_id: int):
        self._service_id = service_id

    def get_time(self) -> datetime:
        connection = psycopg2.connect(**db_config)
        with connection.cursor() as cursor:
            select_script = '''
                SELECT meeting_time
                FROM meeting
                WHERE service_id = %s;'''
            cursor.execute(select_script, (self._service_id,))
            time, = cursor.fetchone()
        connection.commit()
        connection.close()
        return time

    def get_address(self) -> str:
        connection = psycopg2.connect(**db_config)
        with connection.cursor() as cursor:
            select_script = '''
                SELECT meeting_address
                FROM meeting
                WHERE service_id = %s;'''
            cursor.execute(select_script, (self._service_id,))
            address, = cursor.fetchone()
        connection.commit()
        connection.close()
        return address

    def set_time(self, time: datetime) -> None:
        connection = psycopg2.connect(**db_config)
        with connection.cursor() as cursor:
            update_script = '''
                UPDATE meeting
                SET meeting_time = %s
                WHERE service_id = %s;'''
            cursor.execute(update_script, (time, self._service_id,))
        connection.commit()
        connection.close()

    def set_place(self, address: str) -> None:
        connection = psycopg2.connect(**db_config)
        with connection.cursor() as cursor:
            update_script = '''
                UPDATE meeting
                SET meeting_address = %s
                WHERE service_id = %s;'''
            cursor.execute(update_script, (address, self._service_id,))
        connection.commit()
        connection.close()

    @staticmethod
    def new_meeting(service_id: int) -> int:
        connection = psycopg2.connect(**db_config)
        with connection.cursor() as cursor:
            insert_script = '''
                INSERT INTO meeting (service_id)
                VALUES (%s)
                ON CONFLICT DO NOTHING;'''
            cursor.execute(insert_script, (service_id,))
        connection.commit()
        connection.close()
        return service_id


class DriverLicenseServiceData(ServiceData):
    def __init__(self, service_id: int):
        super().__init__(service_id)

    def get_form(self) -> dict:
        connection = psycopg2.connect(**db_config)
        with connection.cursor() as cursor:
            select_script = '''
                SELECT blood_type, height_cm, category_a, category_b, 
                    international
                FROM driver_license_service
                WHERE service_id = %s;'''
            cursor.execute(select_script, (self._service_id,))
            # blood_type, height_cm, category_a, category_b, \
            #     international = cursor.fetchone()
            form = dict(zip(('blood_type', 'height_cm', 'category_a',
                             'category_b', 'international'),
                            cursor.fetchone()))
        connection.commit()
        connection.close()
        return form

    def is_form_complete(self) -> bool:
        connection = psycopg2.connect(**db_config)
        with connection.cursor() as cursor:
            select_script = '''
                SELECT is_form_complete
                FROM driver_license_service
                WHERE service_id = %s;'''
            cursor.execute(select_script, (self._service_id,))
            is_form_complete, = cursor.fetchone()
        connection.commit()
        connection.close()
        return is_form_complete

    def get_passport(self) -> str:
        connection = psycopg2.connect(**db_config)
        with connection.cursor() as cursor:
            select_script = '''
                SELECT passport
                FROM driver_license_service
                WHERE service_id = %s;'''
            cursor.execute(select_script, (self._service_id,))
            passport, = cursor.fetchone()
        connection.commit()
        connection.close()
        return passport

    def is_passport_complete(self) -> bool:
        connection = psycopg2.connect(**db_config)
        with connection.cursor() as cursor:
            select_script = '''
                SELECT is_passport_complete
                FROM driver_license_service
                WHERE service_id = %s;'''
            cursor.execute(select_script, (self._service_id,))
            is_passport_complete, = cursor.fetchone()
        connection.commit()
        connection.close()
        return is_passport_complete

    def get_e_visa(self) -> str:
        connection = psycopg2.connect(**db_config)
        with connection.cursor() as cursor:
            select_script = '''
                SELECT e_visa
                FROM driver_license_service
                WHERE service_id = %s;'''
            cursor.execute(select_script, (self._service_id,))
            e_visa, = cursor.fetchone()
        connection.commit()
        connection.close()
        return e_visa

    def is_visa_complete(self) -> bool:
        connection = psycopg2.connect(**db_config)
        with connection.cursor() as cursor:
            select_script = '''
                SELECT is_visa_complete
                FROM driver_license_service
                WHERE service_id = %s;'''
            cursor.execute(select_script, (self._service_id,))
            is_visa_complete, = cursor.fetchone()
        connection.commit()
        connection.close()
        return is_visa_complete

    def change_blood_type(self, blood_type: str) -> None:
        connection = psycopg2.connect(**db_config)
        with connection.cursor() as cursor:
            update_script = '''UPDATE driver_license_service
                                SET blood_type = %s
                                WHERE service_id = %s;'''
            cursor.execute(update_script, (blood_type, self._service_id,))
        connection.commit()
        connection.close()

    def change_height_cm(self, height_cm: int) -> None:
        connection = psycopg2.connect(**db_config)
        with connection.cursor() as cursor:
            update_script = '''UPDATE driver_license_service
                                SET height_cm = %s
                                WHERE service_id = %s;'''
            cursor.execute(update_script, (height_cm, self._service_id,))
        connection.commit()
        connection.close()

    def change_category_a(self, category_a: bool) -> None:
        connection = psycopg2.connect(**db_config)
        with connection.cursor() as cursor:
            update_script = '''UPDATE driver_license_service
                                SET category_a = %s
                                WHERE service_id = %s;'''
            cursor.execute(update_script, (category_a, self._service_id,))
        connection.commit()
        connection.close()

    def change_category_b(self, category_b: bool) -> None:
        connection = psycopg2.connect(**db_config)
        with connection.cursor() as cursor:
            update_script = '''UPDATE driver_license_service
                                SET category_b = %s
                                WHERE service_id = %s;'''
            cursor.execute(update_script, (category_b, self._service_id,))
        connection.commit()
        connection.close()

    def change_international(self, international: bool) -> None:
        connection = psycopg2.connect(**db_config)
        with connection.cursor() as cursor:
            update_script = '''UPDATE driver_license_service
                                SET international = %s
                                WHERE service_id = %s;'''
            cursor.execute(update_script, (international, self._service_id,))
        connection.commit()
        connection.close()

    def change_passport(self, passport: str) -> None:
        connection = psycopg2.connect(**db_config)
        with connection.cursor() as cursor:
            update_script = '''UPDATE driver_license_service
                                SET passport = %s
                                WHERE service_id = %s;'''
            cursor.execute(update_script, (passport, self._service_id,))
        connection.commit()
        connection.close()

    def passport_complete(self) -> None:
        connection = psycopg2.connect(**db_config)
        with connection.cursor() as cursor:
            update_script = '''UPDATE driver_license_service
                                SET is_passport_complete = TRUE
                                WHERE service_id = %s;'''
            cursor.execute(update_script, (self._service_id,))
        connection.commit()
        connection.close()

    def passport_incomplete(self) -> None:
        connection = psycopg2.connect(**db_config)
        with connection.cursor() as cursor:
            update_script = '''UPDATE driver_license_service
                                SET is_passport_complete = FALSE
                                WHERE service_id = %s;'''
            cursor.execute(update_script, (self._service_id,))
        connection.commit()
        connection.close()

    def change_e_visa(self, e_visa: str) -> None:
        connection = psycopg2.connect(**db_config)
        with connection.cursor() as cursor:
            update_script = '''UPDATE driver_license_service
                                SET e_visa = %s
                                WHERE service_id = %s;'''
            cursor.execute(update_script, (e_visa, self._service_id,))
        connection.commit()
        connection.close()

    def visa_complete(self) -> None:
        connection = psycopg2.connect(**db_config)
        with connection.cursor() as cursor:
            update_script = '''UPDATE driver_license_service
                                SET is_visa_complete = TRUE
                                WHERE service_id = %s;'''
            cursor.execute(update_script, (self._service_id,))
        connection.commit()
        connection.close()

    def visa_incomplete(self) -> None:
        connection = psycopg2.connect(**db_config)
        with connection.cursor() as cursor:
            update_script = '''UPDATE driver_license_service
                                SET is_visa_complete = FALSE
                                WHERE service_id = %s;'''
            cursor.execute(update_script, (self._service_id,))
        connection.commit()
        connection.close()

    def form_complete(self) -> None:
        connection = psycopg2.connect(**db_config)
        with connection.cursor() as cursor:
            update_script = '''UPDATE driver_license_service
                                SET is_form_complete = TRUE
                                WHERE service_id = %s;'''
            cursor.execute(update_script, (self._service_id,))
        connection.commit()
        connection.close()

    def form_incomplete(self) -> None:
        connection = psycopg2.connect(**db_config)
        with connection.cursor() as cursor:
            update_script = '''UPDATE driver_license_service
                                SET is_form_complete = FALSE
                                WHERE service_id = %s;'''
            cursor.execute(update_script, (self._service_id,))
        connection.commit()
        connection.close()

    def put_data_to_field(self, field_name: str, value: any) -> None:
        if field_name == 'blood_type':
            self.change_blood_type(value)
        elif field_name == 'height_cm':
            self.change_height_cm(value)
        elif field_name == 'category_a':
            self.change_category_a(value)
        elif field_name == 'category_b':
            self.change_category_b(value)
        elif field_name == 'international':
            self.change_international(value)
        else:
            raise FieldNotFound

    @classmethod
    def new_service(cls, tg_id: int, customer_name: str,
                    request_date: date) -> int:
        service_id = super().new_service(tg_id, customer_name, request_date)
        MeetingData.new_meeting(service_id)
        connection = psycopg2.connect(**db_config)
        with connection.cursor() as cursor:
            insert_script = '''INSERT INTO driver_license_service (service_id)
                                VALUES (%s)
                                RETURNING service_id;'''
            cursor.execute(insert_script, (service_id,))
            service_id, = cursor.fetchone()
        connection.commit()
        connection.close()
        return service_id


class BankCardServiceData(ServiceData):
    def __init__(self, service_id: int):
        super().__init__(service_id)

    def get_form(self) -> dict:
        connection = psycopg2.connect(**db_config)
        with connection.cursor() as cursor:
            select_script = '''
                SELECT full_name, mother_name, marital_status, last_education,
                    indonesian_phone_number, overseas_phone_number,
                    indonesian_address, overseas_address, address_email, 
                    occupation, company_name, business_type_company, 
                    address_company
                FROM bank_card_service
                WHERE service_id = %s;'''
            cursor.execute(select_script, (self._service_id,))
            form = dict(zip(('full_name', 'mother_name', 'marital_status',
                             'last_education', 'indonesian_phone_number',
                             'overseas_phone_number', 'indonesian_address',
                             'overseas_address', 'address_email', 'occupation',
                             'company_name', 'business_type_company',
                             'address_company'),
                            cursor.fetchone()))
        connection.commit()
        connection.close()
        return form

    def is_form_complete(self) -> bool:
        connection = psycopg2.connect(**db_config)
        with connection.cursor() as cursor:
            select_script = '''
                SELECT is_form_complete
                FROM bank_card_service
                WHERE service_id = %s;'''
            cursor.execute(select_script, (self._service_id,))
            is_form_complete, = cursor.fetchone()
        connection.commit()
        connection.close()
        return is_form_complete

    def get_passport(self) -> str:
        connection = psycopg2.connect(**db_config)
        with connection.cursor() as cursor:
            select_script = '''
                SELECT passport
                FROM bank_card_service
                WHERE service_id = %s;'''
            cursor.execute(select_script, (self._service_id,))
            passport, = cursor.fetchone()
        connection.commit()
        connection.close()
        return passport

    def is_passport_complete(self) -> bool:
        connection = psycopg2.connect(**db_config)
        with connection.cursor() as cursor:
            select_script = '''
                SELECT is_passport_complete
                FROM bank_card_service
                WHERE service_id = %s;'''
            cursor.execute(select_script, (self._service_id,))
            is_passport_complete, = cursor.fetchone()
        connection.commit()
        connection.close()
        return is_passport_complete

    def change_full_name(self, full_name: str) -> None:
        connection = psycopg2.connect(**db_config)
        with connection.cursor() as cursor:
            update_script = '''UPDATE bank_card_service
                                SET full_name = %s
                                WHERE service_id = %s;'''
            cursor.execute(update_script, (full_name, self._service_id,))
        connection.commit()
        connection.close()

    def change_mother_name(self, mother_name: str) -> None:
        connection = psycopg2.connect(**db_config)
        with connection.cursor() as cursor:
            update_script = '''UPDATE bank_card_service
                                SET mother_name = %s
                                WHERE service_id = %s;'''
            cursor.execute(update_script, (mother_name, self._service_id,))
        connection.commit()
        connection.close()

    def change_marital_status(self, marital_status: str) -> None:
        connection = psycopg2.connect(**db_config)
        with connection.cursor() as cursor:
            update_script = '''UPDATE bank_card_service
                                SET marital_status = %s
                                WHERE service_id = %s;'''
            cursor.execute(update_script, (marital_status, self._service_id,))
        connection.commit()
        connection.close()

    def change_last_education(self, last_education: str) -> None:
        connection = psycopg2.connect(**db_config)
        with connection.cursor() as cursor:
            update_script = '''UPDATE bank_card_service
                                SET last_education = %s
                                WHERE service_id = %s;'''
            cursor.execute(update_script, (last_education, self._service_id,))
        connection.commit()
        connection.close()

    def change_indonesian_phone_number(self,
                                       indonesian_phone_number: str) -> None:
        connection = psycopg2.connect(**db_config)
        with connection.cursor() as cursor:
            update_script = '''UPDATE bank_card_service
                                SET indonesian_phone_number = %s
                                WHERE service_id = %s;'''
            cursor.execute(update_script, (indonesian_phone_number,
                                           self._service_id,))
        connection.commit()
        connection.close()

    def change_overseas_phone_number(self, overseas_phone_number: str) -> None:
        connection = psycopg2.connect(**db_config)
        with connection.cursor() as cursor:
            update_script = '''UPDATE bank_card_service
                                SET overseas_phone_number = %s
                                WHERE service_id = %s;'''
            cursor.execute(update_script, (overseas_phone_number,
                                           self._service_id,))
        connection.commit()
        connection.close()

    def change_indonesian_address(self, indonesian_address: str) -> None:
        connection = psycopg2.connect(**db_config)
        with connection.cursor() as cursor:
            update_script = '''UPDATE bank_card_service
                                SET indonesian_address = %s
                                WHERE service_id = %s;'''
            cursor.execute(update_script, (indonesian_address,
                                           self._service_id,))
        connection.commit()
        connection.close()

    def change_overseas_address(self, overseas_address: str) -> None:
        connection = psycopg2.connect(**db_config)
        with connection.cursor() as cursor:
            update_script = '''UPDATE bank_card_service
                                SET overseas_address = %s
                                WHERE service_id = %s;'''
            cursor.execute(update_script,
                           (overseas_address, self._service_id,))
        connection.commit()
        connection.close()

    def change_address_email(self, address_email: str) -> None:
        connection = psycopg2.connect(**db_config)
        with connection.cursor() as cursor:
            update_script = '''UPDATE bank_card_service
                                SET address_email = %s
                                WHERE service_id = %s;'''
            cursor.execute(update_script, (address_email, self._service_id,))
        connection.commit()
        connection.close()

    def change_occupation(self, occupation: str) -> None:
        connection = psycopg2.connect(**db_config)
        with connection.cursor() as cursor:
            update_script = '''UPDATE bank_card_service
                                SET occupation = %s
                                WHERE service_id = %s;'''
            cursor.execute(update_script, (occupation, self._service_id,))
        connection.commit()
        connection.close()

    def change_company_name(self, company_name: str) -> None:
        connection = psycopg2.connect(**db_config)
        with connection.cursor() as cursor:
            update_script = '''UPDATE bank_card_service
                                SET company_name = %s
                                WHERE service_id = %s;'''
            cursor.execute(update_script, (company_name, self._service_id,))
        connection.commit()
        connection.close()

    def change_business_type_company(self, business_type_company: str) -> None:
        connection = psycopg2.connect(**db_config)
        with connection.cursor() as cursor:
            update_script = '''UPDATE bank_card_service
                                SET business_type_company = %s
                                WHERE service_id = %s;'''
            cursor.execute(update_script, (business_type_company,
                                           self._service_id,))
        connection.commit()
        connection.close()

    def change_address_company(self, address_company: str) -> None:
        connection = psycopg2.connect(**db_config)
        with connection.cursor() as cursor:
            update_script = '''UPDATE bank_card_service
                                SET address_company = %s
                                WHERE service_id = %s;'''
            cursor.execute(update_script, (address_company, self._service_id,))
        connection.commit()
        connection.close()

    def form_complete(self) -> None:
        connection = psycopg2.connect(**db_config)
        with connection.cursor() as cursor:
            update_script = '''UPDATE bank_card_service
                                SET is_form_complete = TRUE
                                WHERE service_id = %s;'''
            cursor.execute(update_script, (self._service_id,))
        connection.commit()
        connection.close()

    def form_incomplete(self) -> None:
        connection = psycopg2.connect(**db_config)
        with connection.cursor() as cursor:
            update_script = '''UPDATE bank_card_service
                                SET is_form_complete = FALSE
                                WHERE service_id = %s;'''
            cursor.execute(update_script, (self._service_id,))
        connection.commit()
        connection.close()

    def change_passport(self, passport: str) -> None:
        connection = psycopg2.connect(**db_config)
        with connection.cursor() as cursor:
            update_script = '''UPDATE bank_card_service
                                SET passport = %s
                                WHERE service_id = %s;'''
            cursor.execute(update_script, (passport, self._service_id,))
        connection.commit()
        connection.close()

    def passport_complete(self) -> None:
        connection = psycopg2.connect(**db_config)
        with connection.cursor() as cursor:
            update_script = '''UPDATE bank_card_service
                                SET is_passport_complete = TRUE
                                WHERE service_id = %s;'''
            cursor.execute(update_script, (self._service_id,))
        connection.commit()
        connection.close()

    def passport_incomplete(self) -> None:
        connection = psycopg2.connect(**db_config)
        with connection.cursor() as cursor:
            update_script = '''UPDATE bank_card_service
                                SET is_passport_complete = FALSE
                                WHERE service_id = %s;'''
            cursor.execute(update_script, (self._service_id,))
        connection.commit()
        connection.close()

    def put_data_to_field(self, field_name: str, value: any) -> None:
        if field_name == 'full_name':
            self.change_full_name(value)
        elif field_name == 'mother_name':
            self.change_mother_name(value)
        elif field_name == 'marital_status':
            self.change_marital_status(value)
        elif field_name == 'last_education':
            self.change_last_education(value)
        elif field_name == 'indonesian_phone_number':
            self.change_indonesian_phone_number(value)
        elif field_name == 'overseas_phone_number':
            self.change_overseas_phone_number(value)
        elif field_name == 'indonesian_address':
            self.change_indonesian_address(value)
        elif field_name == 'overseas_address':
            self.change_overseas_address(value)
        elif field_name == 'address_email':
            self.change_address_email(value)
        elif field_name == 'occupation':
            self.change_occupation(value)
        elif field_name == 'company_name':
            self.change_company_name(value)
        elif field_name == 'business_type_company':
            self.change_business_type_company(value)
        elif field_name == 'address_company':
            self.change_address_company(value)
        else:
            raise FieldNotFound

    @classmethod
    def new_service(cls, tg_id: int, customer_name: str,
                    request_date: date) -> int:
        service_id = super().new_service(tg_id, customer_name, request_date)
        MeetingData.new_meeting(service_id)
        connection = psycopg2.connect(**db_config)
        with connection.cursor() as cursor:
            insert_script = '''INSERT INTO bank_card_service (service_id)
                                VALUES (%s)
                                RETURNING service_id;'''
            cursor.execute(insert_script, (service_id,))
            service_id, = cursor.fetchone()
        connection.commit()
        connection.close()
        return service_id
