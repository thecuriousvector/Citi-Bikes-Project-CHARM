from __future__ import print_function
#import sys
#import re
#from operator import add
from pyspark import SparkContext
from pyspark.sql import SQLContext
from pyspark.sql import Row
#import os
#from operator import add
#import random
from IPython.display import display
import numpy as np
import pandas as pd
import matplotlib as mpl
from pandas import datetime
mpl.use('Agg')
from matplotlib import pyplot
pyplot.ioff()
#%matplotlib inline 

sc = SparkContext()
sqlContext = SQLContext(sc)
#os.environ['QT_QPA_PLATFORM']='offscreen'

''' Pre-process the data to select a particular dock and required columns from CSV 
	line[0] = dock_id
	line[1] = dock_name
	line[2] = date
	line[3] = hour
	line[4] = minute
	line[5] = pm
	line[6] = avail_bikes '''
def readDockData(line):
	line = line.split('\t')
	return [line[0], line[1], line[2], line[3], line[4], line[5], line[6]]		


''' For making date as the primary key and hour as the key for inner tuples
    Also, convert time into 24 hour format '''
'''def makeDateAsKey(line):
	if (line[5] == str(1)):
		hour = int(line[3]) + 12
		if (hour == 24):
			hour = 0
		return ((line[2], int(hour)), int(line[6]))
	elif (line[5] == str(0)):
		return ((line[2], int(line[3])), int(line[6]))
'''
def makeDateAsKey(line):
        if (line[5] == str(1)):
                hour = int(line[3])
                return ((line[2], int(hour), 'PM'), int(line[6]))
        elif (line[5] == str(0)):
                return ((line[2], int(line[3]), 'AM'), int(line[6]))
''' Format date '''
def formatDate(date, hour,isPm):
	date = date.split('\"')[1]
	if (hour < 10):
		hour = "0"+str(hour)+":00:00"
	else:
		hour = str(hour)+":00:00"
	x = date + " " + hour + " " + isPm
	return datetime.strptime('20'+x, '%Y-%m-%d %I:%M:%S %p')

''' Variables '''
dataDir_test = "/user/rdv253/DS/Baseline/Test/*"
dockID = 379  #Dock of interest


data = sc.textFile(dataDir_test)
data = data.map(lambda line: readDockData(line))

dock_data = data.filter(lambda line: line[0] == str(dockID))
dock_data_tuple = dock_data.map(lambda line: makeDateAsKey(line))

## There might be more than one record available for every hour. 
## Hence consider the least no of bikes present in an hour's interval
dock_data_per_day = dock_data_tuple.reduceByKey(lambda x,y: min(x,y))
dock_data_per_day = dock_data_per_day.map(lambda ((x,y,p),z): (x,y,p,z))

data_test = dock_data_per_day.map(lambda (date, hour, isPm, bikes): (formatDate(date,hour,isPm),bikes))

data_test_df = data_test.map(lambda row: Row(timestamp=row[0], avail_bikes=row[1]))
data_test_df = sqlContext.createDataFrame(data_test_df)
sqlContext.registerDataFrameAsTable(data_test_df, "test_table")
test_df = sqlContext.sql("Select * from test_table")
test_df = test_df.toPandas()
test_df = test_df.sort_values(by='timestamp')
test_df.to_csv('test_379.csv', sep='\t')
test_series = pd.Series(test_df['avail_bikes'].values, index=test_df['timestamp'])
print(len(test_df))
