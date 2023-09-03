import psycopg2
from psycopg2 import DatabaseError, extensions
from functools import wraps
from time import sleep
from psycopg2._psycopg import connection, cursor
from psycopg2.extras import RealDictCursor
from os import environ as env
from datetime import date


def retry(f):
    @wraps(f)
    def wrapper(*args, **kw):
        cls = args[0]
        for x in range(cls._reconnectTries):
            # print(x, cls._reconnectTries)
            try:
                return f(*args, **kw)
            except (psycopg2.InterfaceError, psycopg2.OperationalError) as e:
                print("\nDatabase Connection [InterfaceError or OperationalError]")
                print("Idle for %s seconds" % (cls._reconnectIdle))
                sleep(cls._reconnectIdle)
                cls._connect()
    return wrapper


class Database(object):
    _reconnectTries = 3
    _reconnectIdle = 0

    def __init__(self, database, user, password, host):
        self.host = host,
        self.database = database,
        self.user = user,
        self.password = password
        self.connection = None
        self.cur = None
        self._connect()

    def _connect(self):
        print(type(self.host))
        if type(self.host) is tuple:
            for host in self.host:
                self.host = host
        if type(self.database) is tuple:
            for database in self.database:
                self.database = database
        if type(self.user) is tuple:
            for user in self.user:
                self.user = user
        print(self.host, self.database, self.user)
        self.connection: connection = psycopg2.connect(host=self.host,
                                                       user=self.user,
                                                       password=self.password,
                                                       database=self.database)
        self.cur: cursor = self.connection.cursor(cursor_factory=RealDictCursor)
        # self.my_connection = psycopg2.connect(**self.params)
        # self.my_cursor = self.my_connection.cursor()

    @retry
    def version(self):
        self.cur.execute("SELECT VERSION()")

        version = self.cur.fetchone()
        return "Database version: {}".format(version['version'])

    @retry
    def get_guild(self, guild_id: int):
        self.cur.execute("""
        SELECT * FROM guilds WHERE guild_id = '%s'""",
                         [guild_id])
        return self.cur.fetchone()

    @retry
    def get_guilds(self):
        self.cur.execute("""
        SELECT * FROM guilds """, )
        return self.cur.fetchall()

    @retry
    def get_requests(self, guild_id: int):
        self.cur.execute("""
        SELECT * FROM requests WHERE guild_id = '%s'""",
                         [guild_id])
        return self.cur.fetchone()

    @retry
    def get_requests_where_status_true(self):
        self.cur.execute("""
        SELECT * FROM requests WHERE status is True""")
        return self.cur.fetchall()

    @retry
    def get_resume_fields_order_by_row(self, guild_id: int):
        self.cur.execute("""
        SELECT * FROM resume_fields WHERE guild_id = '%s' ORDER BY field_row""",
                         [guild_id])
        return self.cur.fetchall()

    @retry
    def get_tasks(self, customer_guild_id: int = None, contactor_guild_id: int = None):
        if customer_guild_id is not None:
            self.cur.execute("""
            SELECT * FROM tasks WHERE customer_guild_id = '%s'""",
                             [customer_guild_id])
            tasks: tuple = self.cur.fetchall()
            print(tasks['23'])
            return self.cur.fetchall()
        elif contactor_guild_id is not None:
            self.cur.execute("""
            SELECT * FROM tasks WHERE contactor_guild_id = '%s'""",
                             [contactor_guild_id])
            return self.cur.fetchall()

    @retry
    def get_tasks_order_by_waiting(self, customer_guild_id: int = None, contactor_guild_id: int = None):
        if customer_guild_id is not None:
            self.cur.execute("""
            SELECT * FROM tasks WHERE customer_guild_id = '%s'""",
                             [customer_guild_id])
            tasks: tuple = self.cur.fetchall()
            print(tasks['23'])
            return self.cur.fetchall()
        elif contactor_guild_id is not None:
            self.cur.execute("""
            SELECT * FROM tasks WHERE contactor_guild_id = '%s'""",
                             [contactor_guild_id])
            return self.cur.fetchall()

    @retry
    def get_tasks_by_user_id(self, user_id: int):
        self.cur.execute("""
        SELECT * FROM tasks WHERE customer_id = '%s' OR contactor_id = '%s'""",
                         [user_id, user_id])
        return self.cur.fetchall()

    @retry
    def get_tasks_by_customer_id(self, user_id: int):
        self.cur.execute("""
        SELECT * FROM tasks WHERE customer_id = '%s'""",
                         [user_id])
        return self.cur.fetchall()

    @retry
    def get_tasks_by_contactor_id(self, user_id: int):
        self.cur.execute("""
        SELECT * FROM tasks WHERE contactor_id = '%s'""",
                         [user_id])
        return self.cur.fetchall()

    @retry
    def get_tasks_by_thread_id(self, thread_id: int):
        self.cur.execute("""
        SELECT * FROM tasks WHERE customer_thread_id = '%s' OR contactor_thread_id = '%s'""",
                         [thread_id, thread_id])
        return self.cur.fetchone()

    @retry
    def get_task_by_task_id(self, task_id: int):
        self.cur.execute("""
        SELECT * FROM tasks WHERE task_id = %s""",
                         [task_id])
        return self.cur.fetchone()

    @retry
    def get_tasks_count(self):
        self.cur.execute("""
        SELECT MAX(task_id) FROM tasks """)
        return self.cur.fetchone()

    @retry
    def get_tasks_order_by_price(self):
        self.cur.execute("""
        SELECT * FROM tasks ORDER BY price""")
        return self.cur.fetchall()

    @retry
    def get_guilds_where_tasks_enabled(self):
        self.cur.execute("""
        SELECT * 
        FROM guilds 
        WHERE task_channel_id IS NOT NULL""")
        return self.cur.fetchall()


    @retry
    def get_user(self, discord_id: int):
        self.cur.execute("""
        SELECT * FROM users WHERE discord_uid = '%s'""",
                         [discord_id])
        return self.cur.fetchone()


    @retry
    def get_users(self, discord_id: int):
        self.cur.execute("""
        SELECT * FROM users """,)
        return self.cur.fetchall()

    @retry
    def add_guild(self, guild_id: int, panel_channel_id: int = None, panel_message_id: int = None,
                  citizen_role_id: int = None, subscription: date = None, invite: str = None):
        self.cur.execute("""
        INSERT INTO guilds
        (guild_id, panel_channel_id, panel_message_id, citizen_role_id, subscription_expires, invite)
        VALUES (%s, %s, %s, %s, %s, %s)""",
                         [guild_id, panel_channel_id, panel_message_id, citizen_role_id, subscription, invite])
        return self.connection.commit()

    @retry
    def add_recruiting(self, guild_id: int, recruiting_channel_id: int, recruiting_message_id: int,
                       resume_channel_id: int, status: bool):
        self.cur.execute("""
        INSERT INTO requests
        (guild_id, recruiting_channel_id, recruiting_message_id, resume_channel_id, status)
        VALUES (%s, %s, %s, %s, %s)""",
                         [guild_id, recruiting_channel_id, recruiting_message_id, resume_channel_id, status])
        return self.connection.commit()

    @retry
    def add_resume_field(self, guild_id: int, field_name: str, field_placeholder: str, field_style: bool,
                         field_required: bool, field_row: int):
        self.cur.execute("""
        INSERT INTO resume_fields
        (guild_id, field_name, field_placeholder, field_style, field_required, field_row)
        VALUES (%s, %s, %s, %s, %s, %s)""",
                         [guild_id, field_name, field_placeholder, field_style, field_required, field_row])
        return self.connection.commit()

    @retry
    def add_task(self, guild_id: int, customer_id: str, customer_thread_id: int, item: str, description: str,
                 customer_thread_message_id: int, price: int, global_status: bool = False):
        self.cur.execute("""
        INSERT INTO tasks
        (customer_guild_id, customer_id, customer_thread_id, item, description,
        price, global_status, customer_thread_message_id)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
                         [guild_id, customer_id, customer_thread_id, item, description, price, global_status,
                          customer_thread_message_id])
        return self.connection.commit()

    @retry
    def update_guild(self, guild_id: int, panel_channel_id: int = None, panel_message_id: int = None,
                     citizen_role_id: int = None, subscription_expires: str = None,
                     recruiting_channel_id: int = None,
                     recruiting_message_id: int = None, resume_channel_id: int = None, recruiting_status: bool = None,
                     task_channel_id: int = None, task_issue_thread_id: int = None, task_tag_global_id: int = None,
                     task_tag_waiting_id: int = None, task_tag_in_progress_id: int = None,
                     task_tag_complete_id: int = None):
        self.cur.execute("""
        UPDATE guilds 
        SET panel_channel_id = %s, panel_message_id = %s, citizen_role_id = %s, subscription_expires = %s,
        recruiting_channel_id = %s, recruiting_message_id = %s, resume_channel_id = %s, recruiting_status = %s,
        task_channel_id = %s, task_issue_thread_id = %s, task_tag_global_id = %s, task_tag_waiting_id = %s,
        task_tag_in_progress_id = %s, task_tag_complete_id = %s
        WHERE guild_id = %s
        """,
                         [panel_channel_id, panel_message_id, citizen_role_id,  subscription_expires,
                          recruiting_channel_id, recruiting_message_id, resume_channel_id, recruiting_status,
                          task_channel_id, task_issue_thread_id, task_tag_global_id, task_tag_waiting_id,
                          task_tag_in_progress_id, task_tag_complete_id,
                          guild_id])
        return self.connection.commit()

    @retry
    def update_panel(self, guild_id: int, panel_channel_id: int, panel_message_id: int):
        self.cur.execute("""
        UPDATE guilds
        SET panel_channel_id = %s, panel_message_id = %s
        WHERE guild_id = %s
        """, [panel_channel_id, panel_message_id,  guild_id])
        return self.connection.commit()

    @retry
    def update_citizen_role_id(self, guild_id: int, citizen_role_id: int):
        self.cur.execute("""
        UPDATE guilds
        SET citizen_role_id = %s
        WHERE guild_id = %s
        """, [citizen_role_id, guild_id])
        return self.connection.commit()

    @retry
    def update_subscription(self, guild_id: int, subscription_expires: str):
        self.cur.execute("""
        UPDATE guilds
        SET subscription_expires = %s
        WHERE guild_id = %s
        """, [subscription_expires, guild_id])
        return self.connection.commit()

    @retry
    def update_invite(self, guild_id: int, invite: str):
        self.cur.execute("""
        UPDATE guilds
        SET invite = %s
        WHERE guild_id = %s
        """, [invite, guild_id])
        return self.connection.commit()

    @retry
    def update_recruiting(self, guild_id: int, recruiting_channel_id: int, recruiting_message_id: int,
                          resume_channel_id: int, status: bool):
        self.cur.execute("""
        UPDATE requests 
        SET recruiting_channel_id = %s, recruiting_message_id = %s, resume_channel_id = %s, status = %s
        WHERE guild_id = %s
        """,
                         [recruiting_channel_id, recruiting_message_id, resume_channel_id, status, guild_id])
        return self.connection.commit()

    @retry
    def update_resume_field(self, guild_id: int, field_name: str, field_placeholder: str, field_style: bool,
                            field_required: bool, field_row: int):
        self.cur.execute("""
        UPDATE resume_fields 
        SET field_name = %s, field_placeholder = %s, field_style = %s, field_required = %s, field_row = %s
        WHERE guild_id = %s
        """,
                         [field_name, field_placeholder, field_style, field_required, field_row, guild_id])
        return self.connection.commit()

    @retry
    def update_resume_field_row(self, guild_id: int, field_name: str, field_placeholder: str, field_style: bool,
                                field_required: bool, field_row: int):
        self.cur.execute("""
        UPDATE resume_fields 
        SET field_name = %s, field_placeholder = %s, field_style = %s, field_required = %s
        WHERE guild_id = %s
        AND field_row = %s
        """,
                         [field_name, field_placeholder, field_style, field_required, guild_id, field_row])
        return self.connection.commit()

    @retry
    def update_recruiting_status(self, guild_id: int, status: bool):
        self.cur.execute("""
        UPDATE requests 
        SET status = %s
        WHERE guild_id = %s
        """,
                         [status, guild_id])
        return self.connection.commit()

    @retry
    def update_guild_task(self, guild_id: int, task_channel_id: int, task_issue_thread_id: int, task_tag_global_id: int,
                          task_tag_waiting_id: int, task_tag_in_progress_id: int, task_tag_complete_id: int,
                          task_webhook_url: str):
        self.cur.execute("""
        UPDATE guilds
        SET task_channel_id = %s, task_issue_thread_id = %s,  task_tag_global_id = %s,
         task_tag_waiting_id = %s, task_tag_in_progress_id = %s, task_tag_complete_id = %s, task_webhook_url = %s
        WHERE guild_id = %s 
        """,
                         [task_channel_id, task_issue_thread_id, task_tag_global_id, task_tag_waiting_id,
                          task_tag_in_progress_id, task_tag_complete_id, task_webhook_url, guild_id])
        return self.connection.commit()

    @retry
    def update_task_accept(self, contactor_id: int, contactor_thread_id: int, contactor_guild_id: int,
                           contactor_thread_message_id: int, customer_thread_id: int):
        self.cur.execute("""
        UPDATE tasks
        SET contactor_id = %s, contactor_thread_id = %s,  contactor_guild_id = %s, contactor_thread_message_id = %s
        WHERE customer_thread_id = %s 
        """,
                         [contactor_id, contactor_thread_id, contactor_guild_id, contactor_thread_message_id,
                          customer_thread_id])
        return self.connection.commit()

    @retry
    def update_citizen_role_id(self, guild_id: int, citizen_role_id: int = None):
        self.cur.execute("""
        UPDATE guilds 
        SET citizen_role_id = %s
        WHERE guild_id = %s
        """,
                         [citizen_role_id, guild_id])
        return self.connection.commit()

    @retry
    def delete_guild(self, guild_id: int):
        self.cur.execute("""
        DELETE FROM guilds 
        WHERE guild_id = %s
        """,
                         [guild_id])
        return self.connection.commit()

    @retry
    def delete_recruiting(self, guild_id: int):
        self.cur.execute("""
        DELETE FROM requests 
        WHERE guild_id = %s
        """,
                         [guild_id])
        return self.connection.commit()

    @retry
    def delete_resume_field(self, guild_id: int, row: int):
        self.cur.execute("""
        DELETE FROM resume_fields 
        WHERE guild_id = %s 
        AND field_row = %s
        """,
                         [guild_id, row])
        return self.connection.commit()

    @retry
    def add_user(self, discord_uid: int, minecraft_uid: str = None):
        self.cur.execute("""
        INSERT INTO users (discord_uid, minecraft_uid)
        VALUES (%s, %s)""",
                         [discord_uid, minecraft_uid])
        return self.connection.commit()


sql = Database(host=env.get('DB_HOST'),
               user=env.get('DB_USER'),
               password=env.get('DB_PASS'),
               database=env.get('DB_NAME'))
