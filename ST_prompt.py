import tkinter as tk
from tkinter import filedialog, messagebox
import json
import copy
import sys
from PyQt6.QtWidgets import (
    QApplication, QWidget, QListWidget, QTextEdit,
    QPushButton, QHBoxLayout, QVBoxLayout, QLabel, QFileDialog, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

class PromptEditor(QWidget):
    #__init__ 初始化
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Editor")
        self.resize(900, 600)

        self.data_v1= [] #儲存prompt的json資料(原版)
        self.data_v2= [] #複製版, 提供修改用

        # 綁定關閉視窗事件
        #self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        self.current_index = None   #目前選擇的prompt

        self.create()       #子程序create = 建立UI
        self.load_json()    #子程序load_json = 讀取json

    def create(self):
            # 左側導覽列區塊
            self.nav_frame = QWidget()
            self.nav_frame.setFixedWidth(250)
            self.nav_frame.setStyleSheet("background-color: #ffffff;")
            nav_layout = QVBoxLayout()
            nav_layout.setContentsMargins(5,5,5,5)
            nav_layout.setSpacing(10)
            self.nav_frame.setLayout(nav_layout)

             # ListBox (QListWidget)
            self.prompt_listbox = QListWidget()
            self.prompt_listbox.setFont(QFont("Helvetica", 12))
            nav_layout.addWidget(self.prompt_listbox)

            # 選擇事件
            self.prompt_listbox.currentRowChanged.connect(self.prompt_select)

            # 重新載入按鈕
            self.load_button = QPushButton("重新載入json")
            self.load_button.clicked.connect(self.load_json)
            nav_layout.addWidget(self.load_button)

            # 儲存按鈕
            self.save_btn = QPushButton("儲存")
            self.save_btn.clicked.connect(self.save_v2)
            nav_layout.addWidget(self.save_btn)

            # 改背景顏色按鈕-黑暗模式
            self.bg_button = QPushButton("黑暗模式")
            self.bg_button.clicked.connect(lambda: self.change_bg_color("#2E2E2E","#ffffff","#525252"))
            nav_layout.addWidget(self.bg_button)

            #改背景顏色-白天模式
            self.bg_button = QPushButton("白天模式")
            self.bg_button.clicked.connect(lambda: self.change_bg_color("#ffffff","#000000","#fcfcfc"))
            nav_layout.addWidget(self.bg_button)

            # 右側編輯區域
            self.edit_frame = QWidget()
            edit_layout = QVBoxLayout()
            edit_layout.setContentsMargins(5,5,5,5)
            edit_layout.setSpacing(10)
            self.edit_frame.setLayout(edit_layout)

            # Label1
            self.label1 = QLabel("Prompt內容(不可修改)")
            self.label1.setFont(QFont("Helvetica", 12, QFont.Weight.Bold))
            edit_layout.addWidget(self.label1, alignment=Qt.AlignmentFlag.AlignLeft)

            # text_area1 (唯讀)
            self.text_area1 = QTextEdit()
            self.text_area1.setFont(QFont("Courier", 10))
            self.text_area1.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)  # 自動換行
            self.text_area1.setReadOnly(True)
            self.text_area1.setFixedHeight(300)  # 約等於 Tkinter height=15 行
            edit_layout.addWidget(self.text_area1)

            # Label2
            self.label2 = QLabel("修改區")
            self.label2.setFont(QFont("Helvetica", 12, QFont.Weight.Bold))
            edit_layout.addWidget(self.label2, alignment=Qt.AlignmentFlag.AlignLeft)

            # text_area2 (可編輯)
            self.text_area2 = QTextEdit()
            self.text_area2.setFont(QFont("Courier", 10))
            self.text_area2.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
            
            self.text_area2.setFixedHeight(300)
            self.text_area2.textChanged.connect(self.on_text_modified)
            edit_layout.addWidget(self.text_area2)

            # 修改偵測
            self.text_area2.document().setModified(False) #檢查是否儲存
            self.text_area2.textChanged.connect(self.on_text_modified)

            # 主畫面佈局，左右排
            main_layout = QHBoxLayout()
            main_layout.addWidget(self.nav_frame)
            main_layout.addWidget(self.edit_frame, 1)

            self.setLayout(main_layout)

    def change_bg_color(self, color, font_color, box_color):
        widgets_to_update = [
                self.nav_frame,
                self.label1,
                self.label2,
                self,
                self.edit_frame,
            ]
        text_area_update = [
                self.text_area1,
                self.text_area2,
                self.bg_button,
                self.save_btn,
                self.load_button,
                self.prompt_listbox,
            ]
        
        for widget in widgets_to_update:
            widget.setStyleSheet(f"color: {font_color}; background-color: {color};")
        
        #self.prompt_listbox.setStyleSheet(f"background-color: {box_color};")
        
        for tarea in text_area_update:
            tarea.setStyleSheet(f"background-color: {box_color};")


    def on_text_modified(self):
        if self.text_area2.document().isModified():
            self.setWindowTitle("Editor-尚未儲存")
        else:
            self.setWindowTitle("Editor")

            #self.text_area2.edit_modified(False)

    #載入json
    def load_json(self):
            #彈出視窗載入json
            #options = QFileDialog.Options()
            filepath, _ = QFileDialog.getOpenFileName(self, "選擇 JSON 檔案", "", "JSON Files (*.json);;All Files (*)")
            #沒選就跳出
            if not filepath:
                    return
            
            try:
                #開啟檔案 = 使用json.load載入
                with open(filepath, "r", encoding="utf-8") as file_data:
                    raw = json.load(file_data)
                    order_data = raw.get("prompt_order",[])

                    #抓取未排序的prompt
                    self.data_v1 = raw.get("prompts",[])

                    #存放order
                    order_list = []
                    #group = character_id => 尋找character_id
                    for group in order_data:
                        #如果找到100001
                        if group.get("character_id") == 100001:
                            #取得order清單
                            order_ids = group.get("order",[])
                            #建立一個dict字典, 存放每個prompt的identifier
                            prompt_dict = {
                                p.get("identifier"): p for p in self.data_v1
                            }
                            
                            #取出order清單
                            for item in order_ids:
                                #取出indentifier
                                ident = item.get("identifier")
                                enabled = item.get("enabled",True)
                                
                                #檢查identifier是否存在dict中 -> true
                                if ident in prompt_dict:
                                    prompt = prompt_dict[ident] #抓出prompt(整個)
                                    order_list.append(prompt)   #放到order list

                            #找到適合的character_id就結束
                            break 
                    
                    #存放prompt
                    self.data_v1 = order_list                   #根據order_list排序
                    self.data_v2 = copy.deepcopy(self.data_v1)  #複製一個可編輯版本

                    #清空listbox(初始化)
                    self.prompt_listbox.clear()

                    #把prompt的標題名放進list中(附贈是否開啟)
                    '''
                    for prompt in self.data_v1:
                        name = prompt.get("name", "未命名")
                        enabled = prompt.get("enabled", True)
                        if not enabled:
                            name = f"❌ {name}"
                        else:
                            name = f"✅ {name}"
                        self.prompt_listbox.insert(tk.END, name)
                    '''

                    #把prompt的標題名放進list中
                    for prompt in self.data_v1:
                        name = prompt.get("name", "未命名")
                        self.prompt_listbox.addItem(name)
                        

            #error訊息
            except Exception as e:
                QMessageBox.critical(self, "錯誤", f"讀取檔案失敗: {e}")

    #偵測是否不可修改
    def detect_ReadOnly(self, index, prompt_content):
            no_change_list = ["chatHistory", "worldInfoAfter", "worldInfoBefore", "dialogueExamples", "charDescription", "charPersonality", "scenario", "personaDescription", ]
            
            ident = self.data_v2[index].get("identifier","")
            
            if ident in no_change_list:
                return True, "此條目不可修改"
            else:
                return False, prompt_content
    #點擊prompt
    def prompt_select(self, index):
        #告知目前點擊哪一行
        if index < 0 or index >= len(self.data_v1):
            return
        
        #暫存上一筆
        if self.current_index is not None:
            self.save_current_v2_edit()

        #index = selection[0]        #目前位置(點選哪一行的prompt)
        self.current_index = index  #存放目前位置到self的cureent index裏面 ->方便日後再次調用

        #顯示prompt內容(v1)
        prompt_v1 = self.data_v1[index].get("content","")
        change, PlainText = self.detect_ReadOnly(index, prompt_v1)
        self.text_area1.setReadOnly(False)
        self.text_area1.setPlainText(PlainText)
        self.text_area1.setReadOnly(True)
        self.label1.setText(f"{self.data_v1[index].get("name","")}")
        
        #顯示V2
        prompt_v2 = self.data_v2[index].get("content", "")        
        self.text_area2.setReadOnly(False)
        self.text_area2.setPlainText(prompt_v2)
        self.text_area2.setReadOnly(change)

        #prompt = self.data[index]   #調用index位置的內容出來

    #儲存修改後的json
    def save_v2(self):
        self.save_current_v2_edit()
        if self.current_index is not None:
            update_text = self.text_area2.toPlainText().strip()
            self.data_v2[self.current_index]["content"] = update_text

        #儲存位置
        options = QFileDialog.Options()
        path, _ = QFileDialog.getSaveFileName(self, "儲存修改後的 JSON", "", "JSON Files (*.json);;All Files (*)", options=options)
        if not path:
            return
        #寫入檔案
        try:
            output = {"prompts": self.data_v2}
            with open(path, "w", encoding="utf-8") as f:
                 json.dump(output, f, indent=2, ensure_ascii=False)
            QMessageBox.information(self, "成功", "已儲存")
            self.text_area2.document().setModified(False)
            self.setWindowTitle("Editor")
        except Exception as e:
            QMessageBox.critical(self, "錯誤", f"儲存失敗: {e}")

        self.saved = True
        #self.text_area2.edit_modified(False)

    #暫存
    def save_current_v2_edit(self):
         if self.current_index is not None:
            update_text = self.text_area2.toPlainText().strip()
            self.data_v2[self.current_index]["content"] = update_text
            
    def closeEvent(self,event):
        if self.text_area2.document().isModified():
            reply = QMessageBox.question(self, "尚未儲存", "你尚未保存，確定要離開嗎？", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)

            if reply == QMessageBox.StandardButton.Yes:
                event.accept()  # 允許關閉
            else:
                event.ignore()  # 阻止關閉
        else:
            event.accept()
            


# if __name__ == "__main__" 是標準啟動方式（代表直接執行）
# root = tk.Tk()：創建 GUI 視窗
# root.mainloop()：進入 GUI 主迴圈，讓畫面持續運作
if __name__ == "__main__":
    app = QApplication(sys.argv)
    editor = PromptEditor()
    editor.show()
    sys.exit(app.exec())
    