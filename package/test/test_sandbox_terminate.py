import unittest
from mock import Mock
from cloudshell.orch.training.services.sandbox_terminate import SandboxTerminateService


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
        # act
        self.logic.end_student_reservation(Mock())
        # assert
        self.sandbox.automation_api.RemoveResourcesFromReservation.assert_not_called()
        self.sandbox.automation_api.EndReservation.assert_called_once()

    def test_end_student_reservation_already_still_running_no_shared(self):
        # arrange
        status_mock_obj = Mock()
        status_mock_obj.ReservationSlimStatus.Status = "NotCompleted"
        self.sandbox.automation_api.GetReservationStatus = Mock(return_value=status_mock_obj)

        instructor_and_student_resources_mock = Mock()
        instructor_and_student_resources_mock.Name= "resource_name"
        instructor_and_student_resources_mock.VmDetails ="vmdetails"
        instructor_reservation_details_mock = Mock()
        instructor_reservation_details_mock.ReservationDescription.Resources = [instructor_and_student_resources_mock]
        self.sandbox.automation_api.GetReservationDetails = Mock(return_value=instructor_reservation_details_mock)

        # act
        self.logic.end_student_reservation(Mock())
        # assert
        self.sandbox.automation_api.EndReservation.assert_called_once()
        self.sandbox.automation_api.RemoveResourcesFromReservation.assert_called_once()