from typing import Dict
import re

from cloudshell.orch.training.services.ips_handler import IPsHandlerService,ALLOWED_INCREMENT_OCTET_LIST


class EmailConfig:
    def __init__(self, smtp_server: str, user: str, password: str, from_address: str,
                 email_template: str = 'cloudshell.orch.training.email_templates.default',
                 template_parameters: Dict[str, str] = None, smtp_port=587):
        """
        :param smtp_server:
        :param user: must in an email address format
        :param password: password for user email address
        :param from_address: the address to be used as the sender
        :param email_template: full path to email template module.
                               Needs to be in a python module path format. Example: a.b.email_template
        :param smtp_port:
        """
        self.smtp_server = smtp_server
        self.user = user
        self.password = password
        self.from_address = from_address
        self.smtp_port = smtp_port
        self.template_name = email_template
        self.template_parameters = {} if not template_parameters else template_parameters


# todo - add config validations
class TrainingWorkflowConfig:
    def __init__(self, training_portal_base_url: str = '', sandbox_api_port: int = 82,
                 app_duplicate_ip_increment: int = 10, app_duplicate_increment_octet: str = '/24',
                 email_config: EmailConfig = None):
        """
        :param training_portal_base_url: Base url for training portal including port
        :param sandbox_api_port:
        :param email_config: if None emails to training users will not be sent
        """
        self._validate_config_params(training_portal_base_url, sandbox_api_port,
                                     app_duplicate_ip_increment, app_duplicate_increment_octet)
        self.training_portal_base_url = training_portal_base_url
        self.sandbox_api_port = sandbox_api_port
        self.app_duplicate_ip_increment = app_duplicate_ip_increment
        self.app_duplicate_increment_octet = app_duplicate_increment_octet
        self.email_config = email_config

    def _validate_config_params(self, training_portal_base_url: str, sandbox_api_port: int,
                                app_duplicate_ip_increment: int, app_duplicate_increment_octet: str):

        return self._validate_url(training_portal_base_url) and \
                self._validate_sandbox_api_port(sandbox_api_port) and \
                self._validate_app_duplicate_ip_increment(app_duplicate_ip_increment) and \
                self._app_duplicate_increment_octet(app_duplicate_increment_octet)

    @staticmethod
    def _validate_url(training_portal_base_url: str) -> bool:
        regex = re.compile(
            r'^(?:http|)s?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        if not re.match(regex, training_portal_base_url):
            raise ValueError
        return True

    @staticmethod
    def _validate_sandbox_api_port(sandbox_api_port: int) -> bool:
        if not 1 <= sandbox_api_port <= 65535:
            raise ValueError
        return True

    @staticmethod
    def _validate_app_duplicate_ip_increment(app_duplicate_ip_increment: int):
        if not 1 <= app_duplicate_ip_increment <= 255:
            raise ValueError
        return True

    @staticmethod
    def _app_duplicate_increment_octet(app_duplicate_increment_octet: str):
        if app_duplicate_increment_octet not in ALLOWED_INCREMENT_OCTET_LIST:
            raise ValueError
        return True

    def _validate(self):
        IPsHandlerService.validate_increment_octet(self.app_duplicate_increment_octet)
