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
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QHeaderView, QLineEdit,
    QMainWindow, QMenu, QMenuBar, QSizePolicy,
    QSplitter, QStatusBar, QTableWidget, QTableWidgetItem,
    QToolBar, QTreeWidget, QTreeWidgetItem, QVBoxLayout,
    QWidget)

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(1200, 800)
        self.action_new = QAction(MainWindow)
        self.action_new.setObjectName(u"action_new")
        self.action_open = QAction(MainWindow)
        self.action_open.setObjectName(u"action_open")
        self.action_edit = QAction(MainWindow)
        self.action_edit.setObjectName(u"action_edit")
        self.action_delete = QAction(MainWindow)
        self.action_delete.setObjectName(u"action_delete")
        self.action_lock = QAction(MainWindow)
        self.action_lock.setObjectName(u"action_lock")
        self.action_unlock = QAction(MainWindow)
        self.action_unlock.setObjectName(u"action_unlock")
        self.action_settings = QAction(MainWindow)
        self.action_settings.setObjectName(u"action_settings")
        self.action_refresh = QAction(MainWindow)
        self.action_refresh.setObjectName(u"action_refresh")
        self.action_quit = QAction(MainWindow)
        self.action_quit.setObjectName(u"action_quit")
        self.action_preferences = QAction(MainWindow)
        self.action_preferences.setObjectName(u"action_preferences")
        self.action_toggle_sidebar = QAction(MainWindow)
        self.action_toggle_sidebar.setObjectName(u"action_toggle_sidebar")
        self.action_about = QAction(MainWindow)
        self.action_about.setObjectName(u"action_about")
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.verticalLayout_main = QVBoxLayout(self.centralwidget)
        self.verticalLayout_main.setSpacing(0)
        self.verticalLayout_main.setObjectName(u"verticalLayout_main")
        self.verticalLayout_main.setContentsMargins(0, 0, 0, 0)
        self.splitter_main = QSplitter(self.centralwidget)
        self.splitter_main.setObjectName(u"splitter_main")
        self.splitter_main.setOrientation(Qt.Horizontal)
        self.sidebar_widget = QWidget(self.splitter_main)
        self.sidebar_widget.setObjectName(u"sidebar_widget")
        self.sidebar_widget.setMinimumSize(QSize(200, 0))
        self.sidebar_widget.setMaximumSize(QSize(350, 16777215))
        self.verticalLayout_sidebar = QVBoxLayout(self.sidebar_widget)
        self.verticalLayout_sidebar.setSpacing(0)
        self.verticalLayout_sidebar.setObjectName(u"verticalLayout_sidebar")
        self.verticalLayout_sidebar.setContentsMargins(0, 0, 0, 0)
        self.sidebar_tree = QTreeWidget(self.sidebar_widget)
        self.sidebar_tree.setObjectName(u"sidebar_tree")
        self.sidebar_tree.setHeaderHidden(True)
        self.sidebar_tree.setRootIsDecorated(True)

        self.verticalLayout_sidebar.addWidget(self.sidebar_tree)

        self.splitter_main.addWidget(self.sidebar_widget)
        self.content_widget = QWidget(self.splitter_main)
        self.content_widget.setObjectName(u"content_widget")
        self.verticalLayout_content = QVBoxLayout(self.content_widget)
        self.verticalLayout_content.setSpacing(0)
        self.verticalLayout_content.setObjectName(u"verticalLayout_content")
        self.verticalLayout_content.setContentsMargins(0, 0, 0, 0)
        self.toolbar_container = QWidget(self.content_widget)
        self.toolbar_container.setObjectName(u"toolbar_container")
        self.toolbar_container.setMaximumSize(QSize(16777215, 60))
        self.verticalLayout_toolbar = QVBoxLayout(self.toolbar_container)
        self.verticalLayout_toolbar.setSpacing(5)
        self.verticalLayout_toolbar.setObjectName(u"verticalLayout_toolbar")
        self.verticalLayout_toolbar.setContentsMargins(10, 5, 10, 5)
        self.search_line = QLineEdit(self.toolbar_container)
        self.search_line.setObjectName(u"search_line")

        self.verticalLayout_toolbar.addWidget(self.search_line)

        self.content_toolbar = QToolBar(self.toolbar_container)
        self.content_toolbar.setObjectName(u"content_toolbar")
        self.content_toolbar.setMovable(False)
        self.content_toolbar.setFloatable(False)

        self.verticalLayout_toolbar.addWidget(self.content_toolbar)


        self.verticalLayout_content.addWidget(self.toolbar_container)

        self.content_table = QTableWidget(self.content_widget)
        if (self.content_table.columnCount() < 4):
            self.content_table.setColumnCount(4)
        __qtablewidgetitem = QTableWidgetItem()
        self.content_table.setHorizontalHeaderItem(0, __qtablewidgetitem)
        __qtablewidgetitem1 = QTableWidgetItem()
        self.content_table.setHorizontalHeaderItem(1, __qtablewidgetitem1)
        __qtablewidgetitem2 = QTableWidgetItem()
        self.content_table.setHorizontalHeaderItem(2, __qtablewidgetitem2)
        __qtablewidgetitem3 = QTableWidgetItem()
        self.content_table.setHorizontalHeaderItem(3, __qtablewidgetitem3)
        self.content_table.setObjectName(u"content_table")
        self.content_table.setAlternatingRowColors(True)
        self.content_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.content_table.setSortingEnabled(True)

        self.verticalLayout_content.addWidget(self.content_table)

        self.splitter_main.addWidget(self.content_widget)

        self.verticalLayout_main.addWidget(self.splitter_main)

        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 1200, 22))
        self.menu_file = QMenu(self.menubar)
        self.menu_file.setObjectName(u"menu_file")
        self.menu_edit = QMenu(self.menubar)
        self.menu_edit.setObjectName(u"menu_edit")
        self.menu_view = QMenu(self.menubar)
        self.menu_view.setObjectName(u"menu_view")
        self.menu_help = QMenu(self.menubar)
        self.menu_help.setObjectName(u"menu_help")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(MainWindow)
        self.statusbar.setObjectName(u"statusbar")
        MainWindow.setStatusBar(self.statusbar)
        self.toolbar = QToolBar(MainWindow)
        self.toolbar.setObjectName(u"toolbar")
        MainWindow.addToolBar(Qt.ToolBarArea.TopToolBarArea, self.toolbar)

        self.content_toolbar.addAction(self.action_new)
        self.content_toolbar.addAction(self.action_edit)
        self.content_toolbar.addAction(self.action_delete)
        self.content_toolbar.addSeparator()
        self.content_toolbar.addAction(self.action_lock)
        self.content_toolbar.addAction(self.action_unlock)
        self.content_toolbar.addSeparator()
        self.content_toolbar.addAction(self.action_settings)
        self.content_toolbar.addSeparator()
        self.content_toolbar.addAction(self.action_refresh)
        self.menubar.addAction(self.menu_file.menuAction())
        self.menubar.addAction(self.menu_edit.menuAction())
        self.menubar.addAction(self.menu_view.menuAction())
        self.menubar.addAction(self.menu_help.menuAction())
        self.menu_file.addAction(self.action_new)
        self.menu_file.addAction(self.action_open)
        self.menu_file.addSeparator()
        self.menu_file.addAction(self.action_quit)
        self.menu_edit.addAction(self.action_edit)
        self.menu_edit.addAction(self.action_delete)
        self.menu_edit.addSeparator()
        self.menu_edit.addAction(self.action_preferences)
        self.menu_view.addAction(self.action_refresh)
        self.menu_view.addSeparator()
        self.menu_view.addAction(self.action_toggle_sidebar)
        self.menu_help.addAction(self.action_about)
        self.toolbar.addAction(self.action_new)
        self.toolbar.addAction(self.action_edit)
        self.toolbar.addAction(self.action_delete)

        self.retranslateUi(MainWindow)

        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"Kripta - Gestionnaire de mots de passe et crypteur de dossiers", None))
        self.action_new.setText(QCoreApplication.translate("MainWindow", u"Nouveau", None))
#if QT_CONFIG(tooltip)
        self.action_new.setToolTip(QCoreApplication.translate("MainWindow", u"Cr\u00e9er un nouvel \u00e9l\u00e9ment", None))
#endif // QT_CONFIG(tooltip)
        self.action_open.setText(QCoreApplication.translate("MainWindow", u"Ouvrir", None))
#if QT_CONFIG(tooltip)
        self.action_open.setToolTip(QCoreApplication.translate("MainWindow", u"Ouvrir un \u00e9l\u00e9ment", None))
#endif // QT_CONFIG(tooltip)
        self.action_edit.setText(QCoreApplication.translate("MainWindow", u"Modifier", None))
#if QT_CONFIG(tooltip)
        self.action_edit.setToolTip(QCoreApplication.translate("MainWindow", u"Modifier l'\u00e9l\u00e9ment s\u00e9lectionn\u00e9", None))
#endif // QT_CONFIG(tooltip)
        self.action_delete.setText(QCoreApplication.translate("MainWindow", u"Supprimer", None))
#if QT_CONFIG(tooltip)
        self.action_delete.setToolTip(QCoreApplication.translate("MainWindow", u"Supprimer l'\u00e9l\u00e9ment s\u00e9lectionn\u00e9", None))
#endif // QT_CONFIG(tooltip)
        self.action_lock.setText(QCoreApplication.translate("MainWindow", u"Verrouiller", None))
#if QT_CONFIG(tooltip)
        self.action_lock.setToolTip(QCoreApplication.translate("MainWindow", u"Verrouiller l'\u00e9l\u00e9ment", None))
#endif // QT_CONFIG(tooltip)
        self.action_unlock.setText(QCoreApplication.translate("MainWindow", u"D\u00e9verrouiller", None))
#if QT_CONFIG(tooltip)
        self.action_unlock.setToolTip(QCoreApplication.translate("MainWindow", u"D\u00e9verrouiller l'\u00e9l\u00e9ment", None))
#endif // QT_CONFIG(tooltip)
        self.action_settings.setText(QCoreApplication.translate("MainWindow", u"Param\u00e8tres", None))
#if QT_CONFIG(tooltip)
        self.action_settings.setToolTip(QCoreApplication.translate("MainWindow", u"Ouvrir les param\u00e8tres", None))
#endif // QT_CONFIG(tooltip)
        self.action_refresh.setText(QCoreApplication.translate("MainWindow", u"Actualiser", None))
#if QT_CONFIG(tooltip)
        self.action_refresh.setToolTip(QCoreApplication.translate("MainWindow", u"Actualiser la vue", None))
#endif // QT_CONFIG(tooltip)
        self.action_quit.setText(QCoreApplication.translate("MainWindow", u"Quitter", None))
#if QT_CONFIG(tooltip)
        self.action_quit.setToolTip(QCoreApplication.translate("MainWindow", u"Quitter l'application", None))
#endif // QT_CONFIG(tooltip)
        self.action_preferences.setText(QCoreApplication.translate("MainWindow", u"Pr\u00e9f\u00e9rences", None))
#if QT_CONFIG(tooltip)
        self.action_preferences.setToolTip(QCoreApplication.translate("MainWindow", u"Ouvrir les pr\u00e9f\u00e9rences", None))
#endif // QT_CONFIG(tooltip)
        self.action_toggle_sidebar.setText(QCoreApplication.translate("MainWindow", u"Masquer/Afficher la barre lat\u00e9rale", None))
#if QT_CONFIG(tooltip)
        self.action_toggle_sidebar.setToolTip(QCoreApplication.translate("MainWindow", u"Basculer l'affichage de la barre lat\u00e9rale", None))
#endif // QT_CONFIG(tooltip)
        self.action_about.setText(QCoreApplication.translate("MainWindow", u"\u00c0 propos", None))
#if QT_CONFIG(tooltip)
        self.action_about.setToolTip(QCoreApplication.translate("MainWindow", u"\u00c0 propos de Kripta", None))
#endif // QT_CONFIG(tooltip)
        ___qtreewidgetitem = self.sidebar_tree.headerItem()
        ___qtreewidgetitem.setText(0, QCoreApplication.translate("MainWindow", u"Section", None));
        self.search_line.setPlaceholderText(QCoreApplication.translate("MainWindow", u"Rechercher...", None))
        self.content_toolbar.setWindowTitle(QCoreApplication.translate("MainWindow", u"content_toolbar", None))
        ___qtablewidgetitem = self.content_table.horizontalHeaderItem(0)
        ___qtablewidgetitem.setText(QCoreApplication.translate("MainWindow", u"Nom", None));
        ___qtablewidgetitem1 = self.content_table.horizontalHeaderItem(1)
        ___qtablewidgetitem1.setText(QCoreApplication.translate("MainWindow", u"Type", None));
        ___qtablewidgetitem2 = self.content_table.horizontalHeaderItem(2)
        ___qtablewidgetitem2.setText(QCoreApplication.translate("MainWindow", u"Date de modification", None));
        ___qtablewidgetitem3 = self.content_table.horizontalHeaderItem(3)
        ___qtablewidgetitem3.setText(QCoreApplication.translate("MainWindow", u"Taille", None));
        self.menu_file.setTitle(QCoreApplication.translate("MainWindow", u"Fichier", None))
        self.menu_edit.setTitle(QCoreApplication.translate("MainWindow", u"\u00c9dition", None))
        self.menu_view.setTitle(QCoreApplication.translate("MainWindow", u"Affichage", None))
        self.menu_help.setTitle(QCoreApplication.translate("MainWindow", u"Aide", None))
        self.toolbar.setWindowTitle(QCoreApplication.translate("MainWindow", u"toolbar", None))
    # retranslateUi

