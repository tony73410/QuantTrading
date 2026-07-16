"""Metadata-driven registration for controllable algorithm components."""

from __future__ import annotations

from collections.abc import Iterable

from .errors import ComponentRegistrationError
from .models import ComponentMetadata, ComponentStatus, ComponentType
from .admission_service import ChangeAdmissionService
from .contracts import DataContractRegistry, default_contract_registry


class AlgorithmComponentRegistry:
    """Expose component metadata without algorithm-specific GUI branches."""

    def __init__(
        self,
        components: Iterable[ComponentMetadata] = (),
        contract_registry: DataContractRegistry | None = None,
    ) -> None:
        self._components: dict[str, ComponentMetadata] = {}
        self.contract_registry = contract_registry or default_contract_registry()
        self.admission = ChangeAdmissionService(self.contract_registry)
        for component in components:
            self.register(component)

    def register(self, component: ComponentMetadata) -> None:
        if component.component_id in self._components:
            raise ComponentRegistrationError(
                f"component already registered: {component.component_id}"
            )
        conflicts = self.admission.assess_component(component)
        if conflicts:
            summary = "; ".join(item.description for item in conflicts)
            raise ComponentRegistrationError(f"component admission failed: {summary}")
        self._components[component.component_id] = component

    def replace(self, component: ComponentMetadata) -> None:
        """Replace existing metadata after applying normal admission checks."""

        if component.component_id not in self._components:
            raise ComponentRegistrationError(
                f"component is not registered: {component.component_id}"
            )
        conflicts = self.admission.assess_component(component)
        if conflicts:
            summary = "; ".join(item.description for item in conflicts)
            raise ComponentRegistrationError(f"component admission failed: {summary}")
        self._components[component.component_id] = component

    def registration_status(self, component: ComponentMetadata) -> ComponentStatus:
        """Return INVALID for rejected metadata without making it runnable."""

        return ComponentStatus.INVALID if self.admission.assess_component(component) else component.status

    def get(self, component_id: str) -> ComponentMetadata:
        try:
            return self._components[component_id]
        except KeyError as exc:
            raise ComponentRegistrationError(
                f"component is not registered: {component_id}"
            ) from exc

    def list(self, component_type: ComponentType | None = None) -> tuple[ComponentMetadata, ...]:
        components = self._components.values()
        if component_type is not None:
            components = (
                item for item in components if item.component_type is component_type
            )
        return tuple(sorted(components, key=lambda item: (item.component_type, -item.priority, item.display_name)))

    @property
    def component_ids(self) -> tuple[str, ...]:
        return tuple(sorted(self._components))
