import unittest

from cloudshell.api.common_cloudshell_api import CloudShellAPIError
from mock import Mock, ANY, MagicMock

from cloudshell.workflow.training.services.users import UsersService


class TestUsersService(unittest.TestCase):

    def setUp(self) -> None:
        self.api = Mock()
        self.users_service = UsersService(self.api, Mock())

    def test_get_training_users_group_name(self):
        # arrange
        sandbox_id = Mock()

        # act
        result = self.users_service.get_training_users_group_name(sandbox_id)

        # assert
        self.assertEqual(result, f'training-{sandbox_id}')

    def test_create_training_users_group(self):
        # arrange
        sandbox_id = Mock()
        domain = Mock()
        group_name = Mock()
        self.users_service.get_training_users_group_name = Mock(return_value=group_name)

        # act
        self.users_service.create_training_users_group(sandbox_id, domain)

        # assert
        self.api.AddNewGroup.assert_called_once_with(group_name, ANY, 'Regular')
        self.api.AddGroupsToDomain.assert_called_once_with(domain, [group_name])

    def test_create_training_users_group_ex135(self):
        # arrange
        sandbox_id = Mock()
        domain = Mock()
        group_name = Mock()
        self.users_service.get_training_users_group_name = Mock(return_value=group_name)
        def raise_group_name_already_exists(*args, **kwargs):
            raise CloudShellAPIError('135', Mock(), Mock())

        self.api.AddNewGroup.side_effect = raise_group_name_already_exists

        # assert & act
        try:
            self.users_service.create_training_users_group(sandbox_id, domain)
        except CloudShellAPIError:
            self.fail("create_training_users_group() raised ExceptionType unexpectedly!")

    def test_create_training_users_group_ex_not135(self):
        # arrange
        sandbox_id = Mock()
        domain = Mock()
        group_name = Mock()
        self.users_service.get_training_users_group_name = Mock(return_value=group_name)
        def raise_group_ex(*args, **kwargs):
            raise CloudShellAPIError(Mock(), Mock(), Mock())

        self.api.AddNewGroup.side_effect = raise_group_ex

        # act & assert
        with self.assertRaises(CloudShellAPIError):
            self.users_service.create_training_users_group(sandbox_id, domain)


    def test_delete_training_users_group(self):
        # arrange
        sandbox_id = Mock()
        group_name = Mock()
        self.users_service.get_training_users_group_name = Mock(return_value=group_name)

        # act
        self.users_service.delete_training_users_group(sandbox_id)

        # assert
        self.api.DeleteGroup.assert_called_once_with(group_name)

    def test_add_training_users_to_group(self):
        # arrange
        sandbox_id = Mock()
        users = MagicMock()
        group_name = Mock()
        self.users_service.get_training_users_group_name = Mock(return_value=group_name)

        # act
        self.users_service.add_training_users_to_group(sandbox_id, users)

        # assert
        self.api.AddUsersToGroup.assert_called_once_with(users, group_name)

    def test_deactivate_training_user(self):
        # arrange
        user = Mock()

        # act
        self.users_service.deactivate_training_user(user)

        # assert
        self.api.UpdateUser.assert_called_once_with(user, user, isActive=False)

    def test_create_or_activate_training_user_when_user_inactive(self):
        # arrange
        user = Mock()
        self.api.GetUserDetails.return_value = Mock(IsActive=False)

        # act
        self.users_service.create_or_activate_training_user(user)

        # assert
        self.api.UpdateUser.assert_called_once_with(user, user, isActive=True)
        self.api.AddNewUser.assert_not_called()

    def test_create_or_activate_training_user_when_user_active(self):
        # arrange
        user = Mock()
        self.api.GetUserDetails.return_value = Mock(IsActive=True)

        # act
        self.users_service.create_or_activate_training_user(user)

        # assert
        self.api.UpdateUser.assert_not_called()
        self.api.AddNewUser.assert_not_called()

    def test_create_or_activate_training_user_when_user_doesnt_exist(self):
        def raise_user_doesnt_exist_error(*args, **kwargs):
            raise CloudShellAPIError('133', Mock(), Mock())

        # arrange
        user = Mock()
        self.api.GetUserDetails.side_effect = raise_user_doesnt_exist_error

        # act
        self.users_service.create_or_activate_training_user(user)

        # assert
        self.api.AddNewUser.assert_called_once_with(user, ANY, user, isActive=True)
        self.api.UpdateUser.assert_not_called()

    def test_create_or_activate_training_user_when_api_error(self):
        def raise_api_error(*args, **kwargs):
            raise CloudShellAPIError(Mock(), Mock(), Mock())

        # arrange
        user = Mock()
        self.api.GetUserDetails.side_effect = raise_api_error

        # act & assert
        with self.assertRaises(CloudShellAPIError):
            self.users_service.create_or_activate_training_user(user)

        self.api.AddNewUser.assert_not_called()
        self.api.UpdateUser.assert_not_called()