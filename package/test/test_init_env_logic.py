import unittest
import random
from typing import List, Dict

from cloudshell.api.cloudshell_api import ReservationAppResource, AttributeNameValue, Connector, CloudShellAPISession, \
    DeploymentPathInfo, ReservationDescriptionInfo
from mock import Mock, call, MagicMock

from cloudshell.orch.training.logic.initialize_env import InitializeEnvironmentLogic
from cloudshell.orch.training.models.position import Position


class TestInitializeEnvironmentLogic(unittest.TestCase):
    def setUp(self) -> None:
        self.env_data = Mock()
        self.config = Mock()
        users_data_manager = Mock()
        sandbox_output_service = Mock()
        self.components_service = Mock()
        self.sandbox_service = Mock()
        self.users_service = Mock()
        ips_increment_provider = Mock()
        self.init_env_logic = InitializeEnvironmentLogic(self.env_data, self.config, users_data_manager,
                                                         sandbox_output_service, self.components_service,
                                                         self.sandbox_service, self.users_service,
                                                         ips_increment_provider)

    def test_prepare_environment_student(self):
        # arrange
        self.env_data.instructor_mode = False

        # act
        self.init_env_logic.prepare_environment(Mock())

        # assert
        self.sandbox_service.clear_sandbox_components.assert_called_once()

    def test_prepare_environment_instructor(self):
        # arrange
        self.env_data.instructor_mode = True
        self.init_env_logic._create_or_activate_users = Mock()
        self.init_env_logic._duplicate_students_apps = Mock()

        # act
        self.init_env_logic.prepare_environment(Mock())

        # assert
        self.init_env_logic._create_or_activate_users.assert_called_once()
        self.init_env_logic._duplicate_students_apps.assert_called_once()

    def test_create_or_activate_users(self):
        # arrange
        sandbox = Mock()
        user1 = Mock()
        user2 = Mock()
        self.env_data.users_list = [user1, user2]

        # act
        self.init_env_logic._create_or_activate_users(sandbox)

        # assert
        self.users_service.create_training_users_group.assert_called_once_with(sandbox.id,
                                                                               sandbox.reservationContextDetails.domain)
        self.users_service.create_or_activate_training_user.assert_has_calls([call(user1), call(user2)])
        self.users_service.add_training_users_to_group.assert_called_once_with(sandbox.id, self.env_data.users_list)

    def test_duplicate_students_apps(self):
        # arrange
        sandbox = Mock()
        sandbox.components.apps.values.return_value = MagicMock()
        self.components_service.get_apps_to_connectors_dict = Mock()
        update_req_1 = Mock()
        self.init_env_logic._prepare_requested_vnic_attr_connector_changes = Mock(return_value=[update_req_1])
        update_req_2 = Mock()
        self.init_env_logic._duplicate_apps = Mock(return_value=[update_req_2])

        # act
        self.init_env_logic._duplicate_students_apps(sandbox)

        # assert
        sandbox.automation_api.SetConnectorAttributes.assert_has_calls([
            call(sandbox.id, update_req_1.Source, update_req_1.Target, update_req_1.AttributeRequests),
            call(sandbox.id, update_req_2.Source, update_req_2.Target, update_req_2.AttributeRequests)
        ])

    def test_calculate_duplicate_app_position(self):
        # arrange
        app_pos = Mock(Y=100)
        user_index = random.randint(1, 9)

        # act
        result = self.init_env_logic._calculate_duplicate_app_position(app_pos, user_index)

        # assert
        self.assertEqual(result.X, app_pos.X)
        self.assertEqual(result.Y, 100 + 100 * (user_index + 1))

    def test_calculate_IP_increment(self):
        # arrange
        user_index = random.randint(1, 9)
        self.config.app_duplicate_ip_increment = 10

        # act
        result = self.init_env_logic._calculate_IP_increment(user_index)

        # assert
        self.assertEqual(result, (user_index + 1) * 10)

    def test_create_duplicate_app_connectors_requests(self):
        # arrange
        mock_app: ReservationAppResource = Mock()
        mock_connector1: Connector = Mock()
        mock_connector1.Source = mock_app.Name
        mock_attr_name = Mock()
        mock_attr_val = Mock()
        mock_attribute = AttributeNameValue(mock_attr_name, mock_attr_val)
        mock_connector1.Attributes = [mock_attribute]

        mock_connector2: Connector = Mock()
        mock_connector2.Target = mock_app.Name
        mock_connector2.Attributes = []

        mock_app_connectors: List[Connector] = [mock_connector1, mock_connector2]

        # act
        returned_set_connector_requests, returned_connectors_attr_updates = self.init_env_logic._create_duplicate_app_connectors_requests(
            mock_app, mock_app_connectors, Mock())

        # assert
        # Checking that connector 2 without attributes was not added
        self.assertEqual(len(returned_set_connector_requests), 2)
        self.assertEqual(len(returned_connectors_attr_updates), 1)

    def test_duplicate_apps(self):
        # arrange
        mock_api: CloudShellAPISession = Mock()
        mock_app: ReservationAppResource = Mock()
        mock_app.Name = "mock_app_name"
        mock_apps: List[ReservationAppResource] = [mock_app]
        mock_app_connectors: Dict[str, List[Connector]] = MagicMock()
        mock_sandbox_id: str = Mock()
        self.init_env_logic._components_service.get_apps_to_duplicate = Mock(return_value=mock_apps)
        service_app_positions_dict = MagicMock()
        mock_service_app_positions = Mock()
        service_app_positions_dict.__getitem__ = MagicMock(return_value=mock_service_app_positions)
        self.init_env_logic._components_service.get_service_and_app_name_to_position_dict = MagicMock(
            return_value=service_app_positions_dict)
        self.init_env_logic._env_data.users_list = [Mock()]
        self.init_env_logic._duplicate_app_and_get_update_request = Mock()

        # act
        self.init_env_logic._duplicate_apps(mock_api, mock_apps, mock_app_connectors, mock_sandbox_id)

        # assert
        self.init_env_logic._duplicate_app_and_get_update_request.assert_called_once_with(mock_api, "1_mock_app_name",
                                                                                          mock_app, mock_sandbox_id,
                                                                                          mock_service_app_positions, 0)

    def test_duplicate_apps_none(self):
        # arrange
        mock_api: CloudShellAPISession = Mock()
        mock_app: ReservationAppResource = Mock()
        mock_app.Name = "mock_app_name"
        mock_apps: List[ReservationAppResource] = [mock_app]
        mock_app_connectors: Dict[str, List[Connector]] = MagicMock()
        mock_sandbox_id: str = Mock()
        self.init_env_logic._components_service.get_apps_to_duplicate = Mock(return_value=[])
        service_app_positions_dict = MagicMock()
        mock_service_app_positions = Mock()
        service_app_positions_dict.__getitem__ = MagicMock(return_value=mock_service_app_positions)
        self.init_env_logic._env_data.users_list = []
        self.init_env_logic._duplicate_app_and_get_update_request = []

        # act
        return_val = self.init_env_logic._duplicate_apps(mock_api, mock_apps, mock_app_connectors, mock_sandbox_id)

        # assert
        mock_api.EditAppsInReservation.assert_not_called()
        mock_api.SetConnectorsInReservation.assert_not_called()
        self.assertEqual(return_val, [])

    def test_get_private_ip_value_for_duplicate_app(self):
        # arrange
        mock_app: ReservationAppResource = Mock()
        mock_deployment_path: DeploymentPathInfo = Mock()
        self.init_env_logic._components_service.get_default_deployment_option = Mock(return_value=mock_deployment_path)
        mock_requested_ips_string = Mock()
        self.init_env_logic._components_service.get_deployment_attribute_value = Mock(
            return_value=mock_requested_ips_string)
        mock_app_duplicate_increment_octet = Mock()
        self.init_env_logic._config.app_duplicate_increment_octet = mock_app_duplicate_increment_octet
        mock_calculated_ip_increment = Mock()
        self.init_env_logic._calculate_IP_increment = Mock(return_value=mock_calculated_ip_increment)
        mock_user_index = Mock()

        # act
        return_value = self.init_env_logic._get_private_ip_value_for_duplicate_app(mock_app, mock_user_index)
        # assert
        self.init_env_logic._calculate_IP_increment.assert_called_once_with(mock_user_index)
        self.init_env_logic._ips_increment_provider.increment_requested_ips_string.assert_called_with(
            mock_requested_ips_string, mock_app_duplicate_increment_octet, \
            mock_calculated_ip_increment)

    def test_prepare_requested_vnic_attr_connector_changes(self):
        # arrange

        mock_mgmt_connector: Connector = Mock()
        mock_app_to_connectors_dict: Dict[str, List[Connector]] = MagicMock()
        mock_app_to_connectors_dict.__getitem__ = MagicMock(return_value=[mock_mgmt_connector])

        mock_sandbox_details: ReservationDescriptionInfo = Mock
        mock_app: ReservationAppResource = Mock()
        mock_sandbox_details.Apps = [mock_app]
        self.init_env_logic._does_app_has_multiple_connectors = Mock(return_value=True)
        self.init_env_logic._components_service.does_connector_has_existing_vnic_req = Mock(return_value=False)
        self.init_env_logic._components_service.get_management_connector = Mock(return_value=mock_mgmt_connector)
        self.init_env_logic._prepare_connector_change_req = Mock()

        # act
        self.init_env_logic._prepare_requested_vnic_attr_connector_changes(mock_app_to_connectors_dict,
                                                                           mock_sandbox_details)

        # assert
        self.init_env_logic._prepare_connector_change_req.assert_called_once_with(mock_app, mock_mgmt_connector, "0")

    def test_duplicate_app_and_get_update_request(self):
        # arrange
        mock_api: CloudShellAPISession = Mock()
        mock_new_app_name: str = "mock_new_app_name"
        mock_app: ReservationAppResource = Mock()
        mock_app.AppTemplateName = "mock_apptemplate_name"
        mock_app.Name = "mock_app_name"
        mock_sandbox_id: str = "mock_sandbox_id"
        mock_app_pos: Position = Mock()
        mock_user_index: int = random.randint(0, 100)
        mock_new_app_pos = Mock()
        mock_new_app_pos.X = random.randint(0, 100)
        mock_new_app_pos.Y = random.randint(0, 100)
        mock_return_position = Mock()
        mock_return_position.X = random.randint(0, 100)
        mock_return_position.Y = random.randint(0, 100)
        mock_api.AddAppToReservation = Mock(return_value=mock_new_app_pos)
        self.init_env_logic._calculate_duplicate_app_position = Mock(return_value=mock_new_app_pos)
        self.init_env_logic._config.app_duplicate_ip_increment = random.randint(0, 100)
        self.init_env_logic._get_private_ip_value_for_duplicate_app = Mock()
        default_deployment_option = Mock()
        self.components_service.get_default_deployment_option.return_value = default_deployment_option

        # act
        self.init_env_logic._duplicate_app_and_get_update_request(mock_api, mock_new_app_name, mock_app,
                                                                  mock_sandbox_id, mock_app_pos, mock_user_index)

        # assert
        self.init_env_logic._calculate_duplicate_app_position.assert_called_once_with(mock_app_pos, mock_user_index)
        mock_api.AddAppToReservation.assert_called_once_with(reservationId=mock_sandbox_id,
                                                             appName=mock_app.AppTemplateName,
                                                             deploymentPath=default_deployment_option.Name,
                                                             positionX=mock_new_app_pos.X, positionY=mock_new_app_pos.Y)
        self.init_env_logic._get_private_ip_value_for_duplicate_app.assert_called_once()
        self.init_env_logic._components_service.create_update_app_request.assert_called_once()
