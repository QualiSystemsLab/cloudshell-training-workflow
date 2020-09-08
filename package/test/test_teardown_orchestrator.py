import unittest

from mock import Mock, MagicMock

from cloudshell.orch.training.models.config import TrainingWorkflowConfig
from cloudshell.orch.training.setup_orchestrator import TrainingSetupWorkflow


class TestTrainingTeardownWorkflow(unittest.TestCase):

    def test_register(self):
        # arrange
        #config = Mock(spec=TrainingWorkflowConfig())
        #setup = TrainingSetupWorkflow(config)
        sandbox = Mock()

        # act


        # assert

