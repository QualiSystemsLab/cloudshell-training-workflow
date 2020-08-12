from cloudshell.workflow.orchestration.sandbox import Sandbox
from cloudshell.workflow.orchestration.setup.default_setup_orchestrator import DefaultSetupWorkflow

from cloudshell.orch.training.logic.create_user_sandboxes import UserSandboxesLogic
from cloudshell.orch.training.models.config import TrainingWorkflowConfig
from cloudshell.orch.training.models.training_env import TrainingEnvironmentDataModel
from cloudshell.orch.training.services.email import EmailService
from cloudshell.orch.training.services.sandbox_api import SandboxAPIService
from cloudshell.orch.training.services.sandbox_create import SandboxCreateService
from cloudshell.orch.training.services.sandbox_output import SandboxOutputService
from cloudshell.orch.training.services.student_links import StudentLinksProvider
from cloudshell.orch.training.services.users_data_manager import UsersDataManagerService


class TrainingSetupWorkflow(object):
    def __init__(self, config: TrainingWorkflowConfig = None):
        self.default_setup_workflow = DefaultSetupWorkflow()
        self.config = config if config else TrainingWorkflowConfig()

    # todo - consider moving to a bootstrap class
    def _bootstrap(self, sandbox: Sandbox):
        sandbox.logger.info("Bootstrapping setup workflow")

        env_data = TrainingEnvironmentDataModel()  # todo - init data, need to merge sandbox inputs parser from Dans branch
        sandbox_output_service = SandboxOutputService(sandbox, env_data.debug_enabled)
        users_data_manager = UsersDataManagerService(sandbox)
        sandbox_create_service = SandboxCreateService(sandbox, sandbox_output_service)
        sandbox_api_service = SandboxAPIService(sandbox, self.config.sandbox_api_port, sandbox_output_service)
        email_service = EmailService(self.config.email_config, sandbox_output_service, sandbox.logger)
        student_links_provider = StudentLinksProvider(self.config.training_portal_base_url, sandbox, sandbox_api_service)

        self.user_sandbox_logic = UserSandboxesLogic(env_data, sandbox_output_service, users_data_manager,
                                                     sandbox_create_service, email_service, student_links_provider)

    def register(self, sandbox: Sandbox, enable_provisioning: bool = True, enable_connectivity: bool = True,
                 enable_configuration: bool = True):
        sandbox.logger.info("Adding training setup orchestration")

        self._bootstrap(sandbox)

        # TODO - add here calls to our training workflow logic
        # TODO - do we want to allow stages enable/disable?

        if enable_provisioning:
            sandbox.logger.debug("Default provisioning is added to sandbox orchestration")
            sandbox.workflow.add_to_provisioning(self.default_setup_workflow.default_provisioning, None)

        if enable_connectivity:
            sandbox.logger.debug("Default connectivity is added to sandbox orchestration")
            sandbox.workflow.add_to_connectivity(self.default_setup_workflow.default_connectivity, None)

        if enable_configuration:
            sandbox.logger.debug("Default configuration is added to sandbox orchestration")
            sandbox.workflow.add_to_configuration(self.default_setup_workflow.default_configuration, None)

        sandbox.logger.debug("Create user sandboxes logic is added to sandbox orchestration")
        sandbox.workflow.on_configuration_ended(self.user_sandbox_logic.create_user_sandboxes, None)
