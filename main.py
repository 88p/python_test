# -*- coding: utf-8 -*-

from typing import List
import pandas as pd
import xml.etree.ElementTree as ET
import numpy as np
import urllib
import urllib.request
from pandas.core.dtypes.missing import notnull
import xmljson
import tkinter as tk
from tkinter import *
from tkinter import ttk
from tkinter import filedialog

class Analytics:
    #pandasでCSVからデータを読み込む
    def DataRead_csv(filePath):
        df = pd.read_csv(filePath)
        return df
    #最新値を読み出す
    def GetData_LatestValue(df):
        result = df
        return result




def OpenDialog():
    filename = filedialog.askopenfilename(
        title="データを開く",
        filetypes=[("CSV File",".csv"),("XMLデータ",".xml"),("JSONデータ",".json")],
        initialdir="./" #Current Dir
    )
    
    #Fileの取得
    readData = DataAnalytics.DataRead_csv(filename) #CSVからデータ取得
    LatestValueData = DataAnalytics.GetData_LatestValue(readData) #最新値取得

    #ComboBox
    v = tk.StringVar()
    
    #テスト
    cb = ttk.Combobox(WindowRoot,values=readData.columns.values.tolist())
    cb.set(readData.columns.values.tolist()[0])
    cb.bind(
        '<<ComboboxSelected>>', 
        lambda e: print('v=%s' % v.get()))
    cb.grid(row=10, column=0)
    
    #重複排除をしたいデータ
    cb_recentry = ttk.Combobox(WindowRoot,values=readData.columns.values.tolist())
    cb_recentry.set(readData.columns.values.tolist()[0])
    cb_recentry.bind(
        '<<ComboboxSelected>>', 
        lambda e: print('v=%s' % v.get()))
    cb_recentry.grid(row=20, column=0)

    #重複排除をしたいデータ
    cb_recentry2 = ttk.Combobox(WindowRoot,values=readData.columns.values.tolist())
    cb_recentry2.set(readData.columns.values.tolist()[0])
    cb_recentry2.bind(
        '<<ComboboxSelected>>', 
        lambda e: print('v=%s' % v.get()))
    cb_recentry2.grid(row=30, column=0)
    return filename #FullPath


if __name__ == '__main__':

    #Create instance
    DataAnalytics = Analytics

    #Create window
    WindowRoot = tk.Tk()
    #Window Size Setting
    WindowRoot.geometry("600x800")
    #name
    WindowRoot.title('CSV Spliter')
    #Label
    labelTop = tk.Label(WindowRoot,text = "元データ選択")
    labelTop.grid(column=0, row=0)
    #Frame
    frame = ttk.Frame(WindowRoot, padding=0)
    frame.grid()
    emptyList = ["empty"]
    cb = ttk.Combobox(WindowRoot,values=emptyList)
    cb.set(emptyList[0])
    cb.grid(row=10, column=0)


    # Button
    #button1 = ttk.Button(
    #    frame, text='OK', 
    #    command=lambda: print('v=%s' % v.get()))
    #button1.grid(row=20, column=1)

    FileSelectButton = ttk.Button(frame,text="Select File", command=OpenDialog)
    FileSelectButton.grid(row=30, column=0)

    #Label
    frame2 = ttk.Frame(WindowRoot,padding=1)
    label_frame2 = tk.Label(WindowRoot,text="最新値抽出")
    label_frame2.grid()
    #重複を排除したいデータ
    #label
    label_frame_cb = tk.Label(WindowRoot,text="固有番号")
    label_frame_cb.grid(row=20,column=1)
    #comboBox
    cb_recentry = ttk.Combobox(WindowRoot,values=emptyList)
    cb_recentry.set(emptyList[0])
    cb_recentry.grid(row=20, column=0)

    #日付データ
    #label
    label_frame_cb2 = tk.Label(WindowRoot,text="日付")
    label_frame_cb2.grid(row=30,column=1)
    #comboBox
    cb_recentry2 = ttk.Combobox(WindowRoot,values=emptyList)
    cb_recentry2.set(emptyList[0])
    cb_recentry2.grid(row=30, column=0)

    # Button
    start1 = tk.StringVar()
    button1 = ttk.Button(
        frame2, text='実行',
        command=lambda: print('v=%s' % start1.get()))
    button1.grid(row=30, column=0)
    frame2.grid()


    #window status
    WindowRoot.mainloop()