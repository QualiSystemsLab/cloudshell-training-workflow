from cloudshell.workflow.orchestration.sandbox import Sandbox
from cloudshell.workflow.orchestration.setup.default_setup_orchestrator import DefaultSetupWorkflow

from package.cloudshell.orch.training.services.users_data_manager import UsersDataManagerService
from package.cloudshell.orch.training.services.sandbox_output import SandboxOutputService



class TrainingSetupWorkflow(object):
    def __init__(self):
        self.default_setup_workflow = DefaultSetupWorkflow()

        self.instructor_mode = False
        self.student_mode = False #remove Instructor=false->Student=True
        self.training_users_list = []

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
        sandbox_output = SandboxOutputService(sandbox,debug_enabled=)
        user_data_manager = UsersDataManagerService(sandbox)
        data_model = TrainingEnvironmentDataModel()
        self._logic1 = LogicClass()

        if "Training Users" in sandbox.global_inputs:
            self.users_list = sandbox.global_inputs.get("Training Users", "").split(";")
            if not len(self.users_list) > 1:
                self.training_users_list = []
            if self.users_list and "#" in self.users_list[0]:
                self.student_mode = True
            else:
                self.instructor_mode = True