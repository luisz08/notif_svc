from .time_window_policy import TimeWindowPolicy
from .base_policy import BasePolicy
from ..repositories import Repositories
from typing import Optional


class DeduplicationManager:
    """Manager for deduplication policies."""

    def __init__(self, repos: Repositories):
        self.repos = repos
        self.policies = self._policies()

    def _policies(self):
        time_window = TimeWindowPolicy(self.repos)
        return {time_window.name: time_window}

    def handle(self, notification) -> bool:
        """Handle a notification by checking deduplication policies."""
        for key, policy in self.policies.items():
            if policy.should_send(notification):
                continue
            else:
                policy.record_duplication(notification)
                return False
        return True

    def get_policy(self, name: str) -> Optional[BasePolicy]:
        """Get a deduplication policy by name."""
        return self.policies.get(name)
