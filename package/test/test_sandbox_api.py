import unittest

from mock import Mock

from cloudshell.orch.training.services.sandbox_api import SandboxAPIService
from cloudshell.orch.training.services.sandbox_components import SandboxComponentsHelperService

class TestSandboxApiService(unittest.TestCase):
    def setUp(self) -> None:
        self.sandbox_api_service = SandboxAPIService(Mock(), Mock(), Mock())
        self.sandbox_api_service._requests_session=Mock()
        self.api_token:str = Mock()
        self.user:str = Mock()

    def test_create_token(self):
        # arrange
        mock_domain = Mock()
        mock_post_return = Mock()
        self.sandbox_api_service._requests_session.post = Mock(return_value=mock_post_return)

        # act
        returned_token = self.sandbox_api_service.create_token(self.api_token,self.user,mock_domain)

        # assert
        self.sandbox_api_service._requests_session.post.assert_called_once()
        self.assertEqual(returned_token,mock_post_return.json())

    def test_delete_token_succesfull(self):
        # arrange
        mock_delete_return = Mock()
        mock_delete_return.status_code = 200
        self.sandbox_api_service._requests_session.delete = Mock(return_value=mock_delete_return)

        # act
        delete_return = self.sandbox_api_service.delete_token(self.api_token,self.user)

        # assert
        self.sandbox_api_service._requests_session.delete.assert_called_once()
        self.assertTrue(delete_return)

    def test_delete_token_failed(self):
        # arrange
        mock_delete_return = Mock()
        mock_delete_return.status_code = 400
        self.sandbox_api_service._requests_session.delete = Mock(return_value=mock_delete_return)

        # act
        delete_return = self.sandbox_api_service.delete_token(self.api_token,self.user)

        # assert
        self.sandbox_api_service._requests_session.delete.assert_called_once()
        self.assertFalse(delete_return)

    def test_login(self):
        # arrange
        mock_json = Mock()
        self.sandbox_api_service._requests_session.put = Mock(return_value=mock_json)
        # act
        login_return = self.sandbox_api_service.login()

        # assert
        self.sandbox_api_service._requests_session.put.assert_called_once()
        self.assertEqual(login_return,mock_json.json())
