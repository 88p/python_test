from asyncio.windows_events import NULL
from cmath import nan
from operator import index
from wsgiref import headers
from numpy import NaN, empty
import pandas as pd
import sys
import os

SKIPROWS = 0 #最初何行飛ばしたところから始めるか
SKIPFOOTER = 0 #最後何行飛ばすか
USECOL = "A:D" #読み込み列を指定

def main(filePath):
    if str(filePath).endswith('.xlsx') == False:
        print("Not Excel File")
        quit()
    input_book = pd.read_excel(filePath,header=None,sheet_name="Sheet1",skiprows=SKIPROWS,skipfooter=SKIPFOOTER,usecols=USECOL)
    #sheet_namesメソッドでExcelブック内の各シートの名前をリストで取得できる
    print(input_book)
    
    keepindex = []
    folderList = []
    #loop
    for loop in input_book.itertuples():
        templist = []
        for index,loop2 in enumerate(loop):
            if index == 0:
                continue
            print(index)
            print(loop2)
            if loop2 is NaN:
                templist.append("")
            else:
                templist.append(loop2)
        folderList.append(templist)
            
    #フォルダパスを作る
    for i, folders in enumerate(folderList):
        list = []
        for j, folder in enumerate(folders):
            if folder != '':
                list.append(folderList[i][j])
            elif j != 0:
                if folder != '':
                    list.append(folderList[i][j])
                else:
                    list.append(folderList[i-1][j])
            else:
                list.append(folderList[i-1][j])

        folderList[i] = list    
    
    print(folderList)
    
    
    
    
if __name__ =='__main__':
    args = sys.argv
    
    if (type(args[1]) is str):
        main(args[1])
    else:
        print("Not Filepath")
        quit()