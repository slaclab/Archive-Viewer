from typing import (Dict, Union)
from qtpy.QtGui import QColor
from qtpy.QtCore import (QModelIndex, Qt, Slot, QAbstractTableModel, QUrl)
from qtpy.QtWidgets import QWidget
from qtpy.QtNetwork import (QNetworkAccessManager, QNetworkReply, QNetworkRequest)
from config import logger


class ArchiversTableModel(QAbstractTableModel):
    def __init__(self, parent: QWidget, init_archivers):
        super().__init__(parent)
        self.network_manager = QNetworkAccessManager()
        self.network_manager.finished.connect(self.archiver_validation)

        self._headers = ["Fetch From", "Archiver", "URL"]

        self._data = []
        self._error = []
        self.init_data(init_archivers)

    def rowCount(self, index: QModelIndex = QModelIndex()):
        """Return the number of rows in the model."""
        return len(self._data)

    def columnCount(self, index: QModelIndex = QModelIndex()):
        """Return the number of columns in the model."""
        return len(self._headers)

    def data(self, index: QModelIndex, role: Qt.ItemDataRole):
        """Return the index's data."""
        if not index.isValid():
            return
        elif role == Qt.DisplayRole or role == Qt.EditRole:
            return str(self._data[index.row()][index.column()])
        elif role == Qt.UserRole:
            return self._data[index.row()][index.column()]
        elif role == Qt.ForegroundRole:
            if self._error[index.row()]:
                return QColor(Qt.red)
            return QColor(Qt.black)

    def setData(self, index: QModelIndex, value: Union[str, bool], role: Qt.ItemDataRole):
        """Set the index's data on edit. If the Archiver URL's validity
        when archiver is enabled and/or the URL changes.

        Parameters
        ----------
        index : QModelIndex
            The index on the table that is being altered.
        value : str or bool
            The new value to be set in the table.
        role : Qt.ItemDataRole
            The QT data role for what data is changing. Only Qt.EditRole
            is accepted.
        """
        if not index.isValid() or role != Qt.EditRole:
            return False

        logger.debug(f"Archiver table data for index: {(index.row(), index.column())}")

        # Check that archiver is valid on 1) enabling or
        #   2) changing an archiver's URL
        send_request = False
        if index.column() == 0 and value:
            base_url = self._data[index.row()][2]
            if not base_url:
                logger.debug(base_url)
                self.dataChanged.emit(index, index)
                return False

            send_request = True
            url = base_url + "/retrieval/ping"
            enable_index = index
        elif index.column() == 2 and self._data[index.row()][0]:
            send_request = True
            url = value + "/retrieval/ping"
            enable_index = self.index(index.row(), 0)

        if send_request:
            reply = self.network_manager.get(QNetworkRequest(QUrl(url)))
            reply.setProperty("index", enable_index)
            logger.debug(f"Archiver validation request: {reply.url()}")

        self._data[index.row()][index.column()] = value
        self.dataChanged.emit(index, index)
        return True

    def headerData(self, section: int, orientation: Qt.Orientation, role: Qt.ItemDataRole):
        """Set the horizontal header's text."""
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self._headers[section]

    def flags(self, index: QModelIndex):
        """Returns a list of the set flags for the given index."""
        fl = super().flags(index)
        fl |= (Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable)
        return fl

    def removeRows(self, row: int, count:int,  parent: QModelIndex = QModelIndex()):
        """Removes a number of rows from the table.

        Parameters
        ----------
        row : int
            The index of the first row to be removed.
        count : int
            The number of rows to be removed from the table.
        """
        if count < 1 or (row + count) > len(self._data):
            return False

        self.beginRemoveRows(parent, row, row + count - 1)
        del self._data[row:(row + count)]
        self.endRemoveRows()

        return True

    def init_data(self, init_archivers: Dict[str, str]):
        """Initializes the table model with the list of initial archivers.

        Parameters
        ----------
        init_archivers : Dict[str, str]
            Initial archivers where the key is the name and value is the url.
        """
        new_data = []
        for name, url in init_archivers.items():
            new_row = [False, name, url]
            new_data.append(new_row)

        self.beginInsertRows(QModelIndex(), 0, len(new_data))
        self._data = new_data
        self._error = [False] * len(new_data)
        self.endInsertRows()

        for row in range(len(self._data)):
            ind = self.index(row, 0)
            self.setData(ind, True, Qt.EditRole)

    def add_empty_row(self):
        """Append an empty row to the end of the table model."""
        new_row = [False, "", ""]
        logger.debug("Adding row to archivers table.")

        self.beginInsertRows(QModelIndex(), len(self._data), len(self._data))
        self._data.append(new_row)
        self._error.append(False)
        self.endInsertRows()

    def get_active_archivers(self) -> Dict[str, str]:
        """Return a dictionary of archivers that are enabled."""
        return {n: u for a, n, u in self._data if a}

    def get_all_archivers(self) -> Dict[str, str]:
        """Return a dictionary of all archivers."""
        return {n: u for _, n, u in self._data}

    @Slot(QNetworkReply)
    def archiver_validation(self, reply: QNetworkReply):
        """Recieves a network reply to check the validity of the entered
        archiver URL."""
        index = reply.property("index")

        error = reply.error() != QNetworkReply.NoError or not index

        if error:
            logger.error("Invalid Network Reply recieved")

        self._data[index.row()][index.column()] = not error
        self.dataChanged.emit(index, index)

        last_index = self.index(index.row(), self.columnCount() - 1)
        self._error[index.row()] = error
        self.dataChanged.emit(index, last_index, [Qt.ForegroundRole])

        reply.deleteLater()
