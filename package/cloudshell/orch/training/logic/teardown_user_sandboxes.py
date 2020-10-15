from cloudshell.workflow.orchestration.sandbox import Sandbox

from cloudshell.orch.training.models.training_env import TrainingEnvironmentDataModel
from cloudshell.orch.training.services.sandbox_api import SandboxAPIService
from cloudshell.orch.training.services.sandbox_output import SandboxOutputService
from cloudshell.orch.training.services.sandbox_lifecycle import SandboxLifecycleService
from cloudshell.orch.training.services.users import UsersService
from cloudshell.orch.training.services.users_data_manager import UsersDataManagerService, \
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
        # in case 'teardown_student_sandboxes' fails we still want to try to run the rest of the teardown
        self._execute_teardown_safely(sandbox)

    def _execute_teardown_safely(self, sandbox: Sandbox):
        try:
            self._teardown_student_sandboxes_inner(sandbox)
        except:
            sandbox.logger.exception('Error in "teardown_student_sandboxes"')
            sandbox.automation_api.WriteMessageToReservationOutput(
                sandbox.id, '<font style="color:red">Error during teardown of student sandboxes. '
                            'Please check logs for more details"</font>')

    def _teardown_student_sandboxes_inner(self, sandbox: Sandbox):
        sandbox.logger.info("Starting tearing down process")
        admin_token = self._sandbox_api.login()

        for user in self._training_env.users_list:
            self._sandbox_output.debug_print(f'Preparing sandbox Teardown for user: {user}')
            self._sandbox_lifecycle_service.end_student_reservation(user, self._training_env.instructor_mode)

            self._sandbox_output.debug_print(f'Deleting Token for user: {user}')
            self._sandbox_api.delete_token(api_token=admin_token,
                                           user_token=self._users_data_manager.get_key(user, userDataKeys.TOKEN))

        if self._training_env.instructor_mode:
            sandbox.logger.info("Deleting user group")
            self._delete_students_group(sandbox)
