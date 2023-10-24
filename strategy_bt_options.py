#!/usr/bin/env python
# coding: utf-8

# In[23]:


import numpy as np
import pandas as pd
import pandas_datareader as web
import matplotlib.pyplot as plt
import matplotlib.style
import datetime as dt

symbol = "BANKNIFTY"
startTimeHour = 9
startTimeMinute = 59
startTime = dt.time(startTimeHour,startTimeMinute)
endTimeHour = 14
endTimeMinute = 59
endTime = dt.time(endTimeHour,endTimeMinute)
noOfEntry = 1
noOfLegs = 2
#{call/put(0), buy/sell(1), qty(2), atm/premium (3), strike value (4), individual stoploss in percent (5), individual target (6), trail_x (7), trail_y (8), momentum_up_down (9), momentum_points in percentage (10)}
leg1 = ['CE', 'S', 50, 'ATM', 100, 0.10, 0, 0, 0, 'D', 0.20]
leg2 = ['PE', 'S', 50, 'ATM', -100, 0.10, 0, 0, 0, 'D', 0.20]


# In[24]:



def findExpiryFormat(indexDate):
    #Monthly expiry format is YYMMM
    #Weekly expiry format is YYMDD
    expiry = "YYMDD"

    # Calculate the day of the week (0 = Monday, 1 = Tuesday, ..., 6 = Sunday)
    day_of_week = indexDate.weekday()

    # Calculate the day of the week (0 = Monday, 1 = Tuesday, ..., 6 = Sunday)
    day_of_week = indexDate.weekday()

    # Calculate the number of days to the next Thursday
    days_to_next_thursday = (3 - day_of_week) % 7

    # Calculate the next closest Thursday date
    next_thursday = indexDate + dt.timedelta(days=days_to_next_thursday)

    # Check if next_thursday is the last Thursday of the month
    last_thursday_of_month = (next_thursday + dt.timedelta(days=7)).month != next_thursday.month

    # Format the date into YYMDD or YYMMM format
    year = next_thursday.strftime("%y")
    month = next_thursday.strftime("%m")
    day = next_thursday.strftime("%d")
    month_abbreviated = next_thursday.strftime("%b")  # Abbreviated month name (first 3 letters)

    formatted_date = ""

    if last_thursday_of_month:
        formatted_date = year + month_abbreviated.upper()
    else:
        month_mapping = {
            '01': '1', '02': '2', '03': '3', '04': '4', '05': '5', '06': '6',
            '07': '7', '08': '8', '09': '9', '10': 'O', '11': 'N', '12': 'D'
        }
        formatted_month = month_mapping[month]
        formatted_date = year + formatted_month + day

    print("Next Thursday:", next_thursday)
    print("Formatted Date:", formatted_date)

    return formatted_date


# In[25]:


def findStrikePrice(indexPrice, leg, expiry, indexDateTime):
    strikeType = leg[3]
    strikeValue = leg[4]
    strikePrice = 0

    if strikeType == "ATM":
        if symbol == "NIFTY":
            strikePrice = int(round((indexPrice/50),0)*50)
        elif symbol == "BANKNIFTY":
            strikePrice = int(round((indexPrice/100),0)*100)

        if (leg[0].upper() == "CE"):
            strikePrice = strikePrice + strikeValue
        else:
            strikePrice = strikePrice - strikeValue

    return strikePrice


# In[26]:


#Straddle and strangle
def optionStrategyBacktest():
    open_position = 0  #0 no position. 1 in position
    strikePriceLeg = [0,0] #contains all the strikePrices of each leg
    symbolLeg = [0,0]      #contains the complete symbols of each leg
    expiry = "0"       #the expiry in format YYMDD or YYMMM
    #df1, df2 contains the option csv
    #indexDF contains the index csv
    #resultDF contains the final results of the strategy
    #resultDFrow1,2 contains the current row number of each leg1,2 in resultDF
    row1number = 0 #is the current row in df1
    row2number = 0 #is the current row in df2
    leg1InTrade = 0 #0 means no trade. 1 means in trade
    leg2InTrade = 0 #0 means no trade. 1 means in trade
    leg1TrailEntry = 0  #this is for using trailing
    leg2TrailEntry = 0  #this is for using trailing
    leg1MTM = 0   #this is for getting MTM after every minute
    leg2MTM = 0   #this is for getting MTM after every minute

    if symbol == "NIFTY":
        indexDF = pd.read_csv('in_nsei_1min.csv')
    elif symbol == "BANKNIFTY":
        indexDF = pd.read_csv('in_nsebank_1min.csv')

    indexDF['minute'] = pd.to_datetime(indexDF['minute'])
    indexDF.set_index('minute', inplace=True)
    indexDF.drop('ticker', axis=1, inplace=True)
    indexDF.drop('instrument_token', axis=1, inplace=True)
    indexDF.sort_index(ascending=True, inplace=True)
    #indexDF.sort_values(by='minute', ascending=True, inplace=True)
    print(indexDF.head())

    columns = ['date', 'underlying', 'entrytime', 'symbol', 'direction', 'entryprice', 'stoploss', 'target', 'exitprice', 'exitdate', 'exittime', 'pnl', 'remarks']
    resultDF = pd.DataFrame(columns=columns)

    #for loop for all dates of index
    for index, row in indexDF.iterrows():

        #check if entry time is reached
        date1 = index.date()
        time1 = index.time()

        if (time1 == startTime) and open_position == 0:
            #initialising
            row1number = 0 #is the current row in df1
            row2number = 0 #is the current row in df2
            leg1InTrade = 0 #0 means no trade. 1 means in trade
            leg2InTrade = 0 #0 means no trade. 1 means in trade
            leg1TrailEntry = 0  #this is for using trailing
            leg2TrailEntry = 0  #this is for using trailing
            leg1MTM = 0   #this is for getting MTM after every minute
            leg2MTM = 0   #this is for getting MTM after every minute

            #print(resultDF)
            #find expiry to trade
            expiry = findExpiryFormat(date1)
            print(expiry)

            for j in range (0, noOfLegs):
                #find strike price to trade
                if j == 0:
                    strikePriceLegTemp = findStrikePrice(row['close'], leg1, expiry, index)
                    strikePriceLeg[j] = strikePriceLegTemp
                    symbolLegTemp = "op_banknifty" + str(expiry) + str(strikePriceLegTemp) + leg1[0].lower() + ".csv"
                    symbolLeg[j] = symbolLegTemp
                    #read csv
                    if expiry[:2] == "20":
                        df1 = pd.read_csv("D:/options_2020_banknifty/"+symbolLegTemp)
                    elif expiry[:2] == "21":
                        df1 = pd.read_csv("D:/options_2021_banknifty/"+symbolLegTemp)

                    df1['minute'] = pd.to_datetime(df1['minute'])
                    df1.set_index('minute', inplace=True)
                    df1.sort_index(ascending=True, inplace=True)

                    #print(strikePriceLeg[j])
                    #print(symbolLeg[j])
                    #print(df1.head())
                if j == 1:
                    strikePriceLegTemp = findStrikePrice(row['close'], leg2, expiry, index)
                    strikePriceLeg[j] = strikePriceLegTemp
                    symbolLegTemp = "op_banknifty" + str(expiry) + str(strikePriceLegTemp) + leg2[0].lower() + ".csv"
                    symbolLeg[j] = symbolLegTemp
                    #read csv
                    if expiry[:2] == "20":
                        df2 = pd.read_csv("D:/options_2020_banknifty/"+symbolLegTemp)
                    elif expiry[:2] == "21":
                        df2 = pd.read_csv("D:/options_2021_banknifty/"+symbolLegTemp)

                    df2['minute'] = pd.to_datetime(df2['minute'])
                    df2.set_index('minute', inplace=True)
                    df2.sort_index(ascending=True, inplace=True)

                    #print(strikePriceLeg[j])
                    #print(symbolLeg[j])
                    #print(df2.head())



            #DO ENTRY
            for j in range (0, noOfLegs):

                #find entry price
                if j == 0:
                    row1number = 0
                    for index1, row1 in df1.iterrows():
                        row1number = row1number + 1
                        if index == index1:
                            entryprice = row1['close']
                            if leg1[1] == "B":
                                stoploss = entryprice*(1 - leg1[5])
                                target = entryprice*(1 + leg1[6])
                            elif leg1[1] == "S":
                                stoploss = entryprice*(1 + leg1[5])
                                target = entryprice*(1 - leg1[6])

                            resultDF = resultDF.append({'date': date1,'underlying': row['close'],'entrytime': time1,'symbol': symbolLeg[j],'direction': leg1[1],'entryprice': entryprice, 'stoploss': stoploss, 'target': target, 'remarks' : "Entry Done"}, ignore_index=True)
                            resultDFrow1 = resultDF.shape[0] - 1
                            leg1InTrade = 1
                            leg1TrailEntry = entryprice
                            break


                elif j == 1:
                    row2number = 0
                    for index2, row2 in df2.iterrows():
                        row2number = row2number + 1
                        if index == index2:
                            entryprice = row2['close']
                            if leg2[1] == "B":
                                stoploss = entryprice*(1 - leg2[5])
                                target = entryprice*(1 + leg2[6])
                            elif leg2[1] == "S":
                                stoploss = entryprice*(1 + leg2[5])
                                target = entryprice*(1 - leg2[6])

                            resultDF = resultDF.append({'date': date1,'underlying': row['close'],'entrytime': time1,'symbol': symbolLeg[j],'direction': leg2[1],'entryprice': entryprice, 'stoploss': stoploss, 'target': target, 'remarks' : "Entry Done"}, ignore_index=True)
                            resultDFrow2 = resultDF.shape[0] - 1
                            leg2InTrade = 1
                            leg2TrailEntry = entryprice
                            break


            open_position = 1

            #print(resultDF)
            print("row1number: ", row1number)
            print("row2number: ", row2number)
            print("resultDFrow1: ", resultDFrow1)
            print("resultDFrow2: ", resultDFrow2)


        elif open_position == 1 :
            for j in range (0, noOfLegs):
                if j == 0 and leg1InTrade == 1:
                    if leg1[1] == "B":
                        leg1MTM = df1.iloc[row1number]['close'] - resultDF.iloc[resultDFrow1]['entryprice']
                        #check for individual stoploss getting hit
                        if df1.iloc[row1number]['low'] <= resultDF.iloc[resultDFrow1]['stoploss']:
                            resultDF.loc[resultDFrow1, 'exitprice'] = resultDF.iloc[resultDFrow1]['stoploss']
                            resultDF.loc[resultDFrow1, 'exitdate'] = df1.iloc[row1number].name.date()
                            resultDF.loc[resultDFrow1, 'exittime'] = df1.iloc[row1number].name.time()
                            pnl = resultDF.iloc[resultDFrow1]['stoploss'] - resultDF.iloc[resultDFrow1]['entryprice']
                            resultDF.loc[resultDFrow1, 'pnl'] = pnl
                            resultDF.loc[resultDFrow1, 'remarks'] = 'Stoploss hit'
                            leg1InTrade = 0
                            leg1MTM = pnl


                        #check for time exit
                        elif (time1 == endTime):
                            resultDF.loc[resultDFrow1, 'exitprice'] = df1.iloc[row1number]['close']
                            resultDF.loc[resultDFrow1, 'exitdate'] = df1.iloc[row1number].name.date()
                            resultDF.loc[resultDFrow1, 'exittime'] = df1.iloc[row1number].name.time()
                            pnl = df1.iloc[row1number]['close'] - resultDF.iloc[resultDFrow1]['entryprice']
                            resultDF.loc[resultDFrow1, 'pnl'] = pnl
                            resultDF.loc[resultDFrow1, 'remarks'] = 'Time Exit'
                            leg1InTrade = 0
                            open_position = 0

                    elif leg1[1] == "S":
                        leg1MTM = resultDF.iloc[resultDFrow1]['entryprice'] - df1.iloc[row1number]['close']
                        #check for individual stoploss getting hit
                        if df1.iloc[row1number]['high'] >= resultDF.iloc[resultDFrow1]['stoploss']:
                            resultDF.loc[resultDFrow1, 'exitprice'] = resultDF.iloc[resultDFrow1]['stoploss']
                            resultDF.loc[resultDFrow1, 'exitdate'] = df1.iloc[row1number].name.date()
                            resultDF.loc[resultDFrow1, 'exittime'] = df1.iloc[row1number].name.time()
                            pnl = resultDF.iloc[resultDFrow1]['entryprice'] - resultDF.iloc[resultDFrow1]['stoploss']
                            resultDF.loc[resultDFrow1, 'pnl'] = pnl
                            resultDF.loc[resultDFrow1, 'remarks'] = 'Stoploss hit'
                            leg1InTrade = 0
                            leg1MTM = pnl

                        #check for time exit
                        elif (time1 == endTime):
                            resultDF.loc[resultDFrow1, 'exitprice'] = df1.iloc[row1number]['close']
                            resultDF.loc[resultDFrow1, 'exitdate'] = df1.iloc[row1number].name.date()
                            resultDF.loc[resultDFrow1, 'exittime'] = df1.iloc[row1number].name.time()
                            pnl = resultDF.iloc[resultDFrow1]['entryprice'] - df1.iloc[row1number]['close']
                            resultDF.loc[resultDFrow1, 'pnl'] = pnl
                            resultDF.loc[resultDFrow1, 'remarks'] = 'Time Exit'
                            leg1InTrade = 0
                            open_position = 0

                    #row1number = row1number + 1


                elif j == 1 and leg2InTrade == 1:
                    if leg2[1] == "B":
                        leg2MTM = df2.iloc[row2number]['close'] - resultDF.iloc[resultDFrow2]['entryprice']
                        #check for individual stoploss getting hit
                        if df2.iloc[row2number]['low'] <= resultDF.iloc[resultDFrow2]['stoploss']:
                            resultDF.loc[resultDFrow2, 'exitprice'] = resultDF.iloc[resultDFrow2]['stoploss']
                            resultDF.loc[resultDFrow2, 'exitdate'] = df2.iloc[row2number].name.date()
                            resultDF.loc[resultDFrow2, 'exittime'] = df2.iloc[row2number].name.time()
                            pnl = resultDF.iloc[resultDFrow2]['stoploss'] - resultDF.iloc[resultDFrow2]['entryprice']
                            resultDF.loc[resultDFrow2, 'pnl'] = pnl
                            resultDF.loc[resultDFrow2, 'remarks'] = 'Stoploss hit'
                            leg2InTrade = 0
                            leg2MTM = pnl

                        #check for time exit
                        elif (time1 == endTime):
                            resultDF.loc[resultDFrow2, 'exitprice'] = df2.iloc[row2number]['close']
                            resultDF.loc[resultDFrow2, 'exitdate'] = df2.iloc[row2number].name.date()
                            resultDF.loc[resultDFrow2, 'exittime'] = df2.iloc[row2number].name.time()
                            pnl = df2.iloc[row2number]['close'] - resultDF.iloc[resultDFrow2]['entryprice']
                            resultDF.loc[resultDFrow2, 'pnl'] = pnl
                            resultDF.loc[resultDFrow2, 'remarks'] = 'Time Exit'
                            leg2InTrade = 0
                            open_position = 0

                    elif leg2[1] == "S":
                        leg2MTM = resultDF.iloc[resultDFrow2]['entryprice'] - df2.iloc[row2number]['close']
                        #check for individual stoploss getting hit
                        if df2.iloc[row2number]['high'] >= resultDF.iloc[resultDFrow2]['stoploss']:
                            resultDF.loc[resultDFrow2, 'exitprice'] = resultDF.iloc[resultDFrow2]['stoploss']
                            resultDF.loc[resultDFrow2, 'exitdate'] = df2.iloc[row2number].name.date()
                            resultDF.loc[resultDFrow2, 'exittime'] = df2.iloc[row2number].name.time()
                            pnl = resultDF.iloc[resultDFrow2]['entryprice'] - resultDF.iloc[resultDFrow2]['stoploss']
                            resultDF.loc[resultDFrow2, 'pnl'] = pnl
                            resultDF.loc[resultDFrow2, 'remarks'] = 'Stoploss hit'
                            leg2InTrade = 0
                            leg2MTM = pnl

                        #check for time exit
                        elif (time1 == endTime):
                            resultDF.loc[resultDFrow2, 'exitprice'] = df2.iloc[row2number]['close']
                            resultDF.loc[resultDFrow2, 'exitdate'] = df2.iloc[row2number].name.date()
                            resultDF.loc[resultDFrow2, 'exittime'] = df2.iloc[row2number].name.time()
                            pnl = resultDF.iloc[resultDFrow2]['entryprice'] - df2.iloc[row2number]['close']
                            resultDF.loc[resultDFrow2, 'pnl'] = pnl
                            resultDF.loc[resultDFrow2, 'remarks'] = 'Time Exit'
                            leg2InTrade = 0
                            open_position = 0

                    #row2number = row2number + 1

            if (time1 > endTime):
                open_position = 0

        row1number = row1number + 1
        row2number = row2number + 1

    print(resultDF)
    resultDF.to_csv("test1.csv")


# In[29]:


#Momentum + Theta
def optionStrategyWaitTradeBacktest():
    check_position = 0  #0 check prices at closing prices
    strikePriceLeg = [0,0] #contains all the strikePrices of each leg
    symbolLeg = [0,0]      #contains the complete symbols of each leg
    expiry = "0"       #the expiry in format YYMDD or YYMMM
    #df1, df2 contains the option csv
    #indexDF contains the index csv
    #resultDF contains the final results of the strategy
    #resultDFrow1,2 contains the current row number of each leg1,2 in resultDF
    row1number = 0 #is the current row in df1
    row2number = 0 #is the current row in df2
    leg1InTrade = 0 #0 means no trade. 1 means in trade
    leg2InTrade = 0 #0 means no trade. 1 means in trade
    leg1TrailEntry = 0  #this is for using trailing
    leg2TrailEntry = 0  #this is for using trailing
    leg1MTM = 0   #this is for getting MTM after every minute
    leg2MTM = 0   #this is for getting MTM after every minute

    if symbol == "NIFTY":
        indexDF = pd.read_csv('in_nsei_1min.csv')
    elif symbol == "BANKNIFTY":
        indexDF = pd.read_csv('in_nsebank_1min.csv')

    indexDF['minute'] = pd.to_datetime(indexDF['minute'])
    indexDF.set_index('minute', inplace=True)
    indexDF.drop('ticker', axis=1, inplace=True)
    indexDF.drop('instrument_token', axis=1, inplace=True)
    indexDF.sort_index(ascending=True, inplace=True)
    #indexDF.sort_values(by='minute', ascending=True, inplace=True)
    print(indexDF.head())

    columns = ['date', 'underlying', 'optionClosingPrice', 'entrytime', 'symbol', 'direction', 'entryprice', 'stoploss', 'target', 'exitprice', 'exitdate', 'exittime', 'pnl', 'remarks']
    resultDF = pd.DataFrame(columns=columns)

    #for loop for all dates of index
    for index, row in indexDF.iterrows():

        #check if entry time is reached
        date1 = index.date()
        time1 = index.time()

        if (time1 == startTime) and check_position == 0:
            #initialising
            row1number = 0 #is the current row in df1
            row2number = 0 #is the current row in df2
            leg1InTrade = 0 #0 means no trade. 1 means in trade. 2 means exit is done
            leg2InTrade = 0 #0 means no trade. 1 means in trade. 2 means exit is done
            leg1TrailEntry = 0  #this is for using trailing
            leg2TrailEntry = 0  #this is for using trailing
            leg1MTM = 0   #this is for getting MTM after every minute
            leg2MTM = 0   #this is for getting MTM after every minute
            checkPrice = 0 #closing price based on which we have to find momentum

            #print(resultDF)
            #find expiry to trade
            expiry = findExpiryFormat(date1)
            print(expiry)

            for j in range (0, noOfLegs):
                #find strike price to trade
                if j == 0:
                    strikePriceLegTemp = findStrikePrice(row['close'], leg1, expiry, index)
                    strikePriceLeg[j] = strikePriceLegTemp
                    symbolLegTemp = "op_banknifty" + str(expiry) + str(strikePriceLegTemp) + leg1[0].lower() + ".csv"
                    symbolLeg[j] = symbolLegTemp
                    #read csv
                    if expiry[:2] == "20":
                        df1 = pd.read_csv("D:/options_2020_banknifty/"+symbolLegTemp)
                    elif expiry[:2] == "21":
                        df1 = pd.read_csv("D:/options_2021_banknifty/"+symbolLegTemp)

                    df1['minute'] = pd.to_datetime(df1['minute'])
                    df1.set_index('minute', inplace=True)
                    df1.sort_index(ascending=True, inplace=True)

                    #print(strikePriceLeg[j])
                    #print(symbolLeg[j])
                    #print(df1.head())
                if j == 1:
                    strikePriceLegTemp = findStrikePrice(row['close'], leg2, expiry, index)
                    strikePriceLeg[j] = strikePriceLegTemp
                    symbolLegTemp = "op_banknifty" + str(expiry) + str(strikePriceLegTemp) + leg2[0].lower() + ".csv"
                    symbolLeg[j] = symbolLegTemp
                    #read csv
                    if expiry[:2] == "20":
                        df2 = pd.read_csv("D:/options_2020_banknifty/"+symbolLegTemp)
                    elif expiry[:2] == "21":
                        df2 = pd.read_csv("D:/options_2021_banknifty/"+symbolLegTemp)

                    df2['minute'] = pd.to_datetime(df2['minute'])
                    df2.set_index('minute', inplace=True)
                    df2.sort_index(ascending=True, inplace=True)

                    #print(strikePriceLeg[j])
                    #print(symbolLeg[j])
                    #print(df2.head())



            #FIND CLOSING PRICE
            for j in range (0, noOfLegs):

                #find entry price
                if j == 0:
                    row1number = 0
                    for index1, row1 in df1.iterrows():
                        row1number = row1number + 1
                        if index == index1:
                            checkPrice = row1['close']
                            resultDF = resultDF.append({'date': date1,'underlying': row['close'], 'optionClosingPrice': checkPrice, 'symbol': symbolLeg[j],'direction': leg1[1], 'remarks' : "Closing Price Found"}, ignore_index=True)
                            resultDFrow1 = resultDF.shape[0] - 1
                            break


                elif j == 1:
                    row2number = 0
                    for index2, row2 in df2.iterrows():
                        row2number = row2number + 1
                        if index == index2:
                            checkPrice = row2['close']
                            resultDF = resultDF.append({'date': date1,'underlying': row['close'], 'optionClosingPrice': checkPrice, 'symbol': symbolLeg[j],'direction': leg2[1], 'remarks' : "Closing Price Found"}, ignore_index=True)
                            resultDFrow2 = resultDF.shape[0] - 1
                            break


            check_position = 1

            #print(resultDF)
            print("row1number: ", row1number)
            print("row2number: ", row2number)
            print("resultDFrow1: ", resultDFrow1)
            print("resultDFrow2: ", resultDFrow2)


        elif check_position == 1 :
            for j in range (0, noOfLegs):
                #Not in trade
                if j == 0 and leg1InTrade == 0 and time1 < endTime:
                    if leg1[9] == "U":
                        if df1.iloc[row1number]['high'] > resultDF.iloc[resultDFrow1]['optionClosingPrice']*(1 + leg1[10]):
                            entryprice = resultDF.iloc[resultDFrow1]['optionClosingPrice']*(1 + leg1[10])
                            if leg1[1] == "B":
                                stoploss = entryprice*(1 - leg1[5])
                                target = entryprice*(1 + leg1[6])
                            elif leg1[1] == "S":
                                stoploss = entryprice*(1 + leg1[5])
                                target = entryprice*(1 - leg1[6])

                            resultDF.loc[resultDFrow1, 'entrytime'] = df1.iloc[row1number].name.time()
                            resultDF.loc[resultDFrow1, 'entryprice'] = entryprice
                            resultDF.loc[resultDFrow1, 'stoploss'] = stoploss
                            resultDF.loc[resultDFrow1, 'target'] = target
                            resultDF.loc[resultDFrow1, 'remarks'] = "Entry Done"

                            leg1InTrade = 1
                            leg1TrailEntry = entryprice
                    elif leg1[9] == "D":
                        if df1.iloc[row1number]['low'] < resultDF.iloc[resultDFrow1]['optionClosingPrice']*(1 - leg1[10]):
                            entryprice = resultDF.iloc[resultDFrow1]['optionClosingPrice']*(1 - leg1[10])
                            if leg1[1] == "B":
                                stoploss = entryprice*(1 - leg1[5])
                                target = entryprice*(1 + leg1[6])
                            elif leg1[1] == "S":
                                stoploss = entryprice*(1 + leg1[5])
                                target = entryprice*(1 - leg1[6])

                            resultDF.loc[resultDFrow1, 'entrytime'] = df1.iloc[row1number].name.time()
                            resultDF.loc[resultDFrow1, 'entryprice'] = entryprice
                            resultDF.loc[resultDFrow1, 'stoploss'] = stoploss
                            resultDF.loc[resultDFrow1, 'target'] = target
                            resultDF.loc[resultDFrow1, 'remarks'] = "Entry Done"

                            leg1InTrade = 1
                            leg1TrailEntry = entryprice

                elif j == 1 and leg2InTrade == 0 and time1 < endTime:
                    if leg1[9] == "U":
                        if df2.iloc[row2number]['high'] > resultDF.iloc[resultDFrow2]['optionClosingPrice']*(1 + leg2[10]):
                            entryprice = resultDF.iloc[resultDFrow2]['optionClosingPrice']*(1 + leg2[10])
                            if leg2[1] == "B":
                                stoploss = entryprice*(1 - leg2[5])
                                target = entryprice*(1 + leg2[6])
                            elif leg2[1] == "S":
                                stoploss = entryprice*(1 + leg2[5])
                                target = entryprice*(1 - leg2[6])

                            resultDF.loc[resultDFrow2, 'entrytime'] = df2.iloc[row2number].name.time()
                            resultDF.loc[resultDFrow2, 'entryprice'] = entryprice
                            resultDF.loc[resultDFrow2, 'stoploss'] = stoploss
                            resultDF.loc[resultDFrow2, 'target'] = target
                            resultDF.loc[resultDFrow2, 'remarks'] = "Entry Done"
                            leg2InTrade = 1
                            leg2TrailEntry = entryprice
                    elif leg1[9] == "D":
                        if df2.iloc[row2number]['low'] < resultDF.iloc[resultDFrow2]['optionClosingPrice']*(1 - leg2[10]):
                            entryprice = resultDF.iloc[resultDFrow2]['optionClosingPrice']*(1 - leg2[10])
                            if leg2[1] == "B":
                                stoploss = entryprice*(1 - leg2[5])
                                target = entryprice*(1 + leg2[6])
                            elif leg2[1] == "S":
                                stoploss = entryprice*(1 + leg2[5])
                                target = entryprice*(1 - leg2[6])

                            resultDF.loc[resultDFrow2, 'entrytime'] = df2.iloc[row2number].name.time()
                            resultDF.loc[resultDFrow2, 'entryprice'] = entryprice
                            resultDF.loc[resultDFrow2, 'stoploss'] = stoploss
                            resultDF.loc[resultDFrow2, 'target'] = target
                            resultDF.loc[resultDFrow2, 'remarks'] = "Entry Done"

                            leg2InTrade = 1
                            leg2TrailEntry = entryprice

                #Already in trade
                elif j == 0 and leg1InTrade == 1:
                    if leg1[1] == "B":
                        leg1MTM = df1.iloc[row1number]['close'] - resultDF.iloc[resultDFrow1]['entryprice']
                        #check for individual stoploss getting hit
                        if df1.iloc[row1number]['low'] <= resultDF.iloc[resultDFrow1]['stoploss']:
                            resultDF.loc[resultDFrow1, 'exitprice'] = resultDF.iloc[resultDFrow1]['stoploss']
                            resultDF.loc[resultDFrow1, 'exitdate'] = df1.iloc[row1number].name.date()
                            resultDF.loc[resultDFrow1, 'exittime'] = df1.iloc[row1number].name.time()
                            pnl = resultDF.iloc[resultDFrow1]['stoploss'] - resultDF.iloc[resultDFrow1]['entryprice']
                            resultDF.loc[resultDFrow1, 'pnl'] = pnl
                            resultDF.loc[resultDFrow1, 'remarks'] = 'Stoploss hit'
                            leg1InTrade = 2
                            leg1MTM = pnl

                        #check for time exit
                        elif (time1 == endTime):
                            resultDF.loc[resultDFrow1, 'exitprice'] = df1.iloc[row1number]['close']
                            resultDF.loc[resultDFrow1, 'exitdate'] = df1.iloc[row1number].name.date()
                            resultDF.loc[resultDFrow1, 'exittime'] = df1.iloc[row1number].name.time()
                            pnl = df1.iloc[row1number]['close'] - resultDF.iloc[resultDFrow1]['entryprice']
                            resultDF.loc[resultDFrow1, 'pnl'] = pnl
                            resultDF.loc[resultDFrow1, 'remarks'] = 'Time Exit'
                            leg1InTrade = 2
                            check_position = 0

                    elif leg1[1] == "S":
                        leg1MTM = resultDF.iloc[resultDFrow1]['entryprice'] - df1.iloc[row1number]['close']
                        #check for individual stoploss getting hit
                        if df1.iloc[row1number]['high'] >= resultDF.iloc[resultDFrow1]['stoploss']:
                            resultDF.loc[resultDFrow1, 'exitprice'] = resultDF.iloc[resultDFrow1]['stoploss']
                            resultDF.loc[resultDFrow1, 'exitdate'] = df1.iloc[row1number].name.date()
                            resultDF.loc[resultDFrow1, 'exittime'] = df1.iloc[row1number].name.time()
                            pnl = resultDF.iloc[resultDFrow1]['entryprice'] - resultDF.iloc[resultDFrow1]['stoploss']
                            resultDF.loc[resultDFrow1, 'pnl'] = pnl
                            resultDF.loc[resultDFrow1, 'remarks'] = 'Stoploss hit'
                            leg1InTrade = 2
                            leg1MTM = pnl

                        #check for time exit
                        elif (time1 == endTime):
                            resultDF.loc[resultDFrow1, 'exitprice'] = df1.iloc[row1number]['close']
                            resultDF.loc[resultDFrow1, 'exitdate'] = df1.iloc[row1number].name.date()
                            resultDF.loc[resultDFrow1, 'exittime'] = df1.iloc[row1number].name.time()
                            pnl = resultDF.iloc[resultDFrow1]['entryprice'] - df1.iloc[row1number]['close']
                            resultDF.loc[resultDFrow1, 'pnl'] = pnl
                            resultDF.loc[resultDFrow1, 'remarks'] = 'Time Exit'
                            leg1InTrade = 2
                            check_position = 0

                    #row1number = row1number + 1


                elif j == 1 and leg2InTrade == 1:
                    if leg2[1] == "B":
                        leg2MTM = df2.iloc[row2number]['close'] - resultDF.iloc[resultDFrow2]['entryprice']
                        #check for individual stoploss getting hit
                        if df2.iloc[row2number]['low'] <= resultDF.iloc[resultDFrow2]['stoploss']:
                            resultDF.loc[resultDFrow2, 'exitprice'] = resultDF.iloc[resultDFrow2]['stoploss']
                            resultDF.loc[resultDFrow2, 'exitdate'] = df2.iloc[row2number].name.date()
                            resultDF.loc[resultDFrow2, 'exittime'] = df2.iloc[row2number].name.time()
                            pnl = resultDF.iloc[resultDFrow2]['stoploss'] - resultDF.iloc[resultDFrow2]['entryprice']
                            resultDF.loc[resultDFrow2, 'pnl'] = pnl
                            resultDF.loc[resultDFrow2, 'remarks'] = 'Stoploss hit'
                            leg2InTrade = 2
                            leg2MTM = pnl

                        elif (time1 == endTime):
                            resultDF.loc[resultDFrow2, 'exitprice'] = df2.iloc[row2number]['close']
                            resultDF.loc[resultDFrow2, 'exitdate'] = df2.iloc[row2number].name.date()
                            resultDF.loc[resultDFrow2, 'exittime'] = df2.iloc[row2number].name.time()
                            pnl = df2.iloc[row2number]['close'] - resultDF.iloc[resultDFrow2]['entryprice']
                            resultDF.loc[resultDFrow2, 'pnl'] = pnl
                            resultDF.loc[resultDFrow2, 'remarks'] = 'Time Exit'
                            leg2InTrade = 2
                            check_position = 0

                    elif leg2[1] == "S":
                        leg2MTM = resultDF.iloc[resultDFrow2]['entryprice'] - df2.iloc[row2number]['close']
                        #check for individual stoploss getting hit
                        if df2.iloc[row2number]['high'] >= resultDF.iloc[resultDFrow2]['stoploss']:
                            resultDF.loc[resultDFrow2, 'exitprice'] = resultDF.iloc[resultDFrow2]['stoploss']
                            resultDF.loc[resultDFrow2, 'exitdate'] = df2.iloc[row2number].name.date()
                            resultDF.loc[resultDFrow2, 'exittime'] = df2.iloc[row2number].name.time()
                            pnl = resultDF.iloc[resultDFrow2]['entryprice'] - resultDF.iloc[resultDFrow2]['stoploss']
                            resultDF.loc[resultDFrow2, 'pnl'] = pnl
                            resultDF.loc[resultDFrow2, 'remarks'] = 'Stoploss hit'
                            leg2InTrade = 2
                            leg2MTM = pnl

                        #check for time exit
                        elif (time1 == endTime):
                            resultDF.loc[resultDFrow2, 'exitprice'] = df2.iloc[row2number]['close']
                            resultDF.loc[resultDFrow2, 'exitdate'] = df2.iloc[row2number].name.date()
                            resultDF.loc[resultDFrow2, 'exittime'] = df2.iloc[row2number].name.time()
                            pnl = resultDF.iloc[resultDFrow2]['entryprice'] - df2.iloc[row2number]['close']
                            resultDF.loc[resultDFrow2, 'pnl'] = pnl
                            resultDF.loc[resultDFrow2, 'remarks'] = 'Time Exit'
                            leg2InTrade = 2
                            check_position = 0

                    #row2number = row2number + 1

            if (time1 > endTime):
                check_position = 0

        row1number = row1number + 1
        row2number = row2number + 1

    print(resultDF)
    resultDF.to_csv("test2.csv")


# In[22]:


optionStrategyBacktest()


# In[30]:


optionStrategyWaitTradeBacktest()


# In[ ]:




