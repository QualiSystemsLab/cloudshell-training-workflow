from cloudshell.workflow.orchestration.sandbox import Sandbox

from cloudshell.orch.training.models.student_link import StudentLinkModel
from cloudshell.orch.training.services.sandbox_api import SandboxAPIService


class StudentLinksProvider:

    def __init__(self, training_portal_base_url: str, sandbox: Sandbox, sandbox_api_service: SandboxAPIService):
        self._training_portal_base_url = training_portal_base_url
        self._sandbox = sandbox
        self._sandbox_api = sandbox_api_service

    def create_student_link(self, user: str, sandbox_id: str) -> StudentLinkModel:
        token = self._create_token(user, self._sandbox.reservationContextDetails.domain)
        student_link = self._format_student_link(sandbox_id, token)
        return StudentLinkModel(token, student_link)

    def _format_student_link(self, sandbox_id: str, token: str) -> str:
        return f"{self._training_portal_base_url}/{sandbox_id}?access={token}"

    def _create_token(self, user: str, domain: str) -> str:
        admin_token = self._sandbox_api.login()
        return self._sandbox_api.create_token(admin_token, user, domain)