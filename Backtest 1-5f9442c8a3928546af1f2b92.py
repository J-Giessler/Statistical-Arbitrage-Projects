import quantopian.algorithm as algo
import quantopian.optimize as opt
import numpy as np
import pandas as pd
import statsmodels
import statsmodels.api as sm
from statsmodels.tsa.stattools import coint, adfuller
from quantopian.pipeline import Pipeline
from quantopian.pipeline.data.builtin import USEquityPricing
from quantopian.pipeline.factors.morningstar import MarketCap
from quantopian.pipeline.classifiers.morningstar import Sector
from quantopian.pipeline.data import morningstar
from quantopian.algorithm import attach_pipeline, pipeline_output
from quantopian.pipeline.data.morningstar import Fundamentals
from quantopian.pipeline.filters import Q1500US, QTradableStocksUS, Q3000US,  Q500US
stock2 = symbol('GLD')


def initialize(context):
    my_pipe = make_pipeline()
    algo.attach_pipeline(my_pipe, 'my_pipeline')
    algo.schedule_function(
        before_trading_start,
        algo.date_rules.month_start(),
        algo.time_rules.market_open(hours=5, minutes=30)
      )
    algo.schedule_function(
        coint_pairs,
        algo.date_rules.month_start(),
        algo.time_rules.market_open(hours=5, minutes=30)
      )
    algo.schedule_function(
        orders,
        algo.date_rules.every_day(),
        algo.time_rules.market_close(hours=5, minutes=30)
      )


def make_pipeline():
    
    my_sic = Fundamentals.morningstar_industry_code.latest.element_of([10150040,10106010])
    

    
    return Pipeline(
        columns={},
        screen=(my_sic ),
    )
def before_trading_start(context, data):
       context.output =  algo.pipeline_output('my_pipeline')
def coint_pairs(context,data):
    pairs = []
    print(context.output.index)
    for stock in context.output.index:
        price1 = data.history(stock, 'price',100, '1d')
        price2 = data.history(stock2, 'price',100, '1d')
        result = coint(price1, price2 )
        pvalue = result[1]
        if pvalue < 0.01:
            pairs.append(stock)
            
    return(pairs)

def orders(context,data):
     open_orders = get_open_orders()
     print(coint_pairs(context,data))
     for stock1 in coint_pairs(context,data):
            prices = data.history([stock1 ,stock2], 'price',200, '1d')
            if zscore(stock1,stock2,prices) > 1:
                if stock1 not in open_orders:
                 order_target_percent(stock1 , 1/len(coint_pairs(context,data))) 
    
            if zscore(stock1,stock2,prices) < 0.5 and zscore(stock1,stock2,prices)> -0.5:
                if stock1 not in open_orders:
                 order_target_percent(stock1 , 0.0)

            if zscore(stock1,stock2,prices)< -1:
                if stock1 not in open_orders:
                  order_target_percent(stock1 , -1/len(coint_pairs(context,data))) 
     for stock3 in context.output.index:
        
            if stock3 not in open_orders:
                 order_target_percent(stock3 , 0.0) 
                    

def zscore(stock_1,stock_2,prices):
    X1 = prices[stock_1]
    X2 = prices[stock_2]
    X1 = sm.add_constant(X1)
    results = sm.OLS(X2, X1).fit()
    X1 = X1[stock_1]
    b = results.params[stock_1]
    Z = X2 - b * X1
    zscore= (Z.iloc[199] - Z.mean()) / np.std(Z)
    return(zscore)