import unittest

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
