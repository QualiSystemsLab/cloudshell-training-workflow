import logging
from typing import List

from cloudshell.api.cloudshell_api import CloudShellAPISession
from cloudshell.api.common_cloudshell_api import CloudShellAPIError

from cloudshell.workflow.training.utils.password import PasswordUtils


class UsersService:
    def __init__(self, api: CloudShellAPISession, logger: logging.Logger):
        self._api = api
        self._logger = logger

    def get_training_users_group_name(self, instructor_sandbox_id: str):
        return f'training-{instructor_sandbox_id}'

    def create_training_users_group(self, instructor_sandbox_id: str, domain: str):
        group_name = self.get_training_users_group_name(instructor_sandbox_id)
        self._logger.debug(f'Creating training users group {group_name} in domain {domain}')
        try:
            self._api.AddNewGroup(group_name, 'Group for training users', 'Regular')
            self._logger.debug(f'Created user group {group_name}')
        except CloudShellAPIError as exc:
            if exc.code == '135':
                self._logger.debug(f'User group {group_name} already exists')
            else:
                raise

        self._api.AddGroupsToDomain(domain, [group_name])

    def delete_training_users_group(self, instructor_sandbox_id: str):
        group_name = self.get_training_users_group_name(instructor_sandbox_id)
        self._logger.debug(f'deleting training users group {group_name}')
        self._api.DeleteGroup(group_name)

    def add_training_users_to_group(self, instructor_sandbox_id: str, users: List[str]):
        group_name = self.get_training_users_group_name(instructor_sandbox_id)
        self._logger.debug(f'adding users {users} to group {group_name}')
        self._api.AddUsersToGroup(users, group_name)

    def deactivate_training_user(self, user):
        self._logger.debug(f'deactivating user {user}')
        self._api.UpdateUser(user, user, isActive=False)

    def create_or_activate_training_user(self, user: str):
        self._logger.debug(f'Creating/Activating user {user}')
        try:
            system_user = self._api.GetUserDetails(user)
            self._logger.debug(f'user {user} exist')
            if not system_user.IsActive:
                self._logger.debug(f'user {user} not active, activating user')
                self._api.UpdateUser(user, user, isActive=True)

        except CloudShellAPIError as exc:
            if exc.code == '133':
                #
                self._logger.debug(f'user {user} doesnt exist, creating user')
                new_user_pass = PasswordUtils.generate_random_password()
                self._api.AddNewUser(user, new_user_pass, user, isActive=True)
            else:
                self._logger.exception('error updating training user')
                raise
