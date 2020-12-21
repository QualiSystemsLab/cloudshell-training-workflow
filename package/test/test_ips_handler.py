import unittest

from mock import Mock

from cloudshell.workflow.training.services.ips_handler import IPsHandlerService


class TestIPsHandlerService(unittest.TestCase):

    def setUp(self) -> None:
        self.ips_handler = IPsHandlerService()

    def test_validate_increment_octet_raises(self):
        with self.assertRaises(ValueError):
            self.ips_handler.validate_increment_octet('/28')

    def test_validate_increment_octet_passes_allowed_values(self):
        # act
        self.ips_handler.validate_increment_octet('/24')
        self.ips_handler.validate_increment_octet('/16')
        self.ips_handler.validate_increment_octet('/8')

    def test_increment_single_ip_last_octet(self):
        # act
        new_ip = self.ips_handler.increment_single_ip('10.0.0.0', '/24', 10)

        # assert
        self.assertEqual('10.0.0.10', new_ip)

    def test_increment_single_ip_third_octet(self):
        # act
        new_ip = self.ips_handler.increment_single_ip('10.0.0.0', '/16', 10)

        # assert
        self.assertEqual('10.0.10.0', new_ip)

    def test_increment_single_ip_second_octet(self):
        # act
        new_ip = self.ips_handler.increment_single_ip('10.0.0.0', '/8', 10)

        # assert
        self.assertEqual('10.10.0.0', new_ip)

    def test_increment_ip_range_last_octet(self):
        # act
        new_ip_range = self.ips_handler.increment_ip_range('10.0.0.10-15', '/24', 10)

        # assert
        self.assertEqual('10.0.0.20-25', new_ip_range)

    def test_increment_ip_range_third_octet(self):
        # act
        new_ip_range = self.ips_handler.increment_ip_range('10.0.0.10-15', '/16', 10)

        # assert
        self.assertEqual('10.0.10.10-15', new_ip_range)

    def test_increment_ip_range_second_octet(self):
        # act
        new_ip_range = self.ips_handler.increment_ip_range('10.0.0.10-15', '/8', 10)

        # assert
        self.assertEqual('10.10.0.10-15', new_ip_range)
