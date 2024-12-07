import peewee as pw

db = pw.SQliteDatabase('pin_database.db')

class Bird(pw.Model):
    eBird_code = pw.PrimaryKeyField()
    common_name = pw.CharField()
    family_common_name = pw.CharField(null=True)
    order = pw.CharField()
    family = pw.CharField()
    genus = pw.CharField()
    species = pw.CharField()

    class Meta:
        database = db

class BirdSubspecies(pw.Model):
    eBird_code = pw.PrimaryKeyField()
    common_name = pw.CharField()
    species = pw.ForeignKeyField(Bird, backref='subspecies')

    class Meta:
        database = db

class Superorganisation(pw.Model):
    name = pw.PrimaryKeyField()
    short_name = pw.CharField(null=True)
    description = pw.CharField(null=True)
    website = pw.CharField(null=True)

    class Meta:
        database = db

class Source(pw.Model):
    name = pw.PrimaryKeyField()
    short_name = pw.CharField(null=True)
    description = pw.CharField(null=True)
    parent = pw.ForeignKeyField(Superorganisation, backref='superorganisations', null=True)
    website = pw.CharField(null=True)

    class Meta:
        database = db

class Suborganisation(pw.Model):
    name = pw.PrimaryKeyField()
    short_name = pw.CharField(null=True)
    description = pw.CharField(null=True)
    parent = pw.ForeignKeyField(Source, backref='suborganisations')
    website = pw.CharField(null=True)

    class Meta:
        database = db

class Pin(pw.Model):
    ID = pw.PrimaryKeyField()
    species = pw.ForeignKeyField(Bird, backref='pins')
    subspecies = pw.ForeignKeyField(BirdSubspecies, backref='pins', null=True)
    source = pw.ForeignKeyField(Source, backref='pins')
    suborganisation = pw.ForeignKeyField(Suborganisation, backref='pins', null=True)

    class Meta:
        database = db