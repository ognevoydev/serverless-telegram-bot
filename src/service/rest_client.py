import requests


class RestClient:
    """
    Rest client class.
    """

    def __init__(self, url, token):
        self.url = url
        self.token = token

    def upload_file(self, filename, user_id):
        """
        Sends file to analysis.
        """
        url = self.url + 'files/'

        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer ' + self.token
        }

        data = {
            "manager_id": str(user_id),
            "file_name": filename,
        }

        response = requests.post(url, headers=headers, json=data).json()

        if not response:
            return None

        file_id = response.get("file_id")

        if not file_id:
            return None

        return file_id

    def get_result(self, operation_id):
        """
        Checks for analysis result by file id.
        """
        url = self.url + 'result/'

        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer ' + self.token
        }

        data = {
            "file_id": operation_id,
        }

        response = requests.post(url, headers=headers, json=data).json()

        return response
