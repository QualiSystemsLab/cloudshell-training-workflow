import unittest

from mock import Mock, patch


from cloudshell.orch.training.parsers.sandbox_inputs_processing import SandboxInputsParser

class TestSandboxInputsParser(unittest.TestCase):
    def setUp(self) -> None:
        self.sandbox = Mock()


    def test_debug_mode_on(self):
        # arrange
        self.sandbox.global_inputs = {"Diagnostics" : "On"}
        # act
        flag = SandboxInputsParser._is_debug_on(self.sandbox)
        # assert
        self.assertTrue(flag)

    def test_debug_mode_off(self):
        # arrange
        self.sandbox.global_inputs = {"Diagnostics" : "Off"}
        # act
        flag = SandboxInputsParser._is_debug_on(self.sandbox)
        # assert
        self.assertFalse(flag)

    def test_debug_mode_none(self):
        # arrange
        self.sandbox.global_inputs = {}
        # act
        flag = SandboxInputsParser._is_debug_on(self.sandbox)
        # assert
        self.assertFalse(flag)

    def test_debug_mode_other(self):
        # arrange
        self.sandbox.global_inputs = {"Diagnostics" : "Tru"}
        # act
        flag = SandboxInputsParser._is_debug_on(self.sandbox)
        # assert
        self.assertFalse(flag)

    ########

    def test_user_list_empty(self):
        # arrange
        self.sandbox.global_inputs = {"Training Users" : ""}
        # act
        user_list = SandboxInputsParser._sandbox_user_list(self.sandbox)
        # assert
        self.assertTrue(len(user_list)==0)

    def test_user_list_doesnt_exist(self):
        # arrange
        self.sandbox.global_inputs = {}
        # act
        user_list = SandboxInputsParser._sandbox_user_list(self.sandbox)
        # assert
        self.assertTrue(len(user_list)==0)

    def test_user_list_one_user(self):
        # arrange
        self.sandbox.global_inputs = {"Training Users" : "test@test"}
        # act
        user_list = SandboxInputsParser._sandbox_user_list(self.sandbox)
        # assert
        self.assertTrue(len(user_list)==0)

    def test_user_list_two_users(self):
        # arrange
        self.sandbox.global_inputs = {"Training Users" : "a;b"}
        # act
        user_list = SandboxInputsParser._sandbox_user_list(self.sandbox)
        # assert
        self.assertTrue(len(user_list)==2)

    def test_is_instructormode_true(self):
        # arrange
        self.sandbox.global_inputs = {"Training Users": "#"}
        # act
        flag = SandboxInputsParser._is_instructor_mode(self.sandbox)
        # assert
        self.assertTrue(flag)

    def test_is_instructormode_false(self):
        # arrange
        self.sandbox.global_inputs = {}
        # act
        flag = SandboxInputsParser._is_instructor_mode(self.sandbox)
        # assert
        self.assertTrue(flag)

    @patch("cloudshell.orch.training.parsers.sandbox_inputs_processing.SandboxInputsParser._sandbox_user_list")
    @patch("cloudshell.orch.training.parsers.sandbox_inputs_processing.SandboxInputsParser._is_instructor_mode")
    @patch("cloudshell.orch.training.parsers.sandbox_inputs_processing.SandboxInputsParser._is_debug_on")
    def test_parse_sandbox_inputs(self,m1_patch: Mock,m2_patch: Mock,m3_patch: Mock):
        m1_patch.return_value = Mock()
        m2_patch.return_value = Mock()
        m3_patch.return_value = Mock()

        SandboxInputsParser.parse_sandbox_inputs(self.sandbox)
        SandboxInputsParser._sandbox_user_list.assert_called_once()
        SandboxInputsParser._sandbox_user_list._is_instructor_mode()
        SandboxInputsParser._sandbox_user_list._is_debug_on()


