import json
import os


class Loc:
    """
    Localization class.
    It allows to get locale messages by language code.
    """
    _locale = 'ru'
    _data = {}

    @staticmethod
    def get_message(code, replace=None):
        """
        Get message by code.
        """
        message = Loc._data.get(Loc._locale, {}).get(code, "Message not found")

        if replace is not None and isinstance(replace, dict):
            for key, value in replace.items():
                message = message.replace(key, value)
        return message

    @staticmethod
    def load_messages(lang='ru'):
        """
        Loads messages for a specific language.
        """
        Loc._locale = lang

        file_path = os.path.join(os.path.dirname(__file__), f'../locale/{lang}.json')

        if lang not in Loc._data:
            Loc._data[lang] = {}

        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as file:
                Loc._data[lang] = json.load(file)
        else:
            return f"Error: '{file_path}' file not found."
