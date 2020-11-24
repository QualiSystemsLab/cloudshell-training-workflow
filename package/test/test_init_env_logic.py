import unittest
import random

from mock import Mock, call, MagicMock

from cloudshell.workflow.training.logic.initialize_env import InitializeEnvironmentLogic


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



