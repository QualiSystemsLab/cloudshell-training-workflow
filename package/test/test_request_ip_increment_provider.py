import unittest

from mock import Mock, call

from cloudshell.orch.training.services.ip import RequestedIPsIncrementProvider


class TestRequestedIPsIncrementProvider(unittest.TestCase):

    def setUp(self) -> None:
        logger = Mock()
        self.ips_handler = Mock()
        self.ip_increment_provider = RequestedIPsIncrementProvider(self.ips_handler, logger)

    def test_increment_requested_ips_string_invalid_octet(self):
        # act
        with self.assertRaises(ValueError):
            self.ip_increment_provider.increment_requested_ips_string(Mock(), '/26', 20)

    def test_validate_increment_octet_raises(self):
        with self.assertRaises(ValueError):
            self.ip_increment_provider.validate_increment_octet('/28')

    def test_validate_increment_octet_passes_allowed_values(self):
        # act
        self.ip_increment_provider.validate_increment_octet('/24')
        self.ip_increment_provider.validate_increment_octet('/16')
        self.ip_increment_provider.validate_increment_octet('/8')

    def test_increment_requested_ips_string_complex(self):
        def change_req(*args, **kwargs):
            return args[0] + "'"

        # arrange
        request = 'x;y;z'
        self.ips_handler.is_range.side_effect = [True, False, False]
        self.ips_handler.increment_ip_range.side_effect = change_req
        self.ip_increment_provider._increment_comma_separated_list = Mock(side_effect=change_req)

        # act
        result = self.ip_increment_provider.increment_requested_ips_string(request, '/24', 10)

        # assert
        self.ips_handler.increment_ip_range.assert_called_once_with('x', '/24', 10)
        self.ip_increment_provider._increment_comma_separated_list.assert_has_calls([call('y', '/24', 10),
                                                                                     call('z', '/24', 10)])
        self.assertEqual("x';y';z'", result)

    def test_increment_requested_ips_string_simple(self):


        # arrange
        request = 'x'
        self.ips_handler.is_range.side_effect = [False]
        self.ip_increment_provider._increment_comma_separated_list = Mock(side_effect=self._change_req_ip)

        # act
        result = self.ip_increment_provider.increment_requested_ips_string(request, '/24', 10)

        # assert
        self.ips_handler.increment_ip_range.assert_not_called()
        self.ip_increment_provider._increment_comma_separated_list.assert_called_once_with('x', '/24', 10)
        self.assertEqual("x'", result)

    def test_increment_comma_separated_list_simple(self):
        # arrange
        request = 'x'
        self.ips_handler.increment_single_ip.side_effect = self._change_req_ip

        # act
        result = self.ip_increment_provider._increment_comma_separated_list(request, '/24', 10)

        # assert
        self.assertEqual("x'", result)
        self.ips_handler.increment_single_ip.assert_called_once()

    def test_increment_comma_separated_list_complex(self):
        # arrange
        request = 'x,y,z'
        self.ips_handler.increment_single_ip.side_effect = self._change_req_ip

        # act
        result = self.ip_increment_provider._increment_comma_separated_list(request, '/24', 10)

        # assert
        self.assertEqual("x',y',z'", result)
        self.ips_handler.increment_single_ip.assert_called()

    def _change_req_ip(self, *args, **kwargs):
        return args[0] + "'"