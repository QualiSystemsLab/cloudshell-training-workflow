import unittest

from mock import Mock, ANY

from cloudshell.workflow.training.services.email import EmailService


class TestEmailService(unittest.TestCase):

    def setUp(self) -> None:
        self.email_config = Mock()
        self.sandbox_output_service = Mock()
        self.logger = Mock()
        self.email_service = EmailService(self.email_config, self.sandbox_output_service, self.logger)

    def test_send_email_invalid_address(self):
        # arrange
        self.email_service._send = Mock()
        invalid_email = 'aaa@bbb'

        # act
        self.email_service.send_email(invalid_email, Mock())

        # assert
        self.sandbox_output_service.notify.assert_called_once_with(f'{invalid_email} is not a valid email address')
        self.email_service._send.assert_not_called()

    def test_send_email(self):
        # arrange
        self.email_service._send = Mock()
        email = 'aaa@bbb.com'
        student_link = Mock()
        self.email_config.template_parameters = {}
        self.email_config.template_name = 'cloudshell.workflow.training.email_templates.default'

        # act
        self.email_service.send_email(email, student_link)

        # assert
        self.email_service._send.assert_called_once_with(email, 'Welcome to Training', ANY)
