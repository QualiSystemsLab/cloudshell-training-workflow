import unittest
from unittest.mock import Mock

from freezegun import freeze_time
from mock import MagicMock, call, ANY

from cloudshell.orch.training.logic.create_user_sandboxes import UserSandboxesLogic
from cloudshell.orch.training.models.position import Position
from cloudshell.orch.training.services.users_data_manager import UsersDataManagerServiceKeys as userDataKeys


class TestUserSandboxesLogic(unittest.TestCase):

    def setUp(self):
        self.env_data = Mock()
        self.sandbox_output_service = Mock()
        self.users_data_manager = Mock()
        self.sandbox_create_service = Mock()
        self.sandbox_api = Mock()
        self.config = Mock()
        self.logic = UserSandboxesLogic(self.config, self.env_data, self.sandbox_output_service, self.users_data_manager,
                                        self.sandbox_create_service, self.sandbox_api)

        self.sandbox = Mock()

    def test_create_no_user_list(self):
        # arrange
        self.env_data.users_list = []
        self.logic._get_latest_sandbox_details = Mock()

        # act
        self.logic.create(Mock(), Mock())

        # assert
        self.logic._get_latest_sandbox_details.assert_not_called()

    def test_create(self):
        # arrange
        sandbox_details_mock = Mock()
        self.logic._get_latest_sandbox_details = Mock(return_value=sandbox_details_mock)
        self.logic._create_user_sandboxes = Mock()
        self.logic._wait_for_active_sandboxes_and_add_duplicated_resources = Mock()
        self.logic._send_emails = Mock()

        # act
        self.logic.create(self.sandbox, Mock())

        # assert
        self.logic._get_latest_sandbox_details.assert_called_once_with(self.sandbox)
        self.logic._create_user_sandboxes.assert_called_once_with(self.sandbox, sandbox_details_mock)
        self.logic._wait_for_active_sandboxes_and_add_duplicated_resources.assert_called_once_with(self.sandbox,
                                                                                                   sandbox_details_mock)
        self.logic._send_emails.assert_called_once()

    def test_wait_for_active_sandboxes_and_add_duplicated_resources(self):
        def get_key_side_effect(*args, **kwargs):
            return args[0] + '_sandbox_id' if args[1] == userDataKeys.SANDBOX_ID else None

        # arrange
        sandbox_details = Mock()
        self.env_data.users_list = ['user1', 'user2']
        self.users_data_manager.get_key = Mock(side_effect=get_key_side_effect)

        self.logic._get_resource_positions = Mock(return_value=MagicMock())
        self.logic._get_shared_resources = Mock(return_value=['shared_r1'])
        self.logic._get_user_resources = Mock(side_effect=[['user1_r1', 'user1_r2'], ['user2_r1', 'user2_r2']])

        # act
        self.logic._wait_for_active_sandboxes_and_add_duplicated_resources(self.sandbox, sandbox_details)

        # assert
        self.sandbox_create_service.wait_ready.assert_has_calls([call('user1_sandbox_id', 'user1'),
                                                                 call('user2_sandbox_id', 'user2')])
        self.sandbox.automation_api.SetResourceSharedState.assert_has_calls(
            [call(self.sandbox.id, ['user1_r1', 'user1_r2', 'shared_r1'], isShared=True),
             call(self.sandbox.id, ['user2_r1', 'user2_r2', 'shared_r1'], isShared=True)]
        )
        self.sandbox.automation_api.AddResourcesToReservation.assert_has_calls(
            [call('user1_sandbox_id', ['user1_r1', 'user1_r2', 'shared_r1'], shared=True),
             call('user2_sandbox_id', ['user2_r1', 'user2_r2', 'shared_r1'], shared=True)]
        )
        self.assertEqual(self.sandbox.automation_api.SetReservationResourcePosition.call_count, 4)
        self.sandbox.automation_api.SetReservationResourcePosition.assert_has_calls([
            call('user1_sandbox_id', 'user1_r1', ANY, ANY),
            call('user1_sandbox_id', 'user1_r2', ANY, ANY),
            call('user2_sandbox_id', 'user2_r1', ANY, ANY),
            call('user2_sandbox_id', 'user2_r2', ANY, ANY)
        ], any_order=True)

    def test_get_resource_positions(self):
        # arrange
        resource_positions = [Mock(ResourceName='r1', X=10, Y=10), Mock(ResourceName='r2', X=20, Y=20)]
        self.sandbox.automation_api.GetReservationResourcesPositions = \
            Mock(return_value=Mock(ResourceDiagramLayouts=resource_positions))

        # act
        result = self.logic._get_resource_positions(self.sandbox)

        # assert
        self.assertEqual(result, {'r1': Position(10, 10), 'r2': Position(20, 20)})

    def test_get_shared_resources(self):
        # arrange
        sandbox_details = Mock()
        sandbox_details.Resources = [Mock(AppTemplateName='t1', Name='r1'),
                                     Mock(AppTemplateName='t2', Name='r2'),
                                     Mock(AppTemplateName='t1', Name='r3'),
                                     Mock(AppTemplateName='t3', Name='r4')]
        self.env_data.shared_apps = ['t1', 't2']

        # act
        result = self.logic._get_shared_resources(sandbox_details)

        # assert
        self.assertEqual(result, ['r1', 'r2', 'r3'])

    def test_get_user_resources(self):
        # arrange
        sandbox_details = Mock(Resources=[Mock(Name='r1'), Mock(Name='user1_r1'), Mock(Name='user1_r2')])
        self.users_data_manager.get_key = Mock(return_value='user1')

        # act
        result = self.logic._get_user_resources(sandbox_details, Mock())

        # assert
        self.assertEqual(result, ['user1_r1', 'user1_r2'])

    @freeze_time("2020-01-01")
    def test_calculate_user_sandbox_duration(self):
        # arrange
        sandbox_details = Mock(EndTime="01/01/2020 02:00")

        # act
        result = self.logic._calculate_user_sandbox_duration(sandbox_details)

        # assert
        self.assertEqual(result, 120)

    def test_create_user_sandboxes(self):
        # arrange
        sandbox_details = Mock()
        self.logic._calculate_user_sandbox_duration = Mock()
        trainee_sandbox = Mock()
        self.sandbox_create_service.create_trainee_sandbox = Mock(return_value=trainee_sandbox)
        self.sandbox_api.create_token = Mock(return_value='token')
        self.env_data.users_list = ['user']
        self.config.training_portal_base_url = 'http://training-portal:8080'

        # act
        self.logic._create_user_sandboxes(self.sandbox, sandbox_details)

        # assert
        self.users_data_manager.add_or_update.assert_has_calls([
            call('user', userDataKeys.SANDBOX_ID, trainee_sandbox.Id),
            call('user', userDataKeys.TOKEN, 'token'),
            call('user', userDataKeys.STUDENT_LINK, f"{self.config.training_portal_base_url}/{trainee_sandbox.Id}?access=token")
        ])

    @unittest.skip
    def test_send_emails(self):
        # arrange
        self.logic._get_resource_positions = Mock()
        self.logic._get_shared_resources = MagicMock()
        self.env_data.users_list = ['user1']
