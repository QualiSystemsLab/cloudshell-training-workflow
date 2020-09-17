import ipaddress

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