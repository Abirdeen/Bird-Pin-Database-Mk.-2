#SQL modules
import sqlite3 as sql
import peewee as pw
#API module
import requests
#Fuzzy searching
from fuzzywuzzy import fuzz
#Typing, decorators, logging
from abc import ABC, abstractmethod
from typing import Callable, TypeVar, TypeAlias
import logging
#Timing functions
import time
#Note to self: download when not on train
#from deprecated import deprecated

from hidden_keys import API_Keys

from pin_database_schema import DATABASE, Bird, BirdSubspecies, Superorganisation, Suborganisation, Source, Pin, table

#Type shorthands for type hinting
Response = requests.models.Response
return_type = TypeVar('return_type')
return_type_2 = TypeVar('return_type_2')
dict_with_score: TypeAlias = tuple[dict,int]


logger = logging.getLogger('eBird_methods')

def logged(print_args: bool = True):
    def logged_decorator(func):
        def log_wrapper(*args, **kwargs):
            start = time.time()
            start_message = f'Started running {func.__name__}'
            if print_args:
                start_message += f' with the arguments \n {args}, {kwargs}'
            logger.info(start_message)
            result = func(*args, **kwargs)
            end = time.time()
            end_message = f'Finished running {func.__name__}'
            try:
                result_length = len(result)
            except TypeError:
                result_length = 0
            if result_length > 20:
                end_message += f' with result of length {result_length}'
            elif not result == None:
                end_message += f' with the result \n {result}'
            end_message += f' \n taking {end - start} seconds.'
            logger.info(end_message)
            return result
            
        return log_wrapper
    return logged_decorator

class APIClass:
    def status_test(self, response: Response, 
                        success_function: Callable[[list[dict]],return_type], 
                        failure_function: Callable[[int],return_type_2], 
                        *args) -> return_type | return_type_2 | None:
        if response.status_code == 200:
            data: list[dict] = response.json()
            return success_function(data, *args)
        if not response:
            return failure_function(response.status_code, *args)
        self.throw_connection_error(response.status_code)
        return None

    def throw_connection_error(self, status_code: int) -> None:
        print(f'Response code: {status_code}')

class eBirdWeb(APIClass):
    def __init__(self) -> None:
        self.api_key: str | None = API_Keys.get('EBIRD_API_KEY')
    
    def __repr__(self):
        return '(class) eBird API manager'

    def get_data(self) -> Response:
        url: str = "https://api.ebird.org/v2/ref/taxonomy/ebird?fmt=json&locale=en_UK"
        response: Response = requests.request("GET", url, headers={'X-eBirdApiToken': self.api_key}, data={})
        return response
    
    def get_subspecies_codes(self, species_code: str) -> Response:
        url: str = f'https://api.ebird.org/v2/ref/taxon/forms/{species_code}'
        response: Response = requests.request("GET", url, headers={'X-eBirdApiToken': self.api_key}, data={})
        return response


class pinDatabaseInterface(ABC):
    def __init__(self) -> None:
        self.open_connection()
        self.bird_table: table
        self.bird_subspecies_table: table
        self.superorganisation_table: table
        self.source_table: table
        self.suborganisation_table: table
        self.pin_table: table

    def __repr__(self):
        return '(class) Local database manager'

    @abstractmethod
    def open_connection(self) -> None:
        pass

    def initialise_database(self) -> None:
        self.bird_table.create()
        self.bird_subspecies_table.create()
        self.suborganisation_table.create()
        self.source_table.create()
        self.suborganisation_table.create()
        self.pin_table.create()

    def clear_ebird_table(self) -> None:
        self.bird_table.drop()
        self.bird_table.create()

    def process_ebird_data(self, api_data: list[dict]) -> list[dict]:
        processed_data: list[dict] = []
        for species_profile in filter(lambda w: w['category'] == 'species', api_data):
            processed_data.append({'eBird_code': species_profile['speciesCode'], 
                                    'common_name': species_profile['comName'], 
                                    'family_common_name': species_profile['familyComName'], 
                                    'bird_order': species_profile['order'], 
                                    'family': species_profile['familySciName'], 
                                    'genus': species_profile['sciName'].split()[0], 
                                    'species': species_profile['sciName'].split()[1]})
        return processed_data

    def update_ebird_data(self, api_data: list[dict]) -> None:
        self.clear_ebird_table()
        processed_data: list[dict] = self.process_ebird_data(api_data)
        self.bird_table.add_data(processed_data)

    @abstractmethod
    def close_connection(self) -> None:
        pass

class pinDatabaseSQLite3(pinDatabaseInterface):
    class sql_table(table):
        def __init__(self, 
                     connection: sql.Connection, cursor: sql.Cursor, 
                     name: str, 
                     table_fields: str, table_constraints: str | None) -> None:
            self.name: str = name
            self.connection = connection
            self.cursor = cursor
            self.cursor.row_factory = self.dict_factory
            self.table_fields: str = table_fields
            self.table_constraints: str | None = table_constraints
            desc: str
            if table_constraints == None:
                desc = f'{name}({table_fields})'
            else:
                desc = f'{name}({table_fields}, {table_constraints})'
            self.description = desc
            self.no_of_cols: int = self.table_fields.count(',')+1
            self.sql_create: str = f'CREATE TABLE IF NOT EXISTS {self.description}'
            self.sql_drop: str = f'DROP TABLE IF EXISTS {self.name}'
            self.sql_insert: str = f'INSERT OR IGNORE INTO {self.name} VALUES({"?,"*(self.no_of_cols-1)}?)'
            self.sql_select: str = f'SELECT * FROM {self.name}'

        def dict_factory(self, cursor, row):
            fields = [column[0] for column in cursor.description]
            return {key: value for key, value in zip(fields, row)}

        def create(self) -> None:
            self.cursor.execute(self.sql_create)
            self.connection.commit()

        def drop(self) -> None:
            self.cursor.execute(self.sql_drop)
            self.connection.commit()

        def add_data(self, data: list[dict]) -> None:
            data_as_tuples: list[tuple] = []
            for row in data:
                data_as_tuples.append(tuple([value for value in row.values()]))
            self.cursor.executemany(self.sql_insert, data_as_tuples)
            self.connection.commit()

        def get_data(self) -> list[dict]:
            return self.cursor.execute(self.sql_select).fetchall()

    def __init__(self) -> None:
        super().__init__()
        self.bird_table = self.sql_table(name = 'Bird', 
                                    connection=self.connection, cursor=self.cursor, 
                                    table_fields = """eBird_code TEXT NOT NULL PRIMARY KEY, 
                                                      common_name TEXT NOT NULL, 
                                                      family_common_name TEXT NOT NULL, 
                                                      bird_order TEXT NOT NULL, 
                                                      family TEXT NOT NULL, 
                                                      genus TEXT NOT NULL, 
                                                      species TEXT NOT NULL""", 
                                    table_constraints = None)
        self.bird_subspecies_table = self.sql_table(name = 'BirdSubspecies', 
                                                connection=self.connection, cursor=self.cursor,
                                                table_fields="""eBird_code TEXT NOT NULL PRIMARY KEY, 
                                                                common_name TEXT NOT NULL, 
                                                                species TEXT NOT NULL""",
                                                table_constraints='FOREIGN KEY(species) REFERENCES bird(eBird_code)')
        self.superorganisation_table = self.sql_table(name = 'Superorganisation', 
                                                connection=self.connection, cursor=self.cursor,
                                                table_fields="""name TEXT NOT NULL PRIMARY KEY, 
                                                                  short_name TEXT, 
                                                                  description TEXT, 
                                                                  website TEXT""",
                                                table_constraints=None)
        self.source_table = self.sql_table(name='Source', 
                                    connection=self.connection, cursor=self.cursor,
                                    table_fields="""name TEXT NOT NULL PRIMARY KEY, 
                                                       short_name TEXT, 
                                                       description TEXT, 
                                                       parent TEXT, 
                                                       website TEXT""",
                                    table_constraints='FOREIGN KEY(parent) REFERENCES Superorganisation(name)')
        self.suborganisation_table = self.sql_table(name='Suborganisation', 
                                                connection=self.connection, cursor=self.cursor,
                                                table_fields="""name TEXT NOT NULL PRIMARY KEY, 
                                                                short_name TEXT, 
                                                                description TEXT, 
                                                                parent TEXT NOT NULL, 
                                                                website TEXT""",
                                                table_constraints='FOREIGN KEY(parent) REFERENCES Source(name)')
        self.pin_table = self.sql_table(name = 'Pin', 
                                    connection=self.connection, cursor=self.cursor,
                                    table_fields="""id INTEGER PRIMARY KEY AUTOINCREMENT, 
                                                    species TEXT NOT NULL, 
                                                    subspecies TEXT, 
                                                    source TEXT NOT NULL, 
                                                    suborganisation TEXT""",
                                    table_constraints="""FOREIGN KEY(species) REFERENCES Bird(eBird_code), 
                                                         FOREIGN KEY(subspecies) REFERENCES BirdSubspecies(eBird_code), 
                                                         FOREIGN KEY(source) REFERENCES Source(name), 
                                                         FOREIGN KEY(suborganisation) REFERENCES Suborganisation(name)""")

    def open_connection(self) -> None:
        self.connection: sql.Connection = sql.connect(DATABASE)
        self.cursor: sql.Cursor = self.connection.cursor()
    
    def close_connection(self) -> None:
        self.connection.close()

class pinDatabasePeewee(pinDatabaseInterface):
    class peewee_table(table):
        def __init__(self, database: pw.SqliteDatabase, model: type[pw.Model]):
            self.db = database
            self.model = model

        def create(self) -> None:
            self.db.create_tables([self.model])

        def drop(self) -> None:
            self.db.drop_tables([self.model])

        def add_data(self, data: list[dict]) -> None:
            #Chunk the data to get around SQL insert_many limits
            chunks = [data[x:x+100] for x in range(0, len(data), 100)]
            for chunk in chunks:
                self.model.insert_many(chunk).execute()

        @logged()
        def get_data(self) -> list[dict]:
            query = self.model.select()
            data: list[dict] = []
            for row in query.dicts().iterator():
                data.append(row)
            return data

    def __init__(self) -> None:
        self.db: pw.SqliteDatabase = pw.SqliteDatabase(DATABASE)
        super().__init__()
        self.bird_table = self.peewee_table(self.db, Bird)
        self.bird_subspecies_table = self.peewee_table(self.db, BirdSubspecies)
        self.superorganisation_table = self.peewee_table(self.db, Superorganisation)
        self.source_table = self.peewee_table(self.db, Source)
        self.suborganisation_table = self.peewee_table(self.db, Suborganisation)
        self.pin_table = self.peewee_table(self.db, Pin)

    def open_connection(self) -> None:
        self.db.connect()

    def close_connection(self) -> None:
        self.db.close()

def pinDatabaseFactory() -> pinDatabaseInterface:
    return pinDatabaseSQLite3()
    # return pinDatabasePeewee()

class eBirdBridge:
    def __init__(self) ->  None:
        self.eBirdWeb = eBirdWeb()
        self.LocalDBInterface: pinDatabaseInterface = pinDatabaseFactory()

    def __repr__(self):
        return '(class) eBird Bridge'

    def update_database(self) -> None:
        response: Response = self.eBirdWeb.get_data()
        self.eBirdWeb.status_test(response=response, 
                                    success_function=self.LocalDBInterface.update_ebird_data, 
                                    failure_function=self.eBirdWeb.throw_connection_error)
        
    def retrieve_subspecies(self):
        pass
   
    def close_connection(self) -> None:
        self.LocalDBInterface.close_connection()


class userBridge:
    @logged(print_args=False)
    def fuzzy_search(self, test_name: str, 
                            database: list[dict], 
                            check_type: str,
                            threshold: int = 80) -> list[dict_with_score]:
        '''
        >>> userLocalDBBridge.species_fuzzy_search(test_name = 'Maroon Pigeon', database = [{'common_name': 'Short-toed Coucal'}, {'common_name': 'Rameron Pigeon'}], check_type = 'common_name')
        [({'common_name': 'Rameron Pigeon'},85)]
        '''
        matching_data: list[dict_with_score] = []
        for data in database:
            ratio = fuzz.partial_ratio(test_name,data[check_type])
            if ratio >= threshold:
                matching_data.append((data,ratio))
        return matching_data

class userLocalDBBridge(userBridge):
    def __init__(self):
        self.LocalDBInterface: pinDatabaseInterface = pinDatabaseFactory()
        self.eBirdDB: table = self.LocalDBInterface.bird_table
        super().__init__()

    def __repr__(self):
        return '(class) Local Database Bridge'

    def fuzzy_search_species_ebird(self, test_name: str, threshold: int = 80) -> list[dict_with_score]:
        database: list[dict] = self.eBirdDB.get_data()
        return self.fuzzy_search(test_name=test_name, database=database, check_type='common_name', threshold=threshold)

@logged()
def main(auto_test: bool = False):
    if auto_test:
        import doctest
        doctest.testmod()
        return None
    
    ebridge = eBirdBridge()
    ubridge = userLocalDBBridge()

    # ebridge.update_database()
    
    print(ebridge.eBirdLocalDB.bird_table.get_data()[1000])
    
    # data = {'eBird_code': 'ostric2', 'common_name': 'Common Ostrich', 'family_common_name': 'Ostriches', 'bird_order': 'Struthioniformes', 'family': 'Struthionidae', 'genus': 'Struthio', 'species': 'camelus'}
    #
    print(ubridge.species_fuzzy_search('Maroon Pigeon', ebridge.eBirdLocalDB.bird_table.get_data(), 80))
    # 
    # api = eBirdWeb()
    # print(','.join(api.get_subspecies_codes('cangoo').json()))
    pass
    
if __name__ == '__main__':
    logging.basicConfig(filename='eBird_methods.log', level=logging.INFO)
    logger.info(f'---------------------------------------- \n begin log')
    try:
        main(True)
    except Exception as err:
        logger.exception(f'Got exception on main handler: {err}')
        raise
    finally:
        logger.info(f'end log \n ----------------------------------------')
