from cloudshell.api.cloudshell_api import ReservationAppResource, ReservedResourceInfo, ResourceInfoVmDetails

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
