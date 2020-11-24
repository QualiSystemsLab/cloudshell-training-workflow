import unittest

from cloudshell.api.cloudshell_api import CloudShellAPISession, GetReservationDescriptionResponseInfo, \
    ReservedResourceInfo, ServiceInstance, ReservationAppResource
from cloudshell.api.common_cloudshell_api import CloudShellAPIError
from cloudshell.workflow.orchestration.sandbox import Sandbox
from mock import Mock, patch

from cloudshell.orch.training.services.sandbox_lifecycle import SandboxLifecycleService
from cloudshell.orch.training.services.users_data_manager import UsersDataManagerService


class TestSandboxCreateService(unittest.TestCase):

    def test_create_trainee_sandbox(self):
        # arrange
        sandbox = Mock()
        sandbox.automation_api = Mock()
        new_reservation = Mock()
        sandbox.automation_api.CreateImmediateTopologyReservation = Mock(return_value=new_reservation)
        sandbox_output = Mock()
        user_data_manager = Mock()
        sandbox_create_service = SandboxLifecycleService(sandbox, sandbox_output, user_data_manager)
        user = Mock()
        user_id = Mock()
        duration = Mock()

        # act
        result = sandbox_create_service.create_trainee_sandbox(sandbox.reservationContextDetails.environment_name,
                                                               user, user_id, duration)

        # assert
        self.assertEqual(result, new_reservation.Reservation)

    @patch("cloudshell.orch.training.services.sandbox_lifecycle.sleep")
    def test_wait_ready(self, sleep_patch):
        # arrange
        sandbox = Mock(automation_api=Mock())
        sandbox.automation_api.GetReservationStatus = Mock(side_effect=[self._get_res_status_mock('Started', 'bla1'),
                                                                        self._get_res_status_mock('Started', 'bla2'),
                                                                        self._get_res_status_mock('Started', 'Ready')])
        sandbox_create_service = SandboxLifecycleService(sandbox, Mock(),Mock())

        # act & assert
        sandbox_create_service.wait_ready(Mock(), Mock())

    @patch("cloudshell.orch.training.services.sandbox_lifecycle.sleep")
    def test_wait_error(self, sleep_patch):
        # arrange
        sandbox = Mock(automation_api=Mock())
        sandbox.automation_api.GetReservationStatus = Mock(side_effect=[self._get_res_status_mock('Started', 'bla1'),
                                                                        self._get_res_status_mock('Started', 'Error')])
        sandbox_create_service = SandboxLifecycleService(sandbox, Mock(),Mock())

        # act & assert
        with self.assertRaises(Exception):
            sandbox_create_service.wait_ready(Mock(), Mock())

    @patch("cloudshell.orch.training.services.sandbox_lifecycle.sleep")
    def test_wait_teardown(self, sleep_patch):
        # arrange
        sandbox = Mock(automation_api=Mock())
        sandbox.automation_api.GetReservationStatus = Mock(side_effect=[self._get_res_status_mock('Started', 'bla1'),
                                                                        self._get_res_status_mock('Teardown', 'bla2')])
        sandbox_create_service = SandboxLifecycleService(sandbox, Mock(),Mock())

        # act & assert
        with self.assertRaises(Exception):
            sandbox_create_service.wait_ready(Mock(), Mock())

    @patch("cloudshell.orch.training.services.sandbox_lifecycle.sleep")
    def test_wait_completed(self, sleep_patch):
        # arrange
        sandbox = Mock(automation_api=Mock())
        sandbox.automation_api.GetReservationStatus = Mock(side_effect=[self._get_res_status_mock('Started', 'bla1'),
                                                                        self._get_res_status_mock('Completed', 'bla2')])
        sandbox_create_service = SandboxLifecycleService(sandbox, Mock(),Mock())

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
        self.logic = SandboxLifecycleService(self.sandbox, self.sandbox_output_service,self.users_data_manager)

    def test_end_student_reservation_student(self):
        # arrange
        mock_obj = Mock()
        mock_obj.ReservationSlimStatus.Status = "NotCompleted"

        mock_api: CloudShellAPISession = Mock()
        mock_reservation_description = Mock()
        mock_resource: ReservedResourceInfo = Mock()
        mock_resource.Name = "mock_resource_name"
        mock_reservation_description.Resources = [mock_resource]

        mock_get_reservation_details: GetReservationDescriptionResponseInfo = Mock()
        mock_get_reservation_details.ReservationDescription = mock_reservation_description

        mock_api.GetReservationDetails = Mock(return_value=mock_get_reservation_details)
        mock_api.GetReservationStatus = Mock(return_value=mock_obj)
        self.logic._api = mock_api

        self.logic._sandbox.id = "mock_user_reservation_id"
        # act
        self.logic.end_student_reservation(Mock(),False)

        # assert
        self.logic._api.ExecuteCommand.assert_called_once_with("mock_user_reservation_id", "mock_resource_name", "Resource", "Power Off", [], True)

    def test_end_student_reservation_already_complete(self):
        # arrange
        mock_obj = Mock()
        mock_obj.ReservationSlimStatus.Status = "Completed"
        self.sandbox.automation_api.GetReservationStatus = Mock(return_value=mock_obj)
        # act
        self.logic.end_student_reservation(Mock(),Mock())
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
        self.logic.end_student_reservation(Mock(),Mock())

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
        self.logic.end_student_reservation(Mock(),Mock())
        # assert
        self.sandbox.automation_api.RemoveResourcesFromReservation.assert_called_once()
        self.sandbox.automation_api.EndReservation.assert_called_once()

    def test_clear_sandbox_components(self):
        # arrange
        mock_sandbox: Sandbox = Mock()
        mock_sandbox.id = "sandbox_id"
        mock_api: CloudShellAPISession = Mock()
        mock_sandbox.automation_api = mock_api
        mock_get_reservation_details:GetReservationDescriptionResponseInfo = Mock()
        mock_reservation_description = Mock()
        mock_resource:ReservedResourceInfo = Mock()
        mock_resource.Name = "mock_resource_name"
        mock_service:ServiceInstance = Mock()
        mock_service.Alias = "mock_alias"
        mock_app:ReservationAppResource = Mock()
        mock_app.Name = "mock_app_name"
        mock_reservation_description.Resources = [mock_resource]
        mock_reservation_description.Services = [mock_service]
        mock_reservation_description.Apps = [mock_app]
        mock_get_reservation_details.ReservationDescription = mock_reservation_description
        mock_api.GetReservationDetails = Mock(return_value=mock_get_reservation_details)

        # act
        self.logic.clear_sandbox_components(mock_sandbox)

        # assert
        mock_sandbox.automation_api.RemoveResourcesFromReservation.assert_called_once_with(mock_sandbox.id,[mock_resource.Name])
        mock_sandbox.automation_api.RemoveServicesFromReservation.assert_called_once_with(mock_sandbox.id,[mock_service.Alias])
        mock_sandbox.automation_api.RemoveAppFromReservation.assert_called_once_with(mock_sandbox.id,appName=mock_app.Name)

    def test_clear_sandbox_components_empty(self):
        # arrange
        mock_sandbox: Sandbox = Mock()
        mock_sandbox.id = "sandbox_id"
        mock_api: CloudShellAPISession = Mock()
        mock_sandbox.automation_api = mock_api
        mock_get_reservation_details:GetReservationDescriptionResponseInfo = Mock()
        mock_reservation_description = Mock()
        mock_reservation_description.Resources = []
        mock_reservation_description.Services = []
        mock_reservation_description.Apps = []
        mock_get_reservation_details.ReservationDescription = mock_reservation_description
        mock_api.GetReservationDetails = Mock(return_value=mock_get_reservation_details)

        # act
        self.logic.clear_sandbox_components(mock_sandbox)

        # assert
        mock_sandbox.automation_api.RemoveResourcesFromReservation.assert_not_called()
        mock_sandbox.automation_api.RemoveServicesFromReservation.assert_not_called()
        mock_sandbox.automation_api.RemoveAppFromReservation.assert_not_called()

    def test_clear_sandbox_components_ex(self):
        # arrange
        mock_sandbox: Sandbox = Mock()
        mock_sandbox.id = "sandbox_id"
        mock_api: CloudShellAPISession = Mock()
        mock_sandbox.automation_api = mock_api
        mock_get_reservation_details:GetReservationDescriptionResponseInfo = Mock()
        mock_reservation_description = Mock()
        mock_reservation_description.Resources = []
        mock_service: ServiceInstance = Mock()
        mock_service.Alias = "mock_alias"
        mock_reservation_description.Services = [mock_service]
        mock_reservation_description.Apps = []
        mock_get_reservation_details.ReservationDescription = mock_reservation_description
        mock_api.GetReservationDetails = Mock(return_value=mock_get_reservation_details)
        mock_api.RemoveServicesFromReservation = Mock(return_value=Exception)

        mock_api.RemoveServicesFromReservation.side_effect = Exception('')

        # act
        self.logic.clear_sandbox_components(mock_sandbox)

        # assert
        mock_sandbox.logger.exception.assert_called_once()