#!/usr/bin/env python3
# -*- coding:utf-8 -*-
######
# -----
# Copyright (c) 2023 FIT-Project
# SPDX-License-Identifier: GPL-3.0-only
# -----
######


from PyQt6 import QtCore, QtWidgets
from PyQt6.QtWidgets import QFileDialog

from view.configurations.tabs.general.typesproceedings import TypesProceedings as TypesproceedingsView
from view.configurations.tabs.general.network import Network as NetworkView
from controller.configurations.tabs.general.general import General as GeneralController

import os

__is_tab__ = True


class Options(QtWidgets.QWidget):

    def __init__(self, parent=None):

        super(Options, self).__init__(parent)

        self.controller = GeneralController()
        self.configuration = self.controller.configuration

        self.setObjectName("configuration_option")

        self.initUI()
        self.retranslateUi()
        self.__set_current_config_values()

    def initUI(self):
        #-----
        self.enable_network_tools_box = QtWidgets.QGroupBox(parent=self)
        self.enable_network_tools_box.setGeometry(QtCore.QRect(10, 20, 691, 171))
        self.enable_network_tools_box.setObjectName("enable_network_tools_box")

        self.whois = QtWidgets.QCheckBox(parent=self.enable_network_tools_box)
        self.whois.setGeometry(QtCore.QRect(20, 20, 251, 17))
        self.whois.setObjectName("whois")

        self.delete_project_folder_3 = QtWidgets.QCheckBox(parent=self.enable_network_tools_box)
        self.delete_project_folder_3.setGeometry(QtCore.QRect(20, 60, 391, 17))
        self.delete_project_folder_3.setObjectName("delete_project_folder_3")

        self.load_css_3 = QtWidgets.QCheckBox(parent=self.enable_network_tools_box)
        self.load_css_3.setGeometry(QtCore.QRect(20, 80, 91, 17))
        self.load_css_3.setChecked(True)
        self.load_css_3.setObjectName("load_css_3")
        self.load_images_3 = QtWidgets.QCheckBox(parent=self.enable_network_tools_box)
        self.load_images_3.setGeometry(QtCore.QRect(20, 100, 111, 17))
        self.load_images_3.setChecked(True)
        self.load_images_3.setObjectName("load_images_3")
        self.zip_project_folder_3 = QtWidgets.QCheckBox(parent=self.enable_network_tools_box)
        self.zip_project_folder_3.setGeometry(QtCore.QRect(20, 40, 331, 17))
        self.zip_project_folder_3.setObjectName("zip_project_folder_3")
        self.load_javascript_3 = QtWidgets.QCheckBox(parent=self.enable_network_tools_box)
        self.load_javascript_3.setGeometry(QtCore.QRect(20, 120, 121, 17))
        self.load_javascript_3.setChecked(True)
        self.load_javascript_3.setObjectName("load_javascript_3")


        # PROCEEDINGS TYPE LIST
        self.group_box_network_check = NetworkView(self)

    def retranslateUi(self):
        _translate = QtCore.QCoreApplication.translate
        self.setWindowTitle(_translate("Options", "Options"))
        self.enable_network_tools_box.setTitle(_translate("Options", "Enable Network Check"))
        self.whois.setText(_translate("Options", "Whois"))


    def __select_cases_folder(self):
        cases_folder = QtWidgets.QFileDialog.getExistingDirectory(self,
                                                                  'Select Cases Folder',
                                                                  os.path.expanduser(self.cases_folder.text()),
                                                                  QFileDialog.Option.ShowDirsOnly)
        self.cases_folder.setText(cases_folder)

    def __set_current_config_values(self):
        pass
    def __get_current_values(self):

        for keyword in self.configuration:
            item = self.findChild(QtCore.QObject, keyword)

            if item is not None:
                if isinstance(item, QtWidgets.QComboBox) is not False and item.currentText():
                    item = item.currentText()
                elif isinstance(item, QtWidgets.QLineEdit) is not False and item.text():
                    item = item.text()
                elif isinstance(item, QtWidgets.QPlainTextEdit) is not False and item.toPlainText():
                    item = item.toPlainText()

                self.configuration[keyword] = item

    def accept(self) -> None:
        self.group_box_types_proceedings.accept()
        self.group_box_network_check.accept()
        self.__get_current_values()
        self.controller.configuration = self.configuration

    def reject(self) -> None:
        pass