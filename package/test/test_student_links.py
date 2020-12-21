import unittest

from mock import Mock

from cloudshell.workflow.training.models.student_link import StudentLinkModel
from cloudshell.workflow.training.services.student_links import StudentLinksProvider


class TestStudentLinksProvider(unittest.TestCase):

    def test_create_student_link(self):
        # arrange
        sandbox_api_service = Mock()
        token = Mock()
        sandbox_api_service.create_token = Mock(return_value=token)
        training_portal_base_url = Mock()
        links_provider = StudentLinksProvider(training_portal_base_url, Mock(), sandbox_api_service)
        user = Mock()
        sandbox_id = Mock()

        # act
        result = links_provider.create_student_link(user, sandbox_id)

        # assert
        self.assertTrue(isinstance(result, StudentLinkModel))
        self.assertEqual(result.token, token)
        self.assertEqual(result.student_link, f"{training_portal_base_url}/{sandbox_id}?access={token}")

