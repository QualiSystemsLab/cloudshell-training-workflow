from time import sleep

from cloudshell.api.cloudshell_api import UpdateTopologyGlobalInputsRequest, ReservationShortInfo
from cloudshell.workflow.orchestration.sandbox import Sandbox

from cloudshell.orch.training.services.sandbox_output import SandboxOutputService


class SandboxCreateService:

    def __init__(self, sandbox: Sandbox, sandbox_output: SandboxOutputService):
        self._sandbox = sandbox
        self._sandbox_output = sandbox_output

    def create_trainee_sandbox(self, user: str, user_id: str, duration: int) -> ReservationShortInfo:
        new_sandbox = self._sandbox.automation_api.CreateImmediateTopologyReservation(
            f"{user} - Trainee Sandbox",
            user, duration, False, False, 10,
            topologyFullPath=self._sandbox.reservationContextDetails.environment_name,
            globalInputs=[
                UpdateTopologyGlobalInputsRequest(
                    "Training Users",
                    f"{user}#{user_id}")])

        return new_sandbox.Reservation

    def wait_active(self, user_sandbox_id: str, user: str):
        time_waited = 0
        interval = 10

        user_sandbox_status = self._sandbox.automation_api.GetReservationStatus(user_sandbox_id)

        while user_sandbox_status.ReservationSlimStatus.Status != "Started" or \
                user_sandbox_status.ReservationSlimStatus.ProvisioningStatus != "Ready":

            self._sandbox_output.notify(f"""waiting for {user}'s sandbox, 
                                        currently {user_sandbox_id}'s sandbox satus is {user_sandbox_status.ReservationSlimStatus.Status} 
                                        and {user_sandbox_status.ReservationSlimStatus.ProvisioningStatus}""")
            sleep(interval)
            time_waited += interval
            user_sandbox_status = self._sandbox.automation_api.GetReservationStatus(user_sandbox_id)

            if user_sandbox_status.ReservationSlimStatus.ProvisioningStatus == 'Error':
                raise Exception('Cannot create student sandbox')

            if user_sandbox_status.ReservationSlimStatus.Status == 'Teardown':
                raise Exception('Cannot create student sandbox')

            if user_sandbox_status.ReservationSlimStatus.Status == 'Completed':
                raise Exception('Cannot create student sandbox')