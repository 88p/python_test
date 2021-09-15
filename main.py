# -*- coding: utf-8 -*-

import pandas as pd
import xml.etree.ElementTree as ET
import numpy as np
import urllib
import urllib.request
import xmljson

class Analytics:
    #CSVからデータを読み込む
    def DataRead_csv(filePath):
        print("test")
        print(filePath)




#setting
filepath = "./alt_fuel_stations (Sep 15 2021).csv"

DataAnalytics = Analytics
DataAnalytics.DataRead_csv(filepath)