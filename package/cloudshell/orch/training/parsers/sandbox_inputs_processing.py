from cloudshell.orch.training.models.training_env import TrainingEnvironmentDataModel
from cloudshell.workflow.orchestration.sandbox import Sandbox

class SandboxInputsParser:
    @staticmethod
    def _is_debug_on(sandbox):
        if sandbox.global_inputs['Diagnostics'] == 'On':
            return True
        return False

    @staticmethod
    def parse_sandbox_inputs(env_data: TrainingEnvironmentDataModel, sandbox: Sandbox):
        env_data.instructor_mode = SandboxInputsParser._is_instructor_mode(sandbox)
        env_data.debug_enabled = SandboxInputsParser._is_debug_on(sandbox)
        env_data.users_list = SandboxInputsParser._sandbox_user_list(sandbox)

    @staticmethod
    def _sandbox_user_list(sandbox):
        training_users_list = []
        if "Training Users" in sandbox.global_inputs:
            users_list = sandbox.global_inputs.get("Training Users", "").split(";")
            if len(training_users_list) > 1:
                training_users_list = users_list
        return training_users_list

    @staticmethod
    def _is_instructor_mode(sandbox):
        #if "#" in user list than this would be student_mode meaning instructor_mode=False
        return not (SandboxInputsParser.sandbox_user_list(sandbox) and "#" in SandboxInputsParser.sandbox_user_list(sandbox)[0])