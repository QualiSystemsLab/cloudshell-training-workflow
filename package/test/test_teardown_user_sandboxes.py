import unittest

from mock import Mock, MagicMock,call

from cloudshell.orch.training.logic.teardown_user_sandboxes import SandboxTerminateLogic


class TestTeardownUserSandboxes(unittest.TestCase):
    def setUp(self) -> None:

        self.sandbox = Mock()
        self.sandbox_output_service = Mock()
        self.sandbox_api = Mock()
        self.users_data_manager = Mock()
        self.admin_login_token = Mock()
        self.sandbox_api.login = Mock(return_value=self.admin_login_token)
        self.sandbox_termination_service = Mock()

        self.training_env = Mock()

        self.logic = SandboxTerminateLogic(self.sandbox,self.sandbox_output_service,self.sandbox_api,self.users_data_manager,self.training_env)


    def test_teardown_student_sandboxes(self):
        # arrange
        self.training_env.users_list = ['user1', 'user2']
        user1_token = Mock()
        user2_token = Mock()
        self.users_data_manager.get_key = Mock(side_effect=[user1_token, user2_token])
        self.logic._delete_students_group = Mock()

        # act
        self.logic.teardown_student_sandboxes()

        # assert
        self.logic._sandbox_termination_service.end_student_reservation.assert_has_calls([call('user1'),call('user2')])
        self.logic._sandbox_api.delete_token.assert_has_calls([call(api_token=self.admin_login_token,user_token=user1_token),call(api_token=self.admin_login_token,user_token=user2_token)])
        self.logic._delete_students_group.assert_called_once()
