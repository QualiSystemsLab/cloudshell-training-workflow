from cloudshell.workflow.orchestration.sandbox import Sandbox
from cloudshell.workflow.training.setup_orchestrator import TrainingSetupWorkflow
import cloudshell.helpers.scripts.cloudshell_dev_helpers as dev_helpers

if dev_helpers.is_dev_mode():
    dev_helpers.attach_to_cloudshell_as('admin', 'admin', 'Global', 'a563eb82-a81f-4ec7-b328-4abb427e0992')

sandbox = Sandbox()

workflow = TrainingSetupWorkflow(sandbox)
workflow.register()
workflow.initialize()

sandbox.execute_setup()
