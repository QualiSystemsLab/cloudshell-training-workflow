from cloudshell.orch.training.models.training_env import TrainingEnvironmentDataModel
from package.cloudshell.orch.training.services.services_class import TrainingEnvironmentServices
from cloudshell.orch.training.services.users_data_manager import UsersDataManagerService


class SandboxInputsParser:
    def __init__(self, env_data: TrainingEnvironmentDataModel, env_services: TrainingEnvironmentServices):
        self._env_data = env_data
        self._env_services = env_services
        self._process_sandbox_global_inputs()

    def _process_sandbox_global_inputs(self):
        if "Training Users" in self._env_data.sandbox.global_inputs:
            self._env_data.users_list = self._env_data.sandbox.global_inputs.get("Training Users", "").split(";")
            if not len(self._env_data.users_list) > 1:
                self._env_data.training_users_list = []
        if self._env_data.users_list and "#" in self._env_data.users_list[0]:
            self._env_data.student_mode = False
        if 'Diagnostics' in self._env_data.sandbox.global_inputs:
            if self._env_data.sandbox.global_inputs['Diagnostics'] == 'On':
                self._env_services.sandbox_output._debug_enabled = True