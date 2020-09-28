from cloudshell.workflow.orchestration.sandbox import Sandbox
from cloudshell.orch.training.setup_orchestrator import TrainingSetupWorkflow
import cloudshell.helpers.scripts.cloudshell_dev_helpers as dev_helpers

if dev_helpers.is_dev_mode():
    dev_helpers.attach_to_cloudshell_as('admin', 'admin', 'Global', '45d80326-72e0-4100-8337-6de156b20dae')

sandbox = Sandbox()

workflow = TrainingSetupWorkflow(sandbox)
workflow.register()
workflow.initialize()

sandbox.execute_setup()
