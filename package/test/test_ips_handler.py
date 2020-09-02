import unittest

from cloudshell.orch.training.services.ips_handler import IPsHandlerService


class TestIPsHandlerService(unittest.TestCase):

    def test_increment_single_ip_last_octet(self):
        # arrange
        ips_handler = IPsHandlerService()

        # act
        new_ip = ips_handler.increment_single_ip('10.0.0.0', '/24', 10)

        # assert
        self.assertEqual('10.0.0.10', new_ip)

    def test_increment_ip_range_last_octet(self):
        # arrange
        ips_handler = IPsHandlerService()

        # act
        new_ip_range = ips_handler.increment_ip_range('10.0.0.10-15', '/24', 10)

        # assert
        self.assertEqual('10.0.0.20-25', new_ip_range)