from cloudshell.orch.training.models.training_env import TrainingEnvironmentDataModel
from cloudshell.orch.training.services.sandbox_output import SandboxOutputService
from cloudshell.api.cloudshell_api import SandboxDataKeyValue
import json


class DeployInfo(dict):
    def __init__(self, deployment_paths):

        deploypaths = []
        for deploy_path in deployment_paths:
            path = dict()
            path['name'] = deploy_path.Name
            path['is_default'] = deploy_path.IsDefault
            path['service_name'] = deploy_path.DeploymentService.Model
            path['attributes'] = dict()
            for attribute in deploy_path.DeploymentService.Attributes:
                path['attributes'][attribute.Name] = attribute.Value
            deploypaths.append(path)
        dict.__init__(self, deploypaths=deploypaths)

class SaveAppDeployment:
    def save(sandbox,data :TrainingEnvironmentDataModel,output_svc :SandboxOutputService,components=None):
        apps = sandbox.automation_api.GetReservationDetails(sandbox.id).ReservationDescription.Apps
        for app in apps:
            app_info = DeployInfo(app.DeploymentPaths)
            for deploy_path in app_info['deploypaths']:
                if 'Private IP' in deploy_path['attributes'] and app.Name in data.original_ip_values:
                    deploy_path['attributes']['Private IP'] = data.original_ip_values[app.Name]
                    output_svc.debug_print(f'overriding value for {app.Name} private IP will be {data.original_ip_values[app.Name]} ')

            serialized_deployment_info = json.dumps(app_info)

            key_value = SandboxDataKeyValue(app.Name, serialized_deployment_info)
            sandbox.automation_api.SetSandboxData(sandbox.id, [key_value])