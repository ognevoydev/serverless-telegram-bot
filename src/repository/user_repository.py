import datetime
import uuid

from ..database.database import Database


class UserRepository:

    def __init__(self, database: Database):
        self.database = database

    def add(self, fields):
        fields['id'] = str(uuid.uuid4())[:8]
        fields['created_at'] = datetime.datetime.now()
        return self.database.add(entity=fields)

    def update(self, user_id, fields):
        return self.database.update(entity_id=user_id, entity=fields)

    def delete(self, user_id):
        return self.database.delete(entity_id=user_id)

    def get_by_account_id(self, account_id):
        return self.database.get_one('*', {'account_id': account_id})
