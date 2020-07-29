from datetime import datetime
from typing import List

import requests
from cloudshell.api.cloudshell_api import UpdateTopologyGlobalInputsRequest, ReservationDescriptionInfo
from cloudshell.workflow.orchestration.sandbox import Sandbox

from cloudshell.orch.training.models.position import Position
from cloudshell.orch.training.models.training_env import TrainingEnvironmentDataModel
from cloudshell.orch.training.services.sandbox_api import SandboxAPIService
from cloudshell.orch.training.services.sandbox_create import SandboxCreateService
from cloudshell.orch.training.services.sandbox_output import SandboxOutputService
from cloudshell.orch.training.services.users_data_manager import UsersDataManagerService


class UserSandboxesLogic:

    def __init__(self, env_data: TrainingEnvironmentDataModel, sandbox_output_service: SandboxOutputService,
                 users_data_manager: UsersDataManagerService, sandbox_create_service: SandboxCreateService,
                 sandbox_api:  SandboxAPIService):
        self._sandbox_api = sandbox_api
        self._env_data = env_data
        self._sandbox_output = sandbox_output_service
        self._users_data = users_data_manager
        self._sandbox_create_service = sandbox_create_service

    def create(self, sandbox, components):

        if not self._env_data.users_list:
            return

        self._sandbox_output.notify("Creating User Sandboxes")

        sandbox.components.refresh_components(sandbox)
        sandbox_details = sandbox.automation_api.GetReservationDetails(sandbox.id, disableCache=True).\
            ReservationDescription

        # create sandbox for each training user - non blocking, this method will not wait for all sandboxes to be ready
        self._create_user_sanboxes(sandbox, sandbox_details)

        # Wait for student sandboxes to be "Active" and add Student Resources into them
        self._wait_for_active_sandboxes_and_add_duplicated_resources(sandbox, sandbox_details)

        self._send_emails()

    def _send_emails(self):
        # Send emails to all users
        for user in self._env_data.users_list:
            student_link = self._users_data.get_key(user, "student_link")
            # todo - add support for emails, need to pass email config in to setup
            # setup_helper.send_email(user, student_link)
            self._sandbox_output.notify("Sending email to {} with link={}".format(user, student_link))

    def _wait_for_active_sandboxes_and_add_duplicated_resources(self, sandbox, sandbox_details):
        resource_positions_dict = self._get_resource_positions(sandbox)
        shared_resources = self._get_shared_resources(sandbox_details)

        for user in self._env_data.users_list:
            user_sandbox_id = self._users_data.get_key(user, "sandbox_id")
            user_id = self._users_data.get_key(user, "id")

            self._sandbox_create_service.wait_active(user_sandbox_id, user)

            user_resources = [resource.Name for resource in sandbox_details.Resources if
                              resource.Name.startswith(f"{user_id}_")]
            sandbox.automation_api.SetResourceSharedState(sandbox.id, user_resources + shared_resources, isShared=True)
            sandbox.automation_api.AddResourcesToReservation(user_sandbox_id, user_resources + shared_resources,
                                                             shared=True)

            for resource in user_resources:
                sandbox.automation_api.SetReservationResourcePosition(user_sandbox_id, resource,
                                                                      resource_positions_dict[resource].X,
                                                                      resource_positions_dict[resource].Y)

    def _get_resource_positions(self, sandbox):
        resource_positions = sandbox.automation_api.GetReservationResourcesPositions(sandbox.id).ResourceDiagramLayouts
        resource_positions_dict = {resource.ResourceName: Position(resource.X, resource.Y) for resource in
                                   resource_positions}
        return resource_positions_dict

    def _get_shared_resources(self, sandbox_details):
        shared_resources = [resource.Name for resource in sandbox_details.Resources if resource.AppTemplateName
                            and resource.AppTemplateName in self._env_data.shared_apps]
        for resource in shared_resources:
            self._sandbox_output.debug_print(f'will add shared resource: {resource}')
        return shared_resources

    def _create_user_sanboxes(self, sandbox: Sandbox, sandbox_details: ReservationDescriptionInfo):
        end_time = datetime.strptime(sandbox_details.EndTime, '%m/%d/%Y %H:%M')
        duration = int((end_time - datetime.utcnow()).total_seconds() / 60)

        for user in self._env_data.users_list:

            new_sandbox = self._sandbox_create_service.create_trainee_sandbox(user,
                                                                              self._users_data.get_key(user, "id"),
                                                                              duration)

            self._users_data.add_or_update(user, "sandbox_id", new_sandbox.Id)

            token = self._create_token(user, sandbox.reservationContextDetails.domain)
            self._users_data.add_or_update(user, "token", token)

            # todo - how to update this data?
            student_link = f"http://18.200.153.138:3000/{new_sandbox.Id}?access={token}"
            self._users_data.add_or_update(user, "student_link", student_link)

            msg = f'<a href="{student_link}" style="font-size:16px">Trainee Sandbox - {user}</a>'
            self._sandbox_output.notify(f'Trainee link for {user}: {msg}')

    def _create_token(self, user: str, domain: str):
        admin_token = self._sandbox_api.login()
        return self._sandbox_api.create_token(admin_token, user, domain)
