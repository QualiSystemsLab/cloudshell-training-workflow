import unittest

from mock import Mock

from cloudshell.workflow.training.services.users_data_manager import UsersDataManagerService, USERS_DICT_KEY


class TestUsersDataManagerService(unittest.TestCase):

    def test_add(self):
        # arrange
        sandbox = Mock()
        users_data_manager = UsersDataManagerService(sandbox)
        user = 'user'

        # act
        users_data_manager.add_or_update(user, 'key', 'value1')

        # assert
        self.assertEqual('value1', users_data_manager._data[user]['key'])

    def test_update(self):
        # arrange
        sandbox = Mock()
        users_data_manager = UsersDataManagerService(sandbox)
        user = 'user'
        users_data_manager.add_or_update(user, 'key', 'value1')
        self.assertEqual('value1', users_data_manager._data[user]['key'])

        # act
        users_data_manager.add_or_update(user, 'key', 'value2')

        # assert
        self.assertEqual('value2', users_data_manager._data[user]['key'])

    def test_get(self):
        # arrange
        sandbox = Mock()
        users_data_manager = UsersDataManagerService(sandbox)
        user = 'user'
        users_data_manager.add_or_update(user, 'key1', 'value1')
        users_data_manager.add_or_update(user, 'key2', 'value2')

        # act
        user_data = users_data_manager.get(user)

        # assert
        self.assertTrue(user_data == {'key1': 'value1', 'key2': 'value2'})

    def test_get_key(self):
        # arrange
        sandbox = Mock()
        users_data_manager = UsersDataManagerService(sandbox)
        user = 'user'
        users_data_manager.add_or_update(user, 'key1', 'value1')

        # act
        value = users_data_manager.get_key(user, 'key1')

        # assert
        self.assertEqual('value1', value)

    def test_get_key_no_such_key(self):
        # arrange
        sandbox = Mock()
        users_data_manager = UsersDataManagerService(sandbox)
        user = 'user'
        users_data_manager.add_or_update(user, 'key1', 'value1')

        # act
        value = users_data_manager.get_key(user, 'key2')

        # assert
        self.assertIsNone(value)

    def test_load_data_exists_in_server(self):
        # arrange
        sandbox = Mock()
        sandbox.automation_api = Mock()
        sandbox_data_kvp = [Mock(Key=USERS_DICT_KEY, Value={'user': {'key1', 'value1'}}),
                            Mock(Key='some_key', Value='some_value')]
        get_sandbox_data_return_val = Mock(SandboxDataKeyValues=sandbox_data_kvp)
        sandbox.automation_api.GetSandboxData = Mock(return_value=get_sandbox_data_return_val)
        users_data_manager = UsersDataManagerService(sandbox)

        # act
        users_data_manager.load()

        # assert
        self.assertTrue(users_data_manager._data == {'user': {'key1', 'value1'}})

    def test_load_no_sandboxdata_from_server(self):
        # arrange
        sandbox = Mock()
        sandbox.automation_api = Mock()
        sandbox_data_kvp = []
        sandbox.automation_api.GetSandboxData = Mock(return_value=Mock(SandboxDataKeyValues=sandbox_data_kvp))
        users_data_manager = UsersDataManagerService(sandbox)

        # act
        users_data_manager.load()

        # assert
        self.assertTrue(users_data_manager._data == {})

    def test_load_no_userdata_in_sandboxdata_from_server(self):
        # arrange
        sandbox = Mock()
        sandbox.automation_api = Mock()
        sandbox_data_kvp = [Mock(Key='some_key', Value='some_value')]
        sandbox.automation_api.GetSandboxData = Mock(return_value=Mock(SandboxDataKeyValues=sandbox_data_kvp))
        users_data_manager = UsersDataManagerService(sandbox)

        # act
        users_data_manager.load()

        # assert
        self.assertTrue(users_data_manager._data == {})
