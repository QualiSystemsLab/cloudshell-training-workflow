from cloudshell.api.cloudshell_api import ReservationDescriptionInfo, ReservationAppResource
from cloudshell.workflow.orchestration.sandbox import Sandbox

from cloudshell.orch.training.services.sandbox_output import SandboxOutputService


class apps_duplicator():

    def _should_duplicate_app(app: ReservationAppResource,output_svc: SandboxOutputService):
        falsey_strings = ['no', 'false', '0']
        share_status = next(
            (attribute for attribute in app.LogicalResource.Attributes if attribute.Name.lower().endswith('shared')),
            None)
        if share_status:
            share_status_value = share_status.Value
            return share_status_value.lower() in falsey_strings

        output_svc.debug_print('no share preference for app: ' + app.Name)
        return False


    def duplicate_students_apps(sandbox: Sandbox, sandbox_details: ReservationDescriptionInfo, components):
        api = sandbox.automation_api
        apps = sandbox_details.Apps
        connectors_attr_updates = []

        apps_to_duplicate = [app for app in apps if _should_duplicate_app(app)]
        for app in apps:
            if not _should_duplicate_app(app):
                apps_to_share.append(app.Name)

        service_positions = api.GetReservationServicesPositions(sandbox.id).ResourceDiagramLayouts
        service_positions_dict = {service.ResourceName: Position(service.X, service.Y) for service in service_positions}
        services_dict = {service.Alias: service for service in sandbox_details.Services}

        # Dictionary of apps and its connectors
        app_connectors = {}
        for app in sandbox_details.Apps:
            app_connectors[app.Name] = []
            for connector in sandbox_details.Connectors:
                # All connectors connected to the app and services (not connectors between resources)
                if (connector.Source == app.Name and connector.Target in
                    services_dict) or (connector.Target == app.Name and
                                       connector.Source in services_dict):
                    app_connectors[app.Name].append(connector)
            output_svc.debug_print(f'connector detected for app {app.Name} are {len(app_connectors[app.Name])}')

        mgmt_service_names = ["mgmt", "management", "mgt"]
        for app in sandbox_details.Apps:
            has_existing_vnic_req = False
            # More than one connector - we should worry about vnic request
            if app.Name in app_connectors and len(app_connectors[app.Name]) > 1:
                connectors = app_connectors[app.Name]
                # Check for mgmt connector based on name convention for service
                mgmt_connector = next((connector for connector in connectors if (connector.Source.lower() in
                                                                                 mgmt_service_names) or (
                                                   connector.Target.lower() in mgmt_service_names)), None)

                for connector in connectors:
                    vnic_request_att = _get_requested_vnic_attribute(connector, app)
                    # if someone specified a vnic - ignore this
                    if vnic_request_att and vnic_request_att.Value:
                        has_existing_vnic_req = True

                # Refactor item #1 - set vNic id for management network
                if mgmt_connector and not has_existing_vnic_req:
                    output_svc.debug_print(f'Setting management connection for {app.Name}')
                    attribute_name = _get_requested_vnic_attribute_name(mgmt_connector, app)
                    attribute_info = AttributeNameValue(attribute_name, '0')
                    mgmt_connector.Attributes.append(attribute_info)
                    connectors_attr_updates.append((mgmt_connector.Source, mgmt_connector.Target,
                                                    [attribute_info]))

                    vnic_index = 1
                    for connector in connectors:
                        attribute_name = _get_requested_vnic_attribute_name(connector, app)
                        attribute_info = AttributeNameValue(attribute_name, str(vnic_index))
                        if connector == mgmt_connector:
                            continue
                        connector.Attributes.append(attribute_info)
                        connectors_attr_updates.append((connector.Source, connector.Target,
                                                        [attribute_info]))
                        vnic_index = vnic_index + 1

        # Refactoring 2: Private IP requests string transform to JSON
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
                output_svc.debug_print(f"Duplicating app {app.Name} for user #{user_index + 1}")
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