import unittest
from mock import Mock, MagicMock , patch

from cloudshell.orch.training.teardown_orchestrator import TrainingTeardownWorkflow


class TestTrainingTeardownWorkflow(unittest.TestCase):
    def setUp(self) -> None:
        self.sandbox = Mock()
        self.sandbox.global_inputs = {"Training Users": "test@test"}
        self.logic = TrainingTeardownWorkflow(self.sandbox)


    def test_register(self):
        # arrange

        # act
        self.logic.register(self.sandbox)

        # assert
        self.sandbox.workflow.add_to_teardown.assert_called_once()

