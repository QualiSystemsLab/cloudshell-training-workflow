import unittest
from typing import List, Dict

from cloudshell.api.cloudshell_api import Connector, ReservationAppResource, ReservationDescriptionInfo, \
    ServiceInstance, CloudShellAPISession, ResourceDiagramLayoutInfo, ReservationDiagramLayoutResponseInfo, \
    AttributeValueInfo
from mock import Mock

from cloudshell.workflow.training.services.sandbox_components import SandboxComponentsHelperService
from cloudshell.workflow.training.models.position import Position


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

    def test_get_requested_vnic_attribute_name_src(self):
        # arrange
        mock_connector: Connector = Mock()
        mock_app: ReservationAppResource = Mock()
        mock_app.Name = "app_name"
        mock_connector.Source =  "app_name"

        # act
        result = self.sandbox_comp_helper.get_requested_vnic_attribute_name(mock_connector,mock_app)

        # assert
        self.assertEqual(result,"Requested Source vNIC Name")

    def test_get_requested_vnic_attribute_name_trgt(self):
        # arrange
        mock_connector: Connector = Mock()
        mock_app: ReservationAppResource = Mock()
        mock_app.Name = "app_name"
        mock_connector.Target =  "app_name"

        # act
        result = self.sandbox_comp_helper.get_requested_vnic_attribute_name(mock_connector,mock_app)

        # assert
        self.assertEqual(result,"Requested Target vNIC Name")

    def test_get_requested_vnic_attribute_name_none(self):
        # arrange
        mock_connector: Connector = Mock()
        mock_app: ReservationAppResource = Mock()
        mock_app.Name = "app_name"

        # act
        result = self.sandbox_comp_helper.get_requested_vnic_attribute_name(mock_connector,mock_app)

        # assert
        self.assertEqual(result,None)

    def test_get_requested_vnic_attribute_name(self):
        # arrange
        mock_connector: Connector = Mock()
        mock_app: ReservationAppResource = Mock()
        mock_app.Name = "app_name"
        mock_connector.Source =  "app_name"
        mock_connector_attribute = Mock()
        mock_connector_attribute.Name = 'Requested Source vNIC Name'
        mock_connector.Attributes = [mock_connector_attribute]

        # act
        result = self.sandbox_comp_helper.get_requested_vnic_attribute(mock_connector,mock_app)

        # assert
        self.assertEqual(result,mock_connector_attribute)

    def test_get_requested_vnic_attribute_name_none(self):
        # arrange
        mock_connector: Connector = Mock()
        mock_app: ReservationAppResource = Mock()
        mock_app.Name = "app_name"
        mock_connector.Source =  "app_name"
        mock_connector.Attributes = [Mock()]

        # act
        result = self.sandbox_comp_helper.get_requested_vnic_attribute(mock_connector,mock_app)

        # assert
        self.assertEqual(result,None)

    def test_get_apps_to_connectors_dict(self):
        # arrange
        mock_app: ReservationAppResource = Mock()
        mock_app.Name = "app_name"
        mock_apps:List[ReservationAppResource] = [mock_app]
        mock_connector: Connector = Mock()
        mock_connector.Source = "app_name"

        mock_sandbox_details:ReservationDescriptionInfo = Mock()
        mock_sandbox_details.Connectors = [mock_connector]

        mock_services_dict:Dict[str, ServiceInstance] = {mock_connector.Target: Mock()}

        # act
        result = self.sandbox_comp_helper.get_apps_to_connectors_dict(mock_apps,mock_sandbox_details,mock_services_dict)

        # assert
        self.assertEqual(result, {"app_name":[mock_connector]})

    def test_get_service_and_app_name_to_position_dict(self):
        # arrange
        mock_api: CloudShellAPISession = Mock()
        mock_sandbox_id = Mock()
        mock_service_position:ResourceDiagramLayoutInfo = Mock()
        mock_resource_name = Mock()
        mock_service_position.ResourceName = mock_resource_name
        mock_x = Mock()
        mock_y = Mock()
        mock_service_position.X = mock_x
        mock_service_position.Y = mock_y

        mock_reservation_services_positions:ReservationDiagramLayoutResponseInfo = Mock()
        mock_reservation_services_positions.ResourceDiagramLayouts = [mock_service_position]
        mock_api.GetReservationServicesPositions = Mock(return_value=mock_reservation_services_positions)

        # act
        result = self.sandbox_comp_helper.get_service_and_app_name_to_position_dict(mock_api,mock_sandbox_id)

        # assert
        self.assertEqual(result, {mock_resource_name: Position(mock_x,mock_y)})

    def test_does_connector_has_existing_vnic_req_no_value(self):
        # arrange
        mock_app: ReservationAppResource = Mock()
        mock_connector: Connector = Mock()
        mock_connectors = [mock_connector]
        mock_vnic_request_attribute:AttributeValueInfo = Mock()
        self.sandbox_comp_helper.get_requested_vnic_attribute = Mock(return_value=mock_vnic_request_attribute)

        # act
        result = self.sandbox_comp_helper.does_connector_has_existing_vnic_req(mock_app,mock_connectors)
        # assert
        self.assertTrue(result)

    def test_does_connector_has_existing_vnic_req_with_value(self):
        # arrange
        mock_app: ReservationAppResource = Mock()
        mock_connector: Connector = Mock()
        mock_connectors = [mock_connector]
        mock_vnic_request_attribute: AttributeValueInfo = Mock()
        mock_vnic_request_attribute.Value = None
        self.sandbox_comp_helper.get_requested_vnic_attribute = Mock(return_value=mock_vnic_request_attribute)

        # act
        result = self.sandbox_comp_helper.does_connector_has_existing_vnic_req(mock_app, mock_connectors)
        # assert
        self.assertFalse(result)