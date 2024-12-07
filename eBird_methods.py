import sqlite3 as sql
import peewee as pw
import requests
from abc import ABC, abstractmethod
from typing import Callable, TypeVar
#Note to self: download when not on train
#from deprecated import deprecated

from database_schema import Bird, BirdSubspecies, Superorganisation, Suborganisation, Source, Pin

from hidden_keys import API_Keys

#Defining some type shorthands for type hinting elsewhere
Response = requests.models.Response
return_type = TypeVar('return_type')
return_type_2 = TypeVar('return_type_2')


class APIClass:
    def status_test(self, response: Response, 
                        success_function: Callable[...,return_type], 
                        failure_function: Callable[...,return_type_2], 
                        *args) -> return_type | return_type_2 | None:
        if response.status_code == 200:
            data: list[dict] = response.json()
            return success_function(data, *args)
        if not response:
            return failure_function(response.status_code, *args)
        return self.throw_connection_error(response.status_code)

    def throw_connection_error(status_code: int) -> None:
        print('Response code: ' + status_code)

class eBirdWeb(APIClass):
    def __init__(self):
        self.api_key: str = API_Keys.get('EBIRD_API_KEY')

    def get_data(self) -> Response:
        url: str = "https://api.ebird.org/v2/ref/taxonomy/ebird?fmt=json&locale=en_UK"
        response: Response = requests.request("GET", url, headers={'X-eBirdApiToken': self.api_key}, data={})
        return response

class pinDatabaseInterface(ABC):
    def __init__(self):
        self.open_connection()

    @abstractmethod
    def open_connection(self) -> None:
        pass

    @abstractmethod
    def close_connection(self) -> None:
        pass

    @abstractmethod
    def initialise_database(self) -> None:
        pass

    @abstractmethod
    def update_ebird_data(self, api_data:list[dict]) -> None:
        pass

    @abstractmethod
    def add_subspecies(self, subspecies_data: dict) -> None:
        pass

    @abstractmethod
    def add_new_pin(self, pin_data: dict) -> None:
        pass

    @abstractmethod
    def add_new_source(self, source_data: dict) -> None:
        pass

    @abstractmethod
    def add_new_superorganisation(self,superorganisation_data:dict) -> None:
        pass

    @abstractmethod
    def add_new_suborganisation(self,suborganisation_data:dict) -> None:
        pass

class pinDatabaseSQLite3(pinDatabaseInterface):
    class table:
        def __init__(self, name: str, table_fields: str, table_constraints: str):
            self.name: str = name
            self.table_fields: str = table_fields
            self.table_constraints: str = table_constraints
            self.description: str = f'{name}({table_fields}, {table_constraints})'
            self.no_of_cols: int = self.table_fields.count(',')+1
            self.sql_create: str = f'CREATE TABLE IF NOT EXISTS {self.name}'
            self.sql_drop: str = f'DROP TABLE IF EXISTS {self.name}'
            self.sql_insert: str = f'INSERT OR IGNORE INTO {self.name} VALUES({'?,'*{self.no_of_cols-1}}?)'

    def __init__(self):
        self.bird_table = self.table(name = 'Bird', 
                                    table_fields = """eBird_code TEXT NOT NULL PRIMARY KEY, 
                                                      common_name TEXT NOT NULL, 
                                                      family_common_name TEXT NOT NULL, 
                                                      order TEXT NOT NULL, 
                                                      family TEXT NOT NULL, 
                                                      genus TEXT NOT NULL, 
                                                      species TEXT NOT NULL""", 
                                    table_constraints = '')
        self.bird_subspecies_table = self.table(name = 'BirdSubspecies',
                                                table_fields="""eBird_code TEXT NOT NULL PRIMARY KEY, 
                                                                common_name TEXT NOT NULL, 
                                                                species TEXT NOT NULL""",
                                                table_constraints='FOREIGN KEY(species) REFERENCES bird(eBird_code)')
        self.superorganisation_table = self.table(name = 'Superorganisation',
                                                table_fields="""name TEXT NOT NULL PRIMARY KEY, 
                                                                  short_name TEXT, 
                                                                  description TEXT, 
                                                                  website TEXT""",
                                                table_constraints='')
        self.source_table = self.table(name='Source',
                                    table_fields="""name TEXT NOT NULL PRIMARY KEY, 
                                                       short_name TEXT, 
                                                       description TEXT, 
                                                       parent TEXT, 
                                                       website TEXT""",
                                    table_constraints='FOREIGN KEY(parent) REFERENCES Superorganisation(name)')
        self.suborganisation_table = self.table(name='Suborganisation',
                                                table_fields="""name TEXT NOT NULL PRIMARY KEY, 
                                                                short_name TEXT, 
                                                                description TEXT, 
                                                                parent TEXT NOT NULL, 
                                                                website TEXT""",
                                                table_constraints='FOREIGN KEY(parent) REFERENCES Source(name)')
        self.pin_table = self.table(name = 'Pin',
                                    table_fields="""id INTEGER PRIMARY KEY AUTOINCREMENT, 
                                                    species TEXT NOT NULL, 
                                                    subspecies TEXT, 
                                                    source TEXT NOT NULL, 
                                                    suborganisation TEXT""",
                                    table_constraints="""FOREIGN KEY(species) REFERENCES Bird(eBird_code), 
                                                         FOREIGN KEY(subspecies) REFERENCES BirdSubspecies(eBird_code), 
                                                         FOREIGN KEY(source) REFERENCES Source(name), 
                                                         FOREIGN KEY(suborganisation) REFERENCES Suborganisation(name)""")
        super().__init__()

    def open_connection(self) -> None:
        self.connection: sql.Connection = sql.connect('pinDatabase.db')
        self.cursor: sql.Cursor = self.connection.cursor()

    def close_connection(self) -> None:
        self.connection.close()

    def initialise_database(self) -> None:
        self.cursor.execute(self.bird_table.sql_create)
        self.cursor.execute(self.bird_subspecies_table.sql_create)
        self.cursor.execute(self.superorganisation_table.sql_create)
        self.cursor.execute(self.source_table.sql_create)
        self.cursor.execute(self.suborganisation_table.sql_create)
        self.cursor.execute(self.pin_table.sql_create)
        self.connection.commit()

    def clear_ebird_table(self) -> None:
        self.cursor.execute(self.bird_table.sql_drop)
        self.cursor.execute(self.bird_table.sql_create)
        self.connection.commit()

    def process_ebird_data(self, api_data: list[dict]) -> list[dict]:
        processed_data: list = []
        for species_profile in filter(lambda w: w['category'] == 'species', api_data):
            processed_data.append({'eBird_code': species_profile['speciesCode'], 
                                    'common_name': species_profile['comName'], 
                                    'family_common_name': species_profile['familyComName'], 
                                    'order': species_profile['order'], 
                                    'family': species_profile['familySciName'], 
                                    'genus': species_profile['sciName'].split()[0], 
                                    'species': species_profile['sciName'].split()[1]})

    def update_ebird_data(self, api_data: list[dict]) -> None:
        self.clear_ebird_table()
        processed_data: list[dict] = self.process_ebird_data(api_data)
        for bird in processed_data:
            self.cursor.execute(self.bird_table.sql_insert, bird)
        self.connection.commit()

    def add_subspecies(self, subspecies_data: dict) -> None:
        self.cursor.execute(self.bird_subspecies_table.sql_insert, subspecies_data)
        self.connection.commit()

    def add_new_pin(self, pin_data: dict) -> None:
        self.cursor.execute(self.bird_table.sql_insert, pin_data)
        self.connection.commit()

    def add_new_source(self, source_data: dict) -> None:
        self.cursor.execute(self.source_table.sql_insert, source_data)
        self.connection.commit()

    def add_new_superorganisation(self, superorganisation_data: dict) -> None:
        self.cursor.execute(self.superorganisation_table.sql_insert, superorganisation_data)
        self.connection.commit()

    def add_new_suborganisation(self,suborganisation_data: dict) -> None:
        self.cursor.execute(self.suborganisation_table.sql_insert, suborganisation_data)
        self.connection.commit()

class pinDatabasePeewee(pinDatabaseInterface):
    def __init__(self):
        self.db = pw.SQliteDatabase('pin_database.db')
        super().__init__()

    def open_connection(self) -> None:
        self.db.connect()

    def close_connection(self) -> None:
        self.db.close()

    def initialise_database(self) -> None:
        self.db.create_tables([Bird, BirdSubspecies, Superorganisation, Suborganisation, Source, Pin])

    def clear_ebird_table(self) -> None:
        self.db.drop_tables([Bird])
        self.db.create_tables([Bird])

    def process_ebird_data(self, api_data: list[dict]) -> list[dict]:
        processed_data: list = []
        for species_profile in filter(lambda w: w['category'] == 'species', api_data):
            processed_data.append({'eBird_code': species_profile['speciesCode'], 
                                    'common_name': species_profile['comName'], 
                                    'family_common_name': species_profile['familyComName'], 
                                    'order': species_profile['order'], 
                                    'family': species_profile['familySciName'], 
                                    'genus': species_profile['sciName'].split()[0], 
                                    'species': species_profile['sciName'].split()[1]})

    def update_ebird_data(self, api_data:list[dict]) -> None:
        self.clear_ebird_table()
        processed_data: list[dict] = self.process_ebird_data(api_data)
        for bird in processed_data:
            Bird.create(**bird)

    def add_subspecies(self, subspecies_data: dict) -> None:
        BirdSubspecies.create(**subspecies_data)

    def add_new_pin(self, pin_data: dict) -> None:
        Pin.create(**pin_data)

    def add_new_source(self, source_data: dict) -> None:
        Source.create(**source_data)

    def add_new_superorganisation(self, superorganisation_data: dict) -> None:
        Superorganisation.create(**superorganisation_data)

    def add_new_suborganisation(self,suborganisation_data: dict) -> None:
        Suborganisation.create(**suborganisation_data)

def pinDatabaseFactory() -> pinDatabaseInterface:
    return pinDatabasePeewee()

class eBirdBridge:
    def __init__(self) ->  None:
        self.eBirdWeb = eBirdWeb()
        self.eBirdLocalDB = pinDatabaseFactory()

    def update_database(self) -> None:
        response: Response = self.eBirdWeb.get_data()
        self.eBirdWeb.status_test(api_response=response, 
                                    success_function=self.eBirdLocalDB.update_ebird_data, 
                                    failure_function=self.eBirdWeb.throw_connection_error)
        
    def close_connection(self) -> None:
        self.eBirdLocalDB.close_connection()
