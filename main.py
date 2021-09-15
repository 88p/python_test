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
    cb = ttk.Combobox(WindowRoot,values=readData.columns.values.tolist())
    cb.set(readData.columns.values.tolist()[0])
    cb.bind(
        '<<ComboboxSelected>>', 
        lambda e: print('v=%s' % v.get()))
    cb.grid(row=10, column=0)

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
    labelTop = tk.Label(WindowRoot,text = "Select the csv header you want to get")
    labelTop.grid(column=0, row=0)
    #Frame
    frame = ttk.Frame(WindowRoot, padding=0)
    frame.grid()
    emptyList = ["empty"]
    cb = ttk.Combobox(WindowRoot,values=emptyList)
    cb.set(emptyList[0])
    cb.grid(row=10, column=0)


    # Button
    button1 = ttk.Button(
        frame, text='OK', 
        command=lambda: print('v=%s' % v.get()))
    button1.grid(row=20, column=1)

    FileSelectButton = ttk.Button(frame,text="Select File", command=OpenDialog)
    FileSelectButton.grid(row=30, column=0)


    #window status
    WindowRoot.mainloop()