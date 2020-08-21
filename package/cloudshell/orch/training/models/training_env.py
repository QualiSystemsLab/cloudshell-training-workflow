from typing import List


class TrainingEnvironmentDataModel:
    def __init__(self):
        self.users_list = []  # type: List[str]
        self.debug_enabled = False
        self.instructor_mode = True
