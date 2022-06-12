import psycopg2
from config import DB_HOST, DB_NAME, DB_USER, DB_PASS, DB_PORT

db_config = {'host': DB_HOST,
             'dbname': DB_NAME,
             'user': DB_USER,
             'password': DB_PASS,
             'port': DB_PORT}

print('connection to database')
connection = psycopg2.connect(**db_config)
with connection.cursor() as cursor:
    print('starting sql file')
    cursor.execute(open("./migrations/001_init_tables.sql", "r").read())
    print('end of sql file')
connection.commit()
connection.close()
print('data base successfully deployed')
