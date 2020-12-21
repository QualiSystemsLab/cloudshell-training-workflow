from typing import List

from cloudshell.workflow.training.models.training_env import TrainingEnvironmentDataModel
from cloudshell.workflow.orchestration.sandbox import Sandbox


class SandboxInputsParser:

    @staticmethod
    def parse_sandbox_inputs(sandbox: Sandbox) -> TrainingEnvironmentDataModel:
        env_data = TrainingEnvironmentDataModel()
        env_data.instructor_mode = SandboxInputsParser._is_instructor_mode(sandbox)
        env_data.debug_enabled = SandboxInputsParser._is_debug_on(sandbox)
        env_data.users_list = SandboxInputsParser._sandbox_user_list(sandbox)
        return env_data

    @staticmethod
    def _is_debug_on(sandbox: Sandbox) -> bool:
        if 'Diagnostics' in sandbox.global_inputs:
            return sandbox.global_inputs['Diagnostics'] == 'On'
        return False

    @staticmethod
    def _sandbox_user_list(sandbox: Sandbox) -> List[str]:
        users_list = SandboxInputsParser._split_training_users_input(sandbox)
        if users_list and len(users_list) == 1 and '#' in users_list[0]:
            # for now we remove the user ID after the hash tag, in the future we might need to parse it into its own
            #  variable in case it will be needed
            hashtag_index = users_list[0].index('#')
            users_list[0] = users_list[0][:hashtag_index]
        if users_list and len(users_list) == 1 and not users_list[0]:
            return []
        return users_list

    @staticmethod
    def _split_training_users_input(sandbox: Sandbox) -> List[str]:
        if "Training Users" in sandbox.global_inputs:
            return sandbox.global_inputs.get('Training Users', '').split(";")
        return []

    @staticmethod
    def _is_instructor_mode(sandbox: Sandbox):
        # if "#" in user list than this would be student_mode meaning instructor_mode=False
        user_list = SandboxInputsParser._split_training_users_input(sandbox)
        return not (user_list and '#' in user_list[0])
