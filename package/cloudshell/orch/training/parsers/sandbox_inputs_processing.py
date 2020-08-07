
class SandboxInputsParser:
    @staticmethod
    def is_debug_on(sandbox):
        if sandbox.global_inputs['Diagnostics'] == 'On':
            return True
        return False

    @staticmethod
    def sandbox_user_list(sandbox):
        training_users_list = []
        if "Training Users" in sandbox.global_inputs:
            users_list = sandbox.global_inputs.get("Training Users", "").split(";")
            if len(training_users_list) > 1:
                training_users_list = users_list
        return training_users_list

    @staticmethod
    def is_instructor_mode(sandbox):
        #if "#" in user list than this would be student_mode meaning instructor_mode=False
        return not (SandboxInputsParser.sandbox_user_list(sandbox) and "#" in SandboxInputsParser.sandbox_user_list(sandbox)[0])