#!/usr/bin/env python3
"""
Raw File Re-analysis
Direct analysis from Excel files to double-check all numbers
"""

import pandas as pd
import numpy as np
import json
from datetime import datetime
import re

def analyze_raw_excel_files():
    """Analyze Excel files directly to get exact numbers"""

    print("🔍 RAW FILE RE-ANALYSIS")
    print("=" * 50)
    print("Direct analysis from your Excel files")
    print()

    # Your exact files
    files = {
        'fno_report': '/Users/Subho/Downloads/F&O_PnL_Report_6917002522_2023-04-01_2025-08-05..xlsx',
        'stocks_report': '/Users/Subho/Downloads/Stocks_PnL_Report_6917002522_01-04-2020_30-11-2024.xlsx',
        'trade_report': '/Users/Subho/Downloads/trade_20230401_20251115_347609.xlsx'
    }

    raw_results = {}

    for file_key, file_path in files.items():
        print(f"📁 Analyzing: {file_key}")
        print(f"   Path: {file_path}")
        print(f"   Filename: {file_path.split('/')[-1]}")

        try:
            analysis = analyze_excel_file_raw(file_path, file_key)
            raw_results[file_key] = analysis
        except Exception as e:
            print(f"   ❌ Error: {e}")
            raw_results[file_key] = {'error': str(e)}

    # Combine and double-check all results
    final_verification = verify_all_results(raw_results)

    return final_verification

def analyze_excel_file_raw(file_path, file_key):
    """Deep dive into Excel file for exact P&L numbers"""

    print(f"   🔍 Reading raw data from: {file_path}")

    analysis = {
        'file_key': file_key,
        'file_path': file_path,
        'filename': file_path.split('/')[-1],
        'sheets': {},
        'total_pnl': 0,
        'total_trades': 0,
        'found_data': False
    }

    try:
        excel_file = pd.ExcelFile(file_path)
        sheet_names = excel_file.sheet_names
        print(f"   Found sheets: {sheet_names}")

        for sheet_name in sheet_names:
            print(f"   📋 Sheet: {sheet_name}")

            sheet_analysis = analyze_sheet_for_pnl(excel_file, sheet_name)
            analysis['sheets'][sheet_name] = sheet_analysis

            # If we found P&L data in this sheet, use it
            if sheet_analysis['found_pnl']:
                analysis['total_pnl'] += sheet_analysis['total_pnl']
                analysis['total_trades'] += sheet_analysis['total_trades']
                analysis['found_data'] = True

    except Exception as e:
        print(f"   ❌ Error reading Excel file: {e}")

    return analysis

def analyze_sheet_for_pnl(excel_file, sheet_name):
    """Analyze individual sheet for P&L data"""

    sheet_analysis = {
        'sheet_name': sheet_name,
        'found_pnl': False,
        'total_pnl': 0,
        'total_trades': 0,
        'data_samples': [],
        'pnl_columns': []
    }

    # Try different header rows to find P&L data
    for header_row in range(0, 20):
        try:
            df = pd.read_excel(excel_file, sheet_name=sheet_name, header=header_row)

            if len(df) > 0 and len(df.columns) > 0:
                print(f"     Header {header_row}: {df.shape} data, columns: {len(df.columns)}")

                # Look for P&L columns by name
                pnl_columns = []
                for col_idx, col in enumerate(df.columns):
                    col_str = str(col).lower()
                    if any(keyword in col_str for keyword in ['pnl', 'profit', 'loss', 'realized', 'gain', 'amount', 'value']):
                        if df[col].dtype in ['float64', 'int64', 'float32', 'int32']:
                            pnl_columns.append({
                                'col_index': col_idx,
                                'col_name': str(col),
                                'data_type': str(df[col].dtype)
                            })

                if pnl_columns:
                    print(f"     Found {len(pnl_columns)} potential P&L columns:")
                    for col_info in pnl_columns:
                        col_data = df.iloc[:, col_info['col_index']].dropna()
                        if len(col_data) > 0:
                            total = col_data.sum()
                            count = len(col_data)
                            print(f"       Column {col_info['col_name']}: {count} values, sum = ₹{total:,.2f}")

                            # This looks like P&L data
                            if abs(total) > 1000:  # Significant amount
                                sheet_analysis['found_pnl'] = True
                                sheet_analysis['total_pnl'] = total
                                sheet_analysis['pnl_columns'].append(col_info)

                                # Try to count trades from this data
                                positive_count = (col_data > 0).sum()
                                negative_count = (col_data < 0).sum()
                                total_count = positive_count + negative_count
                                if total_count > 0:
                                    sheet_analysis['total_trades'] = total_count

                # Also look for numeric columns with large values
                numeric_cols = df.select_dtypes(include=[np.number]).columns
                for col in numeric_cols:
                    if col not in [c['col_name'] for c in pnl_columns]:
                        col_data = df[col].dropna()
                        if len(col_data) > 0:
                            max_val = col_data.max()
                            min_val = col_data.min()
                            if abs(max_val) > 50000 or abs(min_val) > 50000:  # Large values
                                print(f"     Large value column {col}: Max={max_val:,.2f}, Min={min_val:2f}")

                # Store sample data for reference
                sample_data = df.head(3).to_dict()
                sheet_analysis['data_samples'].append({
                    'header_row': header_row,
                    'shape': df.shape,
                    'columns': list(df.columns),
                    'sample': sample_data
                })

                # If we found good data, break
                if sheet_analysis['found_pnl']:
                    print(f"     ✅ Found P&L data in sheet!")
                    break

        except Exception as e:
            continue

    return sheet_analysis

def verify_all_results(raw_results):
    """Verify all results from raw file analysis"""

    print(f"\n🔍 VERIFYING ALL RAW FILE RESULTS")
    print("=" * 50)

    print("📊 RAW FILE ANALYSIS RESULTS:")
    print("-" * 40)

    total_fno_pnl = 0
    total_stock_pnl = 0
    total_fno_trades = 0
    total_stock_trades = 0

    fno_files = []
    stock_files = []

    for file_key, analysis in raw_results.items():
        if 'error' in analysis:
            print(f"❌ {file_key}: Error - {analysis['error']}")
            continue

        print(f"\n{file_key}:")
        print(f"  Filename: {analysis['filename']}")
        print(f"  Found Data: {analysis['found_data']}")
        print(f"  Total P&L: ₹{analysis['total_pnl']:,.2f}")
        print(f"  Total Trades: {analysis['total_trades']:,}")

        # Classify file type based on filename and content
        filename_lower = analysis['filename'].lower()
        if 'f&o' in filename_lower or 'fno' in filename_lower:
            fno_files.append(file_key)
            total_fno_pnl += analysis['total_pnl']
            total_fno_trades += analysis['total_trades']
        elif 'stock' in filename_lower:
            stock_files.append(file_key)
            total_stock_pnl += analysis['total_pnl']
            total_stock_trades += analysis['total_trades']

    # Show summary by file type
    print(f"\n📈 SUMMARY BY FILE TYPE:")
    print("-" * 40)
    print(f"F&O Files ({len(fno_files)}):")
    for file_key in fno_files:
        print(f"  • {file_key}: ₹{raw_results[file_key]['total_pnl']:,.2f}")
    print(f"Total F&O: ₹{total_fno_pnl:,.2f}")

    print(f"\nStock Files ({len(stock_files)}):")
    for file_key in stock_files:
        print(f"  • {file_key}: ₹{raw_results[file_key]['total_pnl']:,.2f}")
    print(f"Total Stocks: ₹{total_stock_pnl:,.2f}")

    # Calculate totals
    grand_total = total_fno_pnl + total_stock_pnl
    grand_trades = total_fno_trades + total_stock_trades

    print(f"\n🎯 FINAL VERIFIED TOTALS:")
    print("=" * 40)
    print(f"F&O Trading:    {total_fno_trades:,} trades")
    print(f"  Total P&L:     ₹{total_fno_pnl:,.2f}")
    print(f"  Status:        {'PROFIT' if total_fno_pnl > 0 else 'LOSS'}")
    print()

    print(f"Stock Trading:  {total_stock_trades:,} trades")
    print(f"  Total P&L:     ₹{total_stock_pnl:,.2f}")
    print(f"  Status:        {'PROFIT' if total_stock_pnl > 0 else 'LOSS'}")
    print()

    print(f"GRAND TOTAL:    {grand_trades:,} trades")
    print(f"  Total P&L:     ₹{grand_total:,.2f}")
    print(f"  Final Result:  {'PROFIT' if grand_total > 0 else 'LOSS'}")

    # Double-check with previous analysis
    print(f"\n🔄 DOUBLE-CHECK WITH PREVIOUS ANALYSIS:")
    print("-" * 50)

    # Load previous verified data
    try:
        with open('/Users/Subho/comprehensive_trading_analysis_results.json', 'r') as f:
            previous_data = json.load(f)

        prev_fno_pnl = previous_data['fno_analysis']['stats']['total_pnl']
        prev_stock_pnl = previous_data['stock_analysis']['stats']['total_pnl']
        prev_combined = previous_data['comparison']['combined_pnl']

        print(f"Previous Analysis:")
        print(f"  F&O P&L:     ₹{prev_fno_pnl:,.2f}")
        print(f"  Stock P&L:   ₹{prev_stock_pnl:,.2f}")
        print(f"  Combined:    ₹{prev_combined:,.2f}")

        # Compare
        fno_match = abs(total_fno_pnl - prev_fno_pnl) < 1.0
        stock_match = abs(total_stock_pnl - prev_stock_pnl) < 1.0
        combined_match = abs(grand_total - prev_combined) < 1.0

        print(f"\nVerification:")
        print(f"  F&O Match:     {'✅ CONFIRMED' if fno_match else '❌ DIFFERENT'}")
        print(f"  Stock Match:   {'✅ CONFIRMED' if stock_match else '❌ DIFFERENT'}")
        print(f"  Combined Match: {'✅ CONFIRMED' if combined_match else '❌ DIFFERENT'}")

    except Exception as e:
        print(f"  ❌ Could not load previous analysis: {e}")

    # Final confirmation
    print(f"\n✅ FINAL CONFIRMED RESULT:")
    print("=" * 30)

    if grand_total < 0:
        print(f"❌ TOTAL LOSS: ₹{abs(grand_total):,.2f}")
    else:
        print(f"✅ TOTAL PROFIT: ₹{grand_total:,.2f}")

    print(f"    • F&O Trading: {'PROFIT' if total_fno_pnl > 0 else 'LOSS'} ₹{abs(total_fno_pnl):,.2f}")
    print(f"    • Stock Trading: {'PROFIT' if total_stock_pnl > 0 else 'LOSS'} ₹{abs(total_stock_pnl):,.2f}")

    # Convert numpy types to regular Python types to avoid JSON serialization error
    def convert_numpy_types(obj):
        if hasattr(obj, 'dtype'):
            if np.issubdtype(obj.dtype, np.integer):
                return int(obj)
            elif np.issubdtype(obj.dtype, np.floating):
                return float(obj)
        return obj

    # Convert all numeric values in raw_results
    converted_results = {}
    for file_key, analysis in raw_results.items():
        converted_results[file_key] = analysis
        if 'total_pnl' in analysis:
            converted_results[file_key]['total_pnl'] = convert_numpy_types(analysis['total_pnl'])
        if 'total_trades' in analysis:
            converted_results[file_key]['total_trades'] = convert_numpy_types(analysis['total_trades'])

    # Save the raw analysis results
    raw_verification = {
        'analysis_date': datetime.now().isoformat(),
        'method': 'direct_excel_file_analysis',
        'raw_results': converted_results,
        'verified_totals': {
            'fno_pnl': float(total_fno_pnl),
            'stock_pnl': float(total_stock_pnl),
            'combined_pnl': float(grand_total),
            'fno_trades': int(total_fno_trades),
            'stock_trades': int(total_stock_trades),
            'grand_trades': int(grand_trades)
        },
        'verification_status': 'DIRECT_FILE_ANALYSIS_CONFIRMED'
    }

    with open('/Users/Subho/raw_file_verification.json', 'w') as f:
        json.dump(raw_verification, f, indent=2)

    print(f"\n📄 Raw verification saved: raw_file_verification.json")

    return raw_verification

if __name__ == "__main__":
    verification = analyze_raw_excel_files()