from flask import Flask, request, jsonify
from web3 import Web3
from web3.middleware import geth_poa_middleware
import pandas as pd
import json
from functools import cache
import threading 
import queue
import time
from concurrent.futures import ThreadPoolExecutor

app = Flask(__name__)

# Replace with the actual Optimism RPC URL
optimism_rpc_url = 'https://eon-rpc.horizenlabs.io/ethv1'

# Create a Web3 instance to connect to the Optimism blockchain
web3 = Web3(Web3.HTTPProvider(optimism_rpc_url))
web3.middleware_onion.inject(geth_poa_middleware, layer=0)

# LATEST_BLOCK = web3.eth.get_block_number()
LATEST_BLOCK = 951714 + 1
FROM_BLOCK = 951714
# FROM_BLOCK = 0

# Replace with the actual Aave V2 contract address
# contract_address = "0x871AfF0013bE6218B61b28b274a6F53DB131795F"


#gets how many decimals our reserve is
def get_reserve_decimals(reserve_address):
    decimals = 0
    if reserve_address == '0x38C2a6953F86a7453622B1E7103b738239728754': # dai
        decimals = 1e18
    elif reserve_address == '0xCc44eB064CD32AAfEEb2ebb2a47bE0B882383b53': # usdc
        decimals = 1e6
    elif reserve_address == '0xA167bcAb6791304EDa9B636C8beEC75b3D2829E6': # usdt
        decimals = 1e6
    elif reserve_address == '0x2c2E0B0c643aB9ad03adBe9140627A645E99E054': # weth
        decimals = 1e18
    elif reserve_address == '0x1d7fb99AED3C365B4DEf061B7978CE5055Dfc1e7': # wbtc
        decimals = 1e8
    
    return decimals
#gets our reserve price
#@cache
# def get_tx_usd_amount(reserve_address, token_amount):
#     contract_address = '0x8429d0AFade80498EAdb9919E41437A14d45A00B'
#     contract_abi = [{"inputs":[{"internalType":"address[]","name":"assets","type":"address[]"},{"internalType":"address[]","name":"sources","type":"address[]"},{"internalType":"address","name":"fallbackOracle","type":"address"},{"internalType":"address","name":"baseCurrency","type":"address"},{"internalType":"uint256","name":"baseCurrencyUnit","type":"uint256"}],"stateMutability":"nonpayable","type":"constructor"},{"anonymous":False,"inputs":[{"indexed":True,"internalType":"address","name":"asset","type":"address"},{"indexed":True,"internalType":"address","name":"source","type":"address"}],"name":"AssetSourceUpdated","type":"event"},{"anonymous":False,"inputs":[{"indexed":True,"internalType":"address","name":"baseCurrency","type":"address"},{"indexed":False,"internalType":"uint256","name":"baseCurrencyUnit","type":"uint256"}],"name":"BaseCurrencySet","type":"event"},{"anonymous":False,"inputs":[{"indexed":True,"internalType":"address","name":"fallbackOracle","type":"address"}],"name":"FallbackOracleUpdated","type":"event"},{"anonymous":False,"inputs":[{"indexed":True,"internalType":"address","name":"previousOwner","type":"address"},{"indexed":True,"internalType":"address","name":"newOwner","type":"address"}],"name":"OwnershipTransferred","type":"event"},{"inputs":[],"name":"BASE_CURRENCY","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"BASE_CURRENCY_UNIT","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"asset","type":"address"}],"name":"getAssetPrice","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address[]","name":"assets","type":"address[]"}],"name":"getAssetsPrices","outputs":[{"internalType":"uint256[]","name":"","type":"uint256[]"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"getFallbackOracle","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"asset","type":"address"}],"name":"getSourceOfAsset","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"owner","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"renounceOwnership","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address[]","name":"assets","type":"address[]"},{"internalType":"address[]","name":"sources","type":"address[]"}],"name":"setAssetSources","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"fallbackOracle","type":"address"}],"name":"setFallbackOracle","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"newOwner","type":"address"}],"name":"transferOwnership","outputs":[],"stateMutability":"nonpayable","type":"function"}]
#     contract = web3.eth.contract(address=contract_address, abi=contract_abi)
#     value_usd = contract.functions.getAssetPrice(reserve_address).call()
#     decimals = get_reserve_decimals(reserve_address)
#     usd_amount = (value_usd/1e18)*(token_amount/decimals)
#     # print(usd_amount)
#     return usd_amount

#gets our web3 contract object
# @cache
def get_contract():
    contract_address = "0x0fdbD7BAB654B5444c96FCc4956B8DF9CcC508bE"
    contract_abi = [{"type":"constructor","stateMutability":"nonpayable","inputs":[{"type":"address","name":"weth","internalType":"address"},{"type":"address","name":"provider","internalType":"address"}]},{"type":"event","name":"OwnershipTransferred","inputs":[{"type":"address","name":"previousOwner","internalType":"address","indexed":True},{"type":"address","name":"newOwner","internalType":"address","indexed":True}],"anonymous":False},{"type":"fallback","stateMutability":"payable"},{"type":"function","stateMutability":"nonpayable","outputs":[],"name":"authorizeLendingPool","inputs":[{"type":"address","name":"lendingPool","internalType":"address"}]},{"type":"function","stateMutability":"nonpayable","outputs":[],"name":"borrowETH","inputs":[{"type":"address","name":"lendingPool","internalType":"address"},{"type":"uint256","name":"amount","internalType":"uint256"},{"type":"uint256","name":"interesRateMode","internalType":"uint256"},{"type":"uint16","name":"referralCode","internalType":"uint16"}]},{"type":"function","stateMutability":"payable","outputs":[],"name":"depositETH","inputs":[{"type":"address","name":"lendingPool","internalType":"address"},{"type":"address","name":"onBehalfOf","internalType":"address"},{"type":"uint16","name":"referralCode","internalType":"uint16"}]},{"type":"function","stateMutability":"nonpayable","outputs":[],"name":"emergencyEtherTransfer","inputs":[{"type":"address","name":"to","internalType":"address"},{"type":"uint256","name":"amount","internalType":"uint256"}]},{"type":"function","stateMutability":"nonpayable","outputs":[],"name":"emergencyTokenTransfer","inputs":[{"type":"address","name":"token","internalType":"address"},{"type":"address","name":"to","internalType":"address"},{"type":"uint256","name":"amount","internalType":"uint256"}]},{"type":"function","stateMutability":"view","outputs":[{"type":"string","name":"","internalType":"string"}],"name":"getSignature","inputs":[]},{"type":"function","stateMutability":"view","outputs":[{"type":"address","name":"","internalType":"address"}],"name":"getWETHAddress","inputs":[]},{"type":"function","stateMutability":"view","outputs":[{"type":"address","name":"","internalType":"address"}],"name":"owner","inputs":[]},{"type":"function","stateMutability":"nonpayable","outputs":[],"name":"renounceOwnership","inputs":[]},{"type":"function","stateMutability":"payable","outputs":[],"name":"repayETH","inputs":[{"type":"address","name":"lendingPool","internalType":"address"},{"type":"uint256","name":"amount","internalType":"uint256"},{"type":"uint256","name":"rateMode","internalType":"uint256"},{"type":"address","name":"onBehalfOf","internalType":"address"}]},{"type":"function","stateMutability":"nonpayable","outputs":[],"name":"setSignature","inputs":[{"type":"string","name":"signature","internalType":"string"}]},{"type":"function","stateMutability":"nonpayable","outputs":[],"name":"transferOwnership","inputs":[{"type":"address","name":"newOwner","internalType":"address"}]},{"type":"function","stateMutability":"nonpayable","outputs":[],"name":"withdrawETH","inputs":[{"type":"address","name":"lendingPool","internalType":"address"},{"type":"uint256","name":"amount","internalType":"uint256"},{"type":"address","name":"to","internalType":"address"}]},{"type":"receive","stateMutability":"payable"}]
    
    contract = web3.eth.contract(address=contract_address, abi=contract_abi)

    return contract

# gets the last block number we have gotten data from and returns this block number
def get_last_block_tracked():
    df = pd.read_csv('all_users.csv')
    
    last_block_monitored = df['last_block_number'].max()

    last_block_monitored = int(last_block_monitored)

    return last_block_monitored

print(get_last_block_tracked())

#makes a dataframe and stores it in a csv file
def make_user_data_csv(df):
    old_df = pd.read_csv('all_users.csv')
    old_df = old_df.drop_duplicates(subset=['wallet_address','tx_hash','number_of_tokens','block_number'], keep='last')

    combined_df_list = [df, old_df]

    combined_df = pd.concat(combined_df_list)
    combined_df = combined_df.drop_duplicates(subset=['wallet_address','tx_hash','number_of_tokens','block_number'], keep='last')

    combined_df['tx_hash'] = combined_df['tx_hash'].str.lower()
    combined_df['wallet_address'] = combined_df['wallet_address'].str.lower()

    # print(df)
    # print(len(old_df), len(df), len(combined_df))

    if len(combined_df) >= len(old_df):
        combined_df['last_block_number'] = int(df['last_block_number'].max())
        combined_df.to_csv('all_users.csv', index=False)
        print('CSV Made')

    elif len(combined_df) > 0:
        combined_df['last_block_number'] = int(df['last_block_number'].max())
        combined_df.to_csv('all_users.csv', index=False)
        print('CSV Made')
    
    return

def get_a_yuzu_zen_contract():
    contract_address = "0xEB329420Fae03176EC5877c34E2c38580D85E069"
    contract_abi = [{"type":"event","name":"Approval","inputs":[{"type":"address","name":"owner","internalType":"address","indexed":True},{"type":"address","name":"spender","internalType":"address","indexed":True},{"type":"uint256","name":"value","internalType":"uint256","indexed":False}],"anonymous":False},{"type":"event","name":"BalanceTransfer","inputs":[{"type":"address","name":"from","internalType":"address","indexed":True},{"type":"address","name":"to","internalType":"address","indexed":True},{"type":"uint256","name":"value","internalType":"uint256","indexed":False},{"type":"uint256","name":"index","internalType":"uint256","indexed":False}],"anonymous":False},{"type":"event","name":"Burn","inputs":[{"type":"address","name":"from","internalType":"address","indexed":True},{"type":"address","name":"target","internalType":"address","indexed":True},{"type":"uint256","name":"value","internalType":"uint256","indexed":False},{"type":"uint256","name":"index","internalType":"uint256","indexed":False}],"anonymous":False},{"type":"event","name":"Initialized","inputs":[{"type":"address","name":"underlyingAsset","internalType":"address","indexed":True},{"type":"address","name":"pool","internalType":"address","indexed":True},{"type":"address","name":"treasury","internalType":"address","indexed":False},{"type":"address","name":"incentivesController","internalType":"address","indexed":False},{"type":"uint8","name":"aTokenDecimals","internalType":"uint8","indexed":False},{"type":"string","name":"aTokenName","internalType":"string","indexed":False},{"type":"string","name":"aTokenSymbol","internalType":"string","indexed":False},{"type":"bytes","name":"params","internalType":"bytes","indexed":False}],"anonymous":False},{"type":"event","name":"Mint","inputs":[{"type":"address","name":"from","internalType":"address","indexed":True},{"type":"uint256","name":"value","internalType":"uint256","indexed":False},{"type":"uint256","name":"index","internalType":"uint256","indexed":False}],"anonymous":False},{"type":"event","name":"Transfer","inputs":[{"type":"address","name":"from","internalType":"address","indexed":True},{"type":"address","name":"to","internalType":"address","indexed":True},{"type":"uint256","name":"value","internalType":"uint256","indexed":False}],"anonymous":False},{"type":"function","stateMutability":"view","outputs":[{"type":"uint256","name":"","internalType":"uint256"}],"name":"ATOKEN_REVISION","inputs":[]},{"type":"function","stateMutability":"view","outputs":[{"type":"bytes32","name":"","internalType":"bytes32"}],"name":"DOMAIN_SEPARATOR","inputs":[]},{"type":"function","stateMutability":"view","outputs":[{"type":"bytes","name":"","internalType":"bytes"}],"name":"EIP712_REVISION","inputs":[]},{"type":"function","stateMutability":"view","outputs":[{"type":"bytes32","name":"","internalType":"bytes32"}],"name":"PERMIT_TYPEHASH","inputs":[]},{"type":"function","stateMutability":"view","outputs":[{"type":"address","name":"","internalType":"contract ILendingPool"}],"name":"POOL","inputs":[]},{"type":"function","stateMutability":"view","outputs":[{"type":"address","name":"","internalType":"address"}],"name":"RESERVE_TREASURY_ADDRESS","inputs":[]},{"type":"function","stateMutability":"view","outputs":[{"type":"address","name":"","internalType":"address"}],"name":"UNDERLYING_ASSET_ADDRESS","inputs":[]},{"type":"function","stateMutability":"view","outputs":[{"type":"uint256","name":"","internalType":"uint256"}],"name":"_nonces","inputs":[{"type":"address","name":"","internalType":"address"}]},{"type":"function","stateMutability":"view","outputs":[{"type":"uint256","name":"","internalType":"uint256"}],"name":"allowance","inputs":[{"type":"address","name":"owner","internalType":"address"},{"type":"address","name":"spender","internalType":"address"}]},{"type":"function","stateMutability":"nonpayable","outputs":[{"type":"bool","name":"","internalType":"bool"}],"name":"approve","inputs":[{"type":"address","name":"spender","internalType":"address"},{"type":"uint256","name":"amount","internalType":"uint256"}]},{"type":"function","stateMutability":"view","outputs":[{"type":"uint256","name":"","internalType":"uint256"}],"name":"balanceOf","inputs":[{"type":"address","name":"user","internalType":"address"}]},{"type":"function","stateMutability":"nonpayable","outputs":[],"name":"burn","inputs":[{"type":"address","name":"user","internalType":"address"},{"type":"address","name":"receiverOfUnderlying","internalType":"address"},{"type":"uint256","name":"amount","internalType":"uint256"},{"type":"uint256","name":"index","internalType":"uint256"}]},{"type":"function","stateMutability":"view","outputs":[{"type":"uint8","name":"","internalType":"uint8"}],"name":"decimals","inputs":[]},{"type":"function","stateMutability":"nonpayable","outputs":[{"type":"bool","name":"","internalType":"bool"}],"name":"decreaseAllowance","inputs":[{"type":"address","name":"spender","internalType":"address"},{"type":"uint256","name":"subtractedValue","internalType":"uint256"}]},{"type":"function","stateMutability":"view","outputs":[{"type":"address","name":"","internalType":"contract IRewarder"}],"name":"getIncentivesController","inputs":[]},{"type":"function","stateMutability":"view","outputs":[{"type":"uint256","name":"","internalType":"uint256"},{"type":"uint256","name":"","internalType":"uint256"}],"name":"getScaledUserBalanceAndSupply","inputs":[{"type":"address","name":"user","internalType":"address"}]},{"type":"function","stateMutability":"nonpayable","outputs":[],"name":"handleRepayment","inputs":[{"type":"address","name":"user","internalType":"address"},{"type":"uint256","name":"amount","internalType":"uint256"}]},{"type":"function","stateMutability":"nonpayable","outputs":[{"type":"bool","name":"","internalType":"bool"}],"name":"increaseAllowance","inputs":[{"type":"address","name":"spender","internalType":"address"},{"type":"uint256","name":"addedValue","internalType":"uint256"}]},{"type":"function","stateMutability":"nonpayable","outputs":[],"name":"initialize","inputs":[{"type":"address","name":"pool","internalType":"contract ILendingPool"},{"type":"address","name":"treasury","internalType":"address"},{"type":"address","name":"underlyingAsset","internalType":"address"},{"type":"address","name":"incentivesController","internalType":"contract IRewarder"},{"type":"uint8","name":"aTokenDecimals","internalType":"uint8"},{"type":"string","name":"aTokenName","internalType":"string"},{"type":"string","name":"aTokenSymbol","internalType":"string"},{"type":"bytes","name":"params","internalType":"bytes"}]},{"type":"function","stateMutability":"nonpayable","outputs":[{"type":"bool","name":"","internalType":"bool"}],"name":"mint","inputs":[{"type":"address","name":"user","internalType":"address"},{"type":"uint256","name":"amount","internalType":"uint256"},{"type":"uint256","name":"index","internalType":"uint256"}]},{"type":"function","stateMutability":"nonpayable","outputs":[],"name":"mintToTreasury","inputs":[{"type":"uint256","name":"amount","internalType":"uint256"},{"type":"uint256","name":"index","internalType":"uint256"}]},{"type":"function","stateMutability":"view","outputs":[{"type":"string","name":"","internalType":"string"}],"name":"name","inputs":[]},{"type":"function","stateMutability":"nonpayable","outputs":[],"name":"permit","inputs":[{"type":"address","name":"owner","internalType":"address"},{"type":"address","name":"spender","internalType":"address"},{"type":"uint256","name":"value","internalType":"uint256"},{"type":"uint256","name":"deadline","internalType":"uint256"},{"type":"uint8","name":"v","internalType":"uint8"},{"type":"bytes32","name":"r","internalType":"bytes32"},{"type":"bytes32","name":"s","internalType":"bytes32"}]},{"type":"function","stateMutability":"view","outputs":[{"type":"uint256","name":"","internalType":"uint256"}],"name":"scaledBalanceOf","inputs":[{"type":"address","name":"user","internalType":"address"}]},{"type":"function","stateMutability":"view","outputs":[{"type":"uint256","name":"","internalType":"uint256"}],"name":"scaledTotalSupply","inputs":[]},{"type":"function","stateMutability":"view","outputs":[{"type":"string","name":"","internalType":"string"}],"name":"symbol","inputs":[]},{"type":"function","stateMutability":"view","outputs":[{"type":"uint256","name":"","internalType":"uint256"}],"name":"totalSupply","inputs":[]},{"type":"function","stateMutability":"nonpayable","outputs":[{"type":"bool","name":"","internalType":"bool"}],"name":"transfer","inputs":[{"type":"address","name":"recipient","internalType":"address"},{"type":"uint256","name":"amount","internalType":"uint256"}]},{"type":"function","stateMutability":"nonpayable","outputs":[{"type":"bool","name":"","internalType":"bool"}],"name":"transferFrom","inputs":[{"type":"address","name":"sender","internalType":"address"},{"type":"address","name":"recipient","internalType":"address"},{"type":"uint256","name":"amount","internalType":"uint256"}]},{"type":"function","stateMutability":"nonpayable","outputs":[],"name":"transferOnLiquidation","inputs":[{"type":"address","name":"from","internalType":"address"},{"type":"address","name":"to","internalType":"address"},{"type":"uint256","name":"value","internalType":"uint256"}]},{"type":"function","stateMutability":"nonpayable","outputs":[{"type":"uint256","name":"","internalType":"uint256"}],"name":"transferUnderlyingTo","inputs":[{"type":"address","name":"target","internalType":"address"},{"type":"uint256","name":"amount","internalType":"uint256"}]}]
    
    contract = web3.eth.contract(address=contract_address, abi=contract_abi)

    return contract

def get_v_yuzu_zen_contract():
    contract_address = "0xBE8afE7E442fFfFE576B979D490c5ADb7823C3c6"
    contract_abi = [{"type":"event","name":"Approval","inputs":[{"type":"address","name":"owner","internalType":"address","indexed":True},{"type":"address","name":"spender","internalType":"address","indexed":True},{"type":"uint256","name":"value","internalType":"uint256","indexed":False}],"anonymous":False},{"type":"event","name":"BorrowAllowanceDelegated","inputs":[{"type":"address","name":"fromUser","internalType":"address","indexed":True},{"type":"address","name":"toUser","internalType":"address","indexed":True},{"type":"address","name":"asset","internalType":"address","indexed":False},{"type":"uint256","name":"amount","internalType":"uint256","indexed":False}],"anonymous":False},{"type":"event","name":"Burn","inputs":[{"type":"address","name":"user","internalType":"address","indexed":True},{"type":"uint256","name":"amount","internalType":"uint256","indexed":False},{"type":"uint256","name":"currentBalance","internalType":"uint256","indexed":False},{"type":"uint256","name":"balanceIncrease","internalType":"uint256","indexed":False},{"type":"uint256","name":"avgStableRate","internalType":"uint256","indexed":False},{"type":"uint256","name":"newTotalSupply","internalType":"uint256","indexed":False}],"anonymous":False},{"type":"event","name":"Initialized","inputs":[{"type":"address","name":"underlyingAsset","internalType":"address","indexed":True},{"type":"address","name":"pool","internalType":"address","indexed":True},{"type":"address","name":"incentivesController","internalType":"address","indexed":False},{"type":"uint8","name":"debtTokenDecimals","internalType":"uint8","indexed":False},{"type":"string","name":"debtTokenName","internalType":"string","indexed":False},{"type":"string","name":"debtTokenSymbol","internalType":"string","indexed":False},{"type":"bytes","name":"params","internalType":"bytes","indexed":False}],"anonymous":False},{"type":"event","name":"Mint","inputs":[{"type":"address","name":"user","internalType":"address","indexed":True},{"type":"address","name":"onBehalfOf","internalType":"address","indexed":True},{"type":"uint256","name":"amount","internalType":"uint256","indexed":False},{"type":"uint256","name":"currentBalance","internalType":"uint256","indexed":False},{"type":"uint256","name":"balanceIncrease","internalType":"uint256","indexed":False},{"type":"uint256","name":"newRate","internalType":"uint256","indexed":False},{"type":"uint256","name":"avgStableRate","internalType":"uint256","indexed":False},{"type":"uint256","name":"newTotalSupply","internalType":"uint256","indexed":False}],"anonymous":False},{"type":"event","name":"Transfer","inputs":[{"type":"address","name":"from","internalType":"address","indexed":True},{"type":"address","name":"to","internalType":"address","indexed":True},{"type":"uint256","name":"value","internalType":"uint256","indexed":False}],"anonymous":False},{"type":"function","stateMutability":"view","outputs":[{"type":"uint256","name":"","internalType":"uint256"}],"name":"DEBT_TOKEN_REVISION","inputs":[]},{"type":"function","stateMutability":"view","outputs":[{"type":"address","name":"","internalType":"contract ILendingPool"}],"name":"POOL","inputs":[]},{"type":"function","stateMutability":"view","outputs":[{"type":"address","name":"","internalType":"address"}],"name":"UNDERLYING_ASSET_ADDRESS","inputs":[]},{"type":"function","stateMutability":"view","outputs":[{"type":"uint256","name":"","internalType":"uint256"}],"name":"allowance","inputs":[{"type":"address","name":"owner","internalType":"address"},{"type":"address","name":"spender","internalType":"address"}]},{"type":"function","stateMutability":"nonpayable","outputs":[{"type":"bool","name":"","internalType":"bool"}],"name":"approve","inputs":[{"type":"address","name":"spender","internalType":"address"},{"type":"uint256","name":"amount","internalType":"uint256"}]},{"type":"function","stateMutability":"nonpayable","outputs":[],"name":"approveDelegation","inputs":[{"type":"address","name":"delegatee","internalType":"address"},{"type":"uint256","name":"amount","internalType":"uint256"}]},{"type":"function","stateMutability":"view","outputs":[{"type":"uint256","name":"","internalType":"uint256"}],"name":"balanceOf","inputs":[{"type":"address","name":"account","internalType":"address"}]},{"type":"function","stateMutability":"view","outputs":[{"type":"uint256","name":"","internalType":"uint256"}],"name":"borrowAllowance","inputs":[{"type":"address","name":"fromUser","internalType":"address"},{"type":"address","name":"toUser","internalType":"address"}]},{"type":"function","stateMutability":"nonpayable","outputs":[],"name":"burn","inputs":[{"type":"address","name":"user","internalType":"address"},{"type":"uint256","name":"amount","internalType":"uint256"}]},{"type":"function","stateMutability":"view","outputs":[{"type":"uint8","name":"","internalType":"uint8"}],"name":"decimals","inputs":[]},{"type":"function","stateMutability":"nonpayable","outputs":[{"type":"bool","name":"","internalType":"bool"}],"name":"decreaseAllowance","inputs":[{"type":"address","name":"spender","internalType":"address"},{"type":"uint256","name":"subtractedValue","internalType":"uint256"}]},{"type":"function","stateMutability":"view","outputs":[{"type":"uint256","name":"","internalType":"uint256"}],"name":"getAverageStableRate","inputs":[]},{"type":"function","stateMutability":"view","outputs":[{"type":"address","name":"","internalType":"contract IRewarder"}],"name":"getIncentivesController","inputs":[]},{"type":"function","stateMutability":"view","outputs":[{"type":"uint256","name":"","internalType":"uint256"},{"type":"uint256","name":"","internalType":"uint256"},{"type":"uint256","name":"","internalType":"uint256"},{"type":"uint40","name":"","internalType":"uint40"}],"name":"getSupplyData","inputs":[]},{"type":"function","stateMutability":"view","outputs":[{"type":"uint256","name":"","internalType":"uint256"},{"type":"uint256","name":"","internalType":"uint256"}],"name":"getTotalSupplyAndAvgRate","inputs":[]},{"type":"function","stateMutability":"view","outputs":[{"type":"uint40","name":"","internalType":"uint40"}],"name":"getTotalSupplyLastUpdated","inputs":[]},{"type":"function","stateMutability":"view","outputs":[{"type":"uint40","name":"","internalType":"uint40"}],"name":"getUserLastUpdated","inputs":[{"type":"address","name":"user","internalType":"address"}]},{"type":"function","stateMutability":"view","outputs":[{"type":"uint256","name":"","internalType":"uint256"}],"name":"getUserStableRate","inputs":[{"type":"address","name":"user","internalType":"address"}]},{"type":"function","stateMutability":"nonpayable","outputs":[{"type":"bool","name":"","internalType":"bool"}],"name":"increaseAllowance","inputs":[{"type":"address","name":"spender","internalType":"address"},{"type":"uint256","name":"addedValue","internalType":"uint256"}]},{"type":"function","stateMutability":"nonpayable","outputs":[],"name":"initialize","inputs":[{"type":"address","name":"pool","internalType":"contract ILendingPool"},{"type":"address","name":"underlyingAsset","internalType":"address"},{"type":"address","name":"incentivesController","internalType":"contract IRewarder"},{"type":"uint8","name":"debtTokenDecimals","internalType":"uint8"},{"type":"string","name":"debtTokenName","internalType":"string"},{"type":"string","name":"debtTokenSymbol","internalType":"string"},{"type":"bytes","name":"params","internalType":"bytes"}]},{"type":"function","stateMutability":"nonpayable","outputs":[{"type":"bool","name":"","internalType":"bool"}],"name":"mint","inputs":[{"type":"address","name":"user","internalType":"address"},{"type":"address","name":"onBehalfOf","internalType":"address"},{"type":"uint256","name":"amount","internalType":"uint256"},{"type":"uint256","name":"rate","internalType":"uint256"}]},{"type":"function","stateMutability":"view","outputs":[{"type":"string","name":"","internalType":"string"}],"name":"name","inputs":[]},{"type":"function","stateMutability":"view","outputs":[{"type":"uint256","name":"","internalType":"uint256"}],"name":"principalBalanceOf","inputs":[{"type":"address","name":"user","internalType":"address"}]},{"type":"function","stateMutability":"view","outputs":[{"type":"string","name":"","internalType":"string"}],"name":"symbol","inputs":[]},{"type":"function","stateMutability":"view","outputs":[{"type":"uint256","name":"","internalType":"uint256"}],"name":"totalSupply","inputs":[]},{"type":"function","stateMutability":"nonpayable","outputs":[{"type":"bool","name":"","internalType":"bool"}],"name":"transfer","inputs":[{"type":"address","name":"recipient","internalType":"address"},{"type":"uint256","name":"amount","internalType":"uint256"}]},{"type":"function","stateMutability":"nonpayable","outputs":[{"type":"bool","name":"","internalType":"bool"}],"name":"transferFrom","inputs":[{"type":"address","name":"sender","internalType":"address"},{"type":"address","name":"recipient","internalType":"address"},{"type":"uint256","name":"amount","internalType":"uint256"}]}]    
    contract = web3.eth.contract(address=contract_address, abi=contract_abi)

    return contract


def get_a_yuzu_zen_transfers(contract):
    
    events = contract.events.Transfer.get_logs(fromBlock=FROM_BLOCK, toBlock=LATEST_BLOCK)
    
    return events

def get_deposits(events):

    for event in events:
        tx_from = event['args']['from'].lower()
        tx_to = event['args']['to'].lower() != "0x0fdbD7BAB654B5444c96FCc4956B8DF9CcC508bE".lower()

        if event['args']['from'].lower() == "0x0000000000000000000000000000000000000000" and event['args']['to'].lower() != "0x0fdbD7BAB654B5444c96FCc4956B8DF9CcC508bE".lower():
            print(event['args']['from'])
            print(event['args']['to'])
            print(event['args']['value'])
            print(event['address'])
            print(event['transactionHash'].hex())
    return


# contract = get_a_yuzu_zen_contract()
contract = get_v_yuzu_zen_contract()
events = get_a_yuzu_zen_transfers(contract)
get_deposits(events)

# find block_numbers that have 
def is_trancation_we_want_to_track(transaction):

    if transaction['to'] == '0x89Aca10e0cb228239c0Aa71729E14D60867299aB':
        print(transaction)

    return

# Gets transactions of all blocks within a specified range and returns a df with info from blocks that include our contract
def get_all_gateway_transactions():

    weth_gateway_address = "0x0fdbD7BAB654B5444c96FCc4956B8DF9CcC508bE"

    # from_block = get_last_block_tracked()

    from_block = 946990

    print('Last Block Number: ', from_block)
    # from_block = 940460

    tx_hash_list = []
    value_list = []
    user_address_list = []
    block_number_list = []

    i = 0
    blocks_to_cover = LATEST_BLOCK - from_block
    
    last_block_number = 0
    # adds our values to our above lists
    for block_number in range(from_block, LATEST_BLOCK + 1):
        block = web3.eth.get_block(block_number)
        tx_hashes = block.transactions

        print(i, '/', blocks_to_cover)
        i += 1

        for tx_hash in tx_hashes:
            transaction = web3.eth.get_transaction(tx_hash)
            print(transaction)
            print('')
            if transaction['to'] == weth_gateway_address:
               # print(transaction)
                user_address_list.append(transaction['from'])
                tx_hash_list.append(transaction['hash'].hex())
                value_list.append(transaction['value'])
                block_number_list.append(transaction['blockNumber'])
        
        last_block_number = int(block_number)
                # print('found')

    print('Last Block Number: ', last_block_number)


    # handles blank dataframes
    if len(user_address_list) < 1:
        df = pd.read_csv('all_users.csv')
        df['last_block_number'] = last_block_number

    else:
        df = pd.DataFrame()
        df['wallet_address'] = user_address_list
        df['tx_hash'] = tx_hash_list
        df['number_of_tokens'] = value_list
        df['block_number'] = block_number_list
        df['last_block_number'] = last_block_number

    make_user_data_csv(df)

# get_all_gateway_transactions()

#gets the ids of all twitter followers of yuzu
# twitter api yahooooooo
def get_all_twitter_follows():
    return


# formats our dataframe response
def make_api_response_string(df):
    
    data = []

    quest_complete = 'False'

    #if we have an address with no transactions
    if len(df) < 1:
        quest_complete = 'False'

    else:
        quest_complete = 'True'

    # Create JSON response
    response = {
        "error": {
            "code": 0,
            "message": "success"
        },
        "data": {
            "result": quest_complete
        }
    }
    
    return response

# reads csv for twitter kids
def search_and_respond(twitter_id, queue):

    df = pd.read_csv('twitter_users.csv')

    df = df.loc[df['follower_id'] == twitter_id]

    response = make_api_response_string(df)

    queue.put(response)

# just reads from csv file
def search_and_respond_2(address, queue):
    
    df = pd.read_csv('all_users.csv')

    df = df.loc[df['wallet_address'] == address]

    response = make_api_response_string(df)

    queue.put(response)

#reads from csv
@app.route("/transactions/", methods=["POST"])
def get_transactions():

    data = json.loads(request.data)  # Parse JSON string into JSON object

    #used to help determine if we received an address or a twitter profile
    is_address = True

    if "address" in data:
        address = data["address"].lower()
        response = "Address Sent"
        print("Address Sent")
        is_address = True

    elif "twitter" in data:
        twitter = data["twitter"].lower()
        response = "Twitter Sent"
        print("Twitter Sent")
        is_address = False

    # Create a queue to store the search result
    result_queue = queue.Queue()

    # search_and_respond_2(address, result_queue)
    if is_address == True:
        thread = threading.Thread(target=search_and_respond_2, args=(address, result_queue))
        thread.start()
    
    else:
        thread = threading.Thread(target=search_and_respond, args=(twitter, result_queue))
        thread.start()
    response = result_queue.get()

    return jsonify(response), 200

# if __name__ == "__main__":
#     app.run()

get_all_gateway_transactions()
