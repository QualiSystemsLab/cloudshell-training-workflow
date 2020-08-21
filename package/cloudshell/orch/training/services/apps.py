from typing import List

from cloudshell.api.cloudshell_api import ReservationAppResource, ReservedResourceInfo, ResourceInfoVmDetails, \
    NameValuePair, DeploymentPathInfo, ApiEditAppRequest, DefaultDeployment, Deployment

from cloudshell.orch.training.models.position import Position
from cloudshell.orch.training.services.sandbox_output import SandboxOutputService

SHARED_ATT_POSTFIX = 'shared'
FALSEY_STRINGS = ['no', 'false', '0']


class AppsService:

    def __init__(self, sandbox_output_service: SandboxOutputService):
        self._sandbox_output = sandbox_output_service

    # def is_deployed_app(self, deployed_app: ReservedResourceInfo) -> bool:
    #     return isinstance(deployed_app.VmDetails, ResourceInfoVmDetails)  # true if deployed app or static VM

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
            [deployment_path for deployment_path in app.DeploymentPaths if deployment_path.IsDefault],
            None)
        return default_deployment_path

    def get_deployment_attribute_value(self, deployment: DeploymentPathInfo, attribute_name: str) -> str:
        return next(
            [attr.Value for attr in deployment.DeploymentService.Attributes if attr.Name == attribute_name],
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
