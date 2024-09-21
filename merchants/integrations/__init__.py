from abc import ABC, abstractmethod

# from dataclasses import dataclass


class BaseIntegration(ABC):
    name: str

    @abstractmethod
    def charge(self):
        raise NotImplementedError("You need to inherit this class and implement your own charge()")

    @abstractmethod
    def refund(self):
        raise NotImplementedError("You need to inherit this class and implement your own refund()")


# no me gusta esto
class DummyIntegration(BaseIntegration):
    name = "Dummy"

    def charge(self): ...

    def refund(self): ...


dummy = DummyIntegration()
