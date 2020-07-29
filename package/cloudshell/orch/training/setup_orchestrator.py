from cloudshell.workflow.orchestration.sandbox import Sandbox
from cloudshell.workflow.orchestration.setup.default_setup_orchestrator import DefaultSetupWorkflow


class TrainingSetupWorkflow(object):
    def __init__(self):
        self.default_setup_workflow = DefaultSetupWorkflow()

    def register(self, sandbox: Sandbox, enable_provisioning: bool = True, enable_connectivity: bool = True,
                 enable_configuration: bool = True):
        sandbox.logger.info("Adding training  setup orchestration")

        # TODO - add here calls to our training workflow logic

        if enable_provisioning:
            sandbox.logger.debug("Default provisioning is added to sandbox orchestration")
            sandbox.workflow.add_to_provisioning(self.default_setup_workflow.default_provisioning, None)

        if enable_connectivity:
            sandbox.logger.debug("Default connectivity is added to sandbox orchestration")
            sandbox.workflow.add_to_connectivity(self.default_setup_workflow.default_connectivity, None)

        if enable_configuration:
            sandbox.logger.debug("Default configuration is added to sandbox orchestration")
            sandbox.workflow.add_to_configuration(self.default_setup_workflow.default_configuration, None)
