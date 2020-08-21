from cloudshell.workflow.orchestration.sandbox import Sandbox
from cloudshell.workflow.orchestration.teardown.default_teardown_orchestrator import DefaultTeardownWorkflow

from cloudshell.orch.training.parsers.sandbox_inputs_processing import SandboxInputsParser
from cloudshell.orch.training.services.sandbox_api import SandboxAPIService
from cloudshell.orch.training.services.sandbox_output import SandboxOutputService
from cloudshell.orch.training.services.sandbox_terminate import SandboxTerminateService
from cloudshell.orch.training.services.users_data_manager import UsersDataManagerService


class TrainingTeardownWorkflow(object):
    def __init__(self):
        self.default_teardown_workflow = DefaultTeardownWorkflow()

    def _bootstrap(self, sandbox: Sandbox):
        sandbox.logger.info("Bootstrapping teardown workflow")

        env_data = SandboxInputsParser.parse_sandbox_inputs(sandbox)
        sandbox_output_service = SandboxOutputService(sandbox, env_data.debug_enabled)
        sandbox_api_service = SandboxAPIService(sandbox, self.config.sandbox_api_port, sandbox_output_service)
        users_data_manager = UsersDataManagerService(sandbox)
        self._sandbox_terminator = SandboxTerminateService(sandbox,sandbox_output_service,sandbox_api_service,users_data_manager,env_data)


    def register(self, sandbox):
        """
        :param Sandbox sandbox:
        :return:
        """
        self._bootstrap(sandbox)
        self._sandbox_terminator.terminate_student_sandboxes()
        #TODO delete users group
        sandbox.logger.info("Adding default teardown orchestration")
        sandbox.workflow.add_to_teardown( self._sandbox_terminator.terminate_student_sandboxes(), None)