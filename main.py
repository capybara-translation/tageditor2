#!/usr/bin/env python3
from enum import Enum, auto
import uuid
import pyperclip
from PyQt5 import QtCore
from PyQt5.QtGui import QPen, QColor, QBrush, QLinearGradient, QPainter, QPainterPath
from PyQt5.QtGui import QTextCursor
from PyQt5.QtGui import QTextFormat
from PyQt5.QtGui import QTextCharFormat
from PyQt5.QtGui import QTextObjectInterface, QTextObject, QFontMetrics, QTextDocument
from PyQt5.QtCore import Qt
from PyQt5.QtCore import QObject, QEvent, QMimeData, QRect, QRectF
from PyQt5.QtWidgets import QWidget
from PyQt5.QtWidgets import QLineEdit, QPushButton, QLabel
from PyQt5.QtWidgets import QTextEdit
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QApplication

OBJECT_REPLACEMENT_CHARACTER = 0xfffc
PARAGRAPH_SEPARATOR = 0x2029


class TagKind(Enum):
    START = auto()
    END = auto()
    EMPTY = auto()


class TagTextEdit(QTextEdit):
    def __init__(self, parent=None):
        super(TagTextEdit, self).__init__(parent)
        self.setAcceptRichText(True)
        # self.setStyleSheet('line-height: 120%;')

    def createMimeDataFromSelection(self) -> QtCore.QMimeData:
        mime = QMimeData()
        cursor = self.textCursor()
        if not cursor.hasSelection():
            return mime
        start_pos = cursor.selectionStart()
        end_pos = cursor.selectionEnd()
        doc = self.document()
        substrings = []
        for pos in range(start_pos, end_pos):
            char = doc.characterAt(pos)
            if ord(char) == OBJECT_REPLACEMENT_CHARACTER:
                current_block = doc.findBlock(pos)

                # iterate text fragments within the block
                it = current_block.begin()
                while not it.atEnd():
                    current_fragment = it.fragment()
                    # check if the current position is located within the fragment
                    if current_fragment.contains(pos):
                        char_format = current_fragment.charFormat()
                        # tag_name = char_format.property(TagTextObject.name_propid)
                        substrings.append(TagTextObject.to_string(char_format))
                        break
                    it += 1
            elif ord(char) == PARAGRAPH_SEPARATOR:
                substrings.append('\n')
            else:
                substrings.append(char)
            # print(pos, len(char), char, hex(ord(char)))
        selected_text = ''.join(substrings)
        mime.setText(selected_text)
        return mime

    # def copy_selection_to_clipboard(self, cut=False):
    #     cursor = self.textCursor()
    #     if not cursor.hasSelection():
    #         return
    #     start_pos = cursor.selectionStart()
    #     end_pos = cursor.selectionEnd()
    #     doc = self.document()
    #     substrings = []
    #     for pos in range(start_pos, end_pos):
    #         char = doc.characterAt(pos)
    #         if ord(char) == OBJECT_REPLACEMENT_CHARACTER:
    #             current_block = doc.findBlock(pos)
    #
    #             # iterate text fragments within the block
    #             it = current_block.begin()
    #             while not it.atEnd():
    #                 current_fragment = it.fragment()
    #                 # check if the current position is located within the fragment
    #                 if current_fragment.contains(pos):
    #                     char_format = current_fragment.charFormat()
    #                     tag_name = char_format.property(TagTextObject.name_propid)
    #                     substrings.append(tag_name)
    #                     break
    #                 it += 1
    #         elif ord(char) == PARAGRAPH_SEPARATOR:
    #             substrings.append('\n')
    #         else:
    #             substrings.append(char)
    #         # print(pos, len(char), char, hex(ord(char)))
    #     selected_text = ''.join(substrings)
    #     print(selected_text)
    #     pyperclip.copy(selected_text)
    #     if cut:
    #         cursor.removeSelectedText()


class TagTextObject(QObject, QTextObjectInterface):
    type = QTextFormat.UserObject + 1
    id_propid = 10000
    name_propid = 10001
    kind_propid = 10002

    @staticmethod
    def to_string(char_format: 'QTextCharFormat') -> str:
        name: str = char_format.property(TagTextObject.name_propid)
        kind: TagKind = char_format.property(TagTextObject.kind_propid)
        if kind == TagKind.START:
            return f'{{{name}>'
        if kind == TagKind.END:
            return f'<{name}}}'
        return f'{{{name}}}'

    def intrinsicSize(self, doc: 'QTextDocument', pos_in_document: int, format_: 'QTextFormat') -> QtCore.QSizeF:
        charformat = format_.toCharFormat()
        font = charformat.font()
        fm = QFontMetrics(font)
        tag_name = format_.property(TagTextObject.name_propid)
        sz = fm.boundingRect(tag_name).size()
        sz.setWidth(sz.width() + 12)
        sz.setHeight(sz.height() + 4)
        return QtCore.QSizeF(sz)

    def drawObject(self, painter: 'QPainter', rect: QtCore.QRectF, doc: 'QTextDocument', pos_in_document: int,
                   format_: 'QTextFormat') -> None:
        painter.setRenderHint(QPainter.Antialiasing, True)
        c = QColor(255, 80, 0, 160)
        painter.setBrush(QBrush(c, Qt.SolidPattern))
        painter.setPen(QPen(QtCore.Qt.white, 2, QtCore.Qt.SolidLine))
        tag_kind: TagKind = format_.property(TagTextObject.kind_propid)

        top = rect.top()
        left = rect.left()
        width = rect.width()
        height = rect.height()
        square_size = rect.height() / 2

        if tag_kind == TagKind.START:
            path = QPainterPath()
            path.setFillRule(Qt.WindingFill)
            path.addRoundedRect(rect, 10, 10)

            # QRectF(aleft: float, atop: float, awidth: float, aheight: float)
            bottom_left_rect = QRectF(left, top + height - square_size, square_size, square_size)
            path.addRoundedRect(bottom_left_rect, 2, 2)  # Bottom left

            top_left_rect = QRectF(left, top, square_size, square_size)
            path.addRoundedRect(top_left_rect, 2, 2)  # Top left
            painter.drawPath(path.simplified())
        elif tag_kind == TagKind.END:
            path = QPainterPath()
            path.setFillRule(Qt.WindingFill)
            path.addRoundedRect(rect, 10, 10)

            top_right_rect = QRectF((left + width) - square_size, top, square_size, square_size)
            path.addRoundedRect(top_right_rect, 2, 2)  # Top right

            bottom_right_rect = QRectF((left + width) - square_size, top + height - square_size, square_size,
                                       square_size)
            path.addRoundedRect(bottom_right_rect, 2, 2)  # Bottom right
            painter.drawPath(path.simplified())
        else:
            painter.drawRoundedRect(rect, 4, 4)
        tag_name = format_.property(TagTextObject.name_propid)
        painter.drawText(rect, QtCore.Qt.AlignHCenter | QtCore.Qt.AlignCenter, tag_name)


class KeyEventFilter(QObject):
    def __init__(self):
        super().__init__()
        self.widget = None

    def install_to(self, widget):
        self.widget = widget
        self.widget.installEventFilter(self)

    def eventFilter(self, obj: 'QObject', event: 'QEvent') -> bool:
        # print('eventFilter', event.type())
        if obj == self.widget and event.type() == QEvent.KeyPress:
            modifiers = QApplication.keyboardModifiers()
            if modifiers == QtCore.Qt.ControlModifier and event.key() == Qt.Key_C:
                print('ctrl+c')
                obj.copy_selection_to_clipboard()
                return True
            if modifiers == QtCore.Qt.ControlModifier and event.key() == Qt.Key_X:
                print('ctrl+x')
                obj.copy_selection_to_clipboard(cut=True)
                return True
        return QObject.eventFilter(self, obj, event)


class MouseEventFilter(QObject):
    def __init__(self):
        super().__init__()
        self.widget = None

    def install_to(self, widget):
        self.widget = widget
        self.widget.installEventFilter(self)

    def eventFilter(self, obj: 'QObject', event: 'QEvent') -> bool:
        return QObject.eventFilter(self, obj, event)


class ExampleWindow(QWidget):
    APPID = str(uuid.uuid4())

    def __init__(self):
        super().__init__()
        self.setWindowTitle('Example window')
        self.tageditor = TagTextEdit()
        self.tageditor.APPID = self.APPID
        self.tageditor.setAlignment(QtCore.Qt.AlignVCenter)

        self.zoomInButton = QPushButton()
        self.zoomInButton.setText('↑')
        self.zoomInButton.clicked.connect(self.zoom_in)

        self.zoomOutButton = QPushButton()
        self.zoomOutButton.setText('↓')
        self.zoomOutButton.clicked.connect(self.zoom_out)

        layout = QVBoxLayout()
        layout.addWidget(self.tageditor)
        layout.addWidget(self.zoomInButton)
        layout.addWidget(self.zoomOutButton)
        self.setLayout(layout)

        self.register_tag_type()

        cursor = self.tageditor.textCursor()

        self.insert_tag(cursor, '1', 'image', TagKind.EMPTY)
        cursor.insertText('start\n')

        cursor.insertText('\n\n')
        self.insert_tag(cursor, '1', 'bold', TagKind.START)
        cursor.insertText('some bold text')
        self.insert_tag(cursor, '1', 'bold', TagKind.END)

        self.insert_tag(cursor, '2', 'italic', TagKind.START)
        cursor.insertText('some italic text')
        self.insert_tag(cursor, '2', 'italic', TagKind.END)

        self.insert_tag(cursor, '3', 'underline', TagKind.START)
        self.insert_tag(cursor, '3', 'underline', TagKind.END)

        cursor.insertText('\n\n')
        cursor.insertText('end')
        self.insert_tag(cursor, '4', 'image', TagKind.EMPTY)
        self.tageditor.setTextCursor(cursor)

        # self.key_event_filter = KeyEventFilter()
        # self.key_event_filter.install_to(self.tageditor)

        # self.tageditor.currentCharFormatChanged.connect(self.on_character_format_change)
        # self.tageditor.selectionChanged.connect(self._trigger_obj_char_rescan)
        self.tageditor.textChanged.connect(self.on_text_changed)

    def zoom_in(self):
        self.tageditor.zoomIn(1)

    def zoom_out(self):
        self.tageditor.zoomOut(1)

    def register_tag_type(self):
        document_layout = self.tageditor.document().documentLayout()
        document_layout.registerHandler(TagTextObject.type, TagTextObject(self))

    def insert_tag(self, cursor, name, content, kind):
        char_format = QTextCharFormat()
        char_format.setProperty(TagTextObject.name_propid, name)
        char_format.setProperty(TagTextObject.id_propid, uuid.uuid4())
        char_format.setProperty(TagTextObject.kind_propid, kind)
        char_format.setToolTip(content)
        char_format.setObjectType(TagTextObject.type)
        char_format.setVerticalAlignment(QTextCharFormat.AlignTop)
        cursor.insertText(chr(OBJECT_REPLACEMENT_CHARACTER), char_format)

    def on_text_changed(self):
        self.tageditor.textCursor().beginEditBlock()
        blocked = self.tageditor.blockSignals(True)
        doc = self.tageditor.document()
        pattern = QtCore.QRegExp(r'\{\d{1,2}\}|\{\d{1,2}>|<\d{1,2}\}')
        cursor = QTextCursor(doc)
        while True:
            cursor = doc.find(pattern, cursor)
            if cursor.isNull():
                break
            matched_str = cursor.selectedText()
            if matched_str.endswith('>'):
                tag_name = cursor.selectedText().strip('{>')
                self.insert_tag(cursor, tag_name, tag_name, TagKind.START)
            elif matched_str.startswith('<'):
                tag_name = cursor.selectedText().strip('<}')
                self.insert_tag(cursor, tag_name, tag_name, TagKind.END)
            else:
                tag_name = cursor.selectedText().strip('{}')
                self.insert_tag(cursor, tag_name, tag_name, TagKind.EMPTY)

        self.tageditor.textCursor().endEditBlock()
        self.tageditor.blockSignals(blocked)


if __name__ == '__main__':
    import sys

    app = QApplication(sys.argv)
    window = ExampleWindow()
    window.show()
    sys.exit(app.exec_())
