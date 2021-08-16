import pyupbit
import pandas as pd
import numpy as np
import time

access = "your access"
secret = "your secret"

upbit = pyupbit.Upbit(access, secret)
print("autotrade start")

def get_balance(ticker):
    """잔고 조회""" #kRW입력시 원화 반환, 기타 KRW 제외 코인코드 입력시 수량 반환, 로그인 필요
    balances = upbit.get_balances()
    for b in balances:
        if b['currency'] == ticker:
            if b['balance'] is not None:
                return float(b['balance'])
            else:
                return 0
    return 0

coin_ticker = pyupbit.get_tickers(fiat="KRW")

for h in coin_ticker:
    a = (h.strip("KRW-"))
    locals()['buy_tf_{}'.format(a)] = 0

buy_list = []
sell_list = []

while True:
    try:

        for i in coin_ticker:
            
            coin_name = i.strip("KRW-")
            locals()['balance_{}'.format(coin_name)] = get_balance(coin_name)
            
            df = pyupbit.get_ohlcv(i, interval="minute30", count=40)
            df = df.reset_index()
            
            #MACD_B 계산
            df["MACD_short_B"]=df["close"].ewm(span=12).mean()
            df["MACD_long_B"]=df["close"].ewm(span=26).mean() 
            df["MACD_B"]=df.apply(lambda x: (x["MACD_short_B"]-x["MACD_long_B"]), axis=1) 
            df["MACD_signal_B"]=df["MACD_B"].ewm(span=9).mean() 
            df["MACD_oscillator_B"]=df.apply(lambda x:(x["MACD_B"]-x["MACD_signal_B"]), axis=1) 
            df["MACD_sign_B"]=np.where((df["MACD_B"]<0) & (df["MACD_B"]>df["MACD_signal_B"]),"Buy",
                            np.where((df["MACD_B"]>0) & (df["MACD_B"]<df["MACD_signal_B"]),"Sell","Wait"))
            
            #MACD_S 계산
            df["MACD_short_S"]=df["close"].ewm(span=19).mean()
            df["MACD_long_S"]=df["close"].ewm(span=39).mean() 
            df["MACD_S"]=df.apply(lambda x: (x["MACD_short_S"]-x["MACD_long_S"]), axis=1) 
            df["MACD_signal_S"]=df["MACD_S"].ewm(span=9).mean() 
            df["MACD_oscillator_S"]=df.apply(lambda x:(x["MACD_S"]-x["MACD_signal_S"]), axis=1) 
            df["MACD_sign_S"]=np.where((df["MACD_S"]<0) & (df["MACD_S"]>df["MACD_signal_S"]),"Buy",
                            np.where((df["MACD_S"]>0) & (df["MACD_S"]<df["MACD_signal_S"]),"Sell","Wait"))
            
            current_price = pyupbit.get_current_price(i)
            
            if df.loc[39,"MACD_sign_B"] == "Buy" and df.loc[39,"MACD_sign_S"] != "Sell" and locals()['buy_tf_{}'.format(coin_name)] == 0:
                #매수주문
                upbit.buy_market_order(i, 300000*0.9995)
                print('Buy')
                #매수수량 계산 
                time.sleep(3)
                locals()['quantity_{}'.format(coin_name)] = get_balance(coin_name) - locals()['balance_{}'.format(coin_name)]
                #매수내역 기록
                buy_list.append([i, df.loc[39,"index"], df.loc[39,"close"], current_price, locals()['quantity_{}'.format(coin_name)]])
                #거래현황 업데이트
                locals()['buy_tf_{}'.format(coin_name)] = 1
            
            elif df.loc[39,"MACD_sign_S"] == "Sell" and locals()['buy_tf_{}'.format(coin_name)] == 1:
                #매도주문
                upbit.sell_market_order(i, locals()['quantity_{}'.format(coin_name)]*0.9995)
                print('Sell')
                #매도내역 기록
                sell_list.append([i, df.loc[39,"index"], df.loc[39,"close"],current_price, locals()['quantity_{}'.format(coin_name)]])
                #거래현황 업데이트
                locals()['buy_tf_{}'.format(coin_name)] = 0  
            
            else: pass

            
            locals()['df_{}'.format(coin_name)] = df

    except Exception as e:
        print(e)
        time.sleep(1)
    