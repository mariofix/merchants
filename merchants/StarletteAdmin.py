# from starlette_admin.contrib.sqla import Admin

# from merchants.database import engine

# admin = Admin(engine, title="Merchants Admin")


class IntegrationAdminMixin:
    exclude_fields_from_list = ["id", "config"]
    exclude_fields_from_create = ["id"]
    exclude_fields_from_edit = ["id"]
    fields_default_sort = ["slug"]
    searchable_fields = ["name", "slug", "integration_class", "config"]


class PaymentAdminMixin:
    exclude_fields_from_list = [
        "id",
        "integration_slug",
        "integration_payload",
        "integration_response",
        "modified_at",
    ]
    exclude_fields_from_create = ["id"]
    exclude_fields_from_edit = ["id"]


# admin.add_view(UserAdmin(User, icon="fas fa-person"))
# admin.add_view(PaymentAdmin(Payment, icon="fas fa-wallet"))
# admin.add_view(IntegrationAdmin(Integration, icon="fas fa-list"))
