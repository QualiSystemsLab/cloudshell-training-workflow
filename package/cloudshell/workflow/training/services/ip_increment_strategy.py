import logging

from cloudshell.workflow.training.services.ips_handler import IPsHandlerService


class RequestedIPsIncrementStrategy:

    def __init__(self, ips_handler: IPsHandlerService, logger: logging.Logger):
        self._ips_handler = ips_handler
        self._logger = logger

    def increment_requested_ips_string(self, requested_ips_string: str, increment_octet: str,
                                       increment_size: int) -> str:

        IPsHandlerService.validate_increment_octet(increment_octet)

        new_ips = []

        for ip_req_for_nic in requested_ips_string.split(";"):
            new_ips.append(
                self._increment_ip_req_for_nic(ip_req_for_nic.strip(), increment_octet, increment_size))

        return ';'.join(new_ips)

    def _increment_ip_req_for_nic(self, ip_req_for_nic: str, increment_octet: str, increment_size: int) -> str:
        new_ips_list = []

        for ip_req_single in ip_req_for_nic.split(','):
            ip_req_single = ip_req_single.strip()

            if self._ips_handler.is_range(ip_req_single):
                new_ip_str = self._ips_handler.increment_ip_range(ip_req_single, increment_octet, increment_size)

            else:
                new_ip_str = self._ips_handler.increment_single_ip(ip_req_single, increment_octet, increment_size)

            new_ips_list.append(new_ip_str)

        return ','.join(new_ips_list)
