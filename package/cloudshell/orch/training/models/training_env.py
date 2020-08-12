from typing import List


class TrainingEnvironmentDataModel:
    def __init__(self):
        self.shared_apps = []  # type: List[str]
        self.users_list = []  # type: List[str]
        self.debug_enabled = False
