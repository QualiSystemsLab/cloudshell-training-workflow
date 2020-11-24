import unittest

from mock import Mock, MagicMock, call

from cloudshell.workflow.training.logic.teardown_user_sandboxes import SandboxTerminateLogic


class TestTeardownUserSandboxes(unittest.TestCase):
    def setUp(self) -> None:
        self.sandbox_output_service = Mock()
        self.sandbox_api = Mock()
        self.users_data_manager = Mock()
        self.admin_login_token = Mock()
        self.sandbox_api.login = Mock(return_value=self.admin_login_token)
        self.sandbox_termination_service = Mock()
        self.sandbox_lifecycle_service = Mock()
        self.training_env = Mock()
        self.users_service = Mock()

        self.logic = SandboxTerminateLogic(self.sandbox_output_service, self.sandbox_api,
                                           self.sandbox_lifecycle_service, self.users_data_manager, self.training_env,
                                           self.users_service)

    def test_teardown_student_sandboxes(self):
        # arrange
        sandbox = Mock()
        self.training_env.users_list = ['user1', 'user2']
        user1_token = Mock()
        user2_token = Mock()
        self.users_data_manager.get_key = Mock(side_effect=[user1_token, user2_token])
        self.logic._delete_students_group = Mock()
        self.logic._sandbox_lifecycle_service = Mock()

        # act
        self.logic.teardown_student_sandboxes(sandbox, None)

        # assert
        self.logic._sandbox_lifecycle_service.end_student_reservation.assert_has_calls([call('user1',self.logic._training_env.instructor_mode), call('user2',self.logic._training_env.instructor_mode)])
        self.logic._sandbox_api.delete_token.assert_has_calls(
            [call(api_token=self.admin_login_token, user_token=user1_token),
             call(api_token=self.admin_login_token, user_token=user2_token)])
        self.logic._delete_students_group.assert_called_once()

    def test_delete_students_group(self):
        # arrange
        sandbox = Mock()

        # act
        self.logic._delete_students_group(sandbox)

        # assert
        self.logic._users_service.delete_training_users_group(sandbox.id)