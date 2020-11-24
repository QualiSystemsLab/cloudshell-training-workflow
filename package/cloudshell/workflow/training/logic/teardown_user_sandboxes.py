from cloudshell.workflow.orchestration.sandbox import Sandbox

from cloudshell.workflow.training.models.training_env import TrainingEnvironmentDataModel
from cloudshell.workflow.training.services.sandbox_api import SandboxAPIService
from cloudshell.workflow.training.services.sandbox_output import SandboxOutputService
from cloudshell.workflow.training.services.sandbox_lifecycle import SandboxLifecycleService
from cloudshell.workflow.training.services.users import UsersService
from cloudshell.workflow.training.services.users_data_manager import UsersDataManagerService, \
    UsersDataManagerServiceKeys as userDataKeys


class SandboxTerminateLogic:

    def __init__(self, sandbox_output: SandboxOutputService, sandbox_api_service: SandboxAPIService,
                 sandbox_lifecycle_service: SandboxLifecycleService, users_data_manager: UsersDataManagerService,
                 training_env: TrainingEnvironmentDataModel, users_service: UsersService):
        self._sandbox_output = sandbox_output
        self._sandbox_api = sandbox_api_service
        self._sandbox_lifecycle_service = sandbox_lifecycle_service
        self._users_data_manager = users_data_manager
        self._training_env = training_env
        self._users_service = users_service

    def _delete_students_group(self, instructor_sandbox: Sandbox) -> None:
        self._users_service.delete_training_users_group(instructor_sandbox.id)

    def teardown_student_sandboxes(self, sandbox, components):
        # todo - move to workflow or some singleton provider?
        admin_token = self._sandbox_api.login()

        for user in self._training_env.users_list:
            self._sandbox_output.debug_print(f'Preparing sandbox Teardown for user: {user}')
            self._sandbox_lifecycle_service.end_student_reservation(user,self._training_env.instructor_mode)

            self._sandbox_output.debug_print(f'Deleting Token for user: {user}')
            self._sandbox_api.delete_token(api_token=admin_token,
                                           user_token=self._users_data_manager.get_key(user, userDataKeys.TOKEN))

        self._delete_students_group(sandbox)
