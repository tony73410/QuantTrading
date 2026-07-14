"""Generic ParameterSchema-driven editor widgets."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from PySide6.QtCore import QDate
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDateEdit,
    QDoubleSpinBox,
    QFormLayout,
    QLineEdit,
    QSpinBox,
    QWidget,
)

from ..models import ParameterSchema, ParameterType, ParameterValue


class ParameterEditor(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._layout = QFormLayout(self)
        self._widgets: dict[str, QWidget] = {}
        self._schemas: dict[str, ParameterSchema] = {}

    def set_schema(self, schemas: tuple[ParameterSchema, ...], values: dict[str, ParameterValue]) -> None:
        while self._layout.rowCount():
            self._layout.removeRow(0)
        self._widgets.clear()
        self._schemas = {schema.name: schema for schema in schemas}
        for schema in schemas:
            widget = self._make_widget(schema, values.get(schema.name, schema.default_value))
            widget.setToolTip(schema.description)
            self._widgets[schema.name] = widget
            label = schema.display_name + (f" ({schema.unit})" if schema.unit else "")
            self._layout.addRow(label, widget)

    def values(self) -> dict[str, ParameterValue]:
        return {
            name: self._read_widget(self._schemas[name], widget)
            for name, widget in self._widgets.items()
        }

    @staticmethod
    def _make_widget(schema: ParameterSchema, value: ParameterValue) -> QWidget:
        if schema.parameter_type is ParameterType.BOOLEAN:
            widget = QCheckBox()
            widget.setChecked(bool(value))
            return widget
        if schema.parameter_type is ParameterType.INTEGER:
            widget = QSpinBox()
            widget.setRange(int(schema.minimum or -2_147_483_648), int(schema.maximum or 2_147_483_647))
            widget.setSingleStep(int(schema.step or 1))
            widget.setValue(int(value or 0))
            return widget
        if schema.parameter_type in {ParameterType.FLOAT, ParameterType.PERCENTAGE, ParameterType.MONEY, ParameterType.DURATION}:
            widget = QDoubleSpinBox()
            widget.setDecimals(6)
            widget.setRange(float(schema.minimum if schema.minimum is not None else -1e12), float(schema.maximum if schema.maximum is not None else 1e12))
            widget.setSingleStep(float(schema.step or Decimal("0.01")))
            widget.setValue(float(value or 0))
            if schema.parameter_type is ParameterType.PERCENTAGE:
                widget.setSuffix(" %")
            elif schema.parameter_type is ParameterType.MONEY:
                widget.setPrefix("$ ")
            return widget
        if schema.parameter_type is ParameterType.ENUM:
            widget = QComboBox()
            widget.addItems(schema.allowed_values)
            if value in schema.allowed_values:
                widget.setCurrentText(str(value))
            return widget
        if schema.parameter_type is ParameterType.DATE:
            widget = QDateEdit()
            widget.setCalendarPopup(True)
            selected = value if isinstance(value, date) else date.today()
            widget.setDate(QDate(selected.year, selected.month, selected.day))
            return widget
        widget = QLineEdit()
        widget.setText(", ".join(value) if schema.parameter_type is ParameterType.LIST and isinstance(value, tuple) else str(value or ""))
        return widget

    @staticmethod
    def _read_widget(schema: ParameterSchema, widget: QWidget) -> ParameterValue:
        if isinstance(widget, QCheckBox):
            return widget.isChecked()
        if isinstance(widget, QSpinBox):
            return widget.value()
        if isinstance(widget, QDoubleSpinBox):
            return Decimal(str(widget.value()))
        if isinstance(widget, QComboBox):
            return widget.currentText()
        if isinstance(widget, QDateEdit):
            selected = widget.date()
            return date(selected.year(), selected.month(), selected.day())
        text = widget.text().strip() if isinstance(widget, QLineEdit) else ""
        if schema.parameter_type is ParameterType.LIST:
            return tuple(item.strip() for item in text.split(",") if item.strip())
        return text
