import logging
from typing import List

from cloudshell.api.cloudshell_api import CloudShellAPISession
from cloudshell.api.common_cloudshell_api import CloudShellAPIError

from cloudshell.workflow.training.utils.password import PasswordUtils


class UsersService:
    def __init__(self, api: CloudShellAPISession, logger: logging.Logger):
        self._api = api
        self._logger = logger

    def create_training_users_group(self, instructor_sandbox_id: str, domain: str):
        self._logger.debug(f'Creating training users group {instructor_sandbox_id} in domain {domain}')
        self._api.AddNewGroup(instructor_sandbox_id, 'Group for training users', 'Regular')
        self._api.AddGroupsToDomain(domain, [instructor_sandbox_id])

    def delete_training_users_group(self, instructor_sandbox_id: str):
        self._logger.debug(f'deleting training users group {instructor_sandbox_id}')
        self._api.DeleteGroup(instructor_sandbox_id)

    def add_training_users_to_group(self, instructor_sandbox_id: str, users: List[str]):
        self._logger.debug(f'adding users {users} to group {instructor_sandbox_id}')
        self._api.AddUsersToGroup(users, instructor_sandbox_id)

    def deactivate_training_user(self, user):
        self._logger.debug(f'deactivating user {user}')
        self._api.UpdateUser(user, user, isActive=False)

    def create_or_activate_training_user(self, user: str):
        self._logger.debug(f'create or activate user {user}')
        try:
            system_user = self._api.GetUserDetails(user)
            self._logger.debug(f'user {user} exist')
            if not system_user.IsActive:
                self._logger.debug(f'user {user} not active, activating user')
                self._api.UpdateUser(user, user, isActive=True)

        except CloudShellAPIError as exc:
            if exc.code == 133:
                #
                self._logger.debug(f'user {user} doesnt exist, creating user')
                new_user_pass = PasswordUtils.generate_random_password()
                self._api.AddNewUser(user, new_user_pass, user, isActive=True)
            else:
                self._logger.exception('error updating training user')
                raise
