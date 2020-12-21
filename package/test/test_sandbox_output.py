import unittest

from mock import Mock

from cloudshell.workflow.training.services.sandbox_output import SandboxOutputService


class TestSandboxOutput(unittest.TestCase):

    def test_notify(self):
        # arrange
        sandbox = Mock(automation_api=Mock())
        output_service = SandboxOutputService(sandbox, Mock())
        message = Mock()

        # act
        output_service.notify(message)

        # assert
        sandbox.automation_api.WriteMessageToReservationOutput.assert_called_once_with(sandbox.id, message)

    def test_debug_enable(self):
        # arrange
        sandbox = Mock(automation_api=Mock())
        output_service = SandboxOutputService(sandbox, True)
        message = Mock()

        # act
        output_service.debug_print(message)

        # assert
        sandbox.automation_api.WriteMessageToReservationOutput.assert_called_once_with(sandbox.id, message)

    def test_debug_disabled(self):
        # arrange
        sandbox = Mock(automation_api=Mock())
        output_service = SandboxOutputService(sandbox, False)
        message = Mock()

        # act
        output_service.debug_print(message)

        # assert
        sandbox.automation_api.WriteMessageToReservationOutput.assert_not_called()