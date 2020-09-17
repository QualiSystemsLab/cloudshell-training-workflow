import unittest
from mock import Mock, MagicMock, patch, call

from cloudshell.orch.training.teardown_orchestrator import TrainingTeardownWorkflow


class TestTrainingTeardownWorkflow(unittest.TestCase):
    def setUp(self) -> None:
        self.sandbox = Mock()
        self.sandbox.global_inputs = {"Training Users": "test@test"}

    @patch('cloudshell.orch.training.teardown_orchestrator.TrainingTeardownWorkflow._initialize')
    def test_register(self, initialiaze_mock):
        # arrange
        teardown = TrainingTeardownWorkflow(self.sandbox)
        teardown.default_teardown_workflow.default_teardown = Mock()
        teardown._sandbox_terminator.teardown_student_sandboxes = Mock()

        # act
        teardown.register(self.sandbox)

        # assert
        self.sandbox.workflow.before_teardown_started.assert_called_with(
           teardown._sandbox_terminator.teardown_student_sandboxes, None)
        self.sandbox.workflow.add_to_teardown.assert_called_with(
            teardown.default_teardown_workflow.default_teardown, None)

    @patch('cloudshell.orch.training.teardown_orchestrator.UsersDataManagerService')
    def test_users_data_loaded_on_init(self, user_data_manager_service_mock):
        # act
        teardown = TrainingTeardownWorkflow(self.sandbox)

        # assert
        teardown._users_data_manager.load.assert_called()