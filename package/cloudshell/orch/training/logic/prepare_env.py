from collections import namedtuple
from typing import Dict, List, Tuple

from cloudshell.api.cloudshell_api import AttributeNameValue, Connector, ReservationAppResource, \
    ReservationDescriptionInfo, ServiceInstance, CloudShellAPISession, ApiEditAppRequest, SetConnectorRequest, \
    NameValuePair
from cloudshell.api.common_cloudshell_api import CloudShellAPIError
from cloudshell.workflow.orchestration.sandbox import Sandbox

from cloudshell.orch.training.models.config import TrainingWorkflowConfig
from cloudshell.orch.training.models.position import Position
from cloudshell.orch.training.models.training_env import TrainingEnvironmentDataModel
from cloudshell.orch.training.services.apps import AppsService
from cloudshell.orch.training.services.ips_handler import IPsHandlerService
from cloudshell.orch.training.services.sandbox_create import SandboxCreateService
from cloudshell.orch.training.services.sandbox_output import SandboxOutputService
from cloudshell.orch.training.services.users import UsersService
from cloudshell.orch.training.services.users_data_manager import UsersDataManagerService, \
    UsersDataManagerServiceKeys as userDataKeys
from cloudshell.orch.training.utils.password import PasswordUtils

PRIVATE_IP_ATTR = "Private IP"
MGMT_SERVICE_NAMES = ['mgmt', 'management', 'mgt']

ConnectorsAttrUpdateRequest = namedtuple('ConnectorsAttrUpdateRequest', ['Souurce', 'Target', 'AttributeRequests'])


class PrepareEnvironmentLogic:

    def __init__(self, env_data: TrainingEnvironmentDataModel, config: TrainingWorkflowConfig,
                 users_data_manager: UsersDataManagerService, sandbox_output_service: SandboxOutputService,
                 apps_service: AppsService, sandbox_service: SandboxCreateService, users_service: UsersService,
                 ips_handler: IPsHandlerService):
        self._env_data = env_data
        self._config = config
        self._users_data_manager = users_data_manager
        self._sandbox_output = sandbox_output_service
        self._apps_service = apps_service
        self._sandbox_service = sandbox_service
        self._users_service = users_service
        self._ips_handler = ips_handler

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

        app_connectors = self._get_apps_to_connectors_dict(apps, sandbox_details, sandbox.components.services)

        # TODO - review this - the logic here is weird
        connectors_attr_updates = self._prepare_requested_vnic_attr_connector_changes(app_connectors, sandbox_details)

        # todo Refactoring 2: Private IP requests string transform to JSON - need to to talk with Costya
        # app_edit_requests = []
        # for app in sandbox_details.Apps:
        #
        #     orig_deployment_path = app.DeploymentPaths[0]
        #     ip_json = get_ip_json(sandbox, app, 0)
        #
        #     if ip_json:
        #         new_deployment_attributes = [NameValuePair(att.Name, att.Value) for att in
        #                                      orig_deployment_path.DeploymentService.Attributes if
        #                                      "Private IP" not in att.Name]
        #         new_deployment_attributes.append(NameValuePair("Private IP", ip_json))
        #
        #         new_default_deployment = DefaultDeployment(orig_deployment_path.Name,
        #                                                    Deployment(new_deployment_attributes))
        #         app_edit_requests.append(ApiEditAppRequest(app.Name, None, None, None, new_default_deployment))

        # duplicate apps including name and IP changes
        connectors_attr_updates.extend(self._duplicate_apps(api, apps, app_connectors, sandbox.id))

        # execute bulk update for connector attributes
        for att_change in connectors_attr_updates:
            api.SetConnectorAttributes(sandbox.id, att_change.Souurce, att_change.Target, att_change.AttributeRequests)

    def _duplicate_apps(self, api: CloudShellAPISession, apps: List[ReservationAppResource],
                        app_connectors: Dict[str, List[Connector]], sandbox_id: str) \
            -> List[ConnectorsAttrUpdateRequest]:

        apps_to_duplicate = self._apps_service.get_apps_to_duplicate(apps)
        service_app_positions_dict = self._get_service_or_app_name_to_position_dict(api, sandbox_id)

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
                app_set_connector_requests, app_connectors_attr_updates = self._duplicate_app_connectors(
                    app, app_connectors, new_app_name)

                set_connector_requests.extend(app_set_connector_requests)
                connectors_attr_updates.extend(app_connectors_attr_updates)

        # run update requests
        if app_edit_requests:
            api.EditAppsInReservation(sandbox_id, app_edit_requests)
        if set_connector_requests:
            api.SetConnectorsInReservation(sandbox_id, set_connector_requests)

        return connectors_attr_updates

    def _duplicate_app_connectors(self, app: ReservationAppResource, app_connectors: Dict[str, List[Connector]],
                                  new_app_name: str) \
            -> Tuple[List[SetConnectorRequest], List[ConnectorsAttrUpdateRequest]]:
        # Copy all attribute values for connectors including vnic requests set before
        set_connector_requests = []
        connectors_attr_updates = []
        for connector in app_connectors[app.Name]:
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

        new_private_ip_attr_val = self._get_private_ip_value_for_duplicate_app(app, user_index)
        attributes_to_update = [NameValuePair(PRIVATE_IP_ATTR, new_private_ip_attr_val)] \
            if new_private_ip_attr_val else []

        # update new app with new name and with updated value to Private IP attribute
        return self._apps_service.create_update_app_request(new_app.ReservedAppName,
                                                            new_app_name,
                                                            self._apps_service.get_default_deployment_option(app),
                                                            attributes_to_update)

    def _calculate_duplicate_app_position(self, app_pos: Position, user_index: int) -> Position:
        return Position(app_pos.X, app_pos.Y + 100 * (user_index + 1))

    # todo move to IPs service?
    def _get_private_ip_value_for_duplicate_app(self, app: ReservationAppResource, user_index: int) -> str:
        default_deployment_path = self._apps_service.get_default_deployment_option(app)
        requested_ips_string = self._apps_service.get_deployment_attribute_value(default_deployment_path,
                                                                                 PRIVATE_IP_ATTR)
        if not requested_ips_string:
            return None

        # calculate increment
        increment = self._calculate_IP_increment(user_index)

        # todo - add validation to check if we have a range bigger then the increment

        self._sandbox_output.debug_print(f'original ip for {app.Name} it is: {requested_ips_string}')
        requested_ips = requested_ips_string.split(";")

        new_ips = []

        for ip in requested_ips:
            # todo - should we add support for specific additional multiple IPs (in addition to range)
            new_ip_str = self._ips_handler.increment_ip(ip, increment)
            new_ips.append(new_ip_str)

        incremented_ips_string = ';'.join(new_ips)
        self._sandbox_output.debug_print(f"incremented requested ips: {incremented_ips_string}")

        return incremented_ips_string

    def _calculate_IP_increment(self, user_index):
        increment = (user_index + 1) * self._config.app_duplicate_ip_increment
        return increment

    def _prepare_requested_vnic_attr_connector_changes(self, app_connectors: Dict[str, List[Connector]],
                                                       sandbox_details: ReservationDescriptionInfo) \
            -> List[ConnectorsAttrUpdateRequest]:
        connectors_attr_updates = []

        for app in sandbox_details.Apps:
            has_existing_vnic_req = False
            # If more than one connector - we should worry about vnic request
            if self._does_app_has_multiple_connectors(app.Name, app_connectors):
                connectors = app_connectors[app.Name]
                # Check for mgmt connector based on name convention for service
                mgmt_connector = next((connector for connector in connectors if
                                       (connector.Source.lower() in MGMT_SERVICE_NAMES) or
                                       (connector.Target.lower() in MGMT_SERVICE_NAMES)), None)

                for connector in connectors:
                    vnic_request_att = self._get_requested_vnic_attribute(connector, app)
                    # if someone specified a vnic - ignore this
                    if vnic_request_att and vnic_request_att.Value:
                        has_existing_vnic_req = True

                # todo - review this logic with Roni
                #  Refactor item #1 - set vNic id for management network
                if mgmt_connector and not has_existing_vnic_req:
                    self._sandbox_output.debug_print(f'Setting management connection for {app.Name}')
                    attribute_name = self._get_requested_vnic_attribute_name(mgmt_connector, app)
                    attribute_info = AttributeNameValue(attribute_name, '0')
                    mgmt_connector.Attributes.append(attribute_info)
                    connectors_attr_updates.append(
                        ConnectorsAttrUpdateRequest(mgmt_connector.Source, mgmt_connector.Target, [attribute_info]))

                    # todo at the moment the code overrides the 'vnic name' attribute, but instead of override we want
                    #  to only to close the gaps. Similar to what the aws shell should be doing.
                    vnic_index = 1
                    for connector in connectors:
                        if connector == mgmt_connector:
                            continue
                        attribute_name = self._get_requested_vnic_attribute_name(connector, app)
                        attribute_info = AttributeNameValue(attribute_name, str(vnic_index))
                        connector.Attributes.append(attribute_info)
                        connectors_attr_updates.append(
                            ConnectorsAttrUpdateRequest(connector.Source, connector.Target, [attribute_info]))
                        vnic_index = vnic_index + 1

        return connectors_attr_updates

    def _does_app_has_multiple_connectors(self, app_name: str, app_connectors: Dict[str, List[Connector]]) -> bool:
        return app_name in app_connectors and len(app_connectors[app_name]) > 1

    def _get_service_or_app_name_to_position_dict(self, api: CloudShellAPISession, sandbox_id: str) -> \
            Dict[str, Position]:
        service_positions = api.GetReservationServicesPositions(sandbox_id).ResourceDiagramLayouts
        service_positions_dict = {service.ResourceName: Position(service.X, service.Y) for service in service_positions}
        return service_positions_dict

    def _get_apps_to_connectors_dict(self, apps: List[ReservationAppResource],
                                     sandbox_details: ReservationDescriptionInfo,
                                     services_dict: Dict[str, ServiceInstance]) -> Dict[str, List[Connector]]:
        app_connectors = {}
        for app in apps:
            app_connectors[app.Name] = []
            for connector in sandbox_details.Connectors:
                # All connectors connected to the app and services (not connectors between resources)
                if (connector.Source == app.Name and connector.Target in services_dict) or \
                        (connector.Target == app.Name and connector.Source in services_dict):
                    app_connectors[app.Name].append(connector)
            self._sandbox_output.debug_print(
                f'connectors detected for app {app.Name} are {len(app_connectors[app.Name])}')
        return app_connectors

    def _get_requested_vnic_attribute_name(self, connector, app):
        if app.Name == connector.Source:
            return 'Requested Source vNIC Name'
        if app.Name == connector.Target:
            return 'Requested Target vNIC Name'
        return None

    def _get_requested_vnic_attribute(self, connector, app):
        attr_name = self._get_requested_vnic_attribute_name(connector, app)
        for attr in connector.Attributes:
            if attr.Name == attr_name:
                return attr
        return None
