from cloudshell.workflow.orchestration.sandbox import Sandbox


class SandboxOutputService:

    def __init__(self, sandbox: Sandbox, debug_enabled: bool):
        self._sandbox = sandbox
        self._debug_enabled = debug_enabled

    def notify(self, message: str):
        self._sandbox.logger.info(message)
        self._sandbox.automation_api.WriteMessageToReservationOutput(self._sandbox.id, message)

    def debug_print(self, message: str):
        self._sandbox.logger.debug(message)
        if self._debug_enabled:
            self._sandbox.automation_api.WriteMessageToReservationOutput(self._sandbox.id, message)
