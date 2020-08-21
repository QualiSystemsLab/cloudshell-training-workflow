from time import sleep

from cloudshell.api.cloudshell_api import UpdateTopologyGlobalInputsRequest, ReservationShortInfo, CloudShellAPISession
from cloudshell.workflow.orchestration.sandbox import Sandbox

from cloudshell.orch.training.services.sandbox_output import SandboxOutputService


class SandboxCreateService:

    def __init__(self, api: CloudShellAPISession, sandbox_output: SandboxOutputService):
        self._api = api
        self._sandbox_output = sandbox_output

    def create_trainee_sandbox(self, blueprint_name: str, user: str, user_id: str, duration: int) -> ReservationShortInfo:
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

            self._sandbox_output.notify(f"""waiting for {user}'s sandbox, 
                                        currently {sandbox_id}'s sandbox status is {user_sandbox_status.ReservationSlimStatus.Status} 
                                        and {user_sandbox_status.ReservationSlimStatus.ProvisioningStatus}""")
            sleep(interval)
            time_waited += interval
            user_sandbox_status = self._api.GetReservationStatus(sandbox_id)

            if user_sandbox_status.ReservationSlimStatus.ProvisioningStatus == 'Error':
                raise Exception('Cannot create student sandbox')

            if user_sandbox_status.ReservationSlimStatus.Status == 'Teardown':
                raise Exception('Cannot create student sandbox')

            if user_sandbox_status.ReservationSlimStatus.Status == 'Completed':
                raise Exception('Cannot create student sandbox')

    def clear_sandbox_components(self, sandbox: Sandbox):
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