from cloudshell.workflow.orchestration.sandbox import Sandbox
from cloudshell.workflow.orchestration.setup.default_setup_orchestrator import DefaultSetupWorkflow

from cloudshell.orch.training.logic.create_user_sandboxes import UserSandboxesLogic
from cloudshell.orch.training.logic.prepare import PrepareEnvironmentLogic
from cloudshell.orch.training.models.config import TrainingWorkflowConfig
from cloudshell.orch.training.models.training_env import TrainingEnvironmentDataModel
from cloudshell.orch.training.services.apps import AppsService
from cloudshell.orch.training.services.email import EmailService
from cloudshell.orch.training.services.sandbox_api import SandboxAPIService
from cloudshell.orch.training.services.sandbox_create import SandboxCreateService
from cloudshell.orch.training.services.sandbox_output import SandboxOutputService
from cloudshell.orch.training.services.student_links import StudentLinksProvider
from cloudshell.orch.training.services.users_data_manager import UsersDataManagerService


class TrainingSetupWorkflow(object):
    def __init__(self, sandbox: Sandbox, config: TrainingWorkflowConfig = None):
        self.sandbox = sandbox
        self.default_setup_workflow = DefaultSetupWorkflow()
        self.config = config if config else TrainingWorkflowConfig()
        # bootstrap setup workflow data and services
        self._bootstrap()

    # todo - consider moving to a bootstrap class
    def _bootstrap(self):
        self.sandbox.logger.info("Bootstrapping setup workflow")

        self.env_data = TrainingEnvironmentDataModel()  # todo - init data, need to merge sandbox inputs parser from Dans branch
        sandbox_output_service = SandboxOutputService(self.sandbox, self.env_data.debug_enabled)
        users_data_manager = UsersDataManagerService(self.sandbox)
        sandbox_create_service = SandboxCreateService(self.sandbox, sandbox_output_service)
        sandbox_api_service = SandboxAPIService(self.sandbox, self.config.sandbox_api_port, sandbox_output_service)
        email_service = EmailService(self.config.email_config, sandbox_output_service, self.sandbox.logger)
        student_links_provider = StudentLinksProvider(self.config.training_portal_base_url, self.sandbox,
                                                      sandbox_api_service)
        apps_service = AppsService(sandbox_output_service)

        self.user_sandbox_logic = UserSandboxesLogic(self.env_data, sandbox_output_service, users_data_manager,
                                                     sandbox_create_service, email_service, student_links_provider,
                                                     apps_service)

        self.preparation_logic = PrepareEnvironmentLogic(self.env_data, users_data_manager, sandbox_output_service,
                                                         apps_service)

    def prepare_environment_and_register(self, enable_provisioning: bool = True, enable_connectivity: bool = True,
                                         enable_configuration: bool = True):
        self.prepare_environment()
        self.register(enable_provisioning, enable_connectivity, enable_configuration)

    def prepare_environment(self):
        """
        Prepare the sandbox environment before sandbox execution
        """
        # prepare environment before setup execution
        self.preparation_logic.prepare_environment(self.sandbox)

    def register(self, enable_provisioning: bool = True, enable_connectivity: bool = True,
                 enable_configuration: bool = True):
        self.sandbox.logger.info("Adding training setup orchestration")

        # TODO - add here calls to our training workflow logic

        if enable_provisioning:
            self.sandbox.logger.debug("Default provisioning is added to sandbox orchestration")
            self.sandbox.workflow.add_to_provisioning(self.default_setup_workflow.default_provisioning, None)

        if enable_connectivity:
            self.sandbox.logger.debug("Default connectivity is added to sandbox orchestration")
            self.sandbox.workflow.add_to_connectivity(self.default_setup_workflow.default_connectivity, None)

        if enable_configuration:
            self.sandbox.logger.debug("Default configuration is added to sandbox orchestration")
            self.sandbox.workflow.add_to_configuration(self.default_setup_workflow.default_configuration, None)

        if self.env_data.instructor_mode:
            self.sandbox.logger.debug("Create user sandboxes logic is added to sandbox orchestration")
            self.sandbox.workflow.on_configuration_ended(self.user_sandbox_logic.create_user_sandboxes, None)
