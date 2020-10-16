from typing import Dict

from cloudshell.orch.training.services.ip_increment_strategy import RequestedIPsIncrementStrategy
from cloudshell.email_config import EmailConfig


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
        self.training_portal_base_url = training_portal_base_url
        self.sandbox_api_port = sandbox_api_port
        self.app_duplicate_ip_increment = app_duplicate_ip_increment
        self.app_duplicate_increment_octet = app_duplicate_increment_octet
        self.email_config = email_config

    def _validate(self):
        RequestedIPsIncrementStrategy.validate_increment_octet(self.app_duplicate_increment_octet)