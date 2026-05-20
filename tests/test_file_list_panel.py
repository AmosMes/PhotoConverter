import pytest
from PySide6.QtWidgets import QPushButton, QListWidgetItem
from ui.file_list_panel import FileListPanel


def _find_button(panel: FileListPanel, label: str) -> QPushButton | None:
    for btn in panel.findChildren(QPushButton):
        if btn.text() == label:
            return btn
    return None


def test_single_mode_has_clear_button(qapp):
    panel = FileListPanel(multi=False)
    assert _find_button(panel, "Clear") is not None


def test_single_clear_empties_list_and_emits(qapp):
    panel = FileListPanel(multi=False)
    # Inject a fake item directly
    panel._list.addItem(QListWidgetItem("fake.jpg"))
    panel._list.item(0).setData(256, "/fake/fake.jpg")

    emitted = []
    panel.files_changed.connect(lambda: emitted.append(True))

    _find_button(panel, "Clear").click()

    assert panel._list.count() == 0
    assert emitted == [True]


def test_batch_mode_has_clear_all_button(qapp):
    panel = FileListPanel(multi=True)
    assert _find_button(panel, "Clear All") is not None


def test_batch_clear_all_empties_list_and_emits(qapp):
    panel = FileListPanel(multi=True)
    for name in ("a.jpg", "b.jpg"):
        item = QListWidgetItem(name)
        item.setData(256, f"/fake/{name}")
        panel._list.addItem(item)

    emitted = []
    panel.files_changed.connect(lambda: emitted.append(True))

    _find_button(panel, "Clear All").click()

    assert panel._list.count() == 0
    assert emitted == [True]
