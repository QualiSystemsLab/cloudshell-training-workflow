from time import sleep

from cloudshell.api.cloudshell_api import UpdateTopologyGlobalInputsRequest, ReservationShortInfo, CloudShellAPISession
from cloudshell.workflow.orchestration.sandbox import Sandbox

from cloudshell.orch.training.services.sandbox_output import SandboxOutputService
from cloudshell.orch.training.services.users_data_manager import UsersDataManagerService, \
    UsersDataManagerServiceKeys as userDataKeys


class SandboxLifecycleService:

    def __init__(self, sandbox: Sandbox, sandbox_output: SandboxOutputService,
                 users_data_manager: UsersDataManagerService):
        self._sandbox = sandbox
        self._sandbox_output = sandbox_output
        self._users_data_manager = users_data_manager
        self._api = self._sandbox.automation_api

    def create_trainee_sandbox(self, blueprint_name: str, user: str, user_id: str,
                               duration: int) -> ReservationShortInfo:
        new_sandbox = self._api.CreateImmediateTopologyReservation(
            f"{user} - Trainee Sandbox",
            user, duration, False, False, 10,
            topologyFullPath=blueprint_name,
            globalInputs=[
                UpdateTopologyGlobalInputsRequest(
                    "Training Users",
                    f"{user}#{user_id}")])

        return new_sandbox.Reservation

    def wait_ready(self, sandbox_id: str, user: str, interval: int = 10):
        time_waited = 0

        user_sandbox_status = self._api.GetReservationStatus(sandbox_id)

        while user_sandbox_status.ReservationSlimStatus.Status != "Started" or \
                user_sandbox_status.ReservationSlimStatus.ProvisioningStatus != "Ready":

            self._sandbox_output.notify(f"waiting for {user}'s sandbox, currently {sandbox_id}'s sandbox status is"
                                        f" {user_sandbox_status.ReservationSlimStatus.Status} and {user_sandbox_status.ReservationSlimStatus.ProvisioningStatus}")
            sleep(interval)
            time_waited += interval
            user_sandbox_status = self._api.GetReservationStatus(sandbox_id)

            if user_sandbox_status.ReservationSlimStatus.ProvisioningStatus == 'Error':
                raise Exception('Cannot create student sandbox')

            if user_sandbox_status.ReservationSlimStatus.Status == 'Teardown':
                raise Exception('Cannot create student sandbox')

            if user_sandbox_status.ReservationSlimStatus.Status == 'Completed':
                raise Exception('Cannot create student sandbox')

    def clear_sandbox_components(self, sandbox: Sandbox) -> None:
        api = sandbox.automation_api
        sandbox_details = api.GetReservationDetails(sandbox.id).ReservationDescription

        # delete all resources
        resource_names = [resource.Name for resource in sandbox_details.Resources]
        if resource_names:
            api.RemoveResourcesFromReservation(sandbox.id, resource_names)

        # delete all services
        service_names = [service.Alias for service in sandbox_details.Services]
        if service_names:
            try:
                api.RemoveServicesFromReservation(sandbox.id, service_names)
            except Exception as ex:
                sandbox.logger.exception('failed to delete services')
                self._sandbox_output.notify(f'failed to delete services with error: {ex}')

        # delete all apps
        for app in sandbox_details.Apps:
            api.RemoveAppFromReservation(sandbox.id, appName=app.Name)

    def end_student_reservation(self, user: str, instructor_mode: bool) -> None:
        user_reservation_id = self._users_data_manager.get_key(user, userDataKeys.SANDBOX_ID) \
            if instructor_mode else self._sandbox.id

        user_reservation_status = self._api.GetReservationStatus(user_reservation_id).ReservationSlimStatus.Status
        self._sandbox_output.debug_print(f'Student reservation status is: {user_reservation_status}')

        # If student (user) reservation has not ended yet -> remove the resources that are shared with the Instructor
        # and than End the reservation
        if user_reservation_status == 'Completed':
            return

        user_reservation_details = self._api.GetReservationDetails(user_reservation_id)
        user_resources = user_reservation_details.ReservationDescription.Resources
        apps_names_shared_with_student = [resource.Name for resource in user_resources if
                                          resource.VmDetails and resource.CreatedInReservation != user_reservation_id]

        self._sandbox_output.notify(f"Cleaning up <{user}> resources")

        # all apps that were deployed in the instructor sandbox will be removed from the student reservation
        if apps_names_shared_with_student:
            self._sandbox_output.debug_print(f"Removing resources for {user}")
            if not instructor_mode:
                for app_name in apps_names_shared_with_student:
                    self._api.ExecuteCommand(user_reservation_id, app_name, "Resource", "Power Off", [], True)
            self._api.RemoveResourcesFromReservation(user_reservation_id, apps_names_shared_with_student)

        self._api.EndReservation(user_reservation_id)