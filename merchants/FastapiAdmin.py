from merchants.models import User, Broker
from merchants.database import engine
from merchants.config import settings

from starlette_admin.contrib.sqlmodel import Admin, ModelView

admin = Admin(engine, title=settings.PROJECT_NAME)


class UserAdmin(ModelView):
    exclude_fields_from_list = ["id", "password"]
    exclude_fields_from_create = ["id"]
    exclude_fields_from_edit = ["id"]


class BrokerAdmin(ModelView):
    exclude_fields_from_list = ["id", "config"]
    exclude_fields_from_create = ["id"]
    exclude_fields_from_edit = ["id"]
    fields_default_sort = ["slug"]
    searchable_fields = ["name", "slug", "integration_class", "config"]


admin.add_view(UserAdmin(User, icon="fas fa-person"))
admin.add_view(BrokerAdmin(Broker, icon="fas fa-list"))
