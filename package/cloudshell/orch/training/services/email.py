import importlib
import logging
import re
import smtplib
from collections import namedtuple
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from cloudshell.orch.training.models.config import EmailConfig
from cloudshell.orch.training.services.sandbox_output import SandboxOutputService

EmailMessage = namedtuple('EmailTemplate', ['subject', 'message'])


class EmailService:

    def __init__(self, email_config: EmailConfig, sandbox_output_service: SandboxOutputService, logger: logging.Logger):
        self._email_config = email_config
        self._sandbox_output = sandbox_output_service
        self._logger = logger

    def is_email_configured(self) -> bool:
        return True if self._email_config else False

    def send_email(self, email_address: str, link: str):
        if not self._is_valid_email_address(email_address):
            self._sandbox_output.notify(f'{email_address} is not a valid email address')
            return

        email_contents = self._load_and_format_template(self._email_config.template_name, link,
                                                        **self._email_config.template_parameters)

        self._send(email_address, email_contents.subject, email_contents.message)

    def _is_valid_email_address(self, email):
        regex = '^\w+([\.-]?\w+)*@\w+([\.-]?\w+)*(\.\w{2,3})+$'
        return re.search(regex, email)

    def _send(self, to_address, subject, message, cc=None):
        from_address = self._email_config.from_address
        msg = MIMEMultipart('alternative')
        msg['From'] = ';'.join(from_address) if isinstance(from_address, list) else from_address
        msg['To'] = ';'.join(to_address) if isinstance(to_address, list) else to_address
        msg['Subject'] = subject
        if cc:
            msg["Cc"] = ';'.join(cc) if isinstance(cc, list) else cc
        mess = MIMEText(message, 'html')
        msg.attach(mess)

        try:
            smtp = smtplib.SMTP(
                host=self._email_config.smtp_server,
                port=self._email_config.smtp_port
            )
            smtp.ehlo()
            smtp.starttls()
            smtp.login(self._email_config.user, self._email_config.password)
            smtp.sendmail(
                from_addr=from_address,
                to_addrs=[to_address, cc] if cc else to_address,
                msg=msg.as_string()
            )
            smtp.close()
        except Exception:
            self._logger.exception(f'failed to send email to {to_address}')
            raise

    def _load_and_format_template(self, template_name, sandbox_link, **extra_args) -> EmailMessage:
        subject = None
        content = None

        try:
            if template_name:
                mod = importlib.import_module(template_name)
                subject, html_template = mod.load_template()
                content = html_template.format(sandbox_link=sandbox_link, **extra_args)
        except Exception:
            self._logger.exception('failed loading email template')
            raise

        return EmailMessage(
            'not found' if not subject else subject,
            'not found' if not content else content
        )
