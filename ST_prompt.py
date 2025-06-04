import tkinter as tk
from tkinter import filedialog, messagebox
import json
import copy

class PromptEditor:
    #__init__ 初始化
    def __init__(self,root):
        self.root = root    #主視窗
        self.root.title("Editor")   
        self.root.geometry("900x600")

        self.data_v1= [] #儲存prompt的json資料(原版)
        self.data_v2= [] #複製版, 提供修改用

        self.saved = False #檢查是否儲存

        # 綁定關閉視窗事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        self.current_index = None   #目前選擇的prompt

        self.create()       #子程序create = 建立UI
        self.load_json()    #子程序load_json = 讀取json

    def create(self):
            #導覽列(左)
            self.nav_frame= tk.Frame(self.root, width=250, bg="#ffffff")
            self.nav_frame.pack(side=tk.LEFT, fill=tk.Y)    #fill=tk.Y 沾滿整個Y

            #選單
            self.prompt_listbox= tk.Listbox(self.nav_frame, font=("Helvetica", 12))
            self.prompt_listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            #User點擊
            self.prompt_listbox.bind("<<ListboxSelect>>", self.prompt_select)  

            #重新載入
            self.load_button = tk.Button(self.nav_frame, text="重新載入json", command=self.load_json)
            self.load_button.pack(pady=10)

            #儲存
            self.save_btn = tk.Button(self.nav_frame, text="儲存", command=self.save_v2)
            self.save_btn.pack(pady=5)

            #編輯區(右)
            #Label1
            self.edit_frame = tk.Frame(self.root)
            self.edit_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

            self.label1= tk.Label(self.edit_frame, text="Prompt內容", font=("Helvetica", 12, "bold"))
            self.label1.pack(anchor='w', padx=5, pady=(5,0)) #?

            #tk.WORD = 自動換行 // Courier=等寬字體
            self.text_area1 = tk.Text(self.edit_frame, height=15, wrap=tk.WORD, font=("Courier", 10))
            self.text_area1.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0,10))
            #不能修改
            self.text_area1.configure(state=tk.DISABLED)

            #Label2 = 可以用來對比編輯用
            self.label2= tk.Label(self.edit_frame, text="修改區", font=("Helvetica", 12, "bold"))
            self.label2.pack(anchor='w', padx=5, pady=(5,0)) #?
            self.text_area2 = tk.Text(self.edit_frame, height=15, wrap=tk.WORD, font=("Courier", 10))
            self.text_area2.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0,10))
            self.text_area2.bind("<<Modified>>", self.on_text_modified) #檢查是否修改

    def on_text_modified(self, event):
        if self.text_area2.edit_modified():
            if self.saved:
                print("內容已修改")
            self.saved = False

            self.text_area2.edit_modified(False)

    #載入json
    def load_json(self):
            #彈出視窗載入json
            filepath = filedialog.askopenfilename(filetypes=[("*.json","JSON files")])
            #沒選就跳出
            if not filepath:
                    return
            
            try:
                #開啟檔案 = 使用json.load載入
                with open(filepath, "r", encoding="utf-8") as file_data:
                    raw = json.load(file_data)
                    #存放prompt
                    self.data_v1 = raw.get("prompts",[])
                    self.data_v2 = copy.deepcopy(self.data_v1)  #複製一個可編輯版本
                    
                    #清空listbox(初始化)
                    self.prompt_listbox.delete(0, tk.END)

                    #把prompt的標題名放進list中
                    for prompt in self.data_v1:
                        name = prompt.get("name","未命名")
                        self.prompt_listbox.insert(tk.END, name)

            #error訊息
            except Exception as e:
                messagebox.showerror("Error", f"讀取檔案失敗: {e}")

    #點擊prompt
    def prompt_select(self, event):
        #告知目前點擊哪一行
        selection = self.prompt_listbox.curselection()
        if not selection:
            return
        
        #暫存上一筆
        if self.current_index is not None:
            self.save_current_v2_edit()

        index = selection[0]        #目前位置(點選哪一行的prompt)
        self.current_index = index  #存放目前位置到self的cureent index裏面 ->方便日後再次調用

        #顯示prompt內容(v1)
        prompt_v1 = self.data_v1[index].get("content","")
        self.text_area1.configure(state=tk.NORMAL)
        self.text_area1.delete("1.0", tk.END)
        self.text_area1.insert(tk.END, prompt_v1)
        self.text_area1.configure(state=tk.DISABLED)

        #顯示V2
        prompt_v2 = self.data_v2[index].get("content","")
        self.text_area2.delete("1.0", tk.END)
        self.text_area2.insert(tk.END, prompt_v2)

        #prompt = self.data[index]   #調用index位置的內容出來

    #儲存修改後的json
    def save_v2(self):
        self.save_current_v2_edit()
        if self.current_index is not None:
              update_text = self.text_area2.get("1.0", tk.END).strip()
              self.data_v2[self.current_index]["content"] = update_text

        #儲存位置
        path = filedialog.asksaveasfilename(defaultextension=".json",
                                            filetypes=[("json檔案", "*.json")],
                                            title="儲存修改後的json")
        if not path:
            return
        #寫入檔案
        try:
            output = {"prompts": self.data_v2}
            with open(path, "w", encoding="utf-8") as f:
                 json.dump(output, f, indent=2, ensure_ascii=False)
            messagebox.showinfo("成功",f"已儲存")
        except Exception as e:
            messagebox.showerror("錯誤",f"儲存失敗:{e}")

        self.saved = True
        self.text_area2.edit_modified(False)

    #暫存
    def save_current_v2_edit(self):
         if self.current_index is not None:
              update_text = self.text_area2.get("1.0", tk.END).strip()
              self.data_v2[self.current_index]["content"] = update_text
            
    def on_close(self):
        if not self.saved:
            answer = messagebox.askyesno("尚未儲存", "你尚未保存，確定要離開嗎？")
            if not answer:
                return  # 使用者取消關閉
        self.root.destroy()  # 關閉視窗
            


# if __name__ == "__main__" 是標準啟動方式（代表直接執行）
# root = tk.Tk()：創建 GUI 視窗
# root.mainloop()：進入 GUI 主迴圈，讓畫面持續運作
if __name__ == "__main__":
    root=tk.Tk()
    app = PromptEditor(root)
    root.mainloop()
    