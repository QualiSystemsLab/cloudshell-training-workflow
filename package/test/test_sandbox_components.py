import unittest

from mock import Mock

from cloudshell.workflow.training.services.sandbox_components import SandboxComponentsHelperService


class TestSandboxComponentsHelperService(unittest.TestCase):

    def setUp(self) -> None:
        self.sandbox_comp_helper = SandboxComponentsHelperService(Mock())

    def test_should_duplicate_app_returns_false_no_shared_attribute(self):
        # arrange
        app = Mock()
        app.LogicalResource.Attributes = [Mock(Name='att1', Value='val1')]

        # act
        result = self.sandbox_comp_helper.should_duplicate_app(app)

        # assert
        self.assertFalse(result)

    def test_should_duplicate_app_returns_false_with_shared_attribute(self):
        # arrange
        app = Mock()
        app.LogicalResource.Attributes = [Mock(Name='att1', Value='val1'), Mock(Name='is_shared', Value='yes')]

        # act
        result = self.sandbox_comp_helper.should_duplicate_app(app)

        # assert
        self.assertFalse(result)

    def test_should_duplicate_app_returns_true_with_shared_attribute(self):
        # arrange
        app = Mock()
        app.LogicalResource.Attributes = [Mock(Name='att1', Value='val1'), Mock(Name='is_shared', Value='no')]

        # act
        result = self.sandbox_comp_helper.should_duplicate_app(app)

        # assert
        self.assertTrue(result)

    def test_should_share_app_returns_true(self):
        # arrange
        app = Mock()
        app.LogicalResource.Attributes = [Mock(Name='att1', Value='val1'), Mock(Name='is_shared', Value='yes')]

        # act
        result = self.sandbox_comp_helper.should_share_app(app)

        # assert
        self.assertTrue(result)

    def test_should_share_app_returns_false(self):
        # arrange
        app = Mock()
        app.LogicalResource.Attributes = [Mock(Name='att1', Value='val1'), Mock(Name='is_shared', Value='no')]

        # act
        result = self.sandbox_comp_helper.should_share_app(app)

        # assert
        self.assertFalse(result)

    def test_get_deployment_attribute_value(self):
        # arrange
        deployment = Mock()
        deployment.DeploymentService.Attributes = [Mock(Name='attr1', Value='val1'), Mock(Name='attr2', Value='val2')]
        attribute_name = 'attr1'

        # act
        result = self.sandbox_comp_helper.get_deployment_attribute_value(deployment, attribute_name)

        # assert
        self.assertEqual('val1', result)

    def test_get_deployment_attribute_returns_none_when_nothing_found(self):
        # arrange
        deployment = Mock()
        deployment.DeploymentService.Attributes = [Mock(Name='attr1', Value='val1'), Mock(Name='attr2', Value='val2')]
        attribute_name = 'attr3'

        # act
        result = self.sandbox_comp_helper.get_deployment_attribute_value(deployment, attribute_name)

        # assert
        self.assertIsNone(result)

    def test_get_default_deployment_option(self):
        # arrange
        default_deployment = Mock(IsDefault=True)
        non_default_deployment_1 = Mock(IsDefault=False)
        non_default_deployment_2 = Mock(IsDefault=False)
        app = Mock(DeploymentPaths=[non_default_deployment_1, non_default_deployment_2, default_deployment])

        # act
        result = self.sandbox_comp_helper.get_default_deployment_option(app)

        # assert
        self.assertEqual(default_deployment, result)

    def test_create_update_app_request(self):
        # arrange
        deployment = Mock()
        deployment.DeploymentService.Attributes=[Mock(Name='attr1', Value='val1'),
                                                 Mock(Name='attr2', Value='val2'),
                                                 Mock(Name='attr3', Value='val3')]
        attributes_to_update = [Mock(Name='attr2', Value='new_value'),
                                Mock(Name='attr4', Value='val4')]
        app_name = Mock()
        app_name_new = Mock()

        # act
        result = self.sandbox_comp_helper.create_update_app_request(app_name, app_name_new, deployment,
                                                                    attributes_to_update)

        # assert
        self.assertEqual(app_name, result.Name)
        self.assertEqual(app_name_new, result.NewName)
        self.assertEqual(deployment.Name, result.DefaultDeployment.Name)
        self.assertIn(attributes_to_update[0], result.DefaultDeployment.Deployment.Attributes)
        self.assertIn(attributes_to_update[1], result.DefaultDeployment.Deployment.Attributes)

    def test_get_management_connector_supports_multiple_variations(self):
        # arrange
        mgmt_name_1 = 'mgmt'
        mgmt_name_2 = 'mgt'
        mgmt_name_3 = 'management'

        mgmt_connector = Mock(Source=mgmt_name_1, Target='app1')
        result = self.sandbox_comp_helper.get_management_connector([mgmt_connector])
        self.assertEqual(mgmt_connector, result)

        mgmt_connector = Mock(Source=mgmt_name_2, Target='app1')
        result = self.sandbox_comp_helper.get_management_connector([mgmt_connector])
        self.assertEqual(mgmt_connector, result)

        mgmt_connector = Mock(Source='app1', Target=mgmt_name_3)
        result = self.sandbox_comp_helper.get_management_connector([mgmt_connector])
        self.assertEqual(mgmt_connector, result)

        connector = Mock(Source='app1', Target='subnet')
        result = self.sandbox_comp_helper.get_management_connector([connector])
        self.assertIsNone(result)
