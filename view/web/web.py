#!/usr/bin/env python3
# -*- coding:utf-8 -*-
######
# -----
# Copyright (c) 2023 FIT-Project
# SPDX-License-Identifier: GPL-3.0-only
# -----
######

import logging
import os.path
import shutil
from urllib.parse import urlparse

import numpy as np
from PIL import Image

from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtWebEngineCore import QWebEnginePage, QWebEngineProfile
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineDownloadRequest
from PyQt6.QtWidgets import QFileDialog

from view.web.navigationtoolbar import NavigationToolBar as NavigationToolBarView
from view.web.screenshot_select_area import SelectArea as SelectAreaView
from view.acquisition.acquisition import Acquisition
from view.acquisition.tasks.task import AcquisitionTask

from view.case import Case as CaseView
from view.configuration import Configuration as ConfigurationView
from view.error import Error as ErrorView

from common.constants import tasks as Tasks, logger as Logger, state, status as Status, error, details as Details
from common.constants.view import general

from common.settings import DEBUG
from common.config import LogConfigTools
from common.utility import screenshot_filename

logger = logging.getLogger(__name__)


class WebEnginePage(QWebEnginePage):
    new_page_after_link_with_target_blank_attribute = QtCore.pyqtSignal(QWebEnginePage)

    def __init__(self, parent=None):
        super().__init__(parent)

    # When you click a link that has the target="_blank" attribute, QT calls the CreateWindow method in
    # QWebEnginePage to create a new tab/new window.
    def createWindow(self, _type, ):
        page = WebEnginePage(self)
        self.new_page_after_link_with_target_blank_attribute.emit(page)
        return page


class Browser(QWebEngineView):
    saveResourcesFinished = QtCore.pyqtSignal()
    downloadItemFinished = QtCore.pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

    def reconnect(self):
        self.selected_directory = os.path.expanduser('~/Downloads')

        self.page().profile().setDownloadPath(self.selected_directory)
        self.page().profile().downloadRequested.connect(self.__retrieve_download_item)
        self.page().profile().downloadRequested.connect(self.__handle_download_request)

    def set_acquisition_dir(self, directory):
        self.acquisition_directory = directory
        self.selected_directory = os.path.join(self.acquisition_directory, "downloads")
        if not os.path.isdir(self.selected_directory):
            os.makedirs(self.selected_directory)
        self.page().profile().setDownloadPath(self.selected_directory)

    def save_resources(self, acquisition_page_folder):

        self.page().profile().downloadRequested.disconnect(self.__handle_download_request)
        hostname = urlparse(self.url().toString()).hostname
        self.page().save(os.path.join(acquisition_page_folder, hostname + '.html'),
                         format=QWebEngineDownloadRequest.SavePageFormat.CompleteHtmlSaveFormat)

    def reconnect_signal(self):
        self.page().profile().downloadRequested.connect(self.__handle_download_request)

    def disconnect_signals(self):
        self.page().profile().downloadRequested.disconnect(self.__retrieve_download_item)
        self.page().profile().downloadRequested.disconnect(self.__handle_download_request)

    def __handle_download_request(self, download):
        if not os.path.isdir(self.selected_directory):
            self.selected_directory = os.path.expanduser('~/Downloads')
        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.FileMode.Directory)
        file_dialog.setDirectory(self.selected_directory)
        filename = download.downloadFileName()
        download.isFinishedChanged.connect(lambda: self.downloadItemFinished.emit(filename))
        if file_dialog.exec() == QFileDialog.DialogCode.Accepted:
            self.selected_directory = file_dialog.selectedFiles()[0]
            download.accept()

    def __retrieve_download_item(self, download_item):
        download_item.isFinishedChanged.connect(self.saveResourcesFinished.emit)

    def closeEvent(self, event):
        self.page().profile().clearHttpCache()


class Web(QtWidgets.QMainWindow):

    def __init__(self, *args, **kwargs):
        super(Web, self).__init__(*args, **kwargs)
        self.acquisition_directory = None
        self.acquisition_page_folder = None
        self.screenshot_directory = None
        self.current_page_load_is_finished = False
        self.log_confing = LogConfigTools()
        self.log_confing.set_web_loggers()
        self.case_info = None
        self.__tasks = []
        self.browser = None

        self.setWindowFlag(QtCore.Qt.WindowType.WindowMinMaxButtonsHint, True)
        self.setObjectName('FITWeb')

    def init(self, case_info, wizard, options=None):

        self.__init__()
        self.wizard = wizard
        self.case_info = case_info
        self.configuration_view = ConfigurationView(self)
        self.configuration_view.hide()

        self.case_view = CaseView(self.case_info, self)
        self.case_view.hide()

        self.tabs = QtWidgets.QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.tabBarDoubleClicked.connect(self.tab_open_doubleclick)
        self.tabs.currentChanged.connect(self.current_tab_changed)
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_current_tab)

        self.setCentralWidget(self.tabs)

        self.status = QtWidgets.QStatusBar()
        self.progress_bar = QtWidgets.QProgressBar()
        self.progress_bar.setMaximumWidth(400)
        self.progress_bar.setFixedHeight(25)
        self.status.addPermanentWidget(self.progress_bar)

        self.progress_bar.setTextVisible(True)
        self.progress_bar.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.setStatusBar(self.status)
        self.progress_bar.setHidden(True)

        # ACQUISITION
        self.acquisition = Acquisition(logger, self.progress_bar, self.status, self)
        self.acquisition.completed.connect(self.__are_external_tasks_completed)

        self.acquisition_is_running = False
        self.start_acquisition_is_finished = False
        self.start_acquisition_is_started = False
        self.stop_acquisition_is_started = False

        self.__clear_cache()
        self.navtb = NavigationToolBarView(self)
        self.addToolBar(self.navtb)

        # Uncomment to disable native menubar on Mac
        self.menuBar().setNativeMenuBar(False)

        tab_menu = self.menuBar().addMenu("&Tab")
        new_tab_action = QtGui.QAction(QtGui.QIcon(os.path.join('assets/images', 'ui-tab--plus.png')), "New Tab",
                                       self)
        new_tab_action.setStatusTip("Open a new tab")
        new_tab_action.triggered.connect(lambda _: self.add_new_tab())
        tab_menu.addAction(new_tab_action)

        # CONFIGURATION ACTION
        configuration_action = QtGui.QAction("Configuration", self)
        configuration_action.setStatusTip("Show configuration info")
        configuration_action.triggered.connect(self.configuration)
        self.menuBar().addAction(configuration_action)

        # CASE ACTION
        case_action = QtGui.QAction("Case", self)
        case_action.setStatusTip("Show case info")
        case_action.triggered.connect(self.case)
        self.menuBar().addAction(case_action)

        self.configuration_general = self.configuration_view.get_tab_from_name("configuration_general")

        # Get network parameters for check (NTP, nslookup)
        self.configuration_network = self.configuration_general.findChild(QtWidgets.QGroupBox,
                                                                          'group_box_network_check')

        # Get timestamp parameters
        self.configuration_timestamp = self.configuration_view.get_tab_from_name("configuration_timestamp")
        self.add_new_tab(QtCore.QUrl(self.configuration_general.configuration['home_page_url']), 'Homepage')

        self.show()

        self.setWindowTitle("Freezing Internet Tool")
        self.setWindowIcon(QtGui.QIcon(os.path.join('assets/svg/', 'FIT.svg')))

        # Enable/Disable other modules logger
        if not DEBUG:
            loggers = [logging.getLogger()]  # get the root logger
            loggers = loggers + [logging.getLogger(name) for name in logging.root.manager.loggerDict if
                                 name not in [__name__, 'hashreport']]

            self.log_confing.disable_loggers(loggers)

    def start_acquisition(self):

        profile = QWebEngineProfile.defaultProfile()
        profile.clearHttpCache()

        self.acquisition_directory = self.case_view.form.controller.create_acquisition_directory(
            'web',
            self.configuration_general.configuration['cases_folder_path'],
            self.case_info['name'],
            self.tabs.currentWidget().url().toString()
        )

        if self.acquisition_directory is not None:
            self.tabs.currentWidget().set_acquisition_dir(self.acquisition_directory)
            self.start_acquisition_is_started = True

            self.screenshot_directory = os.path.join(self.acquisition_directory, "screenshot")
            if not os.path.isdir(self.screenshot_directory):
                os.makedirs(self.screenshot_directory)

            # show progress bar
            self.progress_bar.setHidden(False)

            self.acquisition_is_running = True

            self.acquisition.post_acquisition.finished.connect(self.__are_post_acquisition_finished)

            # disable start acquisition button
            self.navtb.enable_start_acquisition_button()
            # enable screenshot buttons
            self.navtb.enable_screenshot_buttons()
            # enable stop and info acquisition button
            self.navtb.enable_stop_and_info_acquisition_button()

            # external tasks
            tasks = [Tasks.SCREEN_RECORDER, Tasks.PACKET_CAPTURE]
            self.acquisition.start(tasks, self.acquisition_directory, self.case_info)

    def stop_acquisition(self):

        if self.start_acquisition_is_finished:
            self.stop_acquisition_is_started = True
            self.progress_bar.setHidden(False)
            url = self.tabs.currentWidget().url().toString()
            self.__disable_all()
            # external tasks
            tasks = [
                Tasks.PACKET_CAPTURE,
                Tasks.WHOIS,
                Tasks.NSLOOKUP,
                Tasks.HEADERS,
                Tasks.TRACEROUTE,
                Tasks.SSLKEYLOG,
                Tasks.SSLCERTIFICATE,
                Tasks.SCREEN_RECORDER
            ]

            # internal tasks
            screenshot = AcquisitionTask(Tasks.SCREENSHOT, state.STARTED, Status.PENDING)
            self.__tasks.append(screenshot)
            save_page = AcquisitionTask(Tasks.SAVE_PAGE, state.STARTED, Status.PENDING)
            self.__tasks.append(save_page)

            self.acquisition.stop(tasks, url, len(self.__tasks))

    def acquisition_info(self):
        self.acquisition.info.show()

    def __are_external_tasks_completed(self):

        if self.start_acquisition_is_finished is False:
            self.__start_acquisition_is_finished()
        else:
            # start internal tasks
            self.take_full_page_screenshot(last=True)
            self.save_page()

    def __are_internal_tasks_completed(self):
        status = [task.status for task in self.__tasks]
        status = list(set(status))
        if len(status) == 1 and status[0] == Status.COMPLETED:
            # start post acquisition external tasks
            self.acquisition.post_acquisition.execute(self.acquisition_directory, self.case_info, 'web')

    def __are_post_acquisition_finished(self):
        self.__stop_acquisition_is_finished()

    def __start_acquisition_is_finished(self):
        self.acquisition.set_completed_progress_bar()
        self.status.showMessage('')
        # show progress bar for 2 seconds
        loop = QtCore.QEventLoop()
        QtCore.QTimer.singleShot(2000, loop.quit)
        loop.exec()

        self.progress_bar.setHidden(True)
        self.progress_bar.setValue(0)

        self.start_acquisition_is_finished = True
        self.start_acquisition_is_started = False

    def __stop_acquisition_is_finished(self):
        self.tabs.currentWidget().reconnect_signal()
        self.acquisition.log_end_message()
        self.acquisition.set_completed_progress_bar()

        # hidden progress bar
        self.progress_bar.setHidden(True)
        self.status.showMessage('')

        self.__clear_cache()
        profile = QWebEngineProfile.defaultProfile()
        profile.clearHttpCache()

        self.acquisition_is_running = False
        self.start_acquisition_is_finished = False
        self.start_acquisition_is_started = False
        self.stop_acquisition_is_started = False
        try:
            self.tabs.currentWidget().saveResourcesFinished.disconnect()
        except TypeError:
            pass

        self.__tasks.clear()

        self.__enable_all()
        self.__show_finish_acquisition_dialog()

        self.acquisition.post_acquisition.finished.disconnect()

    def __show_finish_acquisition_dialog(self):
        msg = QtWidgets.QMessageBox(self)
        msg.setWindowTitle(Logger.ACQUISITION_FINISHED)
        msg.setText(Details.ACQUISITION_FINISHED)
        msg.setStandardButtons(QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No)

        return_value = msg.exec()
        if return_value == QtWidgets.QMessageBox.StandardButton.Yes:
            self.__open_acquisition_directory()

    def __open_acquisition_directory(self):
        os.startfile(self.acquisition_directory)

    def __disable_all(self):
        self.setEnabled(False)
        self.navtb.setEnabled(False)
        self.navtb.enable_actions(enabled=False)

    def __enable_all(self):
        self.setEnabled(True)
        self.navtb.setEnabled(True)
        # Add information button to re-enable buttons list
        self.navtb.navigation_actions.append('info')
        self.navtb.enable_actions(filter=self.navtb.navigation_actions)
        self.navtb.enable_screenshot_buttons()
        self.navtb.enable_start_acquisition_button()
        self.navtb.enable_stop_and_info_acquisition_button()

    def save_page(self):

        self.acquisition.logger.info(Logger.SAVE_PAGE)
        self.acquisition.info.add_task(Tasks.SAVE_PAGE, state.STARTED, Status.PENDING)

        self.status.showMessage(Logger.SAVE_PAGE)

        self.acquisition_page_folder = os.path.join(self.acquisition_directory, "acquisition_page")
        if not os.path.isdir(self.acquisition_page_folder):
            os.makedirs(self.acquisition_page_folder)

        self.tabs.currentWidget().saveResourcesFinished.connect(self.__zip_and_remove)

        self.tabs.currentWidget().save_resources(self.acquisition_page_folder)

    def __zip_and_remove(self):
        shutil.make_archive(self.acquisition_page_folder, 'zip', self.acquisition_page_folder)
        downloads_folder = os.path.join(self.acquisition_directory, "downloads")
        has_files = os.listdir(downloads_folder)
        if len(has_files) > 0:
            shutil.make_archive(downloads_folder, 'zip', downloads_folder)
        try:
            shutil.rmtree(self.acquisition_page_folder)
            shutil.rmtree(downloads_folder)
        except OSError as e:
            error_dlg = ErrorView(QtWidgets.QMessageBox.Icon.Critical,
                                  Tasks.SAVE_PAGE,
                                  error.DELETE_PROJECT_FOLDER,
                                  "Error: %s - %s." % (e.filename, e.strerror)
                                  )

            error_dlg.exec()

        row = self.acquisition.info.get_row(Tasks.SAVE_PAGE)
        self.acquisition.info.update_task(row, state.FINISHED, Status.COMPLETED, '')
        task = list(filter(lambda task: task.name == Tasks.SAVE_PAGE, self.__tasks))[0]
        self.acquisition.upadate_progress_bar()
        task.state = state.FINISHED
        task.status = Status.COMPLETED
        self.__are_internal_tasks_completed()

    def case(self):
        self.case_view.exec()

    def configuration(self):
        self.configuration_view.exec()

    def take_screenshot(self):
        if self.screenshot_directory is not None:
            self.__disable_all()
            filename = screenshot_filename(self.screenshot_directory, self.tabs.currentWidget().url().host())
            self.tabs.currentWidget().grab().save(filename)
            self.__enable_all()

    def take_screenshot_selected_area(self):
        if self.screenshot_directory is not None:
            self.__disable_all()
            filename = screenshot_filename(self.screenshot_directory,
                                           "selected_" + self.tabs.currentWidget().url().host())
            select_area = SelectAreaView(filename, self)
            select_area.finished.connect(self.__enable_all)
            select_area.snip_area()

    def take_full_page_screenshot(self, last=False):
        if last:
            self.acquisition.logger.info(Logger.SCREENSHOT)
            self.acquisition.info.add_task(Tasks.SCREENSHOT, state.STARTED, Status.PENDING)

        if self.screenshot_directory is not None:
            full_page_folder = os.path.join(
                self.screenshot_directory + "/full_page/{}/".format(self.tabs.currentWidget().url().host()))
            if not os.path.isdir(full_page_folder):
                os.makedirs(full_page_folder)

            self.status.showMessage(Logger.SCREENSHOT)

            if last is False:
                self.progress_bar.setHidden(False)

            self.__disable_all()
            # move page on top
            self.tabs.currentWidget().page().runJavaScript("window.scrollTo(0, 0);")

            next = 0
            part = 0
            step = self.tabs.currentWidget().height()
            end = self.tabs.currentWidget().page().contentsSize().toSize().height()
            parts = end / step

            increment = 90 / parts
            progress = 0

            if last:
                increment = self.acquisition.increment / parts
                progress = self.progress_bar.value()

            images = []

            while next < end:
                filename = screenshot_filename(full_page_folder, "part_" + str(part))
                if next == 0:
                    self.tabs.currentWidget().grab().save(filename)
                else:
                    self.tabs.currentWidget().page().runJavaScript("window.scrollTo({}, {});".format(0, next))
                    ### Waiting everything is synchronized
                    loop = QtCore.QEventLoop()
                    QtCore.QTimer.singleShot(500, loop.quit)
                    loop.exec()
                    self.tabs.currentWidget().grab().save(filename)

                progress += increment
                self.progress_bar.setValue(progress)

                images.append(filename)

                part += 1
                next += step

            # combine all images part in an unique image
            imgs = [Image.open(i) for i in images]
            # pick the image which is the smallest, and resize the others to match it (can be arbitrary image shape here)
            min_shape = sorted([(np.sum(i.size), i.size) for i in imgs])[0][1]

            # for a vertical stacking it is simple: use vstack
            imgs_comb = np.vstack([i.resize(min_shape) for i in imgs])
            imgs_comb = Image.fromarray(imgs_comb)

            whole_img_filename = screenshot_filename(full_page_folder, "full_page" + "")
            if last:
                whole_img_filename = os.path.join(self.acquisition_directory, 'screenshot.png')

            imgs_comb.save(whole_img_filename)

            if last:
                row = self.acquisition.info.get_row(Tasks.SCREENSHOT)
                self.acquisition.info.update_task(row, state.FINISHED, Status.COMPLETED, '')
                task = list(filter(lambda task: task.name == Tasks.SCREENSHOT, self.__tasks))[0]
                task.state = state.FINISHED
                task.status = Status.COMPLETED
                self.__are_internal_tasks_completed()

            else:
                self.progress_bar.setValue(100 - progress)
                self.__enable_all()
                self.progress_bar.setHidden(True)

    def back(self):
        self.tabs.currentWidget().back()

    def forward(self):
        self.tabs.currentWidget().forward()

    def reload(self):
        self.tabs.currentWidget().reload()

    def add_new_tab(self, qurl=None, label="Blank", page=None):
        self.current_page_load_is_finished = False

        if qurl is None:
            qurl = QtCore.QUrl('')
        self.browser = Browser()

        if page is None:
            page = WebEnginePage(self.browser)

        page.new_page_after_link_with_target_blank_attribute.connect(lambda page: self.add_new_tab(page=page))
        self.browser.setPage(page)

        self.browser.setUrl(qurl)
        i = self.tabs.addTab(self.browser, label)

        self.tabs.setCurrentIndex(i)

        # More difficult! We only want to update the url when it's from the
        # correct tab
        self.browser.urlChanged.connect(lambda qurl, browser=self.browser:
                                        self.__update_urlbar(qurl, browser))

        self.browser.loadProgress.connect(self.load_progress)

        self.browser.loadFinished.connect(lambda _, i=i, browser=self.browser:
                                          self.__page_on_loaded(i, browser))

        self.browser.urlChanged.connect(lambda qurl:
                                        self.__allow_notifications(qurl))

        self.browser.downloadItemFinished.connect(self.__handle_download_item_finished)

        if i == 0:
            self.showMaximized()

    def __handle_download_item_finished(self, filename):
        self.status.showMessage(general.DOWNLOAD + ": " + filename)
        loop = QtCore.QEventLoop()
        QtCore.QTimer.singleShot(2000, loop.quit)
        loop.exec()
        self.status.showMessage('')

    def __page_on_loaded(self, tab_index, browser):
        self.tabs.setTabText(tab_index, browser.page().title())

    def tab_open_doubleclick(self, i):
        if i == -1 and self.isEnabled():  # No tab under the click
            self.add_new_tab()

    def current_tab_changed(self, i):
        self.tabs.currentWidget().page().profile().disconnect() # Disconnect the current tab
        for index in range(self.tabs.count()):
            if self.tabs.widget(index) == self.tabs.currentWidget():
                self.tabs.currentWidget().reconnect() # Reconnect only the new current tab

        if self.tabs.currentWidget() is not None:
            qurl = self.tabs.currentWidget().url()
            self.__update_urlbar(qurl, self.tabs.currentWidget())
            self.update_title(self.tabs.currentWidget())

    def close_current_tab(self, i):
        if self.tabs.count() < 2:
            return

        self.tabs.removeTab(i)

    def update_title(self, browser):
        if browser != self.tabs.currentWidget():
            # If this signal is not from the current tab, ignore
            return

        title = self.tabs.currentWidget().page().title()
        self.setWindowTitle("%s - Freezing Internet Tool" % title)

    def navigate_home(self):
        self.tabs.currentWidget().setUrl(QtCore.QUrl(self.configuration_general.configuration['home_page_url']))

    def navigate_to_url(self):  # Does not receive the Url
        q = QtCore.QUrl(self.navtb.urlbar.text())
        if q.scheme() == "":
            q.setScheme("http")

        self.tabs.currentWidget().setUrl(q)

    def load_progress(self, progress):
        if progress == 100:
            self.current_page_load_is_finished = True
            self.navtb.enable_screenshot_buttons()

    def __clear_cache(self):

        profile = QWebEngineProfile.defaultProfile()
        profile.clearAllVisitedLinks()
        cookie_store = profile.cookieStore()
        cookie_store.deleteAllCookies()

    def __update_urlbar(self, q, browser=None):
        self.current_page_load_is_finished = False
        self.navtb.enable_screenshot_buttons()

        if browser != self.tabs.currentWidget():
            # If this signal is not from the current tab, ignore
            return

        if q.scheme() == 'https':
            # Secure padlock icon
            pixmap = QtGui.QPixmap(os.path.join('assets/svg/toolbar', 'lock-close.svg'))
            self.navtb.httpsicon.setPixmap(
                pixmap.scaled(16, 16, aspectRatioMode=QtCore.Qt.AspectRatioMode.KeepAspectRatio))

        else:
            # Insecure padlock icon
            pixmap = QtGui.QPixmap(os.path.join('assets/svg/toolbar', 'lock-open.svg'))
            self.navtb.httpsicon.setPixmap(
                pixmap.scaled(16, 16, aspectRatioMode=QtCore.Qt.AspectRatioMode.KeepAspectRatio))

        self.navtb.urlbar.setText(q.toString())
        self.navtb.urlbar.setCursorPosition(0)

    def __allow_notifications(self, q):
        feature = QWebEnginePage.Feature.Notifications
        permission = QWebEnginePage.PermissionPolicy.PermissionGrantedByUser
        self.browser.page().setFeaturePermission(q, feature, permission)

    def __back_to_wizard(self):
        if self.acquisition_is_running is False:
            self.deleteLater()
            self.wizard.reload_case_info()
            self.wizard.show()

    def closeEvent(self, event):
        event.ignore()
        self.__back_to_wizard()
