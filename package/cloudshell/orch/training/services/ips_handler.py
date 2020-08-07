from cloudshell.api.cloudshell_api import ReservationDescriptionInfo, ReservationAppResource
from cloudshell.workflow.orchestration.sandbox import Sandbox

from cloudshell.orch.training.models.training_env import TrainingEnvironmentDataModel
from package.cloudshell.orch.training.services.sandbox_output import SandboxOutputService

from netaddr import IPAddress, IPNetwork


class ips_handler():

    def _set_deployed_apps_addition_ips(sandbox: Sandbox, reservation_details: ReservationDescriptionInfo,output_svc: SandboxOutputService,data: TrainingEnvironmentDataModel):
        api = sandbox.automation_api
        for resource in reservation_details.Resources:
            output_svc.debug_print(f'checking app:{resource.Name}')
            if resource.VmDetails:
                for network in resource.VmDetails.NetworkData:

                    ip = next((data.Value for data in network.AdditionalData if data.Name.lower() == "ip"), "")
                    if not ip:
                        continue
                        # 10.0.1.10-20
                    eni = next((data.Value for data in network.AdditionalData if data.Name.lower() == "nic"), "")
                    if not eni:
                        continue

                    # We only saved IPs with additional IP range requests
                    if ip not in data.additional_ip_range:
                        continue

                    saved_range = data.additional_ip_range[ip]

                    if not saved_range:
                        continue

                    output_svc.debug_print(f'app:{resource.Name}ip:{ip} eni:{eni} range:{saved_range}')
                    address_and_range = saved_range.split('-')
                    address = address_and_range[0]
                    split_ip = address.split(".")
                    start = int(split_ip[-1])
                    end = int(address_and_range[1])
                    additional_ips = []
                    output_svc.debug_print(f'range start:{start} range end:{end}')
                    if start >= end:
                        continue

                    for addition_ip_ending in range(start + 1, end + 1):
                        # 10.0.1.0 => [10,10,1,0]
                        addition_ip_parts = address.split(".")
                        # [10,0,1,0] => [10,0,1,x]
                        addition_ip_parts[-1] = str(addition_ip_ending)
                        # [10,0,1,x] => 10.0.1.x
                        additional_ips.append('.'.join(addition_ip_parts))

                    addition_ips_string = "; ".join(additional_ips)


                    output_svc.debug_print(f'calling add IP api for {resource.Name} and nic {eni} with: {addition_ips_string}')

                    api.ExecuteResourceConnectedCommand(sandbox.id, resource.Name,
                                                         "assign_additional_private_ipv4s",
                                                         "connectivity", parameterValues=[eni, addition_ips_string],
                                                         printOutput=True)

    def _create_ips_json(sandbox: Sandbox, ips_list, app_name):
        sand_details = sandbox.automation_api.GetReservationDetails(sandbox.id,
                                                                    disableCache=True).ReservationDescription
        connectors = sand_details.Connectors
        sandbox_services_dict = {service.Alias: service for service in sand_details.Services}

        app_connectors = [conn for conn in connectors if conn.Source == app_name or conn.Target == app_name]
        connected_services = [conn.Target if conn.Source == app_name else conn.Source for conn in app_connectors]
        connected_services_CIDR = [
            next((att.Value for att in sandbox_services_dict[service].Attributes if att.Name == "Allocated CIDR"),
                 "255.255.255.255/32")
            for service in connected_services]
        new_ip_pairs = {}
        for ip in ips_list:
            for cidr in connected_services_CIDR:
                if IPAddress(ip) in IPNetwork(cidr):
                    new_ip_pairs[cidr] = ip
        result = json.dumps(new_ip_pairs)
        debug_print(f"Creating private spec for {app_name} string: {result}")
        return result

    def get_ip_json(sandbox: Sandbox, app: ReservationAppResource, increment: int):

        orig_deployment_path = app.DeploymentPaths[0]
        requested_ips_string = next(
            (attr.Value for attr in orig_deployment_path.DeploymentService.Attributes if attr.Name == "Private IP"),
            None)
        if requested_ips_string:
            if requested_ips_string and requested_ips_string.startswith('{') and requested_ips_string.endswith('}'):
                return requested_ips_string
            original_ip_values[app.Name] = requested_ips_string
            debug_print(f'original ip for {app.Name} it is: {requested_ips_string}')
            requested_ips = requested_ips_string.split(";")
            debug_print(f"incrementing requested ips {requested_ips}")
            new_ips = []
            for ip in requested_ips:

                address_and_range = ip.split('-')
                # If user specified a range we want to ignore it
                address = address_and_range[0]
                # We should save the address and range as we will soon override it
                split_ip = address.split(".")
                split_ip[-1] = str(int(split_ip[-1]) + increment)
                new_ip_str = ".".join(split_ip)

                if len(address_and_range) > 1:
                    new_range = str(int(address_and_range[1]) + increment)
                    new_ip_req = new_ip_str + '-' + new_range
                    additional_ip_range[new_ip_str] = new_ip_req
                    debug_print(f'saving ip for {new_ip_str} it is: {new_ip_req}')
                new_ips.append(new_ip_str)

            return _create_ips_json(sandbox, new_ips, app.Name)

        return ''