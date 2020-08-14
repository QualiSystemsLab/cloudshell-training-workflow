from cloudshell.workflow.orchestration.sandbox import Sandbox
from cloudshell.workflow.orchestration.teardown.default_teardown_orchestrator import DefaultTeardownWorkflow




class TrainingTeardownWorkflow(object):
    def __init__(self):
        self.default_teardown_workflow = DefaultTeardownWorkflow()

    def _bootstrap(self, sandbox: Sandbox):
        sandbox.logger.info("Bootstrapping teardown workflow")

    def register(self, sandbox):
        """
        :param Sandbox sandbox:
        :return:
        """
        sandbox.logger.info("Adding default teardown orchestration")
        sandbox.workflow.add_to_teardown(self.default_teardown, None)