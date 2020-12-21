import unittest

from cloudshell.workflow.orchestration.sandbox import Sandbox
from mock import Mock, MagicMock, patch

from cloudshell.workflow.training.models.config import TrainingWorkflowConfig
from cloudshell.workflow.training.setup_orchestrator import TrainingSetupWorkflow


class TestTrainingSetupWorkflow(unittest.TestCase):

    def setUp(self) -> None:
        config = Mock(spec=TrainingWorkflowConfig())
        self.sandbox = Mock(global_inputs=MagicMock())
        self.setup = TrainingSetupWorkflow(self.sandbox, config)

    def test_register(self):
        # act
        self.setup.register(self.sandbox)

        # assert
        self.sandbox.workflow.add_to_provisioning.assert_called_once_with(
            self.setup.default_setup_workflow.default_provisioning, None)
        self.sandbox.workflow.add_to_connectivity.assert_called_once_with(
            self.setup.default_setup_workflow.default_connectivity, None)
        self.sandbox.workflow.add_to_configuration.assert_called_once_with(
            self.setup.default_setup_workflow.default_configuration, None)
        self.sandbox.workflow.on_configuration_ended.assert_called_once_with(
            self.setup._do_on_configuration_ended, None)

    def test_register_negative(self):
        # arrange
        self.setup.env_data.instructor_mode = False


        # act
        self.setup.register(False, False, False)

        # assert
        self.sandbox.workflow.add_to_provisioning.assert_not_called()
        self.sandbox.workflow.add_to_connectivity.assert_not_called()
        self.sandbox.workflow.add_to_configuration.assert_not_called()
        self.sandbox.workflow.on_configuration_ended.assert_not_called()

    @patch('cloudshell.workflow.training.setup_orchestrator.UsersDataManagerService')
    def test_initialize(self, users_data_manager_class):
        # arrange
        self.setup._users_data_manager.load = Mock()
        self.setup.init_logic.prepare_environment = Mock()

        # act
        self.setup.initialize()

        # assert
        self.setup.init_logic.prepare_environment.assert_called_once()
        self.setup._users_data_manager.load.assert_called_once()
        self.setup.init_logic.prepare_environment.assert_called_once()

    def test_do_on_configuration_ended(self):
        # arrange
        mock_sandbox: Sandbox = Mock()
        mock_components = Mock()
        self.setup._users_data_manager.save = Mock()
        self.setup.user_sandbox_logic.create_user_sandboxes = Mock()

        # act
        self.setup._do_on_configuration_ended(mock_sandbox,mock_components)

        # assert
        self.setup.user_sandbox_logic.create_user_sandboxes.assert_called_once_with(mock_sandbox,mock_components)
        self.setup._users_data_manager.save.assert_called_once()

    def test_initialize_and_register(self):
        # arrange
        self.setup.initialize = Mock()
        self.setup.register = Mock()

        # act
        self.setup.initialize_and_register()

        # assert
        self.setup.initialize.assert_called_once()
        self.setup.register.assert_called_once()
