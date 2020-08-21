import unittest

from mock import Mock, patch

from cloudshell.orch.training.services.sandbox_create import SandboxCreateService


class TestSandboxCreateService(unittest.TestCase):

    def test_create_trainee_sandbox(self):
        # arrange
        sandbox = Mock()
        sandbox.automation_api = Mock()
        new_reservation = Mock()
        sandbox.automation_api.CreateImmediateTopologyReservation = Mock(return_value=new_reservation)
        sandbox_output = Mock()
        sandbox_create_service = SandboxCreateService(sandbox.automation_api, sandbox_output)
        user = Mock()
        user_id = Mock()
        duration = Mock()

        # act
        result = sandbox_create_service.create_trainee_sandbox(Mock(), user, user_id, duration)

        # assert
        self.assertEqual(result, new_reservation.Reservation)

    @patch("cloudshell.orch.training.services.sandbox_create.sleep")
    def test_wait_ready(self, sleep_patch):
        # arrange
        sandbox = Mock(automation_api=Mock())
        sandbox.automation_api.GetReservationStatus = Mock(side_effect=[self._get_res_status_mock('Started', 'bla1'),
                                                                        self._get_res_status_mock('Started', 'bla2'),
                                                                        self._get_res_status_mock('Started', 'Ready')])
        sandbox_create_service = SandboxCreateService(sandbox.automation_api, Mock())

        # act & assert
        sandbox_create_service.wait_ready(Mock(), Mock())

    @patch("cloudshell.orch.training.services.sandbox_create.sleep")
    def test_wait_error(self, sleep_patch):
        # arrange
        sandbox = Mock(automation_api=Mock())
        sandbox.automation_api.GetReservationStatus = Mock(side_effect=[self._get_res_status_mock('Started', 'bla1'),
                                                                        self._get_res_status_mock('Started', 'Error')])
        sandbox_create_service = SandboxCreateService(sandbox.automation_api, Mock())

        # act & assert
        with self.assertRaises(Exception):
            sandbox_create_service.wait_ready(Mock(), Mock())

    @patch("cloudshell.orch.training.services.sandbox_create.sleep")
    def test_wait_teardown(self, sleep_patch):
        # arrange
        sandbox = Mock(automation_api=Mock())
        sandbox.automation_api.GetReservationStatus = Mock(side_effect=[self._get_res_status_mock('Started', 'bla1'),
                                                                        self._get_res_status_mock('Teardown', 'bla2')])
        sandbox_create_service = SandboxCreateService(sandbox.automation_api, Mock())

        # act & assert
        with self.assertRaises(Exception):
            sandbox_create_service.wait_ready(Mock(), Mock())

    @patch("cloudshell.orch.training.services.sandbox_create.sleep")
    def test_wait_completed(self, sleep_patch):
        # arrange
        sandbox = Mock(automation_api=Mock())
        sandbox.automation_api.GetReservationStatus = Mock(side_effect=[self._get_res_status_mock('Started', 'bla1'),
                                                                        self._get_res_status_mock('Completed', 'bla2')])
        sandbox_create_service = SandboxCreateService(sandbox.automation_api, Mock())

        # act & assert
        with self.assertRaises(Exception):
            sandbox_create_service.wait_ready(Mock(), Mock())

    def _get_res_status_mock(self, status: str, provisioning_status: str) -> Mock:
        return Mock(ReservationSlimStatus=
                    Mock(Status=status, ProvisioningStatus=provisioning_status))
