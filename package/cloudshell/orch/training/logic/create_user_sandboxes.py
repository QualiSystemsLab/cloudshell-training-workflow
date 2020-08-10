from datetime import datetime
from typing import List

from cloudshell.api.cloudshell_api import ReservationDescriptionInfo
from cloudshell.workflow.orchestration.sandbox import Sandbox

from cloudshell.orch.training.models.config import TrainingConfig
from cloudshell.orch.training.models.position import Position
from cloudshell.orch.training.models.training_env import TrainingEnvironmentDataModel
from cloudshell.orch.training.services.sandbox_api import SandboxAPIService
from cloudshell.orch.training.services.sandbox_create import SandboxCreateService
from cloudshell.orch.training.services.sandbox_output import SandboxOutputService
from cloudshell.orch.training.services.users_data_manager import UsersDataManagerService,\
    UsersDataManagerServiceKeys as userDataKeys


class UserSandboxesLogic:

    def __init__(self, config: TrainingConfig, env_data: TrainingEnvironmentDataModel, sandbox_output_service: SandboxOutputService,
                 users_data_manager: UsersDataManagerService, sandbox_create_service: SandboxCreateService,
                 sandbox_api:  SandboxAPIService):
        self._config = config
        self._sandbox_api = sandbox_api
        self._env_data = env_data
        self._sandbox_output = sandbox_output_service
        self._users_data = users_data_manager
        self._sandbox_create_service = sandbox_create_service

    def create(self, sandbox, components):

        if not self._env_data.users_list:
            return

        self._sandbox_output.notify("Creating User Sandboxes")

        sandbox_details = self._get_latest_sandbox_details(sandbox)

        # create sandbox for each training user - non blocking, this method will not wait for all sandboxes to be ready
        self._create_user_sandboxes(sandbox, sandbox_details)

        # Wait for student sandboxes to be "Active" and add Student Resources into them
        self._wait_for_active_sandboxes_and_add_duplicated_resources(sandbox, sandbox_details)

        self._send_emails()

    def _get_latest_sandbox_details(self, sandbox: Sandbox) -> ReservationDescriptionInfo:
        sandbox.components.refresh_components(sandbox)
        sandbox_details = sandbox.automation_api.GetReservationDetails(sandbox.id, disableCache=True)
        return sandbox_details.ReservationDescription

    def _send_emails(self):
        # Send emails to all users
        for user in self._env_data.users_list:
            student_link = self._users_data.get_key(user, userDataKeys.STUDENT_LINK)
            # todo - add support for emails, need to pass email config in to setup
            # setup_helper.send_email(user, student_link)
            self._sandbox_output.notify("Sending email to {} with link={}".format(user, student_link))

    def _wait_for_active_sandboxes_and_add_duplicated_resources(self, sandbox: Sandbox,
                                                                sandbox_details: ReservationDescriptionInfo):
        resource_positions_dict = self._get_resource_positions(sandbox)
        shared_resources = self._get_shared_resources(sandbox_details)

        for user in self._env_data.users_list:
            user_sandbox_id = self._users_data.get_key(user, userDataKeys.SANDBOX_ID)
            self._sandbox_create_service.wait_ready(user_sandbox_id, user)

            user_resources = self._get_user_resources(sandbox_details, user)
            sandbox.automation_api.SetResourceSharedState(sandbox.id, user_resources + shared_resources, isShared=True)
            sandbox.automation_api.AddResourcesToReservation(user_sandbox_id, user_resources + shared_resources,
                                                             shared=True)

            for resource in user_resources:
                sandbox.automation_api.SetReservationResourcePosition(user_sandbox_id, resource,
                                                                      resource_positions_dict[resource].X,
                                                                      resource_positions_dict[resource].Y)

    def _get_user_resources(self, sandbox_details, user) -> List[str]:
        user_id = self._users_data.get_key(user, userDataKeys.ID)
        user_resources = [resource.Name for resource in sandbox_details.Resources if
                          resource.Name.startswith(f"{user_id}_")]
        return user_resources

    def _get_resource_positions(self, sandbox: Sandbox):
        resource_positions = sandbox.automation_api.GetReservationResourcesPositions(sandbox.id).ResourceDiagramLayouts
        resource_positions_dict = {resource.ResourceName: Position(resource.X, resource.Y) for resource in
                                   resource_positions}
        return resource_positions_dict

    def _get_shared_resources(self, sandbox_details: ReservationDescriptionInfo) -> List[str]:
        shared_resources = [resource.Name for resource in sandbox_details.Resources if resource.AppTemplateName
                            and resource.AppTemplateName in self._env_data.shared_apps]
        for resource in shared_resources:
            self._sandbox_output.debug_print(f'will add shared resource: {resource}')
        return shared_resources

    def _create_user_sandboxes(self, sandbox: Sandbox, sandbox_details: ReservationDescriptionInfo):
        duration = self._calculate_user_sandbox_duration(sandbox_details)

        for user in self._env_data.users_list:

            new_sandbox = self._sandbox_create_service.create_trainee_sandbox(
                user, self._users_data.get_key(user, userDataKeys.ID), duration)
            self._users_data.add_or_update(user, userDataKeys.SANDBOX_ID, new_sandbox.Id)

            token = self._create_token(user, sandbox.reservationContextDetails.domain)
            self._users_data.add_or_update(user, userDataKeys.TOKEN, token)

            student_link = f"{self._config.training_portal_base_url}/{new_sandbox.Id}?access={token}"
            self._users_data.add_or_update(user, userDataKeys.STUDENT_LINK, student_link)

            msg = f'<a href="{student_link}" style="font-size:16px">Trainee Sandbox - {user}</a>'
            self._sandbox_output.notify(f'Trainee link for {user}: {msg}')

    def _calculate_user_sandbox_duration(self, sandbox_details: ReservationDescriptionInfo) -> int:
        """
        :return: user sandbox duration in minutes
        """
        end_time = datetime.strptime(sandbox_details.EndTime, '%m/%d/%Y %H:%M')
        duration = int((end_time - datetime.utcnow()).total_seconds() / 60)
        return duration

    def _create_token(self, user: str, domain: str):
        admin_token = self._sandbox_api.login()
        return self._sandbox_api.create_token(admin_token, user, domain)
