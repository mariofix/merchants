from typing import Any

from starlette.requests import Request
from starlette_admin import action, row_action
from starlette_admin.contrib.sqla import ModelView
from starlette_admin.exceptions import ActionFailed


class IntegrationAdminMixin(ModelView):
    exclude_fields_from_list = ["id", "config"]
    exclude_fields_from_create = ["id"]
    exclude_fields_from_edit = ["id"]
    fields_default_sort = ["slug"]
    searchable_fields = ["name", "slug", "integration_class", "config"]


class PaymentAdminMixin(ModelView):
    exclude_fields_from_list = [
        "id",
        "integration_slug",
        "integration_payload",
        "integration_response",
        "creation",
    ]
    exclude_fields_from_create = ["id"]
    exclude_fields_from_edit = ["id"]

    actions = ["process_payment", "refund_payment", "cancel_payment", "delete"]
    row_actions = ["view", "edit", "process_payment", "refund_payment", "cancel_payment", "delete"]

    @action(
        name="process_payment",
        text="Process Payment",
        confirmation="Are you sure you want to process the selected payments ?",
        submit_btn_text="Yes, proceed",
        submit_btn_class="btn-success",
    )
    async def process_payment_action(self, request: Request, pks: list[Any]) -> str:
        if ...:
            # Display meaningfully error
            raise ActionFailed("There was a problem processing this payment, see logs for more details.")
        # Display successfully message
        return f"{len(pks)} payments were successfully processed"

    @row_action(
        name="process_payment",
        text="Process Payment",
        confirmation="Are you sure you want to process this payment ?",
        icon_class="fas fa-check",
        submit_btn_text="Yes, proceed",
        submit_btn_class="btn-success",
        action_btn_class="btn-info",
    )
    async def process_row_action(self, request: Request, pk: Any) -> str:
        # Write your logic here
        if ...:
            # Display meaningfully error
            raise ActionFailed("There was a problem processing this payment, see logs for more details.")
        # Display successfully message
        return "The payment was succesfully processed"

    @action(
        name="refund_payment",
        text="Refund Payment",
        confirmation="Are you sure you want to refund the selected payments ?",
        submit_btn_text="Yes, proceed",
        submit_btn_class="btn-secondary",
    )
    async def refund_action(self, request: Request, pks: list[Any]) -> str:
        if ...:
            # Display meaningfully error
            raise ActionFailed("There was a problem refunding this payment, see logs for more details.")
        # Display successfully message
        return f"{len(pks)} payments were successfully refunded"

    @row_action(
        name="refund_payment",
        text="Refund Payment",
        confirmation="Are you sure you want to refund this payment ?",
        icon_class="fas fa-rotate-right",
        submit_btn_text="Yes, proceed",
        submit_btn_class="btn-success",
        action_btn_class="btn-info",
    )
    async def refund_row_action(self, request: Request, pk: Any) -> str:
        # Write your logic here
        if ...:
            # Display meaningfully error
            raise ActionFailed("There was a problem refunding this payment, see logs for more details.")
        # Display successfully message
        return "The payment was succesfully refunded"

    @action(
        name="cancel_payment",
        text="Cancel Payment",
        confirmation="Are you sure you want to cancel the selected payments ?",
        submit_btn_text="Yes, proceed",
        submit_btn_class="btn-danger",
    )
    async def cancel_action(self, request: Request, pks: list[Any]) -> str:
        if ...:
            # Display meaningfully error
            raise ActionFailed("There was a problem cancelling this payment, see logs for more details.")
        # Display successfully message
        return f"{len(pks)} payments were successfully cancelled"

    @row_action(
        name="cancel_payment",
        text="Cancel Payment",
        confirmation="Are you sure you want to cancel this payment ?",
        icon_class="fas fa-xmark",
        submit_btn_text="Yes, proceed",
        submit_btn_class="btn-success",
        action_btn_class="btn-info",
    )
    async def cancel_row_action(self, request: Request, pk: Any) -> str:
        # Write your logic here
        if ...:
            # Display meaningfully error
            raise ActionFailed("There was a problem creating this payment, see logs for more details.")
        # Display successfully message
        return "The payment was succesfully created"
