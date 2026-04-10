#!/usr/bin/env python3
"""
Actual Capital Analysis from Trading Excel Files
Calculate real capital invested based on position sizes, margins, and turnover
"""

import pandas as pd
import numpy as np
from datetime import datetime
import json

def analyze_actual_capital_from_excel():
    """Analyze actual capital from your Excel trading files"""

    print("🔍 ANALYZING ACTUAL CAPITAL FROM TRADING FILES")
    print("=" * 60)

    # File paths
    fno_file = '/Users/Subho/Downloads/F&O_PnL_Report_6917002522_2023-04-01_2025-08-05..xlsx'
    stock_file = '/Users/Subho/Downloads/Stocks_PnL_Report_6917002522_01-04-2020_30-11-2024.xlsx'

    capital_analysis = {}

    # Analyze F&O capital
    try:
        print("\n📊 Analyzing F&O Trading Capital...")

        # Try different sheets that might contain capital data
        sheets = pd.ExcelFile(fno_file).sheet_names
        print(f"Available sheets: {sheets}")

        capital_analysis['f&o'] = analyze_fno_capital(fno_file, sheets)

    except Exception as e:
        print(f"Error analyzing F&O file: {e}")
        capital_analysis['f&o'] = {"error": str(e)}

    # Analyze Stock capital
    try:
        print("\n📈 Analyzing Stock Trading Capital...")

        sheets = pd.ExcelFile(stock_file).sheet_names
        print(f"Available sheets: {sheets}")

        capital_analysis['stocks'] = analyze_stock_capital(stock_file, sheets)

    except Exception as e:
        print(f"Error analyzing Stock file: {e}")
        capital_analysis['stocks'] = {"error": str(e)}

    # Calculate total capital and opportunity cost
    total_analysis = calculate_total_opportunity_cost(capital_analysis)

    # Save results
    with open('/Users/Subho/actual_capital_analysis_results.json', 'w') as f:
        json.dump(total_analysis, f, indent=2)

    print(f"\n📄 Analysis saved: actual_capital_analysis_results.json")

    return total_analysis

def analyze_fno_capital(file_path, sheets):
    """Analyze F&O capital requirements from Excel data"""

    analysis = {}

    # Look for position data in different sheets
    for sheet_name in sheets:
        try:
            print(f"  Analyzing sheet: {sheet_name}")
            df = pd.read_excel(file_path, sheet_name=sheet_name)

            print(f"  Columns: {list(df.columns)}")
            print(f"  Rows: {len(df)}")

            # Look for capital-related columns
            capital_cols = []
            for col in df.columns:
                col_lower = str(col).lower()
                if any(keyword in col_lower for keyword in ['margin', 'capital', 'investment', 'value', 'turnover', 'buy', 'sell', 'quantity']):
                    capital_cols.append(col)

            if capital_cols:
                print(f"  Capital-related columns found: {capital_cols}")

                # Analyze numeric columns
                for col in capital_cols:
                    if df[col].dtype in ['float64', 'int64']:
                        max_val = df[col].max()
                        min_val = df[col].min()
                        mean_val = df[col].mean()
                        print(f"    {col}: Max={max_val:,.0f}, Min={min_val:,.0f}, Avg={mean_val:,.0f}")

                # Sample some data
                print(f"  Sample data from {sheet_name}:")
                print(df.head(3).to_string())

                analysis[sheet_name] = {
                    "capital_columns": capital_cols,
                    "total_rows": len(df),
                    "data_sample": df.head(3).to_dict() if len(df) > 0 else None
                }

        except Exception as e:
            print(f"    Error analyzing {sheet_name}: {e}")
            continue

    return analysis

def analyze_stock_capital(file_path, sheets):
    """Analyze Stock capital requirements from Excel data"""

    analysis = {}

    for sheet_name in sheets:
        try:
            print(f"  Analyzing sheet: {sheet_name}")
            df = pd.read_excel(file_path, sheet_name=sheet_name)

            print(f"  Columns: {list(df.columns)}")
            print(f"  Rows: {len(df)}")

            # Look for capital-related columns
            capital_cols = []
            for col in df.columns:
                col_lower = str(col).lower()
                if any(keyword in col_lower for keyword in ['amount', 'value', 'buy', 'sell', 'quantity', 'price', 'turnover']):
                    capital_cols.append(col)

            if capital_cols:
                print(f"  Capital-related columns found: {capital_cols}")

                # Analyze numeric columns
                for col in capital_cols:
                    if df[col].dtype in ['float64', 'int64']:
                        max_val = df[col].max()
                        min_val = df[col].min()
                        mean_val = df[col].mean()

                        # Calculate estimated capital if it looks like position value
                        if 'value' in str(col).lower() or 'amount' in str(col).lower():
                            est_capital = max_val * 10  # Conservative estimate
                            print(f"    {col}: Max={max_val:,.0f}, Estimated Capital Range: ₹{max_val:,.0f} - ₹{est_capital:,.0f}")
                        else:
                            print(f"    {col}: Max={max_val:,.0f}, Min={min_val:,.0f}, Avg={mean_val:,.0f}")

                # Sample some data
                print(f"  Sample data from {sheet_name}:")
                print(df.head(3).to_string())

                analysis[sheet_name] = {
                    "capital_columns": capital_cols,
                    "total_rows": len(df),
                    "data_sample": df.head(3).to_dict() if len(df) > 0 else None
                }

        except Exception as e:
            print(f"    Error analyzing {sheet_name}: {e}")
            continue

    return analysis

def calculate_total_opportunity_cost(capital_analysis):
    """Calculate opportunity cost based on actual capital analysis"""

    print("\n💰 OPPORTUNITY COST CALCULATION")
    print("=" * 50)

    # Load actual P&L data for reference
    try:
        with open('/Users/Subho/comprehensive_trading_analysis_results.json', 'r') as f:
            pnl_data = json.load(f)
    except:
        pnl_data = None

    # Try to extract actual capital from the analysis
    actual_capital_estimates = {}

    # F&O Capital estimates
    if 'f&o' in capital_analysis and 'error' not in capital_analysis['f&o']:
        print("\n📊 F&O Capital Analysis:")
        for sheet, data in capital_analysis['f&o'].items():
            if 'data_sample' in data and data['data_sample']:
                print(f"  Sheet: {sheet}")
                for col in data['capital_columns']:
                    print(f"    Capital Column: {col}")

    # Stock Capital estimates
    if 'stocks' in capital_analysis and 'error' not in capital_analysis['stocks']:
        print("\n📈 Stock Capital Analysis:")
        for sheet, data in capital_analysis['stocks'].items():
            if 'data_sample' in data and data['data_sample']:
                print(f"  Sheet: {sheet}")
                for col in data['capital_columns']:
                    print(f"    Capital Column: {col}")

    # If we can't extract exact capital, use the P&L data to estimate
    if pnl_data:
        print("\n🔢 Using P&L Data to Estimate Minimum Capital:")

        fno_stats = pnl_data['fno_analysis']['stats']
        stock_stats = pnl_data['stock_analysis']['stats']

        # Conservative capital estimates based on:
        # 1. Maximum single loss (if risking 2% per trade)
        # 2. Average position size
        # 3. Total turnover

        fno_max_loss = abs(fno_stats['max_loss'])  # ₹230,280
        stock_max_loss = abs(stock_stats['max_loss'])  # ₹24,858

        # Conservative 1% risk assumption (more realistic for retail traders)
        fno_capital_min = fno_max_loss / 0.01  # ₹2.3 crore minimum
        fno_capital_conservative = fno_max_loss / 0.005  # ₹4.6 crore if 0.5% risk

        stock_capital_min = stock_max_loss / 0.01  # ₹24.9 lakh minimum
        stock_capital_conservative = stock_max_loss / 0.005  # ₹49.7 lakh if 0.5% risk

        # Total estimated capital range
        total_capital_min = fno_capital_min + stock_capital_min
        total_capital_conservative = fno_capital_conservative + stock_capital_conservative

        print(f"\nMinimum Capital Estimates:")
        print(f"  F&O Capital (1% risk): ₹{fno_capital_min:,.0f}")
        print(f"  F&O Capital (0.5% risk): ₹{fno_capital_conservative:,.0f}")
        print(f"  Stock Capital (1% risk): ₹{stock_capital_min:,.0f}")
        print(f"  Stock Capital (0.5% risk): ₹{stock_capital_conservative:,.0f}")
        print(f"\nTotal Capital Range:")
        print(f"  Conservative: ₹{total_capital_min:,.0f}")
        print(f"  Very Conservative: ₹{total_capital_conservative:,.0f}")

        # Calculate opportunity costs with these actual estimates
        your_actual_pnl = pnl_data['comparison']['combined_pnl']  # -₹846,192

        # Market returns over the periods
        # F&O: ~29 months (April 2023 - August 2025)
        # Stocks: ~58 months (April 2020 - November 2024)

        fno_years = 29 / 12
        stock_years = 58 / 12

        # Market return assumptions (conservative)
        nifty_cagr = 12.0  # Conservative NIFTY return
        fd_cagr = 6.0      # Fixed deposit return

        # Calculate what the capital would have earned
        fno_market_return_min = fno_capital_min * (nifty_cagr/100) * fno_years
        stock_market_return_min = stock_capital_min * (nifty_cagr/100) * stock_years
        total_market_return_min = fno_market_return_min + stock_market_return_min

        fno_fd_return_min = fno_capital_min * (fd_cagr/100) * fno_years
        stock_fd_return_min = stock_capital_min * (fd_cagr/100) * stock_years
        total_fd_return_min = fno_fd_return_min + stock_fd_return_min

        # Opportunity costs
        opportunity_cost_vs_nifty = total_market_return_min - your_actual_pnl
        opportunity_cost_vs_fd = total_fd_return_min - your_actual_pnl

        print(f"\n💸 ACTUAL OPPORTUNITY COST CALCULATIONS:")
        print(f"=" * 60)
        print(f"Your Actual P&L: ₹{your_actual_pnl:,.0f}")
        print(f"\nMinimum Capital: ₹{total_capital_min:,.0f}")
        print(f"  Market Return (NIFTY): ₹{total_market_return_min:,.0f}")
        print(f"  FD Return: ₹{total_fd_return_min:,.0f}")
        print(f"\nOpportunity Cost:")
        print(f"  vs NIFTY: ₹{opportunity_cost_vs_nifty:,.0f}")
        print(f"  vs Fixed Deposits: ₹{opportunity_cost_vs_fd:,.0f}")

        # Annual opportunity cost
        avg_years = (fno_years + stock_years) / 2
        annual_opportunity_cost_nifty = opportunity_cost_vs_nifty / avg_years
        annual_opportunity_cost_fd = opportunity_cost_vs_fd / avg_years

        print(f"\nAnnual Opportunity Cost:")
        print(f"  vs NIFTY: ₹{annual_opportunity_cost_nifty:,.0f} per year")
        print(f"  vs Fixed Deposits: ₹{annual_opportunity_cost_fd:,.0f} per year")

        return {
            "capital_analysis": capital_analysis,
            "capital_estimates": {
                "conservative": total_capital_min,
                "very_conservative": total_capital_conservative,
                "fno_capital": fno_capital_min,
                "stock_capital": stock_capital_min,
                "risk_assumption": "1% of capital at risk per trade"
            },
            "opportunity_cost": {
                "actual_pnl": your_actual_pnl,
                "market_return_nifty": total_market_return_min,
                "fd_return": total_fd_return_min,
                "opportunity_cost_vs_nifty": opportunity_cost_vs_nifty,
                "opportunity_cost_vs_fd": opportunity_cost_vs_fd,
                "annual_opportunity_cost_nifty": annual_opportunity_cost_nifty,
                "annual_opportunity_cost_fd": annual_opportunity_cost_fd
            }
        }

    return capital_analysis

if __name__ == "__main__":
    results = analyze_actual_capital_from_excel()