import unittest

from mock import Mock, patch

from cloudshell.orch.training.services.sandbox_lifecycle import SandboxCreateService, SandboxTerminateService


class TestSandboxCreateService(unittest.TestCase):

    def test_create_trainee_sandbox(self):
        # arrange
        sandbox = Mock()
        sandbox.automation_api = Mock()
        new_reservation = Mock()
        sandbox.automation_api.CreateImmediateTopologyReservation = Mock(return_value=new_reservation)
        sandbox_output = Mock()
        sandbox_create_service = SandboxCreateService(sandbox, sandbox_output)
        user = Mock()
        user_id = Mock()
        duration = Mock()

        # act
        result = sandbox_create_service.create_trainee_sandbox(user, user_id, duration)

        # assert
        self.assertEqual(result, new_reservation.Reservation)

    @patch("cloudshell.orch.training.services.sandbox_create.sleep")
    def test_wait_ready(self, sleep_patch):
        # arrange
        sandbox = Mock(automation_api=Mock())
        sandbox.automation_api.GetReservationStatus = Mock(side_effect=[self._get_res_status_mock('Started', 'bla1'),
                                                                        self._get_res_status_mock('Started', 'bla2'),
                                                                        self._get_res_status_mock('Started', 'Ready')])
        sandbox_create_service = SandboxCreateService(sandbox, Mock())

        # act & assert
        sandbox_create_service.wait_ready(Mock(), Mock())

    @patch("cloudshell.orch.training.services.sandbox_create.sleep")
    def test_wait_error(self, sleep_patch):
        # arrange
        sandbox = Mock(automation_api=Mock())
        sandbox.automation_api.GetReservationStatus = Mock(side_effect=[self._get_res_status_mock('Started', 'bla1'),
                                                                        self._get_res_status_mock('Started', 'Error')])
        sandbox_create_service = SandboxCreateService(sandbox, Mock())

        # act & assert
        with self.assertRaises(Exception):
            sandbox_create_service.wait_ready(Mock(), Mock())

    @patch("cloudshell.orch.training.services.sandbox_create.sleep")
    def test_wait_teardown(self, sleep_patch):
        # arrange
        sandbox = Mock(automation_api=Mock())
        sandbox.automation_api.GetReservationStatus = Mock(side_effect=[self._get_res_status_mock('Started', 'bla1'),
                                                                        self._get_res_status_mock('Teardown', 'bla2')])
        sandbox_create_service = SandboxCreateService(sandbox, Mock())

        # act & assert
        with self.assertRaises(Exception):
            sandbox_create_service.wait_ready(Mock(), Mock())

    @patch("cloudshell.orch.training.services.sandbox_create.sleep")
    def test_wait_completed(self, sleep_patch):
        # arrange
        sandbox = Mock(automation_api=Mock())
        sandbox.automation_api.GetReservationStatus = Mock(side_effect=[self._get_res_status_mock('Started', 'bla1'),
                                                                        self._get_res_status_mock('Completed', 'bla2')])
        sandbox_create_service = SandboxCreateService(sandbox, Mock())

        # act & assert
        with self.assertRaises(Exception):
            sandbox_create_service.wait_ready(Mock(), Mock())

    def _get_res_status_mock(self, status: str, provisioning_status: str) -> Mock:
        return Mock(ReservationSlimStatus=
                    Mock(Status=status, ProvisioningStatus=provisioning_status))

class TestSandboxTerminateService(unittest.TestCase):
    def setUp(self) -> None:

        self.sandbox = Mock()
        self.sandbox_output_service = Mock()
        self.users_data_manager = Mock()
        self.admin_login_token = Mock()
        self.logic = SandboxTerminateService(self.sandbox, self.sandbox_output_service,self.users_data_manager)

    def test_end_student_reservation_already_complete(self):
        # arrange
        mock_obj = Mock()
        mock_obj.ReservationSlimStatus.Status = "Completed"
        self.sandbox.automation_api.GetReservationStatus = Mock(return_value=mock_obj)
        # act
        self.logic.end_student_reservation(Mock())
        # assert
        self.sandbox.automation_api.EndReservation.assert_not_called()

    def test_end_student_reservation_already_still_running_no_shared(self):
        # arrange
        status_mock_obj = Mock()
        status_mock_obj.ReservationSlimStatus.Status = "NotCompleted"
        self.sandbox.automation_api.GetReservationStatus = Mock(return_value=status_mock_obj)
        instructor_and_student_resources_mock = Mock()

        instructor_and_student_resources_mock.Name= "resource_name"
        instructor_and_student_resources_mock.VmDetails = None
        instructor_reservation_details_mock = Mock()
        instructor_reservation_details_mock.ReservationDescription.Resources = [instructor_and_student_resources_mock]
        self.sandbox.automation_api.GetReservationDetails = Mock(return_value=instructor_reservation_details_mock)
        # act
        self.logic.end_student_reservation(Mock())

        # assert
        self.sandbox.automation_api.RemoveResourcesFromReservation.assert_not_called()
        self.sandbox.automation_api.EndReservation.assert_called_once()

    def test_end_student_reservation_already_still_running_shared(self):
        # arrange
        status_mock_obj = Mock()
        status_mock_obj.ReservationSlimStatus.Status = "NotCompleted"
        self.sandbox.automation_api.GetReservationStatus = Mock(return_value=status_mock_obj)
        instructor_and_student_resources_mock = Mock()

        instructor_and_student_resources_mock.Name = "resource_name"
        instructor_and_student_resources_mock.VmDetails = "vm"
        instructor_reservation_details_mock = Mock()
        instructor_reservation_details_mock.ReservationDescription.Resources = [instructor_and_student_resources_mock]
        self.sandbox.automation_api.GetReservationDetails = Mock(return_value=instructor_reservation_details_mock)

        # act
        self.logic.end_student_reservation(Mock())
        # assert
        self.sandbox.automation_api.RemoveResourcesFromReservation.assert_called_once()
        self.sandbox.automation_api.EndReservation.assert_called_once()