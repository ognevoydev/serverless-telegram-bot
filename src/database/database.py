from abc import ABC, abstractmethod


class Database(ABC):

    @abstractmethod
    def add(self, entity):
        pass

    @abstractmethod
    def update(self, entity_id, entity):
        pass

    @abstractmethod
    def delete(self, entity_id):
        pass

    @abstractmethod
    def get_one(self, select, filter):
        pass

    @abstractmethod
    def get_list(self, select, filter):
        pass
