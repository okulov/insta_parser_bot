import psycopg2
from psycopg2._psycopg import Error
from psycopg2.extras import NamedTupleCursor

import settings


class DataBase():
    def __init__(self):
        self.connection = None

    def create_connection(self):
        try:
            self.connection = psycopg2.connect(
                database=settings.db_name,
                user=settings.db_user,
                password=settings.db_password,
                host=settings.db_host,
                port=settings.db_port,
            )
            self.connection.autocommit = True
            print("Соединение с БД Postgres успешно установлено")

        except psycopg2.OperationalError as e:
            print(f"Ошибка '{e}' при установке соединения")

    def create_tables(self):
        create_posts_table = """
        CREATE TABLE IF NOT EXISTS posts (
          id serial PRIMARY KEY,
          task_id INTEGER,
          url TEXT NOT NULL,
          likes INT,
          create_on TEXT NOT NULL,
          FOREIGN KEY (task_id) REFERENCES tasks (id) ON DELETE CASCADE
        )
        """

        create_tasks_table = """
        CREATE TABLE IF NOT EXISTS tasks (
          id serial PRIMARY KEY,
          url TEXT NOT NULL, 
          count_posts INT, 
          status TEXT NOT NULL
        )
        """

        with self.connection.cursor() as cursor:
            try:
                cursor.execute(create_tasks_table)
                cursor.execute(create_posts_table)
                # self.connection.commit()
                print("Таблицы в БД проверены")
            except Error as e:
                print(f"Ошибка '{e}' при создании таблиц в БД")

    def create_demo_task(self):
        demo_records = [
            ('https://www.instagram.com/vcdynamo/', 5, 'new'),
            ('https://www.instagram.com/leomessi/', 3, 'new'),
            ('https://www.instagram.com/fantenberg7/', 3, 'new'),
        ]

        task_records = ", ".join(["%s"] * len(demo_records))
        insert_query = (
            f"INSERT INTO tasks (url, count_posts, status) VALUES {task_records}"
        )
        with self.connection.cursor() as cursor:
            cursor.execute(insert_query, demo_records)

    def execute_read_query(self, query):
        with self.connection.cursor(cursor_factory=NamedTupleCursor) as cursor:
            result = None
            try:
                cursor.execute(query)
                result = cursor.fetchall()
                return result
            except psycopg2.OperationalError as e:
                print(f"The error '{e}' occurred")

    def execute_query(self, query):
        with self.connection.cursor() as cursor:
            try:
                cursor.execute(query)
                self.connection.commit()
                # print("Query executed successfully")
            except Error as e:
                print(f"The error '{e}' occurred")

    def get_records(self, table, column, value):
        select_tasks = f"SELECT * FROM {table} WHERE {column}='{value}'"
        tasks = self.execute_read_query(select_tasks)
        return tasks

    def set_value(self, table, column, id, new_value):
        update_query = f"UPDATE {table} SET {column} = '{new_value}' WHERE id = {id}"
        self.execute_query(update_query)

    def insert_record(self, table, record: dict):
        s = ', '.join(record.keys())
        insert_query = (
            f"INSERT INTO {table}({s}) VALUES {tuple(record.values())}"
        )

        # print(insert_query)
        cursor = self.connection.cursor()
        cursor.execute(insert_query)


if __name__ == '__main__':
    db = DataBase()
    db.create_connection()
    db.create_tables()
    # db.create_demo_task()
    db.get_records('tasks', 'status', 'new')
    db.set_value('tasks', 'status', 2, 'done')
    print(db.get_records('tasks', 'status', 'new'))
    print(db.get_records('tasks', 'status', 'done'))
    new_record = {'task_id': '1', 'url': '/vcdynamo/', 'likes': '12',
                  'create_on': '2021-05-25'}
    # db.insert_record('posts', new_record)
