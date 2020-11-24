from typing import List, Dict

from cloudshell.api.cloudshell_api import ReservationAppResource, NameValuePair, DeploymentPathInfo, ApiEditAppRequest, \
    DefaultDeployment, Deployment, Connector, \
    ReservationDescriptionInfo, ServiceInstance, CloudShellAPISession

from cloudshell.workflow.training.models.position import Position
from cloudshell.workflow.training.services.sandbox_output import SandboxOutputService

SHARED_ATT_POSTFIX = 'shared'
FALSEY_STRINGS = ['no', 'false', '0']
MGMT_SERVICE_NAMES = ['mgmt', 'management', 'mgt']


class SandboxComponentsHelperService:

    def __init__(self, sandbox_output_service: SandboxOutputService):
        self._sandbox_output = sandbox_output_service

    def should_share_app(self, app: ReservationAppResource) -> bool:
        return not self.should_duplicate_app(app)

    def should_duplicate_app(self, app: ReservationAppResource) -> bool:
        share_status = next(
            (attribute for attribute in app.LogicalResource.Attributes
             if attribute.Name.lower().endswith(SHARED_ATT_POSTFIX)), None)
        if share_status:
            share_status_value = share_status.Value
            return share_status_value.lower() in FALSEY_STRINGS

        self._sandbox_output.debug_print(f'no share preference for app: {app.Name}')
        return False

    def get_apps_to_duplicate(self, apps: List[ReservationAppResource]):
        return [app for app in apps if self.should_duplicate_app(app)]

    def get_default_deployment_option(self, app: ReservationAppResource) -> DeploymentPathInfo:
        default_deployment_path = next(
            iter([deployment_path for deployment_path in app.DeploymentPaths if deployment_path.IsDefault]),
            None)
        return default_deployment_path

    def get_deployment_attribute_value(self, deployment: DeploymentPathInfo, attribute_name: str) -> str:
        return next(
            iter([attr.Value for attr in deployment.DeploymentService.Attributes if attr.Name == attribute_name]),
            None)

    def create_update_app_request(self, app_name: str, new_app_name: str, default_deployment_path: DeploymentPathInfo,
                                  attributes_to_update: List[NameValuePair]) -> ApiEditAppRequest:

        attribute_names_to_update = [att_nvp.Name for att_nvp in attributes_to_update]
        attributes_without_update = [NameValuePair(att.Name, att.Value) for att in
                                     default_deployment_path.DeploymentService.Attributes if
                                     att.Name not in attribute_names_to_update]

        new_default_deployment = DefaultDeployment(default_deployment_path.Name,
                                                   Deployment(attributes_to_update + attributes_without_update))

        return ApiEditAppRequest(app_name, new_app_name, None, None, new_default_deployment)

    def get_requested_vnic_attribute_name(self, connector: Connector, app: ReservationAppResource) -> str:
        if app.Name == connector.Source:
            return 'Requested Source vNIC Name'
        if app.Name == connector.Target:
            return 'Requested Target vNIC Name'
        return None

    def get_requested_vnic_attribute(self, connector, app):
        attr_name = self.get_requested_vnic_attribute_name(connector, app)
        for attr in connector.Attributes:
            if attr.Name == attr_name:
                return attr
        return None

    def get_management_connector(self, connectors: List[Connector]) -> Connector:
        mgmt_connector = next((connector for connector in connectors if
                               (connector.Source.lower() in MGMT_SERVICE_NAMES) or
                               (connector.Target.lower() in MGMT_SERVICE_NAMES)), None)
        return mgmt_connector

    def get_apps_to_connectors_dict(self, apps: List[ReservationAppResource],
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

    def get_service_and_app_name_to_position_dict(self, api: CloudShellAPISession, sandbox_id: str) -> \
            Dict[str, Position]:
        service_positions = api.GetReservationServicesPositions(sandbox_id).ResourceDiagramLayouts
        service_positions_dict = {service.ResourceName: Position(service.X, service.Y) for service in service_positions}
        return service_positions_dict

    def does_connector_has_existing_vnic_req(self, app: ReservationAppResource, connectors: List[Connector]) -> bool:
        has_existing_vnic_req = False
        for connector in connectors:
            vnic_request_att = self.get_requested_vnic_attribute(connector, app)
            if vnic_request_att and vnic_request_att.Value:
                has_existing_vnic_req = True
                break
        return has_existing_vnic_req
