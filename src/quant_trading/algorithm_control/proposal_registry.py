"""In-memory index of reviewed proposal records; files remain canonical history."""

from __future__ import annotations

from .admission_models import ChangeProposal, ProposalStatus
from .errors import AlgorithmControlError


_RESOLVED = {
    ProposalStatus.APPROVED,
    ProposalStatus.REJECTED,
    ProposalStatus.IMPLEMENTED_DISABLED,
    ProposalStatus.DRY_RUN,
    ProposalStatus.PAPER_ENABLED,
    ProposalStatus.ACTIVE,
    ProposalStatus.DEPRECATED,
    ProposalStatus.ROLLED_BACK,
}


class ChangeProposalRegistry:
    """Expose proposal status without treating a proposal as activation authority."""

    def __init__(self, proposals: tuple[ChangeProposal, ...] = ()) -> None:
        self._items: dict[str, ChangeProposal] = {}
        for proposal in proposals:
            self.register(proposal)

    def register(self, proposal: ChangeProposal) -> None:
        if proposal.proposal_id in self._items:
            raise AlgorithmControlError(f"duplicate proposal ID: {proposal.proposal_id}")
        self._items[proposal.proposal_id] = proposal

    def list(self) -> tuple[ChangeProposal, ...]:
        return tuple(self._items[key] for key in sorted(self._items))

    def unresolved_ids(self) -> tuple[str, ...]:
        return tuple(
            proposal.proposal_id
            for proposal in self.list()
            if proposal.status not in _RESOLVED
        )
