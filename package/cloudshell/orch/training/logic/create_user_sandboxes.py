from datetime import datetime
from typing import List

from cloudshell.api.cloudshell_api import ReservationDescriptionInfo
from cloudshell.workflow.orchestration.sandbox import Sandbox

from cloudshell.orch.training.models.config import TrainingWorkflowConfig
from cloudshell.orch.training.models.position import Position
from cloudshell.orch.training.models.training_env import TrainingEnvironmentDataModel
from cloudshell.orch.training.services.sandbox_components import SandboxComponentsHelperService
from cloudshell.orch.training.services.email import EmailService
from cloudshell.orch.training.services.sandbox_api import SandboxAPIService
from cloudshell.orch.training.services.sandbox_create import SandboxCreateService
from cloudshell.orch.training.services.sandbox_output import SandboxOutputService
from cloudshell.orch.training.services.student_links import StudentLinksProvider
from cloudshell.orch.training.services.users_data_manager import UsersDataManagerService,\
    UsersDataManagerServiceKeys as userDataKeys


class UserSandboxesLogic:

    def __init__(self, env_data: TrainingEnvironmentDataModel, sandbox_output_service: SandboxOutputService,
                 users_data_manager: UsersDataManagerService, sandbox_create_service: SandboxCreateService,
                 email_service: EmailService, student_links_provider: StudentLinksProvider,
                 apps_service: SandboxComponentsHelperService):
        self._env_data = env_data
        self._sandbox_output = sandbox_output_service
        self._users_data = users_data_manager
        self._sandbox_create_service = sandbox_create_service
        self._email_service = email_service
        self._student_links_provider = student_links_provider
        self._apps_service = apps_service

    def create_user_sandboxes(self, sandbox, components):

        if not self._env_data.users_list:
            return

        self._sandbox_output.notify("Creating User Sandboxes")

        sandbox_details = self._get_latest_sandbox_details(sandbox)

        # Create sandbox for each training user - non blocking, this method will not wait for all sandboxes to be ready
        self._create_user_sandboxes(sandbox, sandbox_details)

        # Wait for student sandboxes to be "Active" and add Student Resources into them
        self._wait_for_active_sandboxes_and_add_duplicated_resources(sandbox, sandbox_details)

        # Send emails to all users
        self._send_emails()

    def _get_latest_sandbox_details(self, sandbox: Sandbox) -> ReservationDescriptionInfo:
        sandbox.components.refresh_components(sandbox)
        sandbox_details = sandbox.automation_api.GetReservationDetails(sandbox.id, disableCache=True)
        return sandbox_details.ReservationDescription

    def _send_emails(self):
        for user in self._env_data.users_list:
            student_link = self._users_data.get_key(user, userDataKeys.STUDENT_LINK)
            self._email_service.send_email(user, student_link)
            self._sandbox_output.notify(f'Sending email to {user} with link={student_link}')

    def _wait_for_active_sandboxes_and_add_duplicated_resources(self, sandbox: Sandbox,
                                                                sandbox_details: ReservationDescriptionInfo):
        resource_positions_dict = self._get_resource_positions(sandbox)
        shared_resources = self._get_shared_resources(sandbox)

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

    def _get_shared_resources(self, sandbox: Sandbox) -> List[str]:
        # todo run this code against live environment to test that logic is correct - alexa
        apps = [app.app_request.app_resource for app in sandbox.components.apps.values()]
        apps_to_share = [app.Name for app in apps if self._apps_service.should_share_app(app)]

        shared_resources = [resource.Name for resource in sandbox.components.resources if resource.AppDetails
                            and resource.AppDetails.AppName and resource.AppDetails.AppName in apps_to_share]

        [self._sandbox_output.debug_print(f'will add shared resource: {resource}') for resource in shared_resources]

        return shared_resources

    def _create_user_sandboxes(self, sandbox: Sandbox, sandbox_details: ReservationDescriptionInfo):
        duration = self._calculate_user_sandbox_duration(sandbox_details)

        for user in self._env_data.users_list:

            # 1. create new trainee sandbox
            new_sandbox = self._sandbox_create_service.create_trainee_sandbox(
                sandbox.reservationContextDetails.environment_name, user,
                self._users_data.get_key(user, userDataKeys.ID), duration)

            # 2. generate student link and to sandbox data
            student_link_model = self._student_links_provider.create_student_link(user, new_sandbox.Id)

            # 3. save important data to sandbox data
            self._users_data.add_or_update(user, userDataKeys.TOKEN, student_link_model.token)
            self._users_data.add_or_update(user, userDataKeys.STUDENT_LINK, student_link_model.student_link)
            self._users_data.add_or_update(user, userDataKeys.SANDBOX_ID, new_sandbox.Id)

            # 4. notify instructor about trainee link
            msg = f'<a href="{student_link_model.student_link}" style="font-size:16px">Trainee Sandbox - {user}</a>'
            self._sandbox_output.notify(f'Trainee link for {user}: {msg}')

    def _calculate_user_sandbox_duration(self, sandbox_details: ReservationDescriptionInfo) -> int:
        """
        :return: user sandbox duration in minutes
        """
        end_time = datetime.strptime(sandbox_details.EndTime, '%m/%d/%Y %H:%M')
        duration = int((end_time - datetime.utcnow()).total_seconds() / 60)
        return duration

