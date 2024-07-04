from abc import ABC, abstractmethod


class Storage(ABC):

    @abstractmethod
    def upload(self, filename):
        pass
