from geopy.distance import geodesic
import pandas as pd
import numpy as np
import csv


#read csv 


data = pd.read_csv('alt_fuel_stations (Mar 13 2023).csv')
dataList = [["LatitudeA","LongitudeA","Station NameA","CityA","StateA","LatitudeB","LongitudeB","Station NameB","CityB","StateB","distance"]]
data.head()
#data kyori keisan
for i in range(0, len(data)):
    print("loop num:"+str(i)+"  dataList num:"+str(len(dataList)))
    for j in range(0,len(data)):
        #iとjが同じならbreak
        if(i==j):
            break
        pointA = ((data.at[i, 'Latitude']), (data.at[i, 'Longitude']))
        pointB = ((data.at[j, 'Latitude']), (data.at[j, 'Longitude']))
        x = geodesic(pointA, pointB).mi
        if(x > 100):
            continue
        #data.at[0+i, 'distance'] = x
        dataList.append([data.at[i, 'Latitude'],data.at[i, 'Longitude'],data.at[i, 'Station Name'],data.at[i, 'City'],data.at[i, 'State'],data.at[j, 'Latitude'],data.at[j, 'Longitude'],data.at[j, 'Station Name'],data.at[j, 'City'],data.at[j, 'State'],x])

with open("test.csv",'w',newline="",encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerows(dataList)



print("END")