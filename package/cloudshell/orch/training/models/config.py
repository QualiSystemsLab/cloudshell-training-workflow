from typing import Dict
from cloudshell.orch.email_service.email_config import EmailConfig


class TrainingWorkflowConfig:
    def __init__(self, training_portal_base_url: str = '', sandbox_api_port: int = 82,
                 email_config: EmailConfig = None):
        """
        :param training_portal_base_url:
        :param sandbox_api_port:
        :param email_config: if None emails to training users will not be sent
        """
        self.training_portal_base_url = training_portal_base_url
        self.sandbox_api_port = sandbox_api_port
        self.email_config = email_config
