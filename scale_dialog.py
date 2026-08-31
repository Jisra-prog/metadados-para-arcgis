# -*- coding: utf-8 -*-
"""Dialog for choosing a reference scale before exporting QGIS metadata."""

import re

from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QVBoxLayout,
)


REFERENCE_SCALE_PROPERTY = "qgis_metadata_arcgis/reference_scale"


def parse_scale_denominator(value):
    """Parse common Brazilian/user scale inputs into a positive integer denominator.

    Accepted examples: 50000, 1:50000, 50.000, 1:50.000, 50000,00.
    Returns an int or None.
    """
    text = str(value or "").strip().lower()
    if not text:
        return None

    text = text.replace("escala", "").strip()
    if ":" in text:
        text = text.split(":", 1)[1]
    text = text.replace(" ", "")

    # Brazilian decimal notation, e.g. 50.000,00 or 50000,00.
    if "," in text:
        integer_part = text.split(",", 1)[0].replace(".", "")
        digits = re.sub(r"\D", "", integer_part)
    # Thousands notation, e.g. 50.000 or 1.000.000.
    elif re.fullmatch(r"\d{1,3}(?:\.\d{3})+", text):
        digits = text.replace(".", "")
    else:
        # Allow a plain integer and tolerate accidental non-digit separators.
        digits = re.sub(r"\D", "", text)

    if not digits:
        return None
    try:
        value_int = int(digits)
    except ValueError:
        return None
    return value_int if value_int > 0 else None


def format_scale(value):
    try:
        value = int(round(float(value)))
    except Exception:
        return "não disponível"
    if value <= 0:
        return "não disponível"
    return "1:" + f"{value:,}".replace(",", ".")


class ScaleChoiceDialog(QDialog):
    """Ask the user to explicitly decide how reference scale should be handled."""

    def __init__(self, layer, current_canvas_scale=None, parent=None):
        super().__init__(parent)
        self.layer = layer
        self.current_canvas_scale = self._valid_canvas_scale(current_canvas_scale)
        self._scale = ""
        self._stored_scale = self._read_stored_scale()

        self.setWindowTitle("Metadados para ArcGIS — Escala de referência")
        self.setMinimumWidth(560)

        layout = QVBoxLayout(self)

        intro = QLabel(
            "O QGIS 3.44 não possui um campo nativo de metadados equivalente à "
            "escala representativa do ISO/ArcGIS. Para evitar preencher uma escala "
            "incorreta, confirme uma escala de referência ou escolha exportar sem escala."
        )
        intro.setWordWrap(True)
        layout.addWidget(intro)

        group = QGroupBox("Escala de referência dos dados (1:n)")
        group_layout = QVBoxLayout(group)

        self.manual_radio = QRadioButton("Informar / confirmar a escala de referência")
        self.manual_radio.setChecked(True)
        group_layout.addWidget(self.manual_radio)

        form = QFormLayout()
        self.scale_edit = QLineEdit()
        self.scale_edit.setPlaceholderText("Ex.: 50000 ou 1:50.000")
        form.addRow("Denominador:", self.scale_edit)
        group_layout.addLayout(form)

        current_text = format_scale(self.current_canvas_scale)
        current_row = QHBoxLayout()
        self.use_current_button = QPushButton(f"Usar escala atual do mapa ({current_text})")
        self.use_current_button.setEnabled(self.current_canvas_scale is not None)
        self.use_current_button.clicked.connect(self._use_current_canvas_scale)
        current_row.addWidget(self.use_current_button)
        current_row.addStretch(1)
        group_layout.addLayout(current_row)

        current_note = QLabel(
            "A escala atual do mapa é apenas uma sugestão baseada na visualização atual do QGIS. "
            "Use-a somente se ela representar adequadamente a escala de referência dos dados."
        )
        current_note.setWordWrap(True)
        current_note.setStyleSheet("color: gray;")
        group_layout.addWidget(current_note)

        self.no_scale_radio = QRadioButton("Não informar escala e continuar a exportação")
        group_layout.addWidget(self.no_scale_radio)

        layout.addWidget(group)

        self.save_checkbox = QCheckBox("Salvar esta escala para esta camada dentro do projeto QGIS")
        self.save_checkbox.setToolTip(
            "O valor é salvo como propriedade personalizada da camada no projeto QGIS. "
            "Salve o projeto para mantê-lo nas próximas sessões."
        )
        layout.addWidget(self.save_checkbox)

        self.status_label = QLabel("")
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)

        if self._stored_scale:
            self.scale_edit.setText(str(self._stored_scale))
            self.save_checkbox.setChecked(True)
            self.status_label.setText(
                f"Escala salva anteriormente para esta camada: {format_scale(self._stored_scale)}."
            )
        else:
            self.status_label.setText(
                "Nenhuma escala de referência foi salva para esta camada. Informe uma escala, "
                "use a escala atual do mapa como sugestão ou exporte sem escala."
            )

        self.no_scale_radio.toggled.connect(self._update_enabled_state)
        self.manual_radio.toggled.connect(self._update_enabled_state)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel | QDialogButtonBox.StandardButton.Ok)
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText("Continuar exportação")
        buttons.accepted.connect(self._validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self._update_enabled_state()

    @staticmethod
    def _valid_canvas_scale(value):
        try:
            value = float(value)
            if value > 0:
                return value
        except (TypeError, ValueError):
            return None
        return None

    def _read_stored_scale(self):
        try:
            value = self.layer.customProperty(REFERENCE_SCALE_PROPERTY, "")
        except Exception:
            return None
        return parse_scale_denominator(value)

    def _use_current_canvas_scale(self):
        if self.current_canvas_scale is None:
            return
        denominator = int(round(self.current_canvas_scale))
        self.manual_radio.setChecked(True)
        self.scale_edit.setText(str(denominator))
        self.scale_edit.setFocus(Qt.FocusReason.OtherFocusReason)
        self.scale_edit.selectAll()
        self.status_label.setText(
            f"Escala atual do mapa copiada como sugestão: {format_scale(denominator)}. "
            "Confirme ou altere antes de continuar."
        )

    def _update_enabled_state(self):
        enabled = self.manual_radio.isChecked()
        self.scale_edit.setEnabled(enabled)
        self.use_current_button.setEnabled(enabled and self.current_canvas_scale is not None)
        self.save_checkbox.setEnabled(enabled)

    def _validate_and_accept(self):
        if self.no_scale_radio.isChecked():
            self._scale = ""
            self.accept()
            return

        denominator = parse_scale_denominator(self.scale_edit.text())
        if denominator is None:
            QMessageBox.warning(
                self,
                "Metadados para ArcGIS",
                "Informe uma escala válida, por exemplo 50000 ou 1:50.000, "
                "ou selecione ‘Não informar escala e continuar a exportação’.",
            )
            self.scale_edit.setFocus(Qt.FocusReason.OtherFocusReason)
            return

        self._scale = str(denominator)
        self.accept()

    def scale_value(self):
        return self._scale

    def should_save_scale(self):
        return bool(self._scale) and self.save_checkbox.isChecked()
