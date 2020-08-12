from typing import Dict


class EmailConfig:
    def __init__(self, smtp_server: str, user: str, password: str, from_address: str,
                 email_template: str = 'cloudshell.orch.training.email_templates.default',
                 template_parameters: Dict[str, str] = None, smtp_port=587):
        """
        :param smtp_server:
        :param user: must in an email address format
        :param password: password for user email address
        :param from_address: the address to be used as the sender
        :param email_template: full path to email template module. Needs to be in a python module path format. Example: a.b.email_template
        :param smtp_port:
        """
        self.smtp_server = smtp_server
        self.user = user
        self.password = password
        self.from_address = from_address
        self.smtp_port = smtp_port
        self.template_name = email_template
        self.template_parameters = {} if not template_parameters else template_parameters


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
