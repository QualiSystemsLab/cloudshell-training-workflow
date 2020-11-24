from cloudshell.workflow.orchestration.sandbox import Sandbox
from cloudshell.workflow.orchestration.setup.default_setup_orchestrator import DefaultSetupWorkflow

from cloudshell.workflow.training.parsers.sandbox_inputs_processing import SandboxInputsParser
from cloudshell.workflow.training.logic.create_user_sandboxes import UserSandboxesLogic
from cloudshell.workflow.training.logic.initialize_env import InitializeEnvironmentLogic
from cloudshell.workflow.training.models.config import TrainingWorkflowConfig
from cloudshell.workflow.training.models.training_env import TrainingEnvironmentDataModel
from cloudshell.workflow.training.services.sandbox_components import SandboxComponentsHelperService
from cloudshell.workflow.training.services.email import EmailService
from cloudshell.workflow.training.services.ip_increment_strategy import RequestedIPsIncrementStrategy
from cloudshell.workflow.training.services.ips_handler import IPsHandlerService
from cloudshell.workflow.training.services.sandbox_api import SandboxAPIService
from cloudshell.workflow.training.services.sandbox_lifecycle import SandboxLifecycleService
from cloudshell.workflow.training.services.sandbox_output import SandboxOutputService
from cloudshell.workflow.training.services.student_links import StudentLinksProvider
from cloudshell.workflow.training.services.users import UsersService
from cloudshell.workflow.training.services.users_data_manager import UsersDataManagerService


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

        # parse sandbox inputs
        self.env_data = SandboxInputsParser.parse_sandbox_inputs(self.sandbox)

        # init services
        self._users_data_manager = UsersDataManagerService(self.sandbox)
        sandbox_output_service = SandboxOutputService(self.sandbox, self.env_data.debug_enabled)
        sandbox_create_service = SandboxLifecycleService(self.sandbox, sandbox_output_service, self._users_data_manager)
        sandbox_api_service = SandboxAPIService(self.sandbox, self.config.sandbox_api_port, sandbox_output_service)
        email_service = EmailService(self.config.email_config, sandbox_output_service, self.sandbox.logger)
        student_links_provider = StudentLinksProvider(self.config.training_portal_base_url, self.sandbox,
                                                      sandbox_api_service)
        apps_service = SandboxComponentsHelperService(sandbox_output_service)
        users_service = UsersService(self.sandbox.automation_api, self.sandbox.logger)
        ips_increment_service = RequestedIPsIncrementStrategy(IPsHandlerService(), self.sandbox.logger)

        # init logic
        self.user_sandbox_logic = UserSandboxesLogic(self.env_data, sandbox_output_service, self._users_data_manager,
                                                     sandbox_create_service, email_service, student_links_provider,
                                                     apps_service)
        self.init_logic = InitializeEnvironmentLogic(self.env_data, self.config, self._users_data_manager,
                                                     sandbox_output_service, apps_service, sandbox_create_service,
                                                     users_service, ips_increment_service)

    def initialize_and_register(self, enable_provisioning: bool = True, enable_connectivity: bool = True,
                                enable_configuration: bool = True):
        self.initialize()
        self.register(enable_provisioning, enable_connectivity, enable_configuration)

    def initialize(self):
        """
        Prepare the sandbox environment before sandbox execution
        """
        # load sandbox data
        self._users_data_manager.load()

        # prepare environment before setup execution
        self.init_logic.prepare_environment(self.sandbox)

    def register(self, enable_provisioning: bool = True, enable_connectivity: bool = True,
                 enable_configuration: bool = True):
        self.sandbox.logger.info("Adding training setup orchestration")

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
            self.sandbox.workflow.on_configuration_ended(self._do_on_configuration_ended, None)

    def _do_on_configuration_ended(self, sandbox, components):
        self.user_sandbox_logic.create_user_sandboxes(sandbox, components)
        # persist to sandbox data the users data
        self._users_data_manager.save()

