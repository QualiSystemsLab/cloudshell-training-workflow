from collections import namedtuple
from typing import Dict, List, Tuple

from cloudshell.api.cloudshell_api import AttributeNameValue, Connector, ReservationAppResource, \
    ReservationDescriptionInfo, CloudShellAPISession, ApiEditAppRequest, SetConnectorRequest, \
    NameValuePair
from cloudshell.workflow.orchestration.sandbox import Sandbox

from cloudshell.orch.training.models.config import TrainingWorkflowConfig
from cloudshell.orch.training.models.position import Position
from cloudshell.orch.training.models.training_env import TrainingEnvironmentDataModel
from cloudshell.orch.training.services.ip_increment_strategy import RequestedIPsIncrementStrategy
from cloudshell.orch.training.services.sandbox_components import SandboxComponentsHelperService
from cloudshell.orch.training.services.sandbox_lifecycle import SandboxLifecycleService
from cloudshell.orch.training.services.sandbox_output import SandboxOutputService
from cloudshell.orch.training.services.users import UsersService
from cloudshell.orch.training.services.users_data_manager import UsersDataManagerService, \
    UsersDataManagerServiceKeys as userDataKeys

PRIVATE_IP_ATTR = "Private IP"

ConnectorsAttrUpdateRequest = namedtuple('ConnectorsAttrUpdateRequest', ['Source', 'Target', 'AttributeRequests'])


class InitializeEnvironmentLogic:

    def __init__(self, env_data: TrainingEnvironmentDataModel, config: TrainingWorkflowConfig,
                 users_data_manager: UsersDataManagerService, sandbox_output_service: SandboxOutputService,
                 sandbox_components_service: SandboxComponentsHelperService, sandbox_service: SandboxLifecycleService,
                 users_service: UsersService, ips_increment_provider: RequestedIPsIncrementStrategy):
        self._env_data = env_data
        self._config = config
        self._users_data_manager = users_data_manager
        self._sandbox_output = sandbox_output_service
        self._components_service = sandbox_components_service
        self._sandbox_service = sandbox_service
        self._users_service = users_service
        self._ips_increment_provider = ips_increment_provider

    def prepare_environment(self, sandbox: Sandbox):
        if self._env_data.instructor_mode:
            self._prepare_instructor_sandbox(sandbox)
        else:
            self._prepare_student_sandbox(sandbox)

    def _prepare_instructor_sandbox(self, sandbox: Sandbox):
        self._create_or_activate_users(sandbox)
        self._duplicate_students_apps(sandbox)

    def _create_or_activate_users(self, sandbox: Sandbox):
        self._sandbox_output.notify("Creating or activating users")

        # create a group for the training users in current sandbox domain, will be removed during teardown
        self._users_service.create_training_users_group(sandbox.id, sandbox.reservationContextDetails.domain)

        for user in self._env_data.users_list:
            self._users_service.create_or_activate_training_user(user)

        self._users_service.add_training_users_to_group(sandbox.id, self._env_data.users_list)

    def _prepare_student_sandbox(self, sandbox: Sandbox):
        self._sandbox_service.clear_sandbox_components(sandbox)

    def _duplicate_students_apps(self, sandbox: Sandbox):
        api = sandbox.automation_api
        sandbox.components.refresh_components(sandbox)
        apps = [app.app_request.app_resource for app in sandbox.components.apps.values()]
        sandbox_details = api.GetReservationDetails(sandbox.id).ReservationDescription
        app_connectors = self._components_service.get_apps_to_connectors_dict(apps, sandbox_details,
                                                                              sandbox.components.services)

        # prepare requests for update to app connectors
        connectors_attr_updates = self._prepare_requested_vnic_attr_connector_changes(app_connectors, sandbox_details)

        # duplicate apps including name and IP changes and get updates for connector attributes
        connectors_attr_updates.extend(
            self._duplicate_apps(api, apps, app_connectors, sandbox.id))

        # execute bulk update for connector attributes
        for att_change in connectors_attr_updates:
            api.SetConnectorAttributes(sandbox.id, att_change.Source, att_change.Target, att_change.AttributeRequests)

    def _duplicate_apps(self, api: CloudShellAPISession, apps: List[ReservationAppResource],
                        app_connectors: Dict[str, List[Connector]], sandbox_id: str) \
            -> List[ConnectorsAttrUpdateRequest]:

        apps_to_duplicate = self._components_service.get_apps_to_duplicate(apps)
        service_app_positions_dict = self._components_service.get_service_and_app_name_to_position_dict(api, sandbox_id)

        app_edit_requests = []
        set_connector_requests = []
        connectors_attr_updates = []

        for user_index, user in enumerate(self._env_data.users_list):
            # set user ID based on index
            user_id = str(user_index + 1)
            self._users_data_manager.add_or_update(user, userDataKeys.ID, user_id)

            for app in apps_to_duplicate:
                self._sandbox_output.debug_print(f"Duplicating app {app.Name} for user #{user_id}")
                # create new name for duplicate app based on user id
                new_app_name = f"{user_id}_{app.Name}"
                # duplicate app and get request for update to be called in batch later
                app_edit_requests.append(
                    self._duplicate_app_and_get_update_request(api, new_app_name, app, sandbox_id,
                                                               service_app_positions_dict[app.Name],
                                                               user_index))
                # duplicate all connectors for duplicated app with all attributes
                app_set_connector_requests, app_connectors_attr_updates = \
                    self._create_duplicate_app_connectors_requests(app, app_connectors[app.Name], new_app_name)

                set_connector_requests.extend(app_set_connector_requests)
                connectors_attr_updates.extend(app_connectors_attr_updates)

        # run bulk update requests
        if app_edit_requests:
            api.EditAppsInReservation(sandbox_id, app_edit_requests)
        if set_connector_requests:
            api.SetConnectorsInReservation(sandbox_id, set_connector_requests)

        return connectors_attr_updates

    # todo move to components service?
    def _create_duplicate_app_connectors_requests(self, app: ReservationAppResource, app_connectors: List[Connector],
                                                  new_app_name: str) -> Tuple[List[SetConnectorRequest],
                                                              List[ConnectorsAttrUpdateRequest]]:
        # Copy all attribute values for connectors including vnic requests set before
        set_connector_requests = []
        connectors_attr_updates = []
        for connector in app_connectors:
            atts_with_values = [AttributeNameValue(att.Name, att.Value) for att in
                                connector.Attributes if att.Value]
            source = None
            target = None

            if connector.Target == app.Name:
                source = connector.Source
                target = new_app_name

            if connector.Source == app.Name:
                source = new_app_name
                target = connector.Target

            connector_request = SetConnectorRequest(source, target, 'bi', '')
            set_connector_requests.append(connector_request)
            if atts_with_values:
                connectors_attr_updates.append((source, target, atts_with_values))

        return set_connector_requests, connectors_attr_updates

    def _duplicate_app_and_get_update_request(self, api: CloudShellAPISession, new_app_name: str,
                                              app: ReservationAppResource, sandbox_id: str, app_pos: Position,
                                              user_index: int) -> ApiEditAppRequest:
        # add duplicate app in new position
        new_app_pos = self._calculate_duplicate_app_position(app_pos, user_index)
        new_app = api.AddAppToReservation(reservationId=sandbox_id, appName=app.AppTemplateName,
                                          positionX=new_app_pos.X, positionY=new_app_pos.Y)

        # todo - update all attributes in new app from original app. At the moment we only update Private IP attr but
        #  if other attributes were changed on the reservation app the duplicate will not get it because we are adding
        #  the duplicate from the app template
        new_private_ip_attr_val = self._get_private_ip_value_for_duplicate_app(app, user_index)

        attributes_to_update = [NameValuePair(PRIVATE_IP_ATTR, new_private_ip_attr_val)] \
            if new_private_ip_attr_val else []

        # update new app with new name and with updated value to Private IP attribute
        return self._components_service.create_update_app_request(
            new_app.ReservedAppName, new_app_name, self._components_service.get_default_deployment_option(app),
            attributes_to_update)

    def _calculate_duplicate_app_position(self, app_pos: Position, user_index: int) -> Position:
        return Position(app_pos.X, app_pos.Y + 100 * (user_index + 1))

    def _get_private_ip_value_for_duplicate_app(self, app: ReservationAppResource, user_index: int) -> str:
        default_deployment_path = self._components_service.get_default_deployment_option(app)
        requested_ips_string = self._components_service.get_deployment_attribute_value(default_deployment_path,
                                                                                       PRIVATE_IP_ATTR)
        if not requested_ips_string:
            return None

        # todo - add validation to check if we have a range bigger then the increment

        self._sandbox_output.debug_print(f'original ip for {app.Name} it is: {requested_ips_string}')
        incremented_ips_string = self._ips_increment_provider.increment_requested_ips_string(
            requested_ips_string, self._config.app_duplicate_increment_octet, self._calculate_IP_increment(user_index))
        self._sandbox_output.debug_print(f"incremented requested ips: {incremented_ips_string}")

        return incremented_ips_string

    def _calculate_IP_increment(self, user_index):
        return (user_index + 1) * self._config.app_duplicate_ip_increment

    def _prepare_requested_vnic_attr_connector_changes(self, app_to_connectors_dict: Dict[str, List[Connector]],
                                                       sandbox_details: ReservationDescriptionInfo) \
            -> List[ConnectorsAttrUpdateRequest]:

        connectors_attr_updates = []

        for app in sandbox_details.Apps:
            # If more than one connector - we should check about vnic request
            if not self._does_app_has_multiple_connectors(app.Name, app_to_connectors_dict):
                continue

            connectors = app_to_connectors_dict[app.Name]

            mgmt_connector = self._components_service.get_management_connector(connectors)
            if not mgmt_connector:
                # if not mgmt connector we will not update requested vNIC attr
                continue

            # check if we have at least one vnic request in all app connectors
            has_existing_vnic_req = self._components_service.does_connector_has_existing_vnic_req(app, connectors)
            if has_existing_vnic_req:
                self._sandbox_output.notify(f"Requested vNICs will not be changed for {app.Name} because "
                                            f"an existing value was detected on one or more connectors")
                continue

            # if we detected a management connector and Requested vNIC was not set on any connector then we set
            # the management connector with index 0 and explicitly assign consecutive index values to all other
            # connectors for current app
            self._sandbox_output.debug_print(f'Setting management connection for {app.Name}')
            connectors_attr_updates.append(
                self._prepare_connector_change_req(app, mgmt_connector, '0'))

            for index, connector in enumerate(connectors):
                if connector == mgmt_connector:
                    continue
                vnic_index = index + 1
                connectors_attr_updates.append(self._prepare_connector_change_req(app, connector, str(vnic_index)))

        return connectors_attr_updates

    def _prepare_connector_change_req(self, app: ReservationAppResource, connector: Connector,
                                      req_vNIC_name_value: str) -> ConnectorsAttrUpdateRequest:
        attribute_name = self._components_service.get_requested_vnic_attribute_name(connector, app)
        attribute_info = AttributeNameValue(attribute_name, req_vNIC_name_value)
        connector.Attributes.append(attribute_info)
        return ConnectorsAttrUpdateRequest(connector.Source, connector.Target, [attribute_info])

    def _does_app_has_multiple_connectors(self, app_name: str, app_connectors: Dict[str, List[Connector]]) -> bool:
        return app_name in app_connectors and len(app_connectors[app_name]) > 1
