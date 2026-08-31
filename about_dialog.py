# -*- coding: utf-8 -*-
"""About dialog for Metadados para ArcGIS."""

from qgis.PyQt.QtWidgets import QDialog, QDialogButtonBox, QLabel, QVBoxLayout


class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Sobre — Metadados para ArcGIS")
        self.setMinimumWidth(610)

        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        title = QLabel(
            "<h2 style='margin:0'>Metadados para ArcGIS</h2>"
            "<p style='margin:4px 0 0 0'><b>Versão 1.2.2</b></p>"
        )
        layout.addWidget(title)

        body = QLabel(
            "<p>Complemento para exportar metadados de camadas do QGIS para XML "
            "compatível com ArcGIS e converter arquivos ISO 19139/MGB.</p>"
            "<p><b>Autores</b><br>"
            "Jorge Jisra<br>"
            "Andresa Dornelas de Castro</p>"
            "<p><b>Desenvolvimento institucional</b><br>"
            "Trabalho desenvolvido no âmbito do <b>Ministério da Integração e do "
            "Desenvolvimento Regional (MIDR)</b>, no <b>Departamento de Obras Hídricas</b> "
            "da <b>Secretaria Nacional de Segurança Hídrica (SNSH)</b>.</p>"
            "<p><b>Compatibilidade alvo:</b> QGIS 3.44.x<br>"
            "<b>Licença:</b> GPL-2.0-or-later</p>"
            "<p>Versão estável validada no QGIS 3.44.13 e no ArcGIS Pro.</p>"
        )
        body.setWordWrap(True)
        layout.addWidget(body)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.reject)
        buttons.clicked.connect(self.accept)
        layout.addWidget(buttons)
