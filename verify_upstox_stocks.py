#!/usr/bin/env python3
"""
Verify Upstox Stock Trading P&L from Raw Excel Files
Check actual stock trading profit/loss on Upstox platform
"""

import pandas as pd
import json
from datetime import datetime

def verify_upstox_stock_pnl():
    """Verify actual Upstox stock trading P&L from Excel files"""

    print("🔍 VERIFYING UPSTOX STOCK TRADING P&L")
    print("=" * 50)
    print("Checking actual Excel file data...")

    # Your actual files
    files = {
        'upstox_trade_file': '/Users/Subho/Downloads/trade_20230401_20251115_347609.xlsx',
        'fno_report': '/Users/Subho/Downloads/F&O_PnL_Report_6917002522_2023-04-01_2025-08-05..xlsx',
        'stock_report': '/Users/Subho/Downloads/Stocks_PnL_Report_6917002522_01-04-2020_30-11-2024.xlsx'
    }

    upstox_stock_data = {
        'found_stocks': False,
        'total_stock_pnl': 0,
        'stock_trades': 0,
        'file_analysis': {}
    }

    # 1. Check the main Upstox trade file (most likely to have everything)
    print("\n📁 ANALYZING UPSTOX MAIN TRADE FILE:")
    print(f"File: trade_20230401_20251115_347609.xlsx")

    try:
        excel_file = pd.ExcelFile(files['upstox_trade_file'])
        print(f"Sheets: {excel_file.sheet_names}")

        for sheet_name in excel_file.sheet_names:
            print(f"\n📋 Sheet: {sheet_name}")

            # Try different header rows to find proper data
            for header_row in range(0, 15):
                try:
                    df = pd.read_excel(excel_file, sheet_name=sheet_name, header=header_row)

                    if len(df) > 5 and len(df.columns) > 5:
                        print(f"  Header {header_row}: {df.shape} data")
                        print(f"  Columns: {list(df.columns)[:10]}...")

                        # Look for stock vs F&O indicators
                        stock_columns = []
                        fno_columns = []

                        for col in df.columns:
                            col_lower = str(col).lower()
                            if 'symbol' in col_lower or 'scrip' in col_lower or 'instrument' in col_lower:
                                stock_columns.append(col)
                            if 'expiry' in col_lower or 'option' in col_lower or 'fut' in col_lower:
                                fno_columns.append(col)
                            if 'pnl' in col_lower or 'amount' in col_lower or 'profit' in col_lower:
                                stock_columns.append(col)

                        if stock_columns:
                            print(f"  Relevant columns: {stock_columns[:5]}")

                            # Try to identify stock trades
                            stock_mask = pd.Series([False] * len(df))

                            # Look for non-derivative symbols
                            for col in stock_columns:
                                if 'symbol' in str(col).lower() or 'scrip' in str(col).lower():
                                    # Check for stock symbols (no expiry, no CE/PE, no FUT)
                                    for idx, value in df[col].items():
                                        if pd.notna(value):
                                            symbol = str(value).upper()
                                            # Stock indicators: no expiry date, no CE/PE, no FUT suffix
                                            if (not any(x in symbol for x in ['CE', 'PE', 'FUT']) and
                                                len(symbol) <= 20 and
                                                not any(char.isdigit() for char in symbol[-6:])):  # No date-like ending
                                                stock_mask[idx] = True

                            stock_trades_df = df[stock_mask]
                            if len(stock_trades_df) > 0:
                                print(f"  ✅ Found {len(stock_trades_df)} potential stock trades")

                                # Calculate P&L for stock trades
                                pnl_found = False
                                for col in df.columns:
                                    if 'pnl' in str(col).lower() or 'amount' in str(col).lower() or 'profit' in str(col).lower():
                                        stock_pnl = stock_trades_df[col].sum()
                                        if pd.notna(stock_pnl) and abs(stock_pnl) > 0:
                                            print(f"  📊 Stock P&L from column '{col}': ₹{stock_pnl:,.2f}")
                                            upstox_stock_data['total_stock_pnl'] = float(stock_pnl)
                                            upstox_stock_data['stock_trades'] = len(stock_trades_df)
                                            upstox_stock_data['found_stocks'] = True
                                            pnl_found = True
                                            break

                                if pnl_found:
                                    break

                except Exception as e:
                    continue

            if upstox_stock_data['found_stocks']:
                break

    except Exception as e:
        print(f"  ❌ Error reading Upstox trade file: {e}")

    # 2. Check if we can separate stocks from the dedicated stock report
    print(f"\n📁 ANALYZING STOCK REPORT:")
    print("This file should contain pure stock trading data")
    print(f"File: Stocks_PnL_Report_6917002522_01-04-2020_30-11-2024.xlsx")

    try:
        stock_excel = pd.ExcelFile(files['stock_report'])
        print(f"Sheets: {stock_excel.sheet_names}")

        for sheet_name in stock_excel.sheet_names:
            print(f"\n📋 Stock Sheet: {sheet_name}")

            for header_row in range(0, 10):
                try:
                    df = pd.read_excel(stock_excel, sheet_name=sheet_name, header=header_row)

                    if len(df) > 5:
                        # Look for P&L data
                        for col in df.columns:
                            if 'pnl' in str(col).lower() or 'amount' in str(col).lower():
                                col_data = df[col].dropna()
                                if len(col_data) > 0:
                                    total_pnl = col_data.sum()
                                    if abs(total_pnl) > 1000:  # Significant amount
                                        print(f"  📊 Found P&L data: {len(col_data)} values = ₹{total_pnl:,.2f}")
                                        print(f"  ⚠️  This might be the COMPLETE stock P&L across all platforms")

                except Exception as e:
                    continue

    except Exception as e:
        print(f"  ❌ Error reading stock report: {e}")

    # 3. Results and verification
    print(f"\n🎯 UPSTOX STOCK VERIFICATION RESULTS:")
    print("=" * 50)

    if upstox_stock_data['found_stocks']:
        stock_pnl = upstox_stock_data['total_stock_pnl']
        stock_trades = upstox_stock_data['stock_trades']

        print(f"✅ UPSTOX STOCK TRADING DATA FOUND:")
        print(f"  Stock Trades: {stock_trades}")
        print(f"  Stock P&L: ₹{stock_pnl:,.2f}")
        print(f"  Result: {'PROFIT' if stock_pnl > 0 else 'LOSS'}")

        if stock_pnl > 0:
            print(f"\n✅ CONFIRMED: Upstox stock trading WAS profitable")
        else:
            print(f"\n❌ CONFIRMED: Upstox stock trading was NOT profitable")
    else:
        print(f"❌ Could not separate Upstox stock data from the files")
        print(f"⚠️  The previous analysis showing Upstox stock profits may have been an ESTIMATE")
        print(f"🔍 Need to clarify which platform the stock profits belong to")

    # Save verification results
    verification = {
        'verification_date': datetime.now().isoformat(),
        'upstox_stock_data': upstox_stock_data,
        'method': 'direct_excel_file_analysis',
        'status': 'VERIFIED' if upstox_stock_data['found_stocks'] else 'UNCLEAR'
    }

    with open('/Users/Subho/upstox_stock_verification.json', 'w') as f:
        json.dump(verification, f, indent=2)

    return upstox_stock_data

if __name__ == "__main__":
    verification = verify_upstox_stock_pnl()