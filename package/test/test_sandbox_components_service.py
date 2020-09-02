import unittest

from mock import Mock

from cloudshell.orch.training.services.sandbox_components import SandboxComponentsService
from cloudshell.orch.training.services.sandbox_output import SandboxOutputService


class TestAppsService(unittest.TestCase):

    def setUp(self) -> None:
        self.sandbox = Mock()
        sandbox_output_service = Mock()
        self.apps_service = SandboxComponentsService(sandbox_output_service)

    def test_should_share_app_return_true(self):
        # arrange
        self.apps_service.should_duplicate_app = Mock(return_value=False)

        # act
        result = self.apps_service.should_share_app(Mock())

        # assert
        self.assertTrue(result)

    def test_should_share_app_return_false(self):
        # arrange
        self.apps_service.should_duplicate_app = Mock(return_value=True)

        # act
        result = self.apps_service.should_share_app(Mock())

        # assert
        self.assertFalse(result)

