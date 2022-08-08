import pandas as pd
import xml.etree.ElementTree as et
import openpyxl

def xml2data():
    tree = et.parse("test1.xml")
    root = tree.getroot()
    print(root.tag)
    print(root.attrib)
    cdata_list = []
    for country in root:
        # 子要素の中身を解析
        name = country.attrib["name"]
        rank = ""
        for child in country.iter():
            print(child)
            # 特定要素の抽出
            if child.tag == 'rank':
                # ファイル名、国名、ランクを出力
                rank = child.text
                print(
                    f'{name},{rank}')
                cdata = [name, rank]
                cdata_list.append(cdata)
                
def xlsx_input():
    wb = openpyxl.load_workbook('book1.xlsx')
    for sheets in wb.sheetnames:
        sheet = wb[sheets]
        sheet['B2'] = 'test1'
        mergedcell = sheet.merged_cells.ranges
        
        for mr in mergedcell:
            print(mr)
            sp_data = str(mr).split(":")
            sheet[sp_data[0]].value = "test"
    wb.save('book1.xlsx')


if __name__ == '__main__':
    #xml2data()
    xlsx_input()