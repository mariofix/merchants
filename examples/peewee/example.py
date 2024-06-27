import peewee

from merchants import settings
from merchants.orm.peewee import MerchantsAccountSettings, MerchantsBaseModel

db = peewee.SqliteDatabase("./examples/peewee/example.sqlite3")


class Payment(MerchantsBaseModel):
    content = peewee.TextField()

    class Meta:
        database = db


class AccountSettings(MerchantsAccountSettings):
    class Meta:
        database = db


def create_database():
    with db:
        db.create_tables([Payment, AccountSettings])


create_database()

# settings.process_on_save = False
settings.load_variants(config=None)
print(f"{settings=}")
