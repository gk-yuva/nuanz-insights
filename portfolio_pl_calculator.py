#!/usr/bin/env python3
"""
Portfolio P&L Calculator using Upstox API and MF API
Calculates real-time P&L for the portfolio holdings
"""

import requests
import json
import time
from datetime import datetime, timedelta
import pandas as pd
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class PortfolioPLCalculator:
    def __init__(self):
        # Upstox API Configuration - Secure with Environment Variables
        self.upstox_config = {
            'api_key': os.getenv('UPSTOX_API_KEY'),
            'api_secret': os.getenv('UPSTOX_API_SECRET'), 
            'access_token': os.getenv('UPSTOX_ACCESS_TOKEN'),
            'base_url': os.getenv('UPSTOX_BASE_URL', 'https://api.upstox.com/v2')
        }
        
        # Validate required environment variables
        if not all([self.upstox_config['api_key'], self.upstox_config['api_secret'], self.upstox_config['access_token']]):
            print("⚠️  Warning: Missing Upstox API credentials in environment variables")
            print("   Please check your .env file contains: UPSTOX_API_KEY, UPSTOX_API_SECRET, UPSTOX_ACCESS_TOKEN")
        
        # MF API Configuration
        self.mf_api_base = os.getenv('MF_API_BASE_URL', 'https://api.mfapi.in/mf')
        
        # Load portfolio data
        self.load_portfolio_data()
    
    def load_portfolio_data(self):
        """Load portfolio holdings from Excel file"""
        try:
            df = pd.read_excel('Portfolio Data_Hypothetical.xlsx')
            self.holdings = []
            
            for _, row in df.iterrows():
                holding = {
                    'instrument': row['Instrument'],
                    'quantity': row['Qty.'],
                    'avg_cost': row['Avg. cost'],
                    'invested': row['Invested'],
                    'current_value': row['Cur. val'],
                    'asset_class': row['Asset Class'],
                    'sector': row['Sector']
                }
                self.holdings.append(holding)
                
            print(f"Loaded {len(self.holdings)} holdings from portfolio")
            return True
            
        except Exception as e:
            print(f"Error loading portfolio data: {e}")
            return False
    
    def get_upstox_stock_price(self, symbol):
        """Get current stock price from Upstox API"""
        try:
            # Map symbol to Upstox format
            upstox_symbol = self.map_to_upstox_symbol(symbol)
            
            headers = {
                'Authorization': f'Bearer {self.upstox_config["access_token"]}',
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
            
            # Get current market data - LTP (Last Traded Price)
            url = f"{self.upstox_config['base_url']}/market-quote/ltp"
            # URL encode the instrument key properly
            import urllib.parse
            encoded_symbol = urllib.parse.quote(upstox_symbol, safe='')
            full_url = f"{url}?instrument_key={encoded_symbol}"
            
            print(f"Fetching price for {symbol} (Upstox: {upstox_symbol})")
            # Mask URL for security - don't log full API endpoints
            masked_url = f"{url}?instrument_key={upstox_symbol}"
            print(f"API URL: {masked_url}")
            
            response = requests.get(full_url, headers=headers, timeout=10)
            
            print(f"Upstox API Response Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"Upstox API Response: {data}")
                
                if data.get('status') == 'success' and 'data' in data:
                    # The response key might be different from the input key
                    # Look for any key that contains our symbol name or matches pattern
                    for key, price_data in data['data'].items():
                        if price_data and 'last_price' in price_data:
                            price = price_data['last_price']
                            print(f"✅ Got price for {symbol}: ₹{price}")
                            return price
            
            if response.status_code == 401:
                print(f"🔑 Upstox API: Access token expired for {symbol} (Status 401)")
                return "TOKEN_EXPIRED"
            else:
                print(f"❌ Upstox API failed for {symbol}: Status {response.status_code}, Response: {response.text}")
                return None
            
        except Exception as e:
            print(f"❌ Error getting Upstox price for {symbol}: {e}")
            return None
    
    def get_mf_nav(self, scheme_name):
        """Get current NAV from MF API"""
        try:
            # Search for scheme code first
            search_url = f"{self.mf_api_base}/search"
            params = {'q': scheme_name.replace(' ', '%20')}
            
            response = requests.get(search_url, params=params)
            
            if response.status_code == 200:
                search_results = response.json()
                
                if search_results and len(search_results) > 0:
                    # Take first match
                    scheme_code = search_results[0]['schemeCode']
                    
                    # Get NAV data
                    nav_url = f"{self.mf_api_base}/{scheme_code}"
                    nav_response = requests.get(nav_url)
                    
                    if nav_response.status_code == 200:
                        nav_data = nav_response.json()
                        if nav_data['meta']['fund_house']:
                            latest_nav = nav_data['data'][0]['nav']
                            return float(latest_nav)
            
            print(f"MF API failed for {scheme_name}")
            return None
            
        except Exception as e:
            print(f"Error getting MF NAV for {scheme_name}: {e}")
            return None
    
    def map_to_upstox_symbol(self, symbol):
        """Map portfolio symbols to Upstox instrument keys"""
        # Map your symbols to Upstox instrument format
        symbol_mapping = {
            'GOLD1': 'NSE_EQ|INE970I01023',  # GOLDBEES - Gold ETF
            'NATIONALUM': 'NSE_EQ|INE139A01034',  # NATIONALUM - National Aluminium Company
            'OIL': 'NSE_EQ|INE213A01029',  # ONGC - Oil and Natural Gas Corporation
        }
        
        return symbol_mapping.get(symbol, f'NSE_EQ|{symbol}')
    
    def calculate_portfolio_pl(self):
        """Calculate current P&L for entire portfolio"""
        try:
            total_invested = 0
            total_current_value = 0
            pl_details = []
            
            for holding in self.holdings:
                instrument = holding['instrument']
                quantity = holding['quantity']
                avg_cost = holding['avg_cost']
                invested = holding['invested']
                
                # Get current price based on asset class
                current_price = None
                
                if holding['asset_class'] == 'Equity':
                    current_price = self.get_upstox_stock_price(instrument)
                elif 'fund' in instrument.lower() or 'mutual' in instrument.lower():
                    current_nav = self.get_mf_nav(instrument)
                    current_price = current_nav
                
                if current_price and isinstance(current_price, (int, float)) and current_price > 0:
                    current_value = quantity * current_price
                    pl_amount = current_value - invested
                    pl_percentage = (pl_amount / invested) * 100 if invested > 0 else 0
                    
                    pl_details.append({
                        'instrument': instrument,
                        'invested': invested,
                        'current_value': current_value,
                        'pl_amount': pl_amount,
                        'pl_percentage': pl_percentage,
                        'current_price': current_price
                    })
                    
                    total_invested += invested
                    total_current_value += current_value
                else:
                    # Fallback to Excel data if API fails
                    current_value = holding['current_value']
                    total_invested += invested
                    total_current_value += current_value
                    
                    pl_details.append({
                        'instrument': instrument,
                        'invested': invested,
                        'current_value': current_value,
                        'pl_amount': current_value - invested,
                        'pl_percentage': ((current_value - invested) / invested) * 100 if invested > 0 else 0,
                        'current_price': 'API_FAILED'
                    })
            
            # Calculate overall P&L
            total_pl = total_current_value - total_invested
            total_pl_percentage = (total_pl / total_invested) * 100 if total_invested > 0 else 0
            
            return {
                'total_invested': total_invested,
                'total_current_value': total_current_value,
                'total_pl': total_pl,
                'total_pl_percentage': total_pl_percentage,
                'details': pl_details,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"Error calculating P&L: {e}")
            return None
    
    def get_pl_summary(self):
        """Get formatted P&L summary for dashboard"""
        pl_data = self.calculate_portfolio_pl()
        
        if pl_data:
            pl_amount = pl_data['total_pl']
            pl_percentage = pl_data['total_pl_percentage']
            
            # Format for display
            sign = '+' if pl_amount >= 0 else ''
            formatted_amount = f"₹{abs(pl_amount):,.2f}"
            formatted_percentage = f"{sign}{pl_percentage:.2f}%"
            
            return {
                'pl_text': f"{sign}{formatted_amount} ({formatted_percentage} today)",
                'pl_amount': pl_amount,
                'pl_percentage': pl_percentage,
                'status': 'success'
            }
        else:
            return {
                'pl_text': 'P&L calculation unavailable',
                'pl_amount': 0,
                'pl_percentage': 0,
                'status': 'error'
            }

# Example usage
if __name__ == "__main__":
    calculator = PortfolioPLCalculator()
    pl_summary = calculator.get_pl_summary()
    print(json.dumps(pl_summary, indent=2))