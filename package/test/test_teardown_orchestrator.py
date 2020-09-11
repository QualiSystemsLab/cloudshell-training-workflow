import unittest
from mock import Mock, MagicMock , patch,call

from cloudshell.orch.training.teardown_orchestrator import TrainingTeardownWorkflow


class TestTrainingTeardownWorkflow(unittest.TestCase):
    def setUp(self) -> None:
        self.sandbox = Mock()
        self.sandbox.global_inputs = {"Training Users": "test@test"}
        self.logic = TrainingTeardownWorkflow(self.sandbox)


    def test_register(self):
        # arrange

        # act
        self.logic.default_teardown_workflow.default_teardown = Mock()
        self.logic._sandbox_terminator.teardown_student_sandboxes = Mock()
        self.logic.register(self.sandbox)

        # assert
        self.sandbox.workflow.add_to_teardown.assert_has_calls([call(self.logic.default_teardown_workflow.default_teardown,None),call(  self.logic._sandbox_terminator.teardown_student_sandboxes,None)])


