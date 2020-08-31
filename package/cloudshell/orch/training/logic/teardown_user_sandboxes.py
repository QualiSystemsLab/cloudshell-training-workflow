from cloudshell.api.cloudshell_api import UpdateTopologyGlobalInputsRequest, ReservationShortInfo
from cloudshell.workflow.orchestration.sandbox import Sandbox
import json

from cloudshell.orch.training.models.training_env import TrainingEnvironmentDataModel
from cloudshell.orch.training.services.sandbox_api import SandboxAPIService
from cloudshell.orch.training.services.sandbox_output import SandboxOutputService
from cloudshell.orch.training.services.sandbox_terminate import SandboxTerminateService
from cloudshell.orch.training.services.users_data_manager import UsersDataManagerService,\
    UsersDataManagerServiceKeys as userDataKeys


class SandboxTerminateLogic:

    def __init__(self, sandbox: Sandbox, sandbox_output: SandboxOutputService, sandbox_api_service: SandboxAPIService,users_data_manager: UsersDataManagerService,sandbox_termination_service:SandboxTerminateService,training_env:TrainingEnvironmentDataModel):
        self._sandbox = sandbox
        self._sandbox_output = sandbox_output
        self._sandbox_api = sandbox_api_service
        self._sandbox_termination_service = sandbox_termination_service(users_data_manager)
        self._users_data_manager = users_data_manager
        self._training_env = training_env

    def _delete_students_group(self):
        # TODO use the service function part of the user service
        api = self._sandbox.automation_api
        self._sandbox_output.debug_print(f'Removing Students Group: {self._sandbox.id}')
        api.RemoveGroupsFromDomain(api.GetReservationDetails(self._sandbox.id).ReservationDescription.DomainName,self._sandbox.id)

    def teardown_student_sandboxes(self):
        self._users_data_manager.load()

        for user in self._training_env:
            self._sandbox_termination_service.end_student_reservation(user)
            admin_token = self._sandbox_api.login()
            self._sandbox_api.delete_token(api_token=admin_token, user_token=self._users_data_manager.get_key(user,userDataKeys.TOKEN))

        self._delete_students_group()



#TODO
# add comments
# Main logic function as Login function that uses terminate_service
# remove using get.key with strings ->Done