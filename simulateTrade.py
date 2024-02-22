from talib import BBANDS
from talib import MA_Type
from talib import MA
from talib import RSI
import math
import yfinance


symbols = ['SOL', 'DOGE', 'LINK', 'ADA', 'MONA', 'DAI', 'MKR', 'ATOM', 'DOT', 'ENJ', 'QTUM', 'XTZ', 'BAT', 'XLM', 'XEM', 'XRP', 'LTC', 'BCH', 'ETH', 'BTC']
spread = [0.9976560547348027, 0.9978123495145631, 0.9978608222901801, 0.9949580020159031, 0.9777939926199262,
          0.9923254334340702, 0.9931107644444445, 0.9975584832904885, 0.9955731578947368, 0.99450666,
          0.9880045910083421, 0.9920382716049382, 0.9947338411843876, 0.9941066535751415, 0.9943466222144235,
          0.9978335622764843, 0.9980113043478261, 0.9938609592573492, 0.9976541243939959, 0.9980151823736345]


def calcPrice(symbol, price):
    if symbol in ['DOGE', 'ADA', 'MONA', 'DAI', 'ENJ', 'QTUM', 'XTZ', 'BAT', 'XLM', 'XEM', 'XRP']:
        return f'{price:.3f}'
    else:
        return f'{price:.0f}'


def calcSize(symbol, size):
    if symbol in ['DOGE', 'ADA', 'MONA', 'DAI', 'ENJ', 'BAT', 'XLM', 'XEM', 'XRP']:
        return f'{size:.0f}'
    elif symbol in ['LINK', 'DOT', 'QTUM', 'XTZ', 'LTC']:
        return f'{size:.1f}'
    elif symbol in ['SOL', 'ATOM', 'BCH', 'ETH']:
        return f'{size:.2f}'
    elif symbol in ['MKR']:
        return f'{size:.3f}'
    else:
        return f'{size:.4f}'


def simulateTrade(symbol, df, spread, stack1, stack2, upper, lower, width, chartStack, interval):
    df['up'], df['MA1'], df['low'] = BBANDS(df['Close'],
                                            timeperiod=stack1,
                                            nbdevup=upper,
                                            nbdevdn=lower)
    df['MA2'] = MA(df['Close'], timeperiod=stack2)
    df['EMA2'] = MA(df['Close'], timeperiod=stack2, matype=MA_Type.EMA)
    df['RSI'] = RSI(df['Close'])
    
    balance = 10000
    firstBalance, evalBalance = balance, balance
    askSize = 10000
    paa, size, minus, loss = 0, 0, 0, 0
    overpay = 0
    countAsk, countBid = 0, 0
    for i in range(chartStack, 0, -1):
        price = df['Close'].iloc[-i]
        up = df['up'].iloc[-i]
        low = df['low'].iloc[-i]
        MA2 = df['MA2'].iloc[-i]
        EMA2 = df['EMA2'].iloc[-i]
        RSI1 = df['RSI'].iloc[-i]
        lstMA2 = df['MA2'].iloc[-i-1]
        lstEMA2 = df['EMA2'].iloc[-i-1]
        ystMA2 = df['MA2'].iloc[-stack1-i]
        ystEMA2 = df['EMA2'].iloc[-stack1-i]
        if paa != 0:
            if price < loss:
                paa = loss
                loss = low
            elif (0 < EMA2 - MA2 < ystEMA2 - ystMA2 or up < price) and paa < price*spread*width:
            #if up < price and RSI1 > 70 or paa < price and 0 < EMA2 - MA2 < ystEMA2 - ystMA2:
                pab = float(calcPrice(symbol, price*spread*1.0018))
                balance = int(minus + pab*size) - math.ceil(pab*size*0.0009)
                evalBalance = int(evalBalance + pab*size) - math.ceil(pab*size*0.0009)
                overpay += math.ceil(pab*size*0.0009) - pab*size*0.0009
                paa = 0
                countBid += 1
        else:
            if MA2 - EMA2 < ystMA2 - ystEMA2 and (price < loss or price < low):
            #elif price < low and RSI1 < 30 and 0 < MA2 - EMA2 < ystMA2 - ystEMA2:
                paa = float(calcPrice(symbol, price))
                size = float(calcSize(symbol, evalBalance/paa))
                minus = int(balance - paa*size) - math.ceil(paa*size*0.0009)
                evalBalance = int(evalBalance - paa*size) - math.ceil(paa*size*0.0009)
                overpay += math.ceil(paa*size*0.0009) - paa*size*0.0009
                paa = loss + (price - low) if price < loss else paa
                loss = low
                countAsk += 1
        if i % (24*60/interval) == 1:
            balance += int(overpay)
            evalBalance += int(overpay)
            overpay = 0
    return [stack1, stack2, upper, lower, countAsk, countBid, width, balance]


def simulateTradeAll(stack1, stack2, upper, lower, width, simulateStack, interval):
    period = (interval*(simulateStack + max(stack2)) + 60*24 - 1)//(60*24) + 1
    df = []
    for i, symbol in enumerate(symbols):
        df.append(yfinance.Ticker(f'{symbol}-JPY').history(period=f'{period}d', interval=f'{interval}m'))
        df[-1]['up'], df[-1]['MA1'], df[-1]['low'] = BBANDS(df[-1]['Close'],
                                                            timeperiod=stack1[i],
                                                            nbdevup=upper[i],
                                                            nbdevdn=lower[i])
        _, _, df[-1]['loss'] = BBANDS(df[-1]['Close'], timeperiod=stack1[i], nbdevdn=lower[i])
        df[-1]['MA2'] = MA(df[-1]['Close'], timeperiod=stack2[i])
        df[-1]['EMA2'] = MA(df[-1]['Close'], timeperiod=stack2[i], matype=MA_Type.EMA)
        df[-1]['RSI'] = RSI(df[-1]['Close'])
    
    balance = 80000
    firstBalance, evalBalance = balance, balance
    askSize = 10000
    paa, size, minus, loss = [0]*len(df), [0]*len(df), [0]*len(df), [0]*len(df)
    overpay = 0
    countAsk, countBid = 0, 0
    for i in range(simulateStack, 0, -1):
        for s, symbol in enumerate(symbols):
            price = df[s]['Close'].iloc[-i]
            up = df[s]['up'].iloc[-i]
            low = df[s]['low'].iloc[-i]
            MA2 = df[s]['MA2'].iloc[-i]
            EMA2 = df[s]['EMA2'].iloc[-i]
            RSI1 = df[s]['RSI'].iloc[-i]
            lstMA2 = df[s]['MA2'].iloc[-i-1]
            lstEMA2 = df[s]['EMA2'].iloc[-i-1]
            ystMA2 = df[s]['MA2'].iloc[-stack1[s]-i]
            ystEMA2 = df[s]['EMA2'].iloc[-stack1[s]-i]
            if paa[s] != 0:
                if MA2 < loss[s]:
                    paa[s] = loss[s]
                    loss[s] = df[s]['loss'].iloc[-i]
                elif (0 < EMA2 - MA2 < ystEMA2 - ystMA2) and paa[s] < price*spread[s]*width[s] or up < price:
                #if up < price and RSI1 > 70 or paa < price and 0 < EMA2 - MA2 < ystEMA2 - ystMA2:
                    pab = float(calcPrice(symbol, price*spread[s]*1.0018))
                    balance = int(minus[s] + pab*size[s]) - math.ceil(pab*size[s]*0.0009)
                    evalBalance = int(evalBalance + pab*size[s]) - math.ceil(pab*size[s]*0.0009)
                    overpay += math.ceil(pab*size[s]*0.0009) - pab*size[s]*0.0009
                    paa[s] = 0
                    countBid += 1
            else:
                if evalBalance > askSize and (0 < MA2 - EMA2 < (lstMA2 - lstEMA2)/2 or price < low):
                #elif price < low and RSI1 < 30 and 0 < MA2 - EMA2 < ystMA2 - ystEMA2:
                    loss[s] = df[s]['loss'].iloc[-i]
                    paa[s] = float(calcPrice(symbol, price))
                    size[s] = float(calcSize(symbol, askSize/paa[s]))
                    minus[s] = int(balance - paa[s]*size[s]) - math.ceil(paa[s]*size[s]*0.0009)
                    evalBalance = int(evalBalance - paa[s]*size[s]) - math.ceil(paa[s]*size[s]*0.0009)
                    overpay += math.ceil(paa[s]*size[s]*0.0009) - paa[s]*size[s]*0.0009
                    countAsk += 1
        if i % (24*60/interval) == 1:
            balance += int(overpay)
            evalBalance += int(overpay)
            overpay = 0
            print([i, countAsk, countBid, balance, balance/firstBalance])


def bestStack(symbol, spread, stack1, stack2, upper, lower, simulateStack, interval):
    period = (interval*(simulateStack + stack2) + 60*24 - 1)//(60*24) + 1
    df = yfinance.Ticker(f'{symbol}-JPY').history(period=f'{period}d', interval=f'{interval}m')
    """
    rst = [0] * 7
    for i in range(max(12, stack1 - 12*6), stack1 + 12*6 + 1, 12):
        for j in range(max(12, stack2 - 12*6), stack2 + 12*6 + 1, 12):
            tmp = simulateTrade(symbol, df, spread, i, j, upper, lower, 1, simulateStack, interval)
            if tmp[-1] > rst[-1]:
                rst = tmp
    stack1, stack2 = rst[0], rst[1]
    
    rst = [0] * 7
    for i in range(max(10, int(10*upper) - 2*10), int(10*upper) + 2*10 + 1, 2):
        for j in range(max(10, int(10*lower) - 2*10), int(10*lower) + 2*10 + 1, 2):
            tmp = simulateTrade(symbol, df, spread, stack1, stack2, i/10, j/10, 1, simulateStack, interval)
            if tmp[-1] > rst[-1]:
                rst = tmp
    upper, lower = rst[2], rst[3]
    
    rst = [0] * 7
    for i in range(900, 1001, 5):
        tmp = simulateTrade(symbol, df, spread, stack1, stack2, upper, lower, i/1000, simulateStack, interval)
        if tmp[-1] > rst[-1]:
            rst = tmp
    """
    rst = simulateTrade(symbol, df, spread, stack1, stack2, upper, lower, 1, simulateStack, interval)
    print(f'{symbol}: {rst}')


stack1 = [24, 96, 96, 132, 72, 24, 132, 12, 96, 24, 36, 120, 156, 96, 12, 120, 96, 12, 12, 60]
stack2 = [132, 72, 108, 132, 60, 108, 96, 96, 108, 96, 168, 156, 156, 168, 120, 48, 180, 84, 120, 144]
upper = [4, 3.8, 3.4, 5, 5, 4.8, 4.8, 3.2, 3.8, 4.4, 4, 4, 4.8, 4.6, 3.4, 4.4, 5.8, 3.4, 3.4, 5]
lower = [3.2, 1.8, 1.8, 2.2, 2, 1.8, 3.2, 2, 2.8, 2.8, 1.8, 1.4, 2.2, 1.8, 1.8, 3.2, 1.8, 3, 2.2, 1.4]

#simulateTradeAll(stack1, stack2, upper, lower, [1]*20, 12*24*30, 5)

for i, s in enumerate(symbols):
    stack1[i] //= 3
    stack2[i] //= 3
    rst = bestStack(s, spread[i], stack1[i], stack2[i], 4, 3, 4*24*30, 15)
