import requests
from cloudshell.workflow.orchestration.sandbox import Sandbox

from cloudshell.workflow.training.services.sandbox_output import SandboxOutputService


class SandboxAPIService:

    def __init__(self, sandbox: Sandbox, port: int, sandbox_output: SandboxOutputService):
        self._port = port
        self._sandbox = sandbox
        self._sandbox_output = sandbox_output

        self._s = requests.Session()
        self._s.verify = False

    def login(self) -> str:
        """
        Login to the Sandbox API as the admin User.
        """
        r = self._s.put(f'http://{self._sandbox.connectivityContextDetails.server_address}:{self._port}/api/login',
                        json={
                            "username": self._sandbox.connectivityContextDetails.admin_user,
                            "password": self._sandbox.connectivityContextDetails.admin_pass,
                            "domain": self._sandbox.reservationContextDetails.domain
                        })
        return r.json()

    def create_token(self, api_token: str, user: str, domain: str) -> str:
        """
        Generate a user token for Sandbox API (and Training Portal) for the designated user.
        """
        self._sandbox_output.debug_print("Generating REST API Token")
        authorization = f"Basic {api_token}"
        headers = {'Content-type': 'application/json', 'Authorization': authorization}
        r = self._s.post(f'http://{self._sandbox.connectivityContextDetails.server_address}:{self._port}/api/Token',
                         json={"username": user, "domain": domain}, headers=headers)
        return r.json()

    def delete_token(self, api_token: str, user_token: str) -> bool:
        """
        Delete a user token
        """
        self._sandbox_output.debug_print(f"Deleting REST API Token {user_token}")
        authorization = f"Basic {api_token}"
        headers = {'Content-type': 'application/json', 'Authorization': authorization}
        r = self._s.delete(f'http://{self._sandbox.connectivityContextDetails.server_address}:{self._port}'
                           f'/api/Token/{user_token}', headers=headers)
        if 400 <= r.status_code < 300:
            self._sandbox_output.debug_print("Error deleting token")
            return False

        return True
