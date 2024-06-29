from dataclasses import dataclass, field


def _available_integrations() -> list:
    return [
        "paypal",
        "square",
        "stripe",
        "payu",
        "braintree",  # es de paypal
        "authorizenet",
        "twocheckout",
        "verifone",  # compró 2checkout
        "worldpay",
        "fis",  # fisglobal.com compro worldpay
        "adyen",
        "skrill",
        "applepay",
        "googlepay",
        "klarna",
        "wepay",
        "alipay",
        "wix",
    ]


@dataclass
class MerchantsSettings:
    available_integrations: list = field(default_factory=_available_integrations)
    enabled_accounts: list = field(default_factory=list)
    process_on_save: bool = True  # Ejecuta el pago al momento de guardar el objeto.

    load_from_database: bool = True  # Obtiene settings desde archivo o db

    def __post__init__(self):
        pass

    def load_variants(self, config: dict) -> list:
        from .integrations.dummy import settings as example_settings

        self.enabled_accounts = [
            {
                "example": {
                    "config": example_settings,
                    "provider_class": "merchants.integrations.dummy.Provider",
                }
            },
        ]
        return self.enabled_accounts


default_settings = MerchantsSettings()
