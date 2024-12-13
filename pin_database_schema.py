import peewee as pw

from abc import ABC, abstractmethod
from typing import Callable, TypeVar

DATABASE: str = 'pin_database.db'

class table(ABC):
        
        def __repr__(self):
            return '(class) table'

        @abstractmethod
        def create(self) -> None:
            pass

        @abstractmethod
        def drop(self) -> None:
            pass

        @abstractmethod
        def add_data(self, data: list[dict]) -> None:
            pass

        @abstractmethod
        def get_data(self) -> list[dict]:
            pass


db = pw.SqliteDatabase(DATABASE)

class Bird(pw.Model):
    eBird_code = pw.CharField(primary_key=True)
    common_name = pw.CharField()
    family_common_name = pw.CharField(null=True)
    bird_order = pw.CharField()
    family = pw.CharField()
    genus = pw.CharField()
    species = pw.CharField()

    class Meta:
        database = db

class BirdSubspecies(pw.Model):
    eBird_code = pw.CharField(primary_key=True)
    common_name = pw.CharField()
    species = pw.ForeignKeyField(Bird, backref='subspecies')

    class Meta:
        database = db

class Superorganisation(pw.Model):
    name = pw.CharField(primary_key=True)
    short_name = pw.CharField(null=True)
    description = pw.CharField(null=True)
    website = pw.CharField(null=True)

    class Meta:
        database = db

class Source(pw.Model):
    name = pw.CharField(primary_key=True)
    short_name = pw.CharField(null=True)
    description = pw.CharField(null=True)
    parent = pw.ForeignKeyField(Superorganisation, backref='superorganisations', null=True)
    website = pw.CharField(null=True)

    class Meta:
        database = db

class Suborganisation(pw.Model):
    name = pw.CharField(primary_key=True)
    short_name = pw.CharField(null=True)
    description = pw.CharField(null=True)
    parent = pw.ForeignKeyField(Source, backref='suborganisations')
    website = pw.CharField(null=True)

    class Meta:
        database = db

class Pin(pw.Model):
    species = pw.ForeignKeyField(Bird, backref='pins')
    subspecies = pw.ForeignKeyField(BirdSubspecies, backref='pins', null=True)
    source = pw.ForeignKeyField(Source, backref='pins')
    suborganisation = pw.ForeignKeyField(Suborganisation, backref='pins', null=True)

    class Meta:
        database = db