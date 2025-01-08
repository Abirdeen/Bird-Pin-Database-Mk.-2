import peewee as pw

from abc import ABC, abstractmethod
from typing import TypeVar, TypedDict, Generic

DATABASE: str = 'pin_database.db'

class BirdDict(TypedDict):
    eBird_code: str
    common_name: str
    family_common_name: str
    bird_order: str
    family: str
    genus: str
    species: str

class SubspeciesDict(TypedDict):
    eBird_code: str
    common_name: str
    subspecies: str
    species: str

class SuperorganisationDict(TypedDict):
    name: str
    short_name: str | None
    description: str | None
    website: str | None

class SourceDict(TypedDict):
    name: str
    short_name: str | None
    description: str | None
    parent: str | None
    website: str | None

class SuborganisationDict(TypedDict):
    name: str
    short_name: str | None
    description: str | None
    parent: str
    website: str | None

class PinDict(TypedDict):
    id: int | None
    species: str
    subspecies: str | None
    source: str
    suborganisation: str | None

DataDict = TypeVar('DataDict', PinDict, BirdDict, SourceDict, SubspeciesDict, SuborganisationDict, SuperorganisationDict)

class Table(ABC, Generic[DataDict]):

        def __repr__(self):
            return '(class) Table'

        @abstractmethod
        def create(self) -> None:
            pass

        @abstractmethod
        def drop(self) -> None:
            pass

        @abstractmethod
        def add_data(self, data: list[DataDict]) -> None:
            pass

        @abstractmethod
        def get_data(self) -> list[DataDict]:
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
    subspecies = pw.CharField()
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