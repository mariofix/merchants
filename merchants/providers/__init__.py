_provider_list = ["dummy", "flow", "khipu", "paypal", "sqare", "stripe", "transbank"]


def factory(slug: str):
    if slug not in _provider_list:
        raise NotImplementedError(f"The provider {slug} is not supported.")

    return slug
