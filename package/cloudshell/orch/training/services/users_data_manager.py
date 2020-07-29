import json
from threading import Lock
from typing import Dict

from cloudshell.api.cloudshell_api import SandboxDataKeyValue
from cloudshell.workflow.orchestration.sandbox import Sandbox

USERS_DICT_KEY = "users_dict"


class UsersDataManagerService:
    """
    This service is thread safe
    """

    def __init__(self, sandbox: Sandbox):
        self._sandbox = sandbox
        self._lock = Lock()
        self._data = {}

    def add_or_update(self, user: str, key: str, value: any):
        with self._lock:
            if user in self._data:
                user_data = self._data.get(user)
                user_data.update({key: value})
            else:
                self._data[user] = {key: value}

    def get(self, user: str) -> Dict:
        return self._data.get(user)

    def get_key(self, user: str, key: str) -> any:
        user_data = self._data.get(user)
        return None if not user_data else user_data.get(key)

    def load(self):
        """
        Method will override internal cache
        """
        with self._lock:
            data_kvp = self._sandbox.automation_api.GetSandboxData(self._sandbox.id).SandboxDataKeyValues
            if data_kvp:
                users_data = next(iter(filter(lambda x: x.Key == USERS_DICT_KEY, data_kvp)), None)
                self._data = users_data.Value if users_data else {}
            else:
                self._data = {}

    def save(self):
        with self._lock:
            self._sandbox.automation_api.SetSandboxData(self._sandbox.id,
                                                        [SandboxDataKeyValue(USERS_DICT_KEY, json.dumps(self._data))])
