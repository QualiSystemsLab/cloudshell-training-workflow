from cloudshell.workflow.orchestration.sandbox import Sandbox
from cloudshell.workflow.orchestration.setup.default_setup_orchestrator import DefaultSetupWorkflow

from package.cloudshell.orch.training.models.training_env import TrainingEnvironmentDataModel
from package.cloudshell.orch.training.services.sandbox_output import SandboxOutputService
from package.cloudshell.orch.training.services.users_data_manager import UsersDataManagerService
from cloudshell.orch.training.parsers.sandbox_inputs_processing import SandboxInputsParser


class TrainingSetupWorkflow(object):
    def __init__(self):
        self.default_setup_workflow = DefaultSetupWorkflow()


    def register(self, sandbox: Sandbox, enable_provisioning: bool = True, enable_connectivity: bool = True,
                 enable_configuration: bool = True):

        self.bootstrap(sandbox)
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

    def bootstrap(self,sandbox: Sandbox):
        self.data = TrainingEnvironmentDataModel(sandbox)
        self.userdata_svc = UsersDataManagerService(sandbox)
        self.training_users_list = SandboxInputsParser.sandbox_user_list(sandbox)
        self.instructor_mode = SandboxInputsParser.is_instructor_mode(sandbox)
        debug_enabled = SandboxInputsParser.is_debug_on(sandbox)
        self.output_svc = SandboxOutputService(sandbox,debug_enabled)



