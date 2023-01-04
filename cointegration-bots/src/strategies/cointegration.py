# -*- encoding: utf-8 -*-
# src/strategies/cointegration.py
# author: steinkirch
# Cointegration class.

import math
import pandas as pd
import numpy as np
import statsmodels.api as sm
from statsmodels.tsa.stattools import coint

import src.utils.os as utils

class Cointegrator:

    def __init__(self, env_vars: dict, currency=None):

        self._env_vars = env_vars
        self.currency = currency or 'USDT'
        self._pvalue_limit = float(self._env_vars['PLIMIT'])
        self._outdir = self._env_vars['OUTPUTDIR']
        self._price_file = self._env_vars['PRICE_HISTORY_FILE'].format(self.currency)
        self._cointegration_file = self._env_vars['COINTEGRATION_FILE'].format(self.currency)
        self._zscore_file = self._env_vars['ZSCORE_FILE'].format(self.currency)
        self._backtest_file = self._env_vars['BACKTEST_FILE']
        self.zscore_list = []
        self.backtest_df = None
        self.cointegration_results = [] 

    #########################
    #   private methods     #
    #########################
    def _get_price_history(self) -> dict:
        """Get price history for a given derivative."""
        
        price_history = utils.open_price_history(self._outdir, self._price_file)
        if price_history is None:
            utils.exit_with_error(f'You need to generate price history first.')
        
        return price_history

    def _extract_close_prices(self, prices_list: list) -> list:
        """Extract all close prices info into a list."""

        close_prices = []

        for prices in prices_list:
            try:
                if not math.isnan(prices["close"]):
                    close_prices.append(prices["close"])
            except KeyError:
                utils.log_error(f'Could not find close price for {prices}')

        return close_prices

    def _calculate_spread(self, first_set: list, second_set: list, hedge_ratio: float) -> list:
        """Calculate spread."""

        return pd.Series(first_set) - (pd.Series(second_set) * hedge_ratio)

    def _calculate_hedge_ration(self, first_set: list, second_set: list) -> float:
        """Calculate hedge ratio."""

        model = sm.OLS(first_set, second_set)
        return model.fit().params[0]

    def _calculate_zscore(self, spread: list) -> list:
        """Calculate zscore."""

        df = pd.DataFrame(spread)

        window = int(self._env_vars['ZSCORE_WINDOW'])
        mean = df.rolling(center=False, window=window).mean()
        std = df.rolling(center=False, window=window).std()
        x = df.rolling(center=False, window=1).mean()
        
        df["zscore"] = (x - mean) / std

        zscore = df["zscore"].astype(float).values
        self.zscore_list.append(zscore)
        return zscore

    def _get_cointegration_for_pair(self, first_set: list, second_set: list) -> dict:
        """Calculate co-integration for two tokens."""

        hot = False
        
        # calculate cointegration
        cointegration = coint(first_set, second_set)
        cointegration_value = cointegration[0]
        pvalue = cointegration[1]
        critical_value = cointegration[2][1]
        
        # calculate hedge ratio
        hedge_ratio = self._calculate_hedge_ration(first_set, second_set)
        
        # calculate spread
        spread = self._calculate_spread(first_set, second_set, hedge_ratio)
        zero_crossings = len(np.where(np.diff(np.sign(spread)))[0])

        # calculate zscore
        self._calculate_zscore(spread)

        # if pvalue is less than 0.05, we can reject the null hypothesis
        if pvalue < self._pvalue_limit and cointegration_value < critical_value:
            hot = True

        return {
                "hot": hot,
                "pvalue": round(pvalue, 3),
                "cointegration_value": cointegration_value,
                "critical_value": critical_value,
                "hedge_ratio": hedge_ratio,
                "zero_crossings": zero_crossings
                }


    def _save_backtest_data(self, coin1: str, coin2: str) -> None:
        """Save backtest data to file."""

        price_history = self._get_price_history()

        try:
            first_set = self._extract_close_prices(price_history[coin1])
            second_set = self._extract_close_prices(price_history[coin2])
        except KeyError:
            utils.exit_with_error(f"Price history does not have {coin1} or {coin2}.")

        df = pd.DataFrame()
        df[coin1] = first_set
        df[coin2] = second_set
        df[f'{coin1}_perc'] = df[coin1] / first_set[0]
        df[f'{coin2}_perc'] = df[coin2] / second_set[0]
        df['spread'] = self._calculate_spread(first_set, second_set, \
                                    self._calculate_hedge_ration(first_set, second_set))
        df['zscore'] = self._calculate_zscore(df['spread'])
        self.backtest_df = df

        self._backtest_file.format(coin1, coin2)
        utils.save_metrics(self.backtest_df, self._outdir, self._backtest_file)

    def _get_file_data(self, filepath) -> bool:
        """Check if a result file exists else calculates cointegration data."""

        if utils.file_exists(self._outdir, filepath):
            return utils.open_metrics(self._outdir, filepath)
        
        else:
            utils.log_info(f'Calculating cointegration first...')  
            self.get_cointegration()
            return None


    ###########################
    #      public methods     #
    ###########################

    def get_best_cointegrated_pairs(self, top: int) -> pd.DataFrame:
        """Get best cointegration pairs."""

        df = self._get_file_data(self._cointegration_file)
        if df is None:
            df = pd.DataFrame(self.cointegration_results)

        df.drop(columns=['hot'], inplace=True)
        df.sort_values(by=['pvalue'], inplace=True, ascending=False)
        return df.head(top)


    def get_cointegration(self) -> pd.DataFrame:
        """Get and store price history for all available pairs."""

        if utils.file_exists(self._outdir, self._cointegration_file) and \
                    utils.file_exists(self._outdir, self._zscore_file):
            return utils.open_metrics(self._outdir, self._cointegration_file)
 
        hot_pairs = []
        price_history = self._get_price_history()

        for symbol1 in price_history.keys():
            utils.log_info(f'Calculating cointegration for {symbol1}...')

            for symbol2 in price_history.keys():
                if symbol1 != symbol2:

                    this_symbol = "".join(sorted([symbol1, symbol2]))
                    if this_symbol in hot_pairs:
                        break

                    first_set = self._extract_close_prices(price_history[symbol1])
                    second_set = self._extract_close_prices(price_history[symbol2])

                    cointegration_dict = self._get_cointegration_for_pair(first_set, 
                                                                        second_set)

                    if cointegration_dict['hot'] == True:
                        utils.log_info(f'   ✅ Found a hot pair: {symbol1} and {symbol2}')
                        hot_pairs.append(this_symbol)
                        cointegration_dict['symbol1'] = symbol1
                        cointegration_dict['symbol2'] = symbol2
                        self.cointegration_results.append(cointegration_dict)
        
        utils.save_metrics(self.zscore_list, self._outdir, self._zscore_file)
        return utils.save_metrics(self.cointegration_results, self._outdir, \
                                self._cointegration_file, 'zero_crossings',)


    def get_zscore(self) -> pd.DataFrame:
        """Get z-score for a given window."""

        df = self._get_file_data(self._zscore_file)

        if df is None:
            df = pd.DataFrame(self.zscore_list)

        return df


    def get_backtests(self, coin1: str, coin2: str) -> pd.DataFrame:
        """Run backtests for all pairs, based on spread and zscore."""

        self._backtest_file = self._backtest_file.format(coin1, coin2)
        df = self._get_file_data(self._backtest_file)
        
        if df is None:
            self._save_backtest_data(coin1, coin2)
            df = self.backtest_df
        
        return df