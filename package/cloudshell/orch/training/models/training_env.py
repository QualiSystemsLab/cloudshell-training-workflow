from typing import List
from cloudshell.workflow.orchestration.sandbox import Sandbox

class TrainingEnvironmentDataModel:
    def __init__(self):
        #TODO Alex check shared_apps location
        self.shared_apps = []  # type: List[str]
        self.users_list = []  # type: List[str]
        self.instructor_mode = True
        self.debug_enabled = False