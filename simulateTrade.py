from talib import BBANDS
from talib import MA_Type
from talib import MA
from talib import RSI
import yfinance


def simulateTrade(df, spread, stack1, stack2, chartStack):
    upper, lower = 4, 2
    df['up'], df['MA1'], df['low'] = BBANDS(df['Close'],
                                            timeperiod=stack1,
                                            nbdevup=upper,
                                            nbdevdn=lower)
    df['MA2'] = MA(df['Close'], timeperiod=stack2)
    df['EMA2'] = MA(df['Close'], timeperiod=stack2, matype=MA_Type.EMA)
    df['RSI'] = RSI(df['Close'])
    
    balance = 100
    paa = 0
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
            if price < low:
                paa = price
            elif 0 < EMA2 - MA2 < ystEMA2 - ystMA2 and paa < price*spread or RSI1 > 70 and up < price:
            #if up < price and RSI1 > 70 or paa < price and 0 < EMA2 - MA2 < ystEMA2 - ystMA2:
                balance = balance * (price / paa) * spread
                paa = 0
                countBid += 1
        else:
            if MA2 - EMA2 < (lstMA2 - lstEMA2)/2 or price < low:
            #elif price < low and RSI1 < 30 and 0 < MA2 - EMA2 < ystMA2 - ystEMA2:
                paa = price
                countAsk += 1
    return (stack1, stack2, countAsk, countBid, balance)


def bestStack(ticker, spread, stack1, stack2, simulateStack, interval):
    period = (interval*(simulateStack + stack2) + 60*24 - 1)//(60*24) + 1
    df = ticker.history(period=f'{period}d', interval=f'{interval}m')
    
    rst5 = 0
    for i in range(max(4, stack1 - 4*3), stack1 + 4*3 + 1, 4):
        for j in range(max(4, stack2 - 4*3), stack2 + 4*3 + 1, 4):
            a, b, c, d, e = simulateTrade(df, spread, i, j, simulateStack)
            if e > rst5:
                rst1 = a
                rst2 = b
                rst3 = c
                rst4 = d
                rst5 = e
    
    #rst1, rst2, rst3, rst4, rst5 = simulateTrade(df, stack1, stack2, simulateStack)
    return (rst1, rst2, rst3, rst4, rst5)


symbols = ['SOL', 'DOGE', 'LINK', 'ADA', 'MONA', 'DAI', 'MKR', 'ATOM', 'DOT', 'ENJ', 'QTUM', 'XTZ', 'BAT', 'XLM', 'XEM', 'XRP', 'LTC', 'BCH', 'ETH', 'BTC']
spread = [0.9976560547348027, 0.9978123495145631, 0.9978608222901801, 0.9949580020159031, 0.9777939926199262,
          0.9923254334340702, 0.9931107644444445, 0.9975584832904885, 0.9955731578947368, 0.99450666,
          0.9880045910083421, 0.9920382716049382, 0.9947338411843876, 0.9941066535751415, 0.9943466222144235,
          0.9978335622764843, 0.9980113043478261, 0.9938609592573492, 0.9976541243939959, 0.9980151823736345]
stack1 = [12, 8, 12, 28, 36, 16, 40, 52, 20, 72, 40, 40, 60, 48, 48, 16, 24, 16, 12, 20]
stack2 = [4, 12, 4, 48, 56, 68, 64, 76, 40, 32, 72, 68, 12, 44, 52, 8, 20, 28, 16, 24]

for i, s in enumerate(symbols):
    if s != 'DAI':
        continue
    rst1, rst2, rst3, rst4, rst5 = bestStack(yfinance.Ticker(f'{s}-JPY'), spread[i], stack1[i], stack2[i], 12*24*30, 5)
    print(f'{s}: {rst1}, {rst2}, {rst3}, {rst4}, {rst5}')
