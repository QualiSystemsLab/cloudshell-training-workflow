from cloudshell.api.cloudshell_api import UpdateTopologyGlobalInputsRequest, ReservationShortInfo
from cloudshell.workflow.orchestration.sandbox import Sandbox
import json

from cloudshell.orch.training.models.training_env import TrainingEnvironmentDataModel
from cloudshell.orch.training.services.sandbox_api import SandboxAPIService
from cloudshell.orch.training.services.sandbox_output import SandboxOutputService
from cloudshell.orch.training.services.users_data_manager import UsersDataManagerService


class SandboxTerminateService:

    def __init__(self, sandbox: Sandbox, sandbox_output: SandboxOutputService, sandbox_api_service: SandboxAPIService,users_data_manager: UsersDataManagerService,training_env:TrainingEnvironmentDataModel):
        self._sandbox = sandbox
        self._sandbox_output = sandbox_output
        self._sandbox_api = sandbox_api_service
        self._users_data_manager = users_data_manager
        self._training_env = training_env

    def terminate_student_sandboxes(self):
        api = self._sandbox.automation_api

        self._users_data_manager.load()

        '''
        sandbox_data_dict = {item.Key: item.Value for item in
                             api.GetSandboxData(self._sandbox.id).SandboxDataKeyValues}              
        if "users_dict" in sandbox_data_dict.keys():
            users_dict = json.loads(sandbox_data_dict["users_dict"])
        '''
        for user in self._training_env:
            for user_data in self._users_data_manager.get(user):
                self._end_student_resrevation(user, user_data)
                admin_token = self._sandbox_api.login()
                self._sandbox_api.delete_token(api_token=admin_token, user_token=self._users_data_manager.get_key("token"))

    def _end_student_resrevation(self,user):
        api = self._sandbox.automation_api

        self._sandbox_output.notify(f"Cleaning up <{user}> resources")
        user_reservation_id = self._users_data_manager.get_key('sandbox_id')

        user_reservation_status = api.GetReservationStatus(user_reservation_id).ReservationSlimStatus.Status
        self._sandbox_output.debug_print(f'Student reservation status is: {user_reservation_status}')

        instructor_resources = api.GetReservationDetails(self._sandbox.id).ReservationDescription.Resources

        instructor_deployed_apps_names = [resource.Name for resource in instructor_resources if resource.VmDetails]

        if user_reservation_status != 'Completed':
            user_resources = api.GetReservationDetails(user_reservation_id).ReservationDescription.Resources
            #TODO check if it`s even needed to removed the shared apps
            student_shared_apps = [resource.Name for resource in user_resources if
                              resource.Name in instructor_deployed_apps_names]
            if student_shared_apps:
                self._sandbox_output.debug_print(f"Removing resources for {user}")
                api.RemoveResourcesFromReservation(user_reservation_id, student_shared_apps)

            api.EndReservation(user_reservation_id)


