#!/usr/bin/python3.6
# coding: utf-8

from PyQt5.QtWebEngineWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.Qt import *

from files.Browthon_utils import parseTheme, dezip

import os, shutil


class DownloadSignal(QObject):
    removeClicked = pyqtSignal()

    def __init__(self, parent):
        super(DownloadSignal, self).__init__()
        self.parent = parent


class DownloadWidget(QWidget):
    def __init__(self, download, url, main):
        super(DownloadWidget, self).__init__()
        self.setupui()
        self.download = download
        self.url = url
        self.main = main
        self.downloadSignal = DownloadSignal(self)
        self.title.setText(QFileInfo(self.download.path()).fileName())

        self.cancel.clicked.connect(self.cancelDownload)
        self.download.downloadProgress.connect(self.updateWidget)
        self.download.stateChanged.connect(self.updateWidget)

        self.updateWidget()

    def updateWidget(self):
            totalBytes = self.download.totalBytes()
            receivedBytes = self.download.receivedBytes()

            state = self.download.state()
            if state == QWebEngineDownloadItem.DownloadRequested:
                pass
            elif state == QWebEngineDownloadItem.DownloadInProgress:
                if totalBytes > 0:
                    self.progressBar.setValue(int(100 * receivedBytes / totalBytes))
                    self.progressBar.setDisabled(False)
                    self.progressBar.setFormat("%p% - {} téléchargés sur {}".format(self.withUnit(receivedBytes), self.withUnit(totalBytes)))
                else:
                    self.progressBar.setValue(0)
                    self.progressBar.setDisabled(False)
                    self.progressBar.setFormat("Taille inconnue - {} téléchargés".format(self.withUnit(receivedBytes)))
            elif state == QWebEngineDownloadItem.DownloadCompleted:
                self.progressBar.setValue(100)
                self.progressBar.setDisabled(True)
                self.progressBar.setFormat("Complété - {} téléchargés".format(self.withUnit(receivedBytes)))
                if self.url == "http://pastagames.fr.nf/browthon/addons.php":
                    rep = QMessageBox().question(self, "Addon "+QFileInfo(self.download.path()).fileName()+" téléchargé", 'Voulez-vous installer cet addon ?', QMessageBox.Yes, QMessageBox.No)
                    if rep == 16384:
                        print(self.download.path())
                        error = None
                        try:
                            shutil.copy(self.download.path(), "addons")
                            os.remove(self.download.path())
                        except:
                            error = "Déplacement impossible"
                        else:
                            try:
                                dezip("addons/"+self.download.path().split('/')[-1], "addons")
                                os.remove("addons/"+self.download.path().split('/')[-1])
                            except:
                                error = "Dézippage impossible"
                        if error != None:
                            QMessageBox().warning(self, "Addon "+QFileInfo(self.download.path()).fileName(), "Installation impossible.\nErreur : "+error)
                            self.main.mainWindow.logger.warning("Installation de l'addon "+QFileInfo(self.download.path()).fileName()+" impossible.\nErreur : "+error)
                        else:
                            QMessageBox().information(self, "Addon "+QFileInfo(self.download.path()).fileName(), "Installation réussie !")
                            self.main.mainWindow.logger.info("Installation de l'addon "+QFileInfo(self.download.path()).fileName()+" réussie !")
            elif state == QWebEngineDownloadItem.DownloadCancelled:
                self.progressBar.setValue(0)
                self.progressBar.setDisabled(True)
                self.progressBar.setFormat("Annulé - {} téléchargés".format(self.withUnit(receivedBytes)))
            elif state == QWebEngineDownloadItem.DownloadInterrupted:
                self.progressBar.setValue(0)
                self.progressBar.setDisabled(True)
                self.progressBar.setFormat("Interrompu - {}".format(self.download.interruptReasonString()))

            if state == QWebEngineDownloadItem.DownloadInProgress:
                self.cancel.setText("Arrêter")
                self.cancel.setToolTip("Stopper le téléchargement")
            else:
                self.cancel.setText("Supprimer")
                self.cancel.setToolTip("Enlever le téléchargement")

    def cancelDownload(self):
        if self.download.state() == QWebEngineDownloadItem.DownloadInProgress:
            self.download.cancel()
        else:
            self.downloadSignal.removeClicked.emit()

    def withUnit(self, bytesNb):
        if bytesNb < 1 << 10:
            return str(round(bytesNb, 2)) + " B"
        elif bytesNb < 1 << 20:
            return str(round(bytesNb / (1 << 10), 2)) + " KiB"
        elif bytesNb < 1 << 30:
            return str(round(bytesNb / (1 << 20), 2)) + " MiB"
        else:
            return str(round(bytesNb / (1 << 30), 2)) + " GiB"

    def setupui(self):
        self.layout = QGridLayout()
        self.title = QLabel("NAME")
        self.cancel = QPushButton("Cancel")
        self.progressBar = QProgressBar()
        self.layout.addWidget(self.title, 1, 1)
        self.layout.addWidget(self.progressBar, 2, 1)
        self.layout.addWidget(self.cancel, 3, 1)
        self.setLayout(self.layout)


class DownloadManagerWidget(QWidget):
    def __init__(self, main):
        super(DownloadManagerWidget, self).__init__()
        self.setMinimumSize(500, 300)
        self.main = main
        self.nbDownload = 0
        self.setupui()

    def downloadRequested(self, download):
        if download:
            if download.state() == QWebEngineDownloadItem.DownloadRequested:
                path = QFileDialog.getSaveFileName(self, "Sauver comme",
                    download.path())
                if path == "":
                    return
                else:
                    download.setPath(path[0])
                    download.accept()
                    self.add(DownloadWidget(download, self.main.browser.url().toString(), self.main))

                    self.show()
            else:
                self.main.mainWindow.logger.critical("Le téléchargement n'a pas été demandé.")
        else:
            self.main.mainWindow.logger.critical("Le téléchargement est nul.")

    def add(self, downloadWidget):
        downloadWidget.downloadSignal.removeClicked.connect(self.remove)
        self.layout.addWidget(downloadWidget)
        self.layout.setAlignment(downloadWidget, Qt.AlignTop)
        self.nbDownload += 1
        if self.nbDownload >= 0:
            self.label.hide()

    def remove(self):
        downloadWidget = self.sender().parent
        self.layout.removeWidget(downloadWidget)
        downloadWidget.deleteLater()
        self.nbDownload -= 1
        if self.nbDownload <= 0:
            self.label.show()

    def setupui(self):
        self.layoutMain = QVBoxLayout(self)
        self.scroll = QScrollArea(self)
        self.scroll.setWidgetResizable(True)
        self.title = QLabel("Téléchargements")
        self.title.setFont(self.main.fonts["titre"])
        self.title.setAlignment(Qt.AlignHCenter)
        self.layoutMain.addWidget(self.title)
        self.layoutMain.addWidget(self.scroll)

        self.container = QWidget()
        self.scroll.setWidget(self.container)
        self.layout = QVBoxLayout(self.container)
        self.label = QLabel("Pas de téléchargement")
        self.label.setAlignment(Qt.AlignHCenter)
        self.layout.addWidget(self.label)
        if self.main.mainWindow.styleSheetParam != "Default":
            with open('style/' + self.main.mainWindow.styleSheetParam + ".bss", 'r') as fichier:
                bss = parseTheme(fichier.read())
                self.setStyleSheet(bss)