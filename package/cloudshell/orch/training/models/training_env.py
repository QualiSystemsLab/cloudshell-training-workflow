from typing import List
from cloudshell.workflow.orchestration.sandbox import Sandbox

class TrainingEnvironmentDataModel:
    def __init__(self, sandbox: Sandbox):
        self.sandbox = sandbox
        self.shared_apps = []  # type: List[str]
        self.users_list = []  # type: List[str]
        self.instructor_mode = True

        self.original_ip_values = {}
        self.additional_ip_range = {}