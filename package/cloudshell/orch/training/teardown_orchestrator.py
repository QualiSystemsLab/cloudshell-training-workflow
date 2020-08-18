from cloudshell.workflow.orchestration.sandbox import Sandbox
from cloudshell.workflow.orchestration.teardown.default_teardown_orchestrator import DefaultTeardownWorkflow

from cloudshell.orch.training.parsers.sandbox_inputs_processing import SandboxInputsParser
from cloudshell.orch.training.services.sandbox_output import SandboxOutputService


class TrainingTeardownWorkflow(object):
    def __init__(self):
        self.default_teardown_workflow = DefaultTeardownWorkflow()

    def _bootstrap(self, sandbox: Sandbox):
        sandbox.logger.info("Bootstrapping teardown workflow")

        env_data = SandboxInputsParser.parse_sandbox_inputs(sandbox)
        sandbox_output_service = SandboxOutputService(sandbox, env_data.debug_enabled)


    def register(self, sandbox):
        """
        :param Sandbox sandbox:
        :return:
        """
        self._bootstrap(sandbox)

        sandbox.logger.info("Adding default teardown orchestration")
        sandbox.workflow.add_to_teardown(self.default_teardown, None)