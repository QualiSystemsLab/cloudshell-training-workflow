from time import sleep

from cloudshell.api.cloudshell_api import UpdateTopologyGlobalInputsRequest, ReservationShortInfo
from cloudshell.workflow.orchestration.sandbox import Sandbox

from cloudshell.orch.training.services.sandbox_output import SandboxOutputService
from cloudshell.orch.training.services.users_data_manager import UsersDataManagerService,\
    UsersDataManagerServiceKeys as userDataKeys


class SandboxTerminateService:

    def __init__(self, sandbox: Sandbox, sandbox_output: SandboxOutputService,users_data_manager: UsersDataManagerService):
        self._sandbox = sandbox
        self._sandbox_output = sandbox_output
        self._users_data_manager = users_data_manager

    def end_student_reservation(self,user):
        api = self._sandbox.automation_api
        self._users_data_manager.load()

        user_reservation_id = self._users_data_manager.get_key(user, userDataKeys.SANDBOX_ID)
        user_reservation_status = api.GetReservationStatus(user_reservation_id).ReservationSlimStatus.Status
        self._sandbox_output.debug_print(f'Student reservation status is: {user_reservation_status}')

        #If student (user) reservation has not ended yet -> remove the resources that are shared with the Instructor and than End the reservation
        if user_reservation_status != 'Completed':
            instructor_resources = api.GetReservationDetails(self._sandbox.id).ReservationDescription.Resources
            instructor_deployed_apps_names = [resource.Name for resource in instructor_resources if resource.VmDetails]

            self._sandbox_output.notify(f"Cleaning up <{user}> resources")

            user_resources = api.GetReservationDetails(user_reservation_id).ReservationDescription.Resources
            student_shared_apps = [resource.Name for resource in user_resources if
                              resource.Name in instructor_deployed_apps_names]
            if student_shared_apps:
                self._sandbox_output.debug_print(f"Removing resources for {user}")
                api.RemoveResourcesFromReservation(user_reservation_id, student_shared_apps)

            api.EndReservation(user_reservation_id)