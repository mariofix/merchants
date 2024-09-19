from starlette_admin.contrib.sqla import Admin, ModelView

from merchants.config import settings
from merchants.database import engine
from merchants.models import Integration, Payment, User

admin = Admin(engine, title=settings.PROJECT_NAME)


class UserAdmin(ModelView):
    exclude_fields_from_list = ["id", "password"]
    exclude_fields_from_create = ["id"]
    exclude_fields_from_edit = ["id"]


class IntegrationAdmin(ModelView):
    exclude_fields_from_list = ["id", "config"]
    exclude_fields_from_create = ["id"]
    exclude_fields_from_edit = ["id"]
    fields_default_sort = ["slug"]
    searchable_fields = ["name", "slug", "integration_class", "config"]


class PaymentAdmin(ModelView):
    exclude_fields_from_list = ["id", "integration_slug", "integration_payload", "integration_response", "modified_at"]
    exclude_fields_from_create = ["id"]
    exclude_fields_from_edit = ["id"]


admin.add_view(UserAdmin(User, icon="fas fa-person"))
admin.add_view(PaymentAdmin(Payment, icon="fas fa-wallet"))
admin.add_view(IntegrationAdmin(Integration, icon="fas fa-list"))
