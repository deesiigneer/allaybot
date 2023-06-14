import psycopg2
from psycopg2 import DatabaseError, extensions
from functools import wraps
from time import sleep
from psycopg2._psycopg import connection, cursor
from os import environ as env

def retry(f):
    @wraps(f)
    def wrapper(*args, **kw):
        cls = args[0]
        for x in range(cls._reconnectTries):
            # print(x, cls._reconnectTries)
            try:
                return f(*args, **kw)
            except (psycopg2.InterfaceError, psycopg2.OperationalError) as e:
                print ("\nDatabase Connection [InterfaceError or OperationalError]")
                print ("Idle for %s seconds" % (cls._reconnectIdle))
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
        self.cur: cursor = self.connection.cursor()
        # self.my_connection = psycopg2.connect(**self.params)
        # self.my_cursor = self.my_connection.cursor()

    @retry
    def version(self):
        self.cur.execute("SELECT VERSION()")

        version = self.cur.fetchone()

        return "Database version: {}".format(version[0])

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
    def get_recruiting(self, guild_id: int):
        self.cur.execute("""
        SELECT * FROM recruitings WHERE guild_id = '%s'""",
                         [guild_id])
        return self.cur.fetchone()

    @retry
    def get_resume_fields_order_by_row(self, guild_id: int):
        self.cur.execute("""
        SELECT * FROM resume_fields WHERE guild_id = '%s' ORDER BY field_row""",
                         [guild_id])
        return self.cur.fetchall()

    @retry
    def get_tasks(self, guild_id: int):
        self.cur.execute("""
        SELECT * FROM tasks WHERE guild_id = '%s'""",
                         [guild_id])
        return self.cur.fetchall()

    @retry
    def get_user(self, discord_id: int):
        self.cur.execute("""
        SELECT * FROM users WHERE discord_uid = '%s'""",
                         [discord_id])
        return self.cur.fetchone()

    @retry
    def add_guild(self, guild_id: int, panel_channel_id: int = None, panel_message_id: int = None,
                  citizen_role_id: int = None):
        self.cur.execute("""
        INSERT INTO guilds
        (guild_id, panel_channel_id, panel_message_id, citizen_role_id)
        VALUES (%s, %s, %s, %s)""",
                         [guild_id, panel_channel_id, panel_message_id, citizen_role_id])
        return self.connection.commit()

    @retry
    def add_recruiting(self, guild_id: int, recruiting_channel_id: int, recruiting_message_id: int,
                       resume_channel_id: int, status: bool):
        self.cur.execute("""
        INSERT INTO recruitings
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
    def update_guild(self, guild_id: int, panel_channel_id: int = None, panel_message_id: int = None,
                     citizen_role_id: int = None):
        self.cur.execute("""
        UPDATE guilds 
        SET panel_channel_id = %s, panel_message_id = %s, citizen_role_id = %s
        WHERE guild_id = %s
        """,
                         [panel_channel_id, panel_message_id, citizen_role_id, guild_id])
        return self.connection.commit()

    @retry
    def update_recruiting(self, guild_id: int, recruiting_channel_id: int, recruiting_message_id: int,
                          resume_channel_id: int, status: bool):
        self.cur.execute("""
        UPDATE recruitings 
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
        UPDATE recruitings 
        SET status = %s
        WHERE guild_id = %s
        """,
                         [status, guild_id])
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
        DELETE FROM recruitings 
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
