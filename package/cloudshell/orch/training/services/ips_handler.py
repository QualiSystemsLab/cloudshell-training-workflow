from cloudshell.cp.core.requested_ips.validator import RequestedIPsValidator

# order of the list is important, change with caution
ALLOWED_INCREMENT_OCTET_LIST = ['/24', '/16', '/8']


class IPsHandlerService:

    def __init__(self):
        pass

    @staticmethod
    def validate_increment_octet(increment_octet: str):
        if increment_octet not in ALLOWED_INCREMENT_OCTET_LIST:
            raise ValueError(f'Requested increment octet {increment_octet} is not supported. '
                             f'Supported values: {ALLOWED_INCREMENT_OCTET_LIST}')

    def increment_single_ip(self, ip: str, increment_octet: str, increment_size: int) -> str:
        RequestedIPsValidator.validate_ip_address(ip)

        octet_index = (ALLOWED_INCREMENT_OCTET_LIST.index(increment_octet) + 1) * -1

        split_ip = ip.split(".")
        split_ip[octet_index] = str(int(split_ip[octet_index]) + increment_size)
        new_ip_str = ".".join(split_ip)

        return new_ip_str

    def increment_ip_range(self, ip: str, increment_octet: str, increment_size: int) -> str:
        RequestedIPsValidator.validate_ip_address_range_basic(ip)

        address_and_range = ip.split('-')
        address = address_and_range[0]
        new_ip_str = self.increment_single_ip(address, increment_octet, increment_size)

        # increment the range only if 'increment_octet' is /24
        new_range = address_and_range[1]
        if increment_octet == '/24':
            new_range = str(int(address_and_range[1]) + increment_size)

        new_ip_str = new_ip_str + '-' + new_range

        return new_ip_str
