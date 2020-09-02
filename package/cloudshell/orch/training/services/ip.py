import ipaddress
import logging


# order of the list is important, change with caution
ALLOWED_INCREMENT_OCTET_LIST = ['/24', '/16', '/8']


class IPsHandlerService:

    def __init__(self):
        pass

    def increment_single_ip(self, ip: str, increment_octet: str, increment_size: int) -> str:
        self.validate_ip_address(ip)

        octet_index = (ALLOWED_INCREMENT_OCTET_LIST.index(increment_octet) + 1) * -1

        split_ip = ip.split(".")
        split_ip[octet_index] = str(int(split_ip[octet_index]) + increment_size)
        new_ip_str = ".".join(split_ip)

        return new_ip_str

    def increment_ip_range(self, ip: str, increment_octet: str, increment_size: int) -> str:
        self.validate_ip_address_range(ip)

        address_and_range = ip.split('-')
        address = address_and_range[0]
        new_ip_str = self.increment_single_ip(address, increment_octet, increment_size)

        # increment the range only if 'increment_octet' is /24
        new_range = address_and_range[1]
        if increment_octet == '/24':
            new_range = str(int(address_and_range[1]) + increment_size)

        new_ip_str = new_ip_str + '-' + new_range

        return new_ip_str

    def validate_ip_address_range(self, ip: str):
        address_and_range = ip.split('-')
        if not len(address_and_range) == 2:
            raise ValueError(f'{ip} is not a valid IP Address range. Valid example: 10.0.0.1-10')
        # also validate that the IP address part of the range has a valid IP address
        self.validate_ip_address(address_and_range[0])
        # todo validate that the range is legal

    def validate_ip_address(self, ip):
        # if ip address is not valid the following line will raise an exception
        ipaddress.ip_address(ip)

    def is_range(self, ip: str) -> bool:
        try:
            self.validate_ip_address_range(ip)
            return True
        except:
            return False


class RequestedIPsIncrementProvider:

    def __init__(self, ips_handler: IPsHandlerService, logger: logging.Logger):
        self._ips_handler = ips_handler
        self._logger = logger

    def increment_requested_ips_string(self, requested_ips_string: str, increment_octet: str,
                                       increment_size: int) -> str:

        RequestedIPsIncrementProvider.validate_increment_octet(increment_octet)

        new_ips = []
        requested_ips = requested_ips_string.split(";")

        for ip_req in requested_ips:
            ip_req = ip_req.strip()

            if self._ips_handler.is_range(ip_req):
                new_ip_str = self._ips_handler.increment_ip_range(ip_req, increment_octet, increment_size)
                new_ips.append(new_ip_str)

            else:
                new_ips_list = self._increment_comma_separated_list(ip_req, increment_octet, increment_size)
                new_ips.append(new_ips_list)

        incremented_ips_string = ';'.join(new_ips)
        return incremented_ips_string

    def _increment_comma_separated_list(self, ip_req: str, increment_octet: str, increment_size: int) -> str:
        new_ips_list = []
        ip_req_list = ip_req.split(',')

        for single_ip in ip_req_list:
            new_ip_str = self._ips_handler.increment_single_ip(single_ip.strip(), increment_octet,
                                                               increment_size)
            new_ips_list.append(new_ip_str)

        return ','.join(new_ips_list)

    @staticmethod
    def validate_increment_octet(increment_octet: str):
        if increment_octet not in ALLOWED_INCREMENT_OCTET_LIST:
            raise ValueError(f'Requested increment octet {increment_octet} is not supported. '
                             f'Supported values: {ALLOWED_INCREMENT_OCTET_LIST}')
