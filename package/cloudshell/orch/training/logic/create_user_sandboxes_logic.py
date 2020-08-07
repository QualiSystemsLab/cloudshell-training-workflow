from datetime import datetime
from typing import List

import requests
from cloudshell.api.cloudshell_api import UpdateTopologyGlobalInputsRequest, ReservationDescriptionInfo
from cloudshell.workflow.orchestration.sandbox import Sandbox

from cloudshell.orch.training.models.position import Position

from cloudshell.orch.training.models.training_env import TrainingEnvironmentDataModel
from cloudshell.orch.training.services.users_data_manager import UsersDataManagerService
from cloudshell.orch.training.services.sandbox_output import SandboxOutputService



class UserSandboxesLogic:

    def __init__(self, env_data: TrainingEnvironmentDataModel, sandbox_output_service: SandboxOutputService ,
                 users_data_manager: UsersDataManagerService):

        self._env_data = env_data
        self._sandbox_output = SandboxOutputService
        self._users_data = users_data_manager

    def create(self, sandbox, components):

        if self._env_data.users_list:
            self._sandbox_output.notify("Creating User Sandboxes")

        sandbox.components.refresh_components(sandbox)
        sandbox_details = sandbox.automation_api.GetReservationDetails(sandbox.id, disableCache=True).ReservationDescription
        end_time = datetime.strptime(sandbox_details.EndTime, '%m/%d/%Y %H:%M')
        minutes_left = int((end_time - datetime.utcnow()).total_seconds() / 60)

        # create sandbox for each training user - non blocking, this method will not wait for all sandboxes to be ready
        self._create_user_sanboxes(minutes_left, sandbox)

        resource_positions_dict = self._get_resource_positions(sandbox)
        shared_resources = self._get_shared_resources(sandbox_details)

        # Wait for student sandboxes to be "Active" and add Student Resources into them

        # Add duplicated resources
        for user in self._env_data.users_list:
            user_sandbox_id = sandbox_data_dict[user]["sandbox_id"]
            user_id = sandbox_data_dict[user]["id"]

            user_sandbox_status = sandbox.automation_api.GetReservationStatus(user_sandbox_id)
            time_waited = 0
            # TODO - create_sb_services(user_sandbox_id, user_spacing_id)
            while user_sandbox_status.ReservationSlimStatus.Status != "Started" or user_sandbox_status.ReservationSlimStatus.ProvisioningStatus != "Ready":
                notify(f"""waiting for {user}'s sandbox, 
                                currently {user_sandbox_id}'s sandbox satus is {user_sandbox_status.ReservationSlimStatus.Status} 
                                and {user_sandbox_status.ReservationSlimStatus.ProvisioningStatus}""")
                sleep(10)
                time_waited += 10
                user_sandbox_status = sandbox.automation_api.GetReservationStatus(user_sandbox_id)
                if user_sandbox_status.ReservationSlimStatus.ProvisioningStatus == 'Error':
                    raise Exception('Cannot create student sandbox')

                if user_sandbox_status.ReservationSlimStatus.Status == 'Teardown':
                    raise Exception('Cannot create student sandbox')

                if user_sandbox_status.ReservationSlimStatus.Status == 'Completed':
                    raise Exception('Cannot create student sandbox')

            user_resources = [resource.Name for resource in sandbox_details.Resources if
                              resource.Name.startswith(f"{user_id}_")]
            sandbox.automation_api.SetResourceSharedState(sandbox.id, user_resources + shared_resources, isShared=True)
            sandbox.automation_api.AddResourcesToReservation(user_sandbox_id, user_resources + shared_resources,
                                                             shared=True)

            for resource in user_resources:
                sandbox.automation_api.SetReservationResourcePosition(user_sandbox_id, resource,
                                                                      resource_positions_dict[resource].X,
                                                                      resource_positions_dict[resource].Y)

        # Send emails to all users
        for user in users_list:
            student_link = sandbox_data_dict[user]["student_link"]
            setup_helper.send_email(user, student_link)
            notify("Sending email to {} with link={}".format(user, student_link))

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

    def _create_user_sanboxes(self, minutes_left, sandbox):
        for user in self._env_data.users_list:
            new_sandbox = sandbox.automation_api.CreateImmediateTopologyReservation(f"{user} - Trainee Sandbox", user,
                                                                                    minutes_left, False, False, 10,
                                                                                    topologyFullPath=sandbox.reservationContextDetails.environment_name,
                                                                                    globalInputs=[
                                                                                        UpdateTopologyGlobalInputsRequest(
                                                                                            "Training Users",
                                                                                            f"{user}#{sandbox_data_dict[user]['id']}")])
            self._users_data.add_or_update(user, "sandbox_id", new_sandbox.Reservation.Id)

            token = self._create_token(sandbox, user, sandbox.reservationContextDetails.domain)
            self._users_data.add_or_update(user, "token", token)

            # todo - how to update this data?
            student_link = f"http://18.200.153.138:3000/{new_sandbox.Reservation.Id}?access={token}"
            self._users_data.add_or_update(user, "student_link", student_link)

            msg = f'<a href="{student_link}" style="font-size:16px">Trainee Sandbox - {user}</a>'
            self._sandbox_output.notify(f'Trainee link for {user}: {msg}')

    # todo - move to a service?
    def _create_token(self, sandbox: Sandbox, user: str, domain: str):
        """
        Generate a user token for Sandbox API (and Training Portal) for the designated user.
        Assumes sandbox API is at port 82
        """
        self._sandbox_output.debug_print("Generating REST API Token")
        authorization = f"Basic {sbapi_login()}"
        headers = {'Content-type': 'application/json', 'Authorization': authorization}
        # todo - update api port so it will not be hard coded
        r = requests.post(f'http://{sandbox.connectivityContextDetails.server_address}:82/api/Token',
                          json={"username": user, "domain": domain}, headers=headers)
        return r.json()