from cloudshell.workflow.orchestration.sandbox import Sandbox
from cloudshell.workflow.orchestration.teardown.default_teardown_orchestrator import DefaultTeardownWorkflow

from cloudshell.orch.training.models.config import TrainingWorkflowConfig
from cloudshell.orch.training.parsers.sandbox_inputs_processing import SandboxInputsParser
from cloudshell.orch.training.services.sandbox_api import SandboxAPIService
from cloudshell.orch.training.services.sandbox_lifecycle import SandboxLifecycleService
from cloudshell.orch.training.services.sandbox_output import SandboxOutputService
from cloudshell.orch.training.logic.teardown_user_sandboxes import SandboxTerminateLogic
from cloudshell.orch.training.services.users_data_manager import UsersDataManagerService


class TrainingTeardownWorkflow(object):
    def __init__(self, sandbox: Sandbox, config: TrainingWorkflowConfig = None):
        self.config = config if config else TrainingWorkflowConfig()
        self.default_teardown_workflow = DefaultTeardownWorkflow()
        self._bootstrap(sandbox)

    def _bootstrap(self, sandbox: Sandbox):
        sandbox.logger.info("Bootstrapping teardown workflow")

        env_data = SandboxInputsParser.parse_sandbox_inputs(sandbox)
        sandbox_output_service = SandboxOutputService(sandbox, env_data.debug_enabled)
        sandbox_api_service = SandboxAPIService(sandbox, self.config.sandbox_api_port, sandbox_output_service)
        users_data_manager = UsersDataManagerService(sandbox)
        sandbox_lifecycle_service = SandboxLifecycleService(sandbox,sandbox_output_service,users_data_manager)
        self._sandbox_terminator = SandboxTerminateLogic(sandbox, sandbox_output_service, sandbox_api_service, sandbox_lifecycle_service,users_data_manager, env_data)


    def register(self, sandbox):
        """
        :param Sandbox sandbox:
        :return:
        """
        sandbox.logger.info("Adding default teardown orchestration")
        sandbox.workflow.add_to_teardown(self.default_teardown_workflow.default_teardown,None)
        sandbox.workflow.add_to_teardown( self._sandbox_terminator.teardown_student_sandboxes, None)