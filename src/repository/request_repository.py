import datetime
import uuid

from ..database.database import Database


class RequestRepository:

    def __init__(self, database: Database):
        self.database = database

    def add(self, fields):
        fields['id'] = str(uuid.uuid4())[:8]
        fields['created_at'] = datetime.datetime.now()
        return self.database.add(entity=fields)

    def update(self, request_id, fields):
        return self.database.update(entity_id=request_id, entity=fields)

    def delete(self, request_id):
        return self.database.delete(entity_id=request_id)

    def get_by_user_id(self, user_id):
        return self.database.get_list('*', {'user_id': user_id})

    def get_by_id(self, request_id):
        return self.database.get_one('*', {'id': request_id})
