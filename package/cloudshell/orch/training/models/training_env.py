from typing import List
from cloudshell.workflow.orchestration.sandbox import Sandbox

class TrainingEnvironmentDataModel:
    def __init__(self):

        self.shared_apps = []  # type: List[str]
        self.users_list = []  # type: List[str]
        self.instructor_mode = True
        self.debug_enabled = False

        self.original_ip_values = {}
        self.additional_ip_range = {}