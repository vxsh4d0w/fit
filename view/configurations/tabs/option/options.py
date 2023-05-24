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

        self.whois_checkbox = QtWidgets.QCheckBox(parent=self.enable_network_tools_box)
        self.whois_checkbox.setGeometry(QtCore.QRect(20, 20, 251, 17))
        self.whois_checkbox.setObjectName("whois_checkbox")

        self.headers_checkbox = QtWidgets.QCheckBox(parent=self.enable_network_tools_box)
        self.headers_checkbox.setGeometry(QtCore.QRect(20, 60, 391, 17))
        self.headers_checkbox.setObjectName("headers_checkbox")

        self.traceroute_checkbox = QtWidgets.QCheckBox(parent=self.enable_network_tools_box)
        self.traceroute_checkbox.setGeometry(QtCore.QRect(20, 80, 91, 17))
        self.traceroute_checkbox.setChecked(True)
        self.traceroute_checkbox.setObjectName("traceroute_checkbox")

        self.SSLkeylog_checkbox = QtWidgets.QCheckBox(parent=self.enable_network_tools_box)
        self.SSLkeylog_checkbox.setGeometry(QtCore.QRect(20, 100, 111, 17))
        self.SSLkeylog_checkbox.setChecked(True)
        self.SSLkeylog_checkbox.setObjectName("SSLkeylog_checkbox")

        self.Nslookup_checkbox = QtWidgets.QCheckBox(parent=self.enable_network_tools_box)
        self.Nslookup_checkbox.setGeometry(QtCore.QRect(20, 40, 331, 17))
        self.Nslookup_checkbox.setObjectName("Nslookup_checkbox")

        self.SSLCertificate_checkbox = QtWidgets.QCheckBox(parent=self.enable_network_tools_box)
        self.SSLCertificate_checkbox.setGeometry(QtCore.QRect(20, 120, 121, 17))
        self.SSLCertificate_checkbox.setChecked(True)
        self.SSLCertificate_checkbox.setObjectName("SSLCertificate_checkbox")


        # PROCEEDINGS TYPE LIST
        self.group_box_network_check = NetworkView(self)

    def retranslateUi(self):
        _translate = QtCore.QCoreApplication.translate
        self.setWindowTitle(_translate("Options", "Options"))
        self.enable_network_tools_box.setTitle(_translate("Options", "Enable Network Check"))
        self.whois_checkbox.setText(_translate("Options", "Whois"))
        self.headers_checkbox.setText(_translate("Options", "Headers"))
        self.SSLkeylog_checkbox.setText(_translate("Options", "SSLkeylog"))
        self.Nslookup_checkbox.setText(_translate("Options", "Nslookup"))
        self.SSLCertificate_checkbox.setText(_translate("Options", "SSLCertificate"))
        self.traceroute_checkbox.setText(_translate("Form", "Traceroute"))




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