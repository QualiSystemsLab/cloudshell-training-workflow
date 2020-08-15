from cloudshell.api.cloudshell_api import AttributeNameValue
from cloudshell.api.common_cloudshell_api import CloudShellAPIError
from cloudshell.workflow.orchestration.sandbox import Sandbox

from cloudshell.orch.training.models.position import Position
from cloudshell.orch.training.models.training_env import TrainingEnvironmentDataModel
from cloudshell.orch.training.services.apps import AppsService
from cloudshell.orch.training.services.sandbox_output import SandboxOutputService
from cloudshell.orch.training.services.users_data_manager import UsersDataManagerService, \
    UsersDataManagerServiceKeys as userDataKeys
from cloudshell.orch.training.utils.password import PasswordUtils


class PrepareEnvironmentLogic:

    def __init__(self, env_data: TrainingEnvironmentDataModel, users_data_manager: UsersDataManagerService,
                 sandbox_output_service: SandboxOutputService, apps_service: AppsService):
        self._env_data = env_data
        self._users_data_manager = users_data_manager
        self._sandbox_output = sandbox_output_service
        self._apps_service = apps_service

    def prepare_environment(self, sandbox: Sandbox):
        if self._env_data.instructor_mode:
            self._prepare_instructor_sandbox(sandbox)
        else:
            self._prepare_student_sandbox(sandbox)

    def _prepare_instructor_sandbox(self, sandbox: Sandbox):
        self._create_or_activate_users(sandbox)

        sandbox_details = sandbox.automation_api.GetReservationDetails(sandbox.id,
                                                                       disableCache=True).ReservationDescription
        duplicate_students_apps(sandbox, sandbox_details, sandbox.components)

    def _create_or_activate_users(self, sandbox: Sandbox):
        self._sandbox_output.notify("Creating or activating users")

        # create a group for the training users in current sandbox domain
        sandbox.automation_api.AddNewGroup(sandbox.id, 'Group for training users', 'Regular')
        sandbox.automation_api.AddGroupsToDomain(sandbox.reservationContextDetails.domain, [sandbox.id])

        for user in self._env_data.users_list:
            new_user_pass = PasswordUtils.generate_random_password()
            self._create_or_activate_user(new_user_pass, sandbox, user)
            self._users_data_manager.add_or_update(user, userDataKeys.PASSWORD, new_user_pass)

        sandbox.automation_api.AddUsersToGroup([self._env_data.users_list], sandbox.id)

    def _create_or_activate_user(self, new_user_pass: str, sandbox: Sandbox, user: str):
        try:
            system_user = sandbox.automation_api.GetUserDetails(user)
            if not system_user.IsActive:
                sandbox.automation_api.UpdateUser(user, user, isActive=True)
                sandbox.automation_api.UpdateUserPassword(user, new_user_pass)

        except CloudShellAPIError as exc:
            if exc.code == 133:
                # user doesnt exist, create user
                sandbox.automation_api.AddNewUser(user, new_user_pass, user, isActive=True)
            else:
                sandbox.logger.exception()
                raise

    def _prepare_student_sandbox(self, sandbox: Sandbox):
        self._clear_sandbox_components(sandbox)

    def _clear_sandbox_components(self, sandbox: Sandbox):
        api = sandbox.automation_api
        sandbox_details = api.GetReservationDetails(sandbox.id).ReservationDescription

        # todo - consider refactoring to a different service
        # delete all resources
        resource_names = [resource.Name for resource in sandbox_details.Resources]
        if resource_names:
            api.RemoveResourcesFromReservation(sandbox.id, resource_names)

        # todo - consider refactoring to a different service
        # delete all services
        service_names = [service.Alias for service in sandbox_details.Services]
        if service_names:
            try:
                api.RemoveServicesFromReservation(sandbox.id, service_names)
            except Exception as ex:
                sandbox.logger.exception('failed to delete services')
                self._sandbox_output.notify(f'failed to delete services with error: {ex}')

        # todo - consider refactoring to a different service
        # delete all apps
        for app in sandbox_details.Apps:
            api.RemoveAppFromReservation(sandbox.id, appName=app.Name)

    def duplicate_students_apps(self, sandbox: Sandbox):
        connectors_attr_updates = []
        api = sandbox.automation_api
        sandbox_details = api.GetReservationDetails(sandbox.id).ReservationDescription

        sandbox.components.refresh_components(sandbox)
        apps = [app.app_request.app_resource for app in sandbox.components.apps.values()]
        apps_to_duplicate = [app for app in apps if self._apps_service.should_duplicate_app(app)]

        service_positions = api.GetReservationServicesPositions(sandbox.id).ResourceDiagramLayouts
        service_positions_dict = {service.ResourceName: Position(service.X, service.Y) for service in service_positions}
        services_dict = sandbox.components.services

        # Dictionary of apps and its connectors
        app_connectors = {}
        for app in apps:
            app_connectors[app.Name] = []
            for connector in sandbox_details.Connectors:
                # All connectors connected to the app and services (not connectors between resources)
                if (connector.Source == app.Name and connector.Target in services_dict) or \
                        (connector.Target == app.Name and connector.Source in services_dict):
                    app_connectors[app.Name].append(connector)
            self._sandbox_output.debug_print(f'connectors detected for app {app.Name} are {len(app_connectors[app.Name])}')

        mgmt_service_names = ["mgmt", "management", "mgt"]
        for app in sandbox_details.Apps:
            has_existing_vnic_req = False
            # More than one connector - we should worry about vnic request
            if app.Name in app_connectors and len(app_connectors[app.Name]) > 1:
                connectors = app_connectors[app.Name]
                # Check for mgmt connector based on name convention for service
                mgmt_connector = next((connector for connector in connectors if
                                       (connector.Source.lower() in mgmt_service_names) or
                                       (connector.Target.lower() in mgmt_service_names)), None)

                for connector in connectors:
                    vnic_request_att = self._get_requested_vnic_attribute(connector, app)
                    # if someone specified a vnic - ignore this
                    if vnic_request_att and vnic_request_att.Value:
                        has_existing_vnic_req = True

                # Refactor item #1 - set vNic id for management network
                if mgmt_connector and not has_existing_vnic_req:
                    self._sandbox_output.debug_print(f'Setting management connection for {app.Name}')
                    attribute_name = self._get_requested_vnic_attribute_name(mgmt_connector, app)
                    attribute_info = AttributeNameValue(attribute_name, '0')
                    mgmt_connector.Attributes.append(attribute_info)
                    connectors_attr_updates.append((mgmt_connector.Source, mgmt_connector.Target, [attribute_info]))

                    # todo at the moment the code overrides the 'vnic name' attribute, but instead of override we want
                    #  to only to close the gaps. Similar to what the aws shell should be doing.
                    vnic_index = 1
                    for connector in connectors:
                        if connector == mgmt_connector:
                            continue
                        attribute_name = self._get_requested_vnic_attribute_name(connector, app)
                        attribute_info = AttributeNameValue(attribute_name, str(vnic_index))
                        connector.Attributes.append(attribute_info)
                        connectors_attr_updates.append((connector.Source, connector.Target,
                                                        [attribute_info]))
                        vnic_index = vnic_index + 1

        # todo Refactoring 2: Private IP requests string transform to JSON - need to to talk with Costya
        app_edit_requests = []
        for app in sandbox_details.Apps:

            orig_deployment_path = app.DeploymentPaths[0]
            ip_json = get_ip_json(sandbox, app, 0)

            if ip_json:
                new_deployment_attributes = [NameValuePair(att.Name, att.Value) for att in
                                             orig_deployment_path.DeploymentService.Attributes if
                                             "Private IP" not in att.Name]
                new_deployment_attributes.append(NameValuePair("Private IP", ip_json))

                new_default_deployment = DefaultDeployment(orig_deployment_path.Name,
                                                           Deployment(new_deployment_attributes))
                app_edit_requests.append(ApiEditAppRequest(app.Name, None, None, None, new_default_deployment))

        set_connector_requests = []

        # App duplication including name and IP changes
        for user_index in range(len(users_list)):
            sandbox_data_dict[users_list[user_index]]["id"] = str(user_index + 1)
            for app in apps_to_duplicate:
                debug_print(f"Duplicating app {app.Name} for user #{user_index + 1}")
                app_pos = service_positions_dict[app.Name]
                new_app = api.AddAppToReservation(reservationId=sandbox.id, appName=app.AppTemplateName,
                                                  positionX=app_pos.X, positionY=app_pos.Y + 100 * (user_index + 1))
                new_app_name = f"{str(user_index + 1)}_{app.Name}"

                orig_deployment_path = app.DeploymentPaths[0]
                ip_json = get_ip_json(sandbox, app, (user_index + 1) * 10)

                if ip_json:

                    new_deployment_attributes = [NameValuePair(att.Name, att.Value) for att in
                                                 orig_deployment_path.DeploymentService.Attributes if
                                                 "Private IP" not in att.Name]
                    new_deployment_attributes.append(NameValuePair("Private IP", ip_json))

                    new_default_deployment = DefaultDeployment(orig_deployment_path.Name,
                                                               Deployment(new_deployment_attributes))
                    api_edit_app_request = ApiEditAppRequest(new_app.ReservedAppName, new_app_name, None, None,
                                                             new_default_deployment)
                else:
                    api_edit_app_request = ApiEditAppRequest(new_app.ReservedAppName, new_app_name, None, None, None)

                app_edit_requests.append(api_edit_app_request)

                # Copy all attribute values for connectors including vnic requests set before
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

        if app_edit_requests:
            api.EditAppsInReservation(sandbox.id, app_edit_requests)
        if set_connector_requests:
            api.SetConnectorsInReservation(sandbox.id, set_connector_requests)

        for att_change in connectors_attr_updates:
            api.SetConnectorAttributes(sandbox.id, att_change[0], att_change[1], att_change[2])

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