import datetime

import ydb

from .database import Database


class YandexDatabase(Database):
    """
    MySQL database class.
    """

    def __init__(self, connection_params, table_name):
        """
        Initializes the Yandex database object.
        :param connection_params: Connection parameters dictionary: {endpoint=, database=, credentials=}
        :param table_name
        """
        driver_config = ydb.DriverConfig(**connection_params)

        driver = ydb.Driver(driver_config)

        try:
            driver.wait(timeout=5)
            print('Successfully connected to YDB')
        except:
            print('Connect failed to YDB')
            print(driver.discovery_debug_details())
            return

        self.session = driver.table_client.session().create()

        self.table_name = table_name
        # self.create_tables()

    def add(self, entity):
        """
        Adds a new entity.
        :param entity: Dictionary containing the values of the entity to be added.
        """
        entity_values = list(entity.values())

        entity_values = self.prepare_values(entity_values)

        columns = ', '.join(entity.keys())
        values = ', '.join(entity_values)

        query = f"INSERT INTO {self.table_name} ({columns}) VALUES ({values})"
        result = self.session.transaction().execute(query, commit_tx=True)

        if result is not None:
            return entity['id']
        else:
            return None

    def update(self, entity_id, entity):
        """
        Updates an existing entity.
        :param entity_id: The ID of the entity to be updated.
        :param entity: List of new values of the entity.
        """
        entity_id = "'" + entity_id + "'"

        entity_values = list(entity.values())

        entity_values = self.prepare_values(entity_values)

        set_query = ', '.join([f'{k} = %s' for k in entity.keys()])

        query = f"UPDATE {self.table_name} SET {set_query} WHERE id = %s" % tuple(entity_values + [entity_id])
        result = self.session.transaction().execute(query, commit_tx=True)

        if result is not None:
            return True
        else:
            return None

    def delete(self, entity_id):
        """
        Deletes an existing entity.
        :param entity_id: The ID of the entity to be deleted.
        """
        self.session.execute_scheme(f"DELETE FROM {self.table_name} WHERE id = %s", (entity_id,))

    def get_one(self, select, filter):
        """
        Retrieves a single entity.
        :param select: A list of columns to be selected.
        :param filter: A dictionary containing the filter conditions.
        """
        filter_values = list(filter.values())

        filter_values = self.prepare_values(filter_values)

        select_query = ', '.join(select)
        filter_query = ' AND '.join([f'{k} == %s' for k in filter.keys()])

        query = f"SELECT {select_query} FROM {self.table_name} WHERE {filter_query}" % tuple(filter_values)
        result = self.session.transaction().execute(query, commit_tx=True)

        rows = result[0].rows

        if rows and len(rows) > 0:
            row = rows[0]

            for k, v in row.items():
                if isinstance(v, (bytes, bytearray)):
                    row[k] = v.decode('utf8')

            return row
        else:
            return None

    def get_list(self, select, filter):
        """
        Retrieves list of entities.
        :param select: A list of columns to be selected.
        :param filter: A dictionary containing the filter conditions.
        """
        filter_values = list(filter.values())

        filter_values = self.prepare_values(filter_values)

        select_query = ', '.join(select)
        filter_query = ' AND '.join([f'{k} == %s' for k in filter.keys()])

        query = f"SELECT {select_query} FROM {self.table_name} WHERE {filter_query}" % tuple(filter_values)
        result = self.session.transaction().execute(query, commit_tx=True)

        rows = result[0].rows

        if rows and len(rows) > 0:

            for i, row in enumerate(rows):
                for k, v in row.items():
                    if isinstance(v, (bytes, bytearray)):
                        rows[i][k] = v.decode('utf8')

            return rows
        else:
            return []

    def create_tables(self):
        script = '''
        CREATE TABLE users (
            id String NOT NULL,
            account_id Uint64,
            chat_id Uint64,
            name String,
            phone String,
            created_at Datetime,
            PRIMARY KEY (id)
        );
        CREATE TABLE requests (
            id String NOT NULL,
            stage String,
            user_id String,
            operation_id String,
            file_name String,
            attempt Uint64,
            created_at Datetime,
            PRIMARY KEY (id)
        )
        '''
        sql_commands = script.split(';')

        for command in sql_commands:
            self.session.execute_scheme(command)

    def prepare_values(self, values):
        for i, val in enumerate(values):
            if isinstance(val, str):
                val = "'" + val.replace("'", "\"") + "'"
            if isinstance(val, datetime.datetime):
                val = f"DATETIME('{val.strftime('%Y-%m-%dT%H:%M:%SZ')}')"

            values[i] = str(val)

        return values
