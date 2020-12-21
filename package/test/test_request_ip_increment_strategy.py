import unittest

from mock import Mock, call, patch

from cloudshell.workflow.training.services.ip_increment_strategy import RequestedIPsIncrementStrategy


class TestRequestedIPsIncrementStrategy(unittest.TestCase):

    def setUp(self) -> None:
        logger = Mock()
        self.ips_handler = Mock()
        self.ip_increment_strategy = RequestedIPsIncrementStrategy(self.ips_handler, logger)

    def test_increment_requested_ips_string_invalid_octet(self):
        # act
        with self.assertRaises(ValueError):
            self.ip_increment_strategy.increment_requested_ips_string(Mock(), '/26', 20)

    def test_increment_requested_ips_string_complex(self):
        # arrange
        request = 'x;y;z'
        self.ip_increment_strategy._increment_ip_req_for_nic = Mock(side_effect=self._change_req_ip)

        # act
        result = self.ip_increment_strategy.increment_requested_ips_string(request, '/24', 10)

        # assert
        self.ip_increment_strategy._increment_ip_req_for_nic.assert_has_calls([call('x', '/24', 10),
                                                                               call('y', '/24', 10),
                                                                               call('z', '/24', 10)])
        self.assertEqual("x';y';z'", result)

    def test_increment_requested_ips_string_simple(self):
        # arrange
        request = 'x'
        self.ip_increment_strategy._increment_ip_req_for_nic = Mock(side_effect=self._change_req_ip)

        # act
        result = self.ip_increment_strategy.increment_requested_ips_string(request, '/24', 10)

        # assert
        self.ip_increment_strategy._increment_ip_req_for_nic.assert_called_once_with('x', '/24', 10)
        self.assertEqual("x'", result)

    @patch('cloudshell.workflow.training.services.ip_increment_strategy.RequestedIPsValidator')
    def test_increment_ip_req_for_nic_single_ip(self, req_ip_validator_mock):
        # arrange
        request = 'x'
        req_ip_validator_mock.is_range.return_value = False
        self.ips_handler.increment_single_ip.side_effect = self._change_req_ip

        # act
        result = self.ip_increment_strategy._increment_ip_req_for_nic(request, '/24', 10)

        # assert
        self.assertEqual(result, "x'")
        self.ips_handler.increment_single_ip.assert_called_once()

    @patch('cloudshell.workflow.training.services.ip_increment_strategy.RequestedIPsValidator')
    def test_increment_ip_req_for_nic_complex(self, req_ip_validator_mock):
        # arrange
        request = 'x,y,z'
        req_ip_validator_mock.is_range.side_effect = [False, True, False]
        self.ips_handler.increment_single_ip.side_effect = self._change_req_ip
        self.ips_handler.increment_ip_range.side_effect = self._change_req_ip

        # act
        result = self.ip_increment_strategy._increment_ip_req_for_nic(request, '/24', 10)

        # assert
        self.assertEqual(result, "x',y',z'")
        self.ips_handler.increment_ip_range.assert_called_once_with('y', '/24', 10)
        self.ips_handler.increment_single_ip.assert_has_calls([call('x', '/24', 10),
                                                               call('z', '/24', 10)])

    def _change_req_ip(self, *args, **kwargs):
        return args[0] + "'"