# -*- coding: utf-8 -*-
"""Main QGIS plugin UI for Metadados para ArcGIS."""

import os
import traceback

from qgis.PyQt.QtCore import QSettings, QUrl
from qgis.PyQt.QtGui import QDesktopServices, QIcon
from qgis.PyQt.QtWidgets import QAction, QFileDialog, QMessageBox
from qgis.core import Qgis, QgsMessageLog, QgsProject

from .about_dialog import AboutDialog
from .arcgis_writer import write_arcgis_xml
from .iso19139_reader import read_iso19139
from .qgis_reader import read_qgis_layer
from .scale_dialog import REFERENCE_SCALE_PROPERTY, ScaleChoiceDialog
from .scale_utils import format_scale

PLUGIN_NAME = "Metadados para ArcGIS"
MENU_NAME = "&Metadados para ArcGIS"
LOG_TAG = "MetadadosParaArcGIS"


class MetadataArcGISPlugin:
    def __init__(self, iface):
        self.iface = iface
        self.plugin_dir = os.path.dirname(__file__)
        self.actions = []
        self.toolbar_action = None

    def initGui(self):
        icon_path = os.path.join(self.plugin_dir, "icon.png")
        icon = QIcon(icon_path)

        export_action = QAction(
            icon,
            "Exportar metadados da camada para ArcGIS XML...",
            self.iface.mainWindow(),
        )
        export_action.setToolTip(
            "Metadados para ArcGIS — exportar a camada ativa para XML"
        )
        export_action.triggered.connect(self.export_active_layer)
        self.iface.addPluginToMenu(MENU_NAME, export_action)
        self.iface.addToolBarIcon(export_action)
        self.actions.append(export_action)
        self.toolbar_action = export_action

        iso_action = QAction(
            icon,
            "Converter XML ISO 19139 / MGB para ArcGIS XML...",
            self.iface.mainWindow(),
        )
        iso_action.triggered.connect(self.convert_iso_file)
        self.iface.addPluginToMenu(MENU_NAME, iso_action)
        self.actions.append(iso_action)

        about_action = QAction(
            icon,
            "Sobre o Metadados para ArcGIS",
            self.iface.mainWindow(),
        )
        about_action.triggered.connect(self.show_about)
        self.iface.addPluginToMenu(MENU_NAME, about_action)
        self.actions.append(about_action)

    def unload(self):
        for action in self.actions:
            self.iface.removePluginMenu(MENU_NAME, action)
            if action is self.toolbar_action:
                self.iface.removeToolBarIcon(action)
        self.actions = []
        self.toolbar_action = None

    def _last_folder(self):
        # Keep the old settings namespace for compatibility with v1.0/v1.1.
        return QSettings().value("qgis_metadata_arcgis/last_folder", "", type=str)

    def _remember_folder(self, path):
        folder = os.path.dirname(os.path.abspath(path))
        QSettings().setValue("qgis_metadata_arcgis/last_folder", folder)

    def _save_dialog(self, suggested_name):
        start = (
            os.path.join(self._last_folder(), suggested_name)
            if self._last_folder()
            else suggested_name
        )
        path, _ = QFileDialog.getSaveFileName(
            self.iface.mainWindow(),
            "Metadados para ArcGIS — Salvar XML",
            start,
            "Arquivo XML (*.xml)",
        )
        if path and not path.lower().endswith(".xml"):
            path += ".xml"
        return path

    def export_active_layer(self):
        layer = self.iface.activeLayer()
        if layer is None:
            QMessageBox.warning(
                self.iface.mainWindow(),
                PLUGIN_NAME,
                "Selecione uma camada no painel Camadas antes de exportar.",
            )
            return

        try:
            current_scale = float(self.iface.mapCanvas().scale())
        except Exception:
            current_scale = None

        scale_dialog = ScaleChoiceDialog(
            layer,
            current_canvas_scale=current_scale,
            parent=self.iface.mainWindow(),
        )
        scale_dialog.setWindowIcon(QIcon(os.path.join(self.plugin_dir, "icon.png")))
        if not scale_dialog.exec_():
            return

        reference_scale = scale_dialog.scale_value()
        save_scale_for_layer = scale_dialog.should_save_scale()

        suggested = self._safe_filename(layer.name()) + "_ArcGIS.xml"
        output_path = self._save_dialog(suggested)
        if not output_path:
            return

        try:
            record = read_qgis_layer(layer)

            # v1.2.1 restores the successful v1.1 behavior:
            # one user-confirmed scale is used as:
            # - equivalent/reference scale (rfDenom);
            # - maximum scale of the ArcGIS appropriate scale range;
            # - minimum scale of the ArcGIS appropriate scale range.
            record.scale = reference_scale
            record.scale_maximum = reference_scale
            record.scale_minimum = reference_scale
            write_arcgis_xml(record, output_path)

            if save_scale_for_layer:
                layer.setCustomProperty(REFERENCE_SCALE_PROPERTY, reference_scale)
                QgsProject.instance().setDirty(True)

            self._remember_folder(output_path)

            if reference_scale:
                scale_message = (
                    f" Escala de referência e faixa ArcGIS: {format_scale(reference_scale)}."
                )
            else:
                scale_message = " Exportado sem informação de escala."

            self.iface.messageBar().pushMessage(
                PLUGIN_NAME,
                "XML ArcGIS exportado com sucesso." + scale_message,
                level=Qgis.Success,
                duration=9,
            )
            self._show_success(output_path)
        except Exception as exc:
            self._show_error(exc)

    def convert_iso_file(self):
        input_path, _ = QFileDialog.getOpenFileName(
            self.iface.mainWindow(),
            "Metadados para ArcGIS — Selecionar XML ISO 19139",
            self._last_folder(),
            "Arquivo XML (*.xml)",
        )
        if not input_path:
            return

        base = os.path.splitext(os.path.basename(input_path))[0]
        output_path = self._save_dialog(base + "_ArcGIS.xml")
        if not output_path:
            return

        try:
            record = read_iso19139(input_path)
            write_arcgis_xml(record, output_path)
            self._remember_folder(output_path)
            self.iface.messageBar().pushMessage(
                PLUGIN_NAME,
                "XML ISO 19139 convertido com sucesso.",
                level=Qgis.Success,
                duration=7,
            )
            self._show_success(output_path)
        except Exception as exc:
            self._show_error(exc)

    def _show_success(self, output_path):
        box = QMessageBox(self.iface.mainWindow())
        box.setIcon(QMessageBox.Information)
        box.setWindowIcon(QIcon(os.path.join(self.plugin_dir, "icon.png")))
        box.setWindowTitle(PLUGIN_NAME)
        box.setText("Arquivo XML criado com sucesso.")
        box.setInformativeText(output_path)
        open_button = box.addButton("Abrir pasta", QMessageBox.ActionRole)
        box.addButton(QMessageBox.Ok)
        box.exec_()
        if box.clickedButton() is open_button:
            QDesktopServices.openUrl(QUrl.fromLocalFile(os.path.dirname(output_path)))

    def _show_error(self, exc):
        details = traceback.format_exc()
        QgsMessageLog.logMessage(details, LOG_TAG, Qgis.Critical)
        box = QMessageBox(self.iface.mainWindow())
        box.setIcon(QMessageBox.Critical)
        box.setWindowIcon(QIcon(os.path.join(self.plugin_dir, "icon.png")))
        box.setWindowTitle(PLUGIN_NAME)
        box.setText("Não foi possível gerar o XML.")
        box.setInformativeText(str(exc))
        box.setDetailedText(details)
        box.exec_()

    def show_about(self):
        dialog = AboutDialog(self.iface.mainWindow())
        dialog.setWindowIcon(QIcon(os.path.join(self.plugin_dir, "icon.png")))
        dialog.exec_()

    @staticmethod
    def _safe_filename(name):
        invalid = '<>:"/\\|?*'
        result = str(name)
        for char in invalid:
            result = result.replace(char, "_")
        return result.strip() or "metadados"
