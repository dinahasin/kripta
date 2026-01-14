# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'main_window.ui'
##
## Created by: Qt User Interface Compiler version 6.10.1
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QAction, QBrush, QColor, QConicalGradient,
    QCursor, QFont, QFontDatabase, QGradient,
    QIcon, QImage, QKeySequence, QLinearGradient,
    QPainter, QPalette, QPixmap, QRadialGradient,
    QTransform)
from PySide6.QtWidgets import (QApplication, QHBoxLayout, QLabel, QMainWindow,
    QMenu, QMenuBar, QPushButton, QSizePolicy,
    QStatusBar, QVBoxLayout, QWidget)

class Ui_MenuPrincipal(object):
    def setupUi(self, MenuPrincipal):
        if not MenuPrincipal.objectName():
            MenuPrincipal.setObjectName(u"MenuPrincipal")
        MenuPrincipal.resize(1000, 700)
        icon = QIcon()
        icon.addFile(u".", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        MenuPrincipal.setWindowIcon(icon)
        self.action_about = QAction(MenuPrincipal)
        self.action_about.setObjectName(u"action_about")
        self.action_clear_security = QAction(MenuPrincipal)
        self.action_clear_security.setObjectName(u"action_clear_security")
        self.centralwidget = QWidget(MenuPrincipal)
        self.centralwidget.setObjectName(u"centralwidget")
        self.verticalLayout_main = QVBoxLayout(self.centralwidget)
        self.verticalLayout_main.setSpacing(20)
        self.verticalLayout_main.setObjectName(u"verticalLayout_main")
        self.verticalLayout_main.setContentsMargins(50, 30, 50, 50)
        self.title_label = QLabel(self.centralwidget)
        self.title_label.setObjectName(u"title_label")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet(u"font-size: 36px; font-weight: bold; padding: 10px;")

        self.verticalLayout_main.addWidget(self.title_label)

        self.subtitle_label = QLabel(self.centralwidget)
        self.subtitle_label.setObjectName(u"subtitle_label")
        self.subtitle_label.setAlignment(Qt.AlignCenter)
        self.subtitle_label.setStyleSheet(u"font-size: 14px; color: #666666; padding-bottom: 20px;")
        self.subtitle_label.setWordWrap(True)

        self.verticalLayout_main.addWidget(self.subtitle_label)

        self.horizontalLayout_buttons = QHBoxLayout()
        self.horizontalLayout_buttons.setSpacing(20)
        self.horizontalLayout_buttons.setObjectName(u"horizontalLayout_buttons")
        self.btn_password_manager = QPushButton(self.centralwidget)
        self.btn_password_manager.setObjectName(u"btn_password_manager")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        sizePolicy.setHorizontalStretch(1)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.btn_password_manager.sizePolicy().hasHeightForWidth())
        self.btn_password_manager.setSizePolicy(sizePolicy)
        self.btn_password_manager.setMinimumSize(QSize(0, 150))
        self.btn_password_manager.setStyleSheet(u"QPushButton {\n"
"    font-size: 18px;\n"
"    font-weight: bold;\n"
"    padding: 20px;\n"
"    border: 2px solid #3498db;\n"
"    border-radius: 10px;\n"
"    background-color: #ecf0f1;\n"
"}\n"
"QPushButton:hover {\n"
"    background-color: #3498db;\n"
"    color: white;\n"
"}\n"
"QPushButton:pressed {\n"
"    background-color: #2980b9;\n"
"}")

        self.horizontalLayout_buttons.addWidget(self.btn_password_manager)

        self.btn_file_encryptor = QPushButton(self.centralwidget)
        self.btn_file_encryptor.setObjectName(u"btn_file_encryptor")
        sizePolicy.setHeightForWidth(self.btn_file_encryptor.sizePolicy().hasHeightForWidth())
        self.btn_file_encryptor.setSizePolicy(sizePolicy)
        self.btn_file_encryptor.setMinimumSize(QSize(0, 150))
        self.btn_file_encryptor.setStyleSheet(u"QPushButton {\n"
"    font-size: 18px;\n"
"    font-weight: bold;\n"
"    padding: 20px;\n"
"    border: 2px solid #27ae60;\n"
"    border-radius: 10px;\n"
"    background-color: #ecf0f1;\n"
"}\n"
"QPushButton:hover {\n"
"    background-color: #27ae60;\n"
"    color: white;\n"
"}\n"
"QPushButton:pressed {\n"
"    background-color: #229954;\n"
"}")

        self.horizontalLayout_buttons.addWidget(self.btn_file_encryptor)

        self.btn_disk_analyzer = QPushButton(self.centralwidget)
        self.btn_disk_analyzer.setObjectName(u"btn_disk_analyzer")
        sizePolicy.setHeightForWidth(self.btn_disk_analyzer.sizePolicy().hasHeightForWidth())
        self.btn_disk_analyzer.setSizePolicy(sizePolicy)
        self.btn_disk_analyzer.setMinimumSize(QSize(0, 150))
        self.btn_disk_analyzer.setStyleSheet(u"QPushButton {\n"
"    font-size: 18px;\n"
"    font-weight: bold;\n"
"    padding: 20px;\n"
"    border: 2px solid #e67e22;\n"
"    border-radius: 10px;\n"
"    background-color: #ecf0f1;\n"
"}\n"
"QPushButton:hover {\n"
"    background-color: #e67e22;\n"
"    color: white;\n"
"}\n"
"QPushButton:pressed {\n"
"    background-color: #d35400;\n"
"}")

        self.horizontalLayout_buttons.addWidget(self.btn_disk_analyzer)


        self.verticalLayout_main.addLayout(self.horizontalLayout_buttons)

        MenuPrincipal.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MenuPrincipal)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 1000, 22))
        self.menu_help = QMenu(self.menubar)
        self.menu_help.setObjectName(u"menu_help")
        MenuPrincipal.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(MenuPrincipal)
        self.statusbar.setObjectName(u"statusbar")
        MenuPrincipal.setStatusBar(self.statusbar)

        self.menubar.addAction(self.menu_help.menuAction())
        self.menu_help.addAction(self.action_about)
        self.menu_help.addAction(self.action_clear_security)

        self.retranslateUi(MenuPrincipal)

        QMetaObject.connectSlotsByName(MenuPrincipal)
    # setupUi

    def retranslateUi(self, MenuPrincipal):
        MenuPrincipal.setWindowTitle(QCoreApplication.translate("MenuPrincipal", u"Kripta - Menu Principal", None))
        self.action_about.setText(QCoreApplication.translate("MenuPrincipal", u"\u00c0 propos", None))
#if QT_CONFIG(tooltip)
        self.action_about.setToolTip(QCoreApplication.translate("MenuPrincipal", u"\u00c0 propos de Kripta", None))
#endif // QT_CONFIG(tooltip)
        self.action_clear_security.setText(QCoreApplication.translate("MenuPrincipal", u"Effacer mes donn\u00e9es de s\u00e9curit\u00e9\u2026", None))
#if QT_CONFIG(tooltip)
        self.action_clear_security.setToolTip(QCoreApplication.translate("MenuPrincipal", u"Supprimer toutes les donn\u00e9es de s\u00e9curit\u00e9 locales (profil, certificats, mots de passe)", None))
#endif // QT_CONFIG(tooltip)
        self.title_label.setText(QCoreApplication.translate("MenuPrincipal", u"Kripta", None))
        self.subtitle_label.setText(QCoreApplication.translate("MenuPrincipal", u"Gestionnaire de mots de passe s\u00e9curis\u00e9, crypteur de fichiers et dossiers, et analyseur d'espace disque", None))
        self.btn_password_manager.setText(QCoreApplication.translate("MenuPrincipal", u"Gestionnaire\n"
"de mots de passe", None))
        self.btn_file_encryptor.setText(QCoreApplication.translate("MenuPrincipal", u"Crypteur de fichiers", None))
        self.btn_disk_analyzer.setText(QCoreApplication.translate("MenuPrincipal", u"Spaces optimisations", None))
        self.menu_help.setTitle(QCoreApplication.translate("MenuPrincipal", u"Aide", None))
    # retranslateUi

