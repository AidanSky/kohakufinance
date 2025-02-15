import yfinance as yf
import pandas as pd
from flask import Flask, flash, redirect, render_template, request, session, jsonify
from datetime import datetime, timedelta

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/fetch-data', methods=['POST'])
def fetch():
    return datafetch()

def datafetch(): 
    try: 
        request_data = request.json
        function = request_data.get("function")

        ticker = request_data.get("ticker").upper()
        if not ticker:
            return jsonify({'error': 'Please enter a ticker'}), 400
        
        # check if rsi or sma are checked
        rsiButton = request_data.get("rsiButton")
        smaButton = request_data.get("smaButton")   

        # test ticker for valid data
        test = yf.Ticker(ticker).history(period='1d', interval='1m')
        if test.empty:
            return jsonify({'error': 'Invalid ticker'}), 400
        
        datatype = (request_data.get("dataType", 'close')).capitalize()

        # start and end date if custom range. Check if custom then determine what yf function to use
        customRange = request_data.get("customRange")

        # check if customrange or not, if customrange, request start and end date, if not, request daterange, which is autoselected at 1y
        if customRange:
            start = request_data.get("startDate")
            end = request_data.get("endDate")
            dateRange = None
            if not start or not end:
                return jsonify({'error': 'Invalid start or end date'}), 400
            if start >= end:
                return jsonify({'error': 'Start date must be before end date'}), 400
        else:
            dateRange = request_data.get("dateRange", "1year")

            #calculate amount of days in year for RSI+SMI calculations on ytd 
            today = datetime.today()
            newYear = datetime(today.year, 1, 1)
            ytdCounter = (today-newYear).days 

            data_ranges = {
                '1year': ('1y', '1d', 365, 14, 365),
                '6month': ('6mo', '1d', 180, 14, 182),
                '1month': ('1mo', '1d', 30, 14, 30),
                '5year': ('5y', '1wk', 1825, 14, 1825),
                '1day': ('1d', '1m', 1, 390, 390), # calculate amount of intervals necessary for 1d and 5d
                '1week': ('5d', '30m', 5, 14, 65),
                'ytd': ('ytd', '1d', ytdCounter, 14, ytdCounter)
            }
            #dataScalp should be how many additional periods I need data from in order to calculate RSI and SMA at max (14)
            period, interval, yeardays, dataScalp, delta = data_ranges.get(dateRange, ('1y', '1d', 365, 14, None))
            start = (datetime.today() - timedelta(days=yeardays)).strftime('%Y-%m-%d')
            end = None
        
        rsiLength = int(request_data.get("rsiLength", 0))
        smaLength = int(request_data.get("smaLength", 0))

        #create default length for calculation functions
        if (rsiLength >= smaLength):
            length = rsiLength
        else: 
            length = smaLength

        tickertwo = request_data.get("secondSymbol", None)
        if tickertwo:
            tickertwo = tickertwo.upper()
            testtwo = yf.Ticker(tickertwo).history(period='1d', interval='1m')
            if testtwo.empty:
                return jsonify({'error': 'Invalid second ticker'}), 400

        if (function == "compare" and not tickertwo):
            return jsonify({'error': 'Please enter a second ticker'}), 400

        if function == "graph":
            i = 0
            if customRange and (rsiButton or smaButton):
                preStart = length + 10
                dtStart = datetime.strptime(start, '%Y-%m-%d')
                techStart = dtStart - timedelta(days=preStart)
                data = yf.download(ticker, start=techStart, end=end)
            elif customRange: 
                data = yf.download(ticker, start, end)
            elif rsiButton or smaButton:
                if dateRange in ['1year', '5year', '6month', '1month', 'ytd']:
                    preStart = yeardays + length + 10
                    techStart = (datetime.today() - timedelta(days=preStart)).strftime('%Y-%m-%d')
                    techEnd = datetime.today().strftime('%Y-%m-%d')
                    data = yf.download(ticker, start=techStart, end=techEnd)
                elif dateRange in ['1day']:
                    today = datetime.today()
                    # Determine the last two trading days (excluding weekends)
                    if today.weekday() == 0:  # Monday
                        day1 = today - timedelta(days=3) # Friday
                        day2 = today - timedelta(days=4) # Thursday
                    elif today.weekday() == 6: # Sunday
                        day1 = today - timedelta(days=2) # Friday
                        day2 = today - timedelta(days=3) # Thursday
                    elif today.weekday() == 5: # Saturday 
                        day1 = today - timedelta(days=1) # Friday
                        day2 = today - timedelta(days=2) # Thursday
                    else:  # Other days
                        day1 = today - timedelta(days=1)
                        day2 = today - timedelta(days=2)

                    yfday1 = day1.strftime('%Y-%m-%d')
                    yfday2 = day2.strftime('%Y-%m-%d')
                    yftoday = today.strftime('%Y-%m-%d')

                    dataone = yf.download(ticker, start=yfday1, end=yftoday, interval=interval)
                    datatwo = yf.download(ticker, start=yfday2, end=yfday1, interval=interval)
                    data = pd.concat([datatwo, dataone])
                elif dateRange in ['1week']:
                    today = datetime.today()
                    yftoday = today.strftime('%Y-%m-%d')

                    start = today - timedelta(days=9)
                    yfstart = start.strftime('%Y-%m-%d')

                    data = yf.download(ticker, start=yfstart, end=yftoday, interval=interval)

                    #slice first day after determining RSI and SMA 
            else: 
                data = yf.download(ticker, period=period, interval=interval)

            if dateRange in ['1day', '1week', '1month', '6month']: 
                data.index = pd.to_datetime(data.index, utc=True).tz_convert('America/New_York')

            datacopy = data.copy()

            data.reset_index(inplace=True)

            if 'Datetime' in data.columns:
                data['Date'] = pd.to_datetime(data['Datetime']).dt.strftime('%m/%d/%Y %H:%M')
            else:
                data['Date'] = pd.to_datetime(data['Date']).dt.strftime('%m/%d/%Y')

            filtered_data = {
                'labels': data['Date'].values.tolist(),
                'data': data[datatype].squeeze().round(2).values.tolist()
            }

            #amount of things to slice out of SMA and RSI
            subtract = length - 1
            
            
            # gather RSI and SMA data if requested, subtract wasted length at beginning // is this redundant with trimmed_data?
            if rsiButton:
                rsi_data = rsi(datacopy, datatype, rsiLength)
                if (dateRange in ['1day', '1week', '1month', '6month']): 
                    filtered_data['rsi'] = [None] * subtract + rsi_data['rsi'][subtract:]
                    filtered_data['overbought'] = rsi_data['overbought']
                    filtered_data['oversold'] = rsi_data['oversold']
                else: 
                    filtered_data['rsi'] = rsi_data['rsi']
                    filtered_data['overbought'] = rsi_data['overbought']
                    filtered_data['oversold'] = rsi_data['oversold']

            if smaButton:
                sma_data = movingavg(datacopy, datatype, smaLength)
                if (dateRange in ['1day', '1week', '1month', '6month']): 
                    filtered_data['sma'] = [None] * subtract + sma_data['data'][subtract:]
                else:
                    filtered_data['sma'] = sma_data['data']
            
            if (dateRange in ['1year', '5year', '1month', '6month', 'ytd']):
                ## DATE CALCULATIONS MUST BE DONE DIFFERENTLY FOR MINUTE CHARTS
                # count amount of labels from first label up until target label, remove that amount
                if today.weekday() == 6: # Sunday = offset delta by 2
                    target_date = today - timedelta(days=delta+2)
                elif today.weekday() == 5: #saturday = offset delta by 1
                    target_date = today - timedelta(days=delta+1)
                else:
                    target_date = today - timedelta(days=delta)

                date_list = [datetime.strptime(date, '%m/%d/%Y') for date in filtered_data['labels']]

                # make sure target date and filtered_data labels are formatted in the same way
                while datetime.strptime(filtered_data['labels'][i], '%m/%d/%Y') < target_date:
                    i += 1
                # remove = sum(1 for date in date_list if date < target_date)
                print(i)
            elif dateRange in ['1week']:
                # manually calculate target date based on what day of the week
                target_date = today - timedelta(days=7)
                target_datetime = target_date.replace(hour=4, minute=30)
                while datetime.strptime(filtered_data['labels'][i], '%m/%d/%Y %H:%M') < target_datetime:
                    i += 1
            elif customRange: 
                target_date = datetime.strptime(start, '%Y-%m-%d')
                while datetime.strptime(filtered_data['labels'][i], '%m/%d/%Y') < target_date:
                    i += 1

            # remove only if RSI or SMA are selected, should be different for day vs datetime 
            if dateRange in ['1year', '5year', '1month', '6month', 'ytd', '1week'] or customRange:
                trimmed_data = ({key: values[i:] for key, values in filtered_data.items()} if rsiButton or smaButton else filtered_data)
            elif dateRange in ['1day']:
                trimmed_data = ({key: values[dataScalp:] for key, values in filtered_data.items()} if rsiButton or smaButton else filtered_data)
            else: 
                trimmed_data = filtered_data

            return jsonify(trimmed_data)

        elif function == "compare":
            i = 0
            # start date must be day earlier than requested start date to calculate percentage change
            if customRange:
                preStart = length + 10
                dtStart = datetime.strptime(start, '%Y-%m-%d')
                techStart = dtStart - timedelta(days=preStart)
                dataalpha = yf.download(ticker, start=techStart, end=end)
                databeta = yf.download(tickertwo, start=techStart, end=end)
            elif dateRange in ['1year', '5year', '6month', '1month', 'ytd']:
                    preStart = yeardays + length + 10
                    techStart = (datetime.today() - timedelta(days=preStart)).strftime('%Y-%m-%d')
                    techEnd = datetime.today().strftime('%Y-%m-%d')
                    dataalpha = yf.download(ticker, start=techStart, end=techEnd)
                    databeta = yf.download(tickertwo, start=techStart, end=techEnd)
            elif dateRange in ['1day']:
                    today = datetime.today()
                    # Determine the last two trading days (excluding weekends)
                    if today.weekday() == 0: # Monday
                        day1 = today - timedelta(days=3) # Friday
                        day2 = today - timedelta(days=4)  # Thursday
                    elif today.weekday() == 6: # Sunday
                        day1 = today - timedelta(days=2) # Friday
                        day2 = today - timedelta(days=3) # Thursday
                    elif today.weekday() == 5: # Saturday 
                        day1 = today - timedelta(days=1) # Friday
                        day2 = today - timedelta(days=2) # Thursday
                    else:  # Other days
                        day1 = today - timedelta(days=1)
                        day2 = today - timedelta(days=2)

                    yfday1 = day1.strftime('%Y-%m-%d')
                    yfday2 = day2.strftime('%Y-%m-%d')
                    yftoday = today.strftime('%Y-%m-%d')

                    dataone = yf.download(ticker, start=yfday1, end=yftoday, interval=interval)
                    datatwo = yf.download(ticker, start=yfday2, end=yfday1, interval=interval)
                    dataalpha = pd.concat([datatwo, dataone])                

                    datathree = yf.download(tickertwo, start=yfday1, end=yftoday, interval=interval)
                    datafour = yf.download(tickertwo, start=yfday2, end=yfday1, interval=interval)
                    databeta = pd.concat([datathree, datafour])
            elif dateRange in ['1week']:
                today = datetime.today()
                yftoday = today.strftime('%Y-%m-%d')
                start = today - timedelta(days=9)
                yfstart = start.strftime('%Y-%m-%d')
                dataalpha = yf.download(ticker, start=yfstart, end=yftoday, interval=interval)
                databeta = yf.download(tickertwo, start=yfstart, end=yftoday, interval=interval)
            else:
                dataalpha = yf.download(ticker, start, end)
                databeta = yf.download(tickertwo, start, end)

            dataalpha.reset_index(inplace=True)
            databeta.reset_index(inplace=True)

            dfalpha = ((dataalpha[datatype].diff(1))/dataalpha[datatype].shift(1)*100).fillna(0)
            dfbeta = ((databeta[datatype].diff(1))/databeta[datatype].shift(1)*100).fillna(0)

            datealpha = dict()
            if 'Datetime' in dataalpha.columns:
                datealpha['Date'] = pd.to_datetime(dataalpha['Datetime']).dt.strftime('%m/%d/%Y %H:%M')
            else:
                datealpha['Date'] = pd.to_datetime(dataalpha['Date']).dt.strftime('%m/%d/%Y')

            filtered_data = {
                'labels': datealpha['Date'].values.tolist(),
                'dataalpha': dfalpha.squeeze().round(2).values.tolist(),
                'databeta': dfbeta.squeeze().round(2).values.tolist(),
            }
            if (dateRange in ['1year', '5year', '1month', '6month', 'ytd']):
                ## DATE CALCULATIONS MUST BE DONE DIFFERENTLY FOR MINUTE CHARTS
                # count amount of labels from first label up until target label, remove that amount
                if today.weekday() == 6: # Sunday = offset delta by 2
                    target_date = today - timedelta(days=delta+2)
                elif today.weekday() == 5: #saturday = offset delta by 1
                    target_date = today - timedelta(days=delta+1)
                else:
                    target_date = today - timedelta(days=delta)

                date_list = [datetime.strptime(date, '%m/%d/%Y') for date in filtered_data['labels']]

                # make sure target date and filtered_data labels are formatted in the same way
                while datetime.strptime(filtered_data['labels'][i], '%m/%d/%Y') < target_date:
                    i += 1
                print(i)
            elif dateRange in ['1week']:
                # manually calculate target date based on what day of the week
                target_date = today - timedelta(days=7)
                target_datetime = target_date.replace(hour=4, minute=30)
                while datetime.strptime(filtered_data['labels'][i], '%m/%d/%Y %H:%M') < target_datetime:
                    i += 1
            elif customRange: 
                target_date = datetime.strptime(start, '%Y-%m-%d')
                while datetime.strptime(filtered_data['labels'][i], '%m/%d/%Y') < target_date:
                    i += 1

            #    remove only if RSI or SMA are selected, should be different for day vs datetime 
            if dateRange in ['1year', '5year', '1month', '6month', 'ytd', '1week'] or customRange:
                trimmed_data = ({key: values[i:] for key, values in filtered_data.items()})
            elif dateRange in ['1day']:
                trimmed_data = ({key: values[dataScalp:] for key, values in filtered_data.items()})
            else: 
                trimmed_data = filtered_data

            return jsonify(trimmed_data)
        
        elif function == 'percentage':
            i = 0
            if customRange:
                preStart = length + 10
                dtStart = datetime.strptime(start, '%Y-%m-%d')
                techStart = dtStart - timedelta(days=preStart)
                data = yf.download(ticker, start=techStart, end=end)                
            elif dateRange in ['1year', '5year', '6month', '1month', 'ytd']:
                    preStart = yeardays + length + 10
                    techStart = (datetime.today() - timedelta(days=preStart)).strftime('%Y-%m-%d')
                    techEnd = datetime.today().strftime('%Y-%m-%d')
                    data = yf.download(ticker, start=techStart, end=techEnd)
            elif dateRange in ['1day']:
                    today = datetime.today()
                    # Determine the last two trading days (excluding weekends)
                    if today.weekday() == 0: # Monday 
                        day1 = today - timedelta(days=3) # Friday
                        day2 = today - timedelta(days=4) # Thursday
                    elif today.weekday() == 6: # Sunday 
                        day1 = today - timedelta(days=2) # Friday
                        day2 = today - timedelta(days=3) # Thursday
                    elif today.weekday() == 5: # Saturday
                        day1 = today - timedelta(days=1) # Friday
                        day2 = today - timedelta(days=2) # Thursday
                    else:  # Other days
                        day1 = today - timedelta(days=1)
                        day2 = today - timedelta(days=2)

                    yfday1 = day1.strftime('%Y-%m-%d')
                    yfday2 = day2.strftime('%Y-%m-%d')
                    yftoday = today.strftime('%Y-%m-%d')

                    dataone = yf.download(ticker, start=yfday1, end=yftoday, interval=interval)
                    datatwo = yf.download(ticker, start=yfday2, end=yfday1, interval=interval)
                    data = pd.concat([datatwo, dataone])     
            elif dateRange in ['1week']:
                today = datetime.today()
                yftoday = today.strftime('%Y-%m-%d')
                start = today - timedelta(days=9)
                yfstart = start.strftime('%Y-%m-%d')
                data = yf.download(ticker, start=yfstart, end=yftoday, interval=interval)
            else:
                data = yf.download(ticker, start=start, end=end)

            data.reset_index(inplace=True)

            percentdata = ((data[datatype].diff(1))/data[datatype].shift(1)*100).fillna(0) 

            datealpha = dict()
            if 'Datetime' in data.columns:
                datealpha['Date'] = pd.to_datetime(data['Datetime']).dt.strftime('%m/%d/%Y %H:%M')
            else:
                datealpha['Date'] = pd.to_datetime(data['Date']).dt.strftime('%m/%d/%Y')

            filtered_data = {
                'labels': datealpha['Date'].values.tolist(),
                'data': percentdata.squeeze().round(2).values.tolist()
            }
            if (dateRange in ['1year', '5year', '1month', '6month', 'ytd']): 
                ## DATE CALCULATIONS MUST BE DONE DIFFERENTLY FOR MINUTE CHARTS
                # count amount of labels from first label up until target label, remove that amount
                if today.weekday() == 6: # Sunday = offset delta by 2
                    target_date = today - timedelta(days=delta+2)
                elif today.weekday() == 5: #saturday = offset delta by 1
                    target_date = today - timedelta(days=delta+1)
                else:
                    target_date = today - timedelta(days=delta)

                date_list = [datetime.strptime(date, '%m/%d/%Y') for date in filtered_data['labels']]

                # make sure target date and filtered_data labels are formatted in the same way
                while datetime.strptime(filtered_data['labels'][i], '%m/%d/%Y') < target_date:
                    i += 1
                # remove = sum(1 for date in date_list if date < target_date)
                print(i)
            elif dateRange in ['1week']:
                # manually calculate target date based on what day of the week
                target_date = today - timedelta(days=7)
                target_datetime = target_date.replace(hour=4, minute=30)
                while datetime.strptime(filtered_data['labels'][i], '%m/%d/%Y %H:%M') < target_datetime:
                    i += 1
            elif customRange: 
                target_date = datetime.strptime(start, '%Y-%m-%d')
                while datetime.strptime(filtered_data['labels'][i], '%m/%d/%Y') < target_date:
                    i += 1

            #    remove only if RSI or SMA are selected, should be different for day vs datetime 
            if dateRange in ['1year', '5year', '1month', '6month', 'ytd', '1week'] or customRange:
                trimmed_data = ({key: values[i:] for key, values in filtered_data.items()})
            elif dateRange in ['1day']:
                trimmed_data = ({key: values[dataScalp:] for key, values in filtered_data.items()})
            else: 
                trimmed_data = filtered_data            
            return jsonify(trimmed_data)
            
        elif function == 'movingavg':
            # get (length) of past date then download
            i = 0
            subtract = smaLength - 1
            if customRange:
                preStart = smaLength + 10
                dtStart = datetime.strptime(start, '%Y-%m-%d')
                techStart = dtStart - timedelta(days=preStart)
                techEnd = datetime.today().strftime('%Y-%m-%d')
                df = yf.download(ticker, start=techStart, end=techEnd)
            else: 
                if dateRange in ['1year', '5year', '6month', '1month', 'ytd']:
                    preStart = yeardays + length + 10
                    techStart = (datetime.today() - timedelta(days=preStart)).strftime('%Y-%m-%d')
                    techEnd = datetime.today().strftime('%Y-%m-%d')
                    df = yf.download(ticker, start=techStart, end=techEnd)
                elif dateRange in ['1day']:
                    today = datetime.today()
                    if today.weekday() == 0: # Monday
                        day1 = today - timedelta(days=3) # Friday
                        day2 = today - timedelta(days=4) # Thursday
                    elif today.weekday() == 6: # Sunday
                        day1 = today - timedelta(days=2) # Friday
                        day2 = today - timedelta(days=3) # Thursday
                    elif today.weekday() == 5: # Saturday
                        day1 = today - timedelta(days=1) # Friday
                        day2 = today - timedelta(days=2) # Thursday
                    else:  # Other days
                        day1 = today - timedelta(days=1)
                        day2 = today - timedelta(days=2)

                    yfday1 = day1.strftime('%Y-%m-%d')
                    yfday2 = day2.strftime('%Y-%m-%d')
                    yftoday = today.strftime('%Y-%m-%d')

                    dataone = yf.download(ticker, start=yfday1, end=yftoday, interval=interval)
                    datatwo = yf.download(ticker, start=yfday2, end=yfday1, interval=interval)
                    df = pd.concat([datatwo, dataone])
                elif dateRange in ['1week']:
                    today = datetime.today()
                    yftoday = today.strftime('%Y-%m-%d')

                    start = today - timedelta(days=9)
                    yfstart = start.strftime('%Y-%m-%d')

                    df = yf.download(ticker, start=yfstart, end=yftoday, interval=interval)
            data = movingavg(df, datatype, smaLength)
            if dateRange in ['1day', '1week']: 
                df.index = pd.to_datetime(df.index, utc=True).tz_convert('America/New_York')
            df.reset_index(inplace=True)

            filtered_data = {
                'data': data['data']
            }
            if 'Datetime' in df.columns:
                data['Date'] = pd.to_datetime(df['Datetime']).dt.strftime('%m/%d/%Y %H:%M')
            else:
                data['Date'] = pd.to_datetime(df['Date']).dt.strftime('%m/%d/%Y')
            data['labels'] = data['Date'].values.tolist()

            filtered_data['labels'] = data['labels']

            if (dateRange in ['1year', '5year', '1month', '6month', 'ytd']):
                ## DATE CALCULATIONS MUST BE DONE DIFFERENTLY FOR MINUTE CHARTS
                # count amount of labels from first label up until target label, remove that amount
                if today.weekday() == 6: # Sunday = offset delta by 2
                    target_date = today - timedelta(days=delta+2)
                elif today.weekday() == 5: #saturday = offset delta by 1
                    target_date = today - timedelta(days=delta+1)
                else:
                    target_date = today - timedelta(days=delta)

                # make sure target date and filtered_data labels are formatted in the same way
                while datetime.strptime(filtered_data['labels'][i], '%m/%d/%Y') < target_date:
                    i += 1
                # remove = sum(1 for date in date_list if date < target_date)
                print("\n", i)
            elif dateRange in ['1week']:
                # manually calculate target date based on what day of the week
                target_date = today - timedelta(days=7)
                target_datetime = target_date.replace(hour=4, minute=30)
                while datetime.strptime(filtered_data['labels'][i], '%m/%d/%Y %H:%M') < target_datetime:
                    i += 1
            elif customRange: 
                target_date = datetime.strptime(start, '%Y-%m-%d')
                while datetime.strptime(filtered_data['labels'][i], '%m/%d/%Y') < target_date:
                    i += 1

            # remove only if RSI or SMA are selected, should be different for day vs datetime 
            if dateRange in ['1year', '5year', '1month', '6month', 'ytd', '1week'] or customRange:
                trimmed_data = ({key: values[i:] for key, values in filtered_data.items()})
            elif dateRange in ['1day']:
                trimmed_data = ({key: values[dataScalp:] for key, values in filtered_data.items()})
            else: 
                trimmed_data = filtered_data
            return jsonify(trimmed_data)

        return jsonify({'error': 'Invalid function'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def quote(dataframe, date, type): 
    # simply pulls information from a given date 
    number = round(dataframe.loc[date, type], 2)
    return f"${number:,.2f}";

def compare(dataframeone, dataframetwo, type, length):

    # calculate percentage change for first ticker and second ticker 
    dfalpha = ((dataframeone[type].diff(1))/dataframeone[type].shift(1)*100).fillna(0)
    dfbeta = ((dataframetwo[type].diff(1))/dataframetwo[type].shift(1)*100).fillna(0)

    # concatenate both dataframes into one that can be returned
    dfmain = pd.concat([dfalpha, dfbeta])

    # return main as json
    return dfmain.to_dict(orient='split')

def rsi(dataframe, datatype, length): # user inputs ticker + range and RSI is calculated for the user at the time selected, or graphed based on input 
    change = dataframe[datatype].diff(1)

    # next need to download info from (length) days before start date but not include in chart

    #if positive, is gain, if negative, is loss
    gain = change.where(change > 0, 0)
    loss =  change.where(change < 0, 0).abs()

    gaintwo = gain.rolling(window=length, min_periods=length).mean()
    losstwo = loss.rolling(window=length, min_periods=length).mean()

    division = gaintwo/losstwo

    rsi = 100 - (100 / (1+division))

    oversold = []
    overbought = []

    rsi_dict = {
        'rsi': rsi[dataframe.columns[0][1]].fillna(0).round(2).tolist(),
    }

    oversold = [30] * len(rsi_dict['rsi'])
    overbought = [70] * len(rsi_dict['rsi'])

    rsi_dict['oversold'] = oversold
    rsi_dict['overbought'] = overbought

    return rsi_dict

                                                            
def movingavg(dataframe, datatype, length):
    change = dataframe[datatype]
    sma = change.rolling(window=length, min_periods=length).mean()

    sma_dict = {
        'data': sma.squeeze().round(2).fillna(0).values.tolist()
    }
    return sma_dict 

if __name__ == "__main__":
    app.run(debug=True)