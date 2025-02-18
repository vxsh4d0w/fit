#!/usr/bin/env python3
# -*- coding:utf-8 -*-
######
# -----
# Copyright (c) 2023 FIT-Project
# SPDX-License-Identifier: GPL-3.0-only
# -----
######
import string

from PyQt6 import QtCore, QtGui, QtWidgets

from controller.case import Case as CaseController
from controller.configurations.tabs.general.typesproceedings import TypesProceedings as TypesProceedingsController

from common.constants.view.case import *

class CaseForm(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(CaseForm, self).__init__(parent)
        self.controller = CaseController()
        self.cases = self.controller.cases
        self.proceedings = TypesProceedingsController().proceedings

        self.setGeometry(QtCore.QRect(40, 30, 401, 202))
        self.setObjectName("form_layout")


        self.initUI()
        self.retranslateUi()
        self.set_current_cases()
        self.__set_current_config_values()
    

    def initUI(self):
        self.case_form_layout = QtWidgets.QFormLayout(self)
        self.case_form_layout.setSizeConstraint(QtWidgets.QLayout.SizeConstraint.SetDefaultConstraint)
        self.case_form_layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight | QtCore.Qt.AlignmentFlag.AlignTop | QtCore.Qt.AlignmentFlag.AlignTrailing)

        self.case_form_layout.setFormAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.case_form_layout.setContentsMargins(9, 13, 0, 13)
        self.case_form_layout.setVerticalSpacing(10)
        self.case_form_layout.setObjectName("case_form_layout")

        #CASE_NAME_COMBO
        self.name_label = QtWidgets.QLabel(self)
        font = QtGui.QFont()
        font.setPointSize(10)
        self.name_label.setFont(font)
        self.name_label.setObjectName("name_label")
        self.case_form_layout.setWidget(0, QtWidgets.QFormLayout.ItemRole.LabelRole, self.name_label)
        self.name = QtWidgets.QComboBox(self)
        self.name.editTextChanged.connect(self.__validate_input)

        font = QtGui.QFont()
        font.setPointSize(10)
        self.name.setFont(font)
        self.name.setObjectName("name")
        self.case_form_layout.setWidget(0, QtWidgets.QFormLayout.ItemRole.FieldRole, self.name)

        

        #LAWYER_NAME_LINE_EDIT
        self.lawyer_name_label = QtWidgets.QLabel(self)
        font = QtGui.QFont()
        font.setPointSize(10)
        self.lawyer_name_label.setFont(font)
        self.lawyer_name_label.setObjectName("lawyer_name_label")
        self.case_form_layout.setWidget(1, QtWidgets.QFormLayout.ItemRole.LabelRole, self.lawyer_name_label)
        self.lawyer_name = QtWidgets.QLineEdit(self)
        font = QtGui.QFont()
        font.setPointSize(10)
        self.lawyer_name.setFont(font)
        self.lawyer_name.setObjectName("lawyer_name")
        self.case_form_layout.setWidget(1, QtWidgets.QFormLayout.ItemRole.FieldRole, self.lawyer_name)


        #types_proceedings_COMBO
        self.types_proceedings_label = QtWidgets.QLabel(self)
        font = QtGui.QFont()
        font.setPointSize(10)
        self.types_proceedings_label.setFont(font)
        self.types_proceedings_label.setObjectName("proceeding_type_label")
        self.case_form_layout.setWidget(2, QtWidgets.QFormLayout.ItemRole.LabelRole, self.types_proceedings_label)
        self.types_proceedings = QtWidgets.QComboBox(self)
        font = QtGui.QFont()
        font.setPointSize(10)
        self.types_proceedings.setFont(font)
        self.types_proceedings.setObjectName("proceeding_type")        
        self.case_form_layout.setWidget(2, QtWidgets.QFormLayout.ItemRole.FieldRole, self.types_proceedings)


        #COURTHOUSE_LINE_EDIT
        self.courthouse_label = QtWidgets.QLabel(self)
        font = QtGui.QFont()
        font.setPointSize(10)
        self.courthouse_label.setFont(font)
        self.courthouse_label.setObjectName("courthouse_label")
        self.case_form_layout.setWidget(3, QtWidgets.QFormLayout.ItemRole.LabelRole, self.courthouse_label)
        self.courthouse = QtWidgets.QLineEdit(self)
        font = QtGui.QFont()
        font.setPointSize(10)
        self.courthouse.setFont(font)
        self.courthouse.setObjectName("courthouse")
        self.case_form_layout.setWidget(3, QtWidgets.QFormLayout.ItemRole.FieldRole, self.courthouse)


        #proceeding_number_LINE_EDIT
        self.proceeding_number_label = QtWidgets.QLabel(self)
        font = QtGui.QFont()
        font.setPointSize(10)
        self.proceeding_number_label.setFont(font)
        self.proceeding_number_label.setObjectName("proceeding_number_label")
        self.case_form_layout.setWidget(4, QtWidgets.QFormLayout.ItemRole.LabelRole, self.proceeding_number_label)
        self.proceeding_number = QtWidgets.QLineEdit(self)
        font = QtGui.QFont()
        font.setPointSize(10)
        self.proceeding_number.setFont(font)
        self.proceeding_number.setObjectName("proceeding_number")
        self.case_form_layout.setWidget(4, QtWidgets.QFormLayout.ItemRole.FieldRole, self.proceeding_number)

        self.retranslateUi()

    def __validate_input(self, text):
        valid_text = self.__remove_chars(text)
        self.name.setEditText(valid_text)

    def __remove_chars(self, text):
        valid_characters = string.ascii_letters + string.digits + "_-"
        valid_text = ''.join(c for c in text if c.lower() in valid_characters)
        return valid_text
    def retranslateUi(self):

        self.setWindowTitle(TITLE)
        self.name_label.setText(NAME)
        self.lawyer_name_label.setText(LAWYER)
        self.types_proceedings_label.setText(PROCEEDING_TYPE)
        self.courthouse_label.setText(COURTHOUSE)
        self.proceeding_number_label.setText(PROCEEDING_NUMBER)
    

    def set_index_from_type_proceedings_id(self, type_proceedings_id):
        self.types_proceedings.setCurrentIndex(self.types_proceedings.findData(type_proceedings_id))
    
    def set_index_from_case_id(self, case_id):
        self.name.setCurrentIndex(self.name.findData(case_id))
    

    def set_current_cases(self):
         self.name.clear()
         for case in self.cases:
            self.name.addItem(case['name'], case['id'])

    def __set_current_config_values(self):
        for proceedings in self.proceedings:
            self.types_proceedings.addItem(proceedings['name'], proceedings['id'])
    
    def set_case_information(self):
        case_info = next((item for item in self.cases if item["name"] == self.name.currentText()), None)
        if case_info is not None:
            for keyword, value in case_info.items():
                item = self.findChild(QtCore.QObject, keyword)
                if item is not None:
                    if isinstance(item, QtWidgets.QLineEdit) is not False:
                        if value is not None:
                            item.setText(str(value))
                    if isinstance(item, QtWidgets.QComboBox):
                        if keyword in 'proceeding_type': 
                            type_proceeding = next((proceeding for proceeding in self.proceedings if proceeding["id"] == value), None)
                            if type_proceeding is not None:
                                value = type_proceeding["id"]
                            else:
                                value = -1

                            self.set_index_from_type_proceedings_id(value)
    
    def clear_case_information(self):
        self.lawyer_name.setText("")
        self.types_proceedings.setCurrentIndex(-1)
        self.courthouse.setText("")
        self.proceeding_number.setText("")
    
    def get_current_case_info(self):
        case_info = next((item for item in self.cases if item["name"] == self.name.currentText()), {})
        for keyword in self.controller.keys:
            item = self.findChild(QtCore.QObject, keyword)
            if item is not None:
                if isinstance(item, QtWidgets.QComboBox):
                    item= item.currentText()
                    if keyword in 'proceeding_type':
                        type_proceeding = next((proceeding for proceeding in self.proceedings if proceeding["name"] == item), None)
                        if type_proceeding is not None:
                            item = type_proceeding["id"]
                        else:
                            item = 0
                    
                elif isinstance(item, QtWidgets.QLineEdit) is not False:
                    if item.text():
                        item = item.text()
                    else:
                        item = ''

                case_info[keyword] = item

        return case_info
