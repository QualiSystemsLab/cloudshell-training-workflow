class IPsHandlerService:

    def __init__(self):
        pass

    def increment_ip(self, ip: str, increment: int) -> str:
        """
        Increment single IP or range
        :param ip: IP address or range in format 10.0.0.1-10
        :param increment:
        :return:
        """
        address_and_range = ip.split('-')
        # If user specified a range we want to ignore it
        address = address_and_range[0]
        # We should save the address and range as we will soon override it
        split_ip = address.split(".")
        split_ip[-1] = str(int(split_ip[-1]) + increment)
        new_ip_str = ".".join(split_ip)

        if len(address_and_range) > 1:
            new_range = str(int(address_and_range[1]) + increment)
            new_ip_str = new_ip_str + '-' + new_range

        return new_ip_str