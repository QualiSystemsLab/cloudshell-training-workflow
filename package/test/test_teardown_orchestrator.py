import unittest

from mock import Mock, MagicMock

from cloudshell.orch.training.models.config import TrainingWorkflowConfig
from cloudshell.orch.training.setup_orchestrator import TrainingSetupWorkflow


class TestTrainingTeardownWorkflow(unittest.TestCase):

    def test_register(self):
        # arrange
        #config = Mock(spec=TrainingWorkflowConfig())
        #setup = TrainingSetupWorkflow(config)
        #sandbox = Mock(global_inputs = MagicMock())

        # act
        setup.register(sandbox)

        # assert
        sandbox.workflow.add_to_provisioning.assert_called_once_with(
            setup.default_setup_workflow.default_provisioning, None)
        sandbox.workflow.add_to_connectivity.assert_called_once_with(
            setup.default_setup_workflow.default_connectivity, None)
        sandbox.workflow.add_to_configuration.assert_called_once_with(
            setup.default_setup_workflow.default_configuration, None)
        sandbox.workflow.on_configuration_ended.assert_called_once_with(
            setup.user_sandbox_logic.create_user_sandboxes, None)
