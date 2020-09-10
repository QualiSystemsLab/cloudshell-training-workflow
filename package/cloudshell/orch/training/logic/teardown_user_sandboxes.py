from cloudshell.workflow.orchestration.sandbox import Sandbox

from cloudshell.orch.training.models.training_env import TrainingEnvironmentDataModel
from cloudshell.orch.training.services.sandbox_api import SandboxAPIService
from cloudshell.orch.training.services.sandbox_output import SandboxOutputService
from cloudshell.orch.training.services.sandbox_lifecycle import SandboxLifecycleService
from cloudshell.orch.training.services.users_data_manager import UsersDataManagerService,\
    UsersDataManagerServiceKeys as userDataKeys


class SandboxTerminateLogic:

    def __init__(self, sandbox: Sandbox, sandbox_output: SandboxOutputService, sandbox_api_service: SandboxAPIService,sandbox_lifecycle_service:SandboxLifecycleService,users_data_manager: UsersDataManagerService,training_env:TrainingEnvironmentDataModel):
        self._instructor_sandbox = sandbox
        self._sandbox_output = sandbox_output
        self._sandbox_api = sandbox_api_service
        self._sandbox_lifecycle_service = sandbox_lifecycle_service
        self._users_data_manager = users_data_manager
        self._training_env = training_env

    def _delete_students_group(self):
        # TODO use the service function part of the user service
        api = self._instructor_sandbox.automation_api
        self._sandbox_output.debug_print(f'Removing Students Group: {self._instructor_sandbox.id}')
        api.RemoveGroupsFromDomain(api.GetReservationDetails(self._instructor_sandbox.id).ReservationDescription.DomainName,self._instructor_sandbox.id)

    def teardown_student_sandboxes(self):
        admin_token = self._sandbox_api.login()

        for user in self._training_env.users_list:
            self._sandbox_output.debug_print(f'Preparing sandbox Teardown for user: {user}')
            self._sandbox_termination_service.end_student_reservation(user)
            self._sandbox_output.debug_print(f'Deleting Token for user: {user}')
            self._sandbox_api.delete_token(api_token=admin_token, user_token=self._users_data_manager.get_key(user,userDataKeys.TOKEN))

        self._delete_students_group()