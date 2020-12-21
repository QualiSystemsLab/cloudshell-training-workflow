from cloudshell.workflow.orchestration.sandbox import Sandbox
from cloudshell.workflow.training.teardown_orchestrator import TrainingTeardownWorkflow
import cloudshell.helpers.scripts.cloudshell_dev_helpers as dev_helpers

if dev_helpers.is_dev_mode():
    dev_helpers.attach_to_cloudshell_as('admin', 'admin', 'Global', '45d80326-72e0-4100-8337-6de156b20dae')

sandbox = Sandbox()

TrainingTeardownWorkflow(sandbox).register()

sandbox.execute_teardown()
