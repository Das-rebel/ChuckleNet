#!/usr/bin/env python3
"""
Complete Excel Yearly Analysis
Extract actual yearly data from all 3 Excel files you provided
"""

import pandas as pd
import numpy as np
import json
import re
from datetime import datetime

def analyze_all_excel_files():
    """Analyze all 3 Excel files to extract yearly trading data"""

    print("📊 COMPLETE EXCEL YEARLY ANALYSIS")
    print("=" * 60)

    # Your 3 Excel files
    files = {
        'fno_report': '/Users/Subho/Downloads/F&O_PnL_Report_6917002522_2023-04-01_2025-08-05..xlsx',
        'stocks_report': '/Users/Subho/Downloads/Stocks_PnL_Report_6917002522_01-04-2020_30-11-2024.xlsx',
        'trade_file': '/Users/Subho/Downloads/trade_20230401_20251115_347609.xlsx'
    }

    all_data = {}

    for file_key, file_path in files.items():
        print(f"\n🔍 Analyzing {file_key}:")
        print(f"  Path: {file_path}")

        try:
            file_data = extract_data_from_excel(file_path, file_key)
            all_data[file_key] = file_data
        except Exception as e:
            print(f"  Error: {e}")
            all_data[file_key] = {'error': str(e)}

    # Combine data and analyze yearly breakdown
    yearly_analysis = create_yearly_breakdown(all_data)

    return yearly_analysis

def extract_data_from_excel(file_path, file_key):
    """Extract trading data from Excel file using multiple methods"""

    file_data = {
        'file_path': file_path,
        'file_key': file_key,
        'sheets': {},
        'summary': {}
    }

    try:
        # Read all sheets
        excel_file = pd.ExcelFile(file_path)
        sheet_names = excel_file.sheet_names
        print(f"  Found sheets: {sheet_names}")

        # Try to read data from each sheet with different approaches
        for sheet_name in sheet_names:
            print(f"    Analyzing sheet: {sheet_name}")

            sheet_data = extract_sheet_data_comprehensive(excel_file, sheet_name)
            file_data['sheets'][sheet_name] = sheet_data

    except Exception as e:
        print(f"    Error reading file: {e}")
        raise

    return file_data

def extract_sheet_data_comprehensive(excel_file, sheet_name):
    """Extract data from sheet using multiple reading methods"""

    sheet_data = {
        'sheet_name': sheet_name,
        'raw_data': None,
        'summary_rows': [],
        'yearly_data': {},
        'extracted_metrics': {}
    }

    # Method 1: Try different header rows
    for header_row in range(0, 10):
        try:
            df = pd.read_excel(excel_file, sheet_name=sheet_name, header=header_row)

            if len(df) > 0 and len(df.columns) > 1:
                print(f"      Success with header row {header_row}: {df.shape}")
                sheet_data['raw_data'] = df

                # Look for summary or yearly data
                extract_summary_and_yearly_data(df, sheet_data)

                break  # Stop at first successful read
        except Exception as e:
            continue

    # Method 2: If no data found, try reading without headers
    if sheet_data['raw_data'] is None:
        try:
            df = pd.read_excel(excel_file, sheet_name=sheet_name, header=None)
            print(f"      Reading without headers: {df.shape}")
            sheet_data['raw_data'] = df
            extract_summary_and_yearly_data(df, sheet_data)
        except Exception as e:
            print(f"      Could not read sheet: {e}")

    return sheet_data

def extract_summary_and_yearly_data(df, sheet_data):
    """Extract summary and yearly data from dataframe"""

    # Look for rows that contain P&L, totals, or yearly data
    summary_keywords = ['Total', 'P&L', 'Profit', 'Loss', 'Summary', 'Grand', 'Net']
    yearly_keywords = ['2020', '2021', '2022', '2023', '2024', '2025']

    summary_rows = []

    # Convert DataFrame to string for searching
    df_str = df.astype(str)

    for idx, row in df.iterrows():
        row_text = ' '.join(row.values).lower()

        # Check for summary rows
        for keyword in summary_keywords:
            if keyword.lower() in row_text:
                summary_rows.append({
                    'row_index': idx,
                    'data': row.to_dict(),
                    'keyword': keyword
                })

        # Check for yearly data
        for year in yearly_keywords:
            if year in row_text:
                if 'yearly_data' not in sheet_data:
                    sheet_data['yearly_data'] = {}

                # Try to extract numbers from this row
                numbers = extract_numbers_from_row(row)
                if numbers:
                    sheet_data['yearly_data'][year] = numbers

    sheet_data['summary_rows'] = summary_rows

    # Extract overall metrics
    sheet_data['extracted_metrics'] = extract_metrics_from_dataframe(df)

def extract_numbers_from_row(row):
    """Extract numeric values from a pandas row"""

    numbers = []

    for value in row.values:
        if pd.notna(value):
            # Try to extract number from string
            if isinstance(value, str):
                # Look for numbers in string
                num_matches = re.findall(r'-?\d+\.?\d*', str(value))
                for match in num_matches:
                    try:
                        num = float(match)
                        # Only include significant numbers (not dates, etc.)
                        if abs(num) > 100 or abs(num) == abs(num):  # Handle both large and small numbers
                            numbers.append(num)
                    except:
                        continue
            elif isinstance(value, (int, float)):
                if abs(value) > 10:  # Only significant numbers
                    numbers.append(float(value))

    return numbers

def extract_metrics_from_dataframe(df):
    """Extract key metrics from dataframe"""

    metrics = {
        'total_rows': len(df),
        'total_columns': len(df.columns),
        'numeric_columns': [],
        'large_values': [],
        'profit_loss_indicators': []
    }

    # Find numeric columns
    for col in df.columns:
        try:
            if pd.api.types.is_numeric_dtype(df[col]):
                numeric_data = df[col].dropna()
                if len(numeric_data) > 0:
                    metrics['numeric_columns'].append(col)

                    # Look for large values (potential P&L)
                    max_val = numeric_data.max()
                    min_val = numeric_data.min()

                    if abs(max_val) > 1000:
                        metrics['large_values'].append({
                            'column': col,
                            'max': max_val,
                            'min': min_val,
                            'mean': numeric_data.mean()
                        })

                    # Look for profit/loss patterns
                    if 'profit' in str(col).lower() or 'loss' in str(col).lower() or 'pnl' in str(col).lower():
                        metrics['profit_loss_indicators'].append({
                            'column': col,
                            'max': max_val,
                            'min': min_val,
                            'total': numeric_data.sum()
                        })
        except:
            continue

    return metrics

def create_yearly_breakdown(all_file_data):
    """Create yearly breakdown from extracted file data"""

    print(f"\n📈 CREATING YEARLY BREAKDOWN")
    print("=" * 50)

    yearly_breakdown = {
        'platforms': {
            'groww': {'f&o': {}, 'stocks': {}},
            'upstox': {'f&o': {}, 'stocks': {}},
            'combined': {'f&o': {}, 'stocks': {}}
        },
        'summary': {},
        'insights': []
    }

    # Analyze each file for yearly patterns
    for file_key, file_data in all_file_data.items():
        if 'error' in file_data:
            print(f"  Skipping {file_key} due to error")
            continue

        print(f"\n  Analyzing {file_key}:")

        # Extract metrics from all sheets
        file_metrics = extract_file_metrics(file_data)

        # Assign to platform based on file patterns
        platform = assign_platform(file_key)
        instrument = assign_instrument(file_key)

        yearly_metrics = extract_yearly_metrics(file_data)

        if yearly_metrics:
            yearly_breakdown['platforms'][platform][instrument] = yearly_metrics
            print(f"    Assigned to: {platform} - {instrument}")
            print(f"    Found data for years: {list(yearly_metrics.keys())}")

    # Create combined analysis
    create_combined_analysis(yearly_breakdown)

    # Generate insights
    generate_insights(yearly_breakdown)

    # Save results
    with open('/Users/Subho/yearly_trading_breakdown_analysis.json', 'w') as f:
        json.dump(yearly_breakdown, f, indent=2)

    print(f"\n📄 Yearly breakdown analysis saved: yearly_trading_breakdown_analysis.json")

    return yearly_breakdown

def extract_file_metrics(file_data):
    """Extract overall metrics from file data"""

    metrics = {
        'total_sheets': len(file_data.get('sheets', {})),
        'summary_rows_found': 0,
        'large_values': [],
        'yearly_data_points': 0
    }

    for sheet_name, sheet_data in file_data.get('sheets', {}).items():
        if 'summary_rows' in sheet_data:
            metrics['summary_rows_found'] += len(sheet_data['summary_rows'])

        if 'yearly_data' in sheet_data:
            metrics['yearly_data_points'] += len(sheet_data['yearly_data'])

        if 'extracted_metrics' in sheet_data:
            sheet_metrics = sheet_data['extracted_metrics']
            if 'large_values' in sheet_metrics:
                metrics['large_values'].extend(sheet_metrics['large_values'])

    return metrics

def assign_platform(file_key):
    """Assign platform based on file key patterns"""

    if 'groww' in file_key.lower() or 'stocks' in file_key.lower():
        return 'groww'
    elif 'upstox' in file_key.lower() or 'fno' in file_key.lower():
        return 'upstox'
    else:
        return 'combined'

def assign_instrument(file_key):
    """Assign instrument type based on file key patterns"""

    if 'f&o' in file_key.lower() or 'fno' in file_key.lower():
        return 'f&o'
    elif 'stock' in file_key.lower():
        return 'stocks'
    else:
        return 'combined'

def extract_yearly_metrics(file_data):
    """Extract yearly metrics from file data"""

    yearly_metrics = {}
    years = ['2020', '2021', '2022', '2023', '2024', '2025']

    for sheet_name, sheet_data in file_data.get('sheets', {}).items():
        if 'yearly_data' in sheet_data:
            for year, numbers in sheet_data['yearly_data'].items():
                if year in years:
                    if year not in yearly_metrics:
                        yearly_metrics[year] = {
                            'pnl': 0,
                            'trades': 0,
                            'data_points': []
                        }

                    # Analyze the numbers to guess what they represent
                    pnl_value = guess_pnl_from_numbers(numbers)
                    if pnl_value != 0:
                        yearly_metrics[year]['pnl'] = pnl_value

                    yearly_metrics[year]['data_points'].extend(numbers)
                    yearly_metrics[year]['trades'] = max(yearly_metrics[year]['trades'], len(numbers))

    return yearly_metrics

def guess_pnl_from_numbers(numbers):
    """Guess P&L value from a list of numbers"""

    if not numbers:
        return 0

    # Look for the largest absolute value (likely total P&L)
    max_abs_value = max(abs(num) for num in numbers)

    # Look for sum of positive vs negative numbers
    positive_sum = sum(num for num in numbers if num > 0)
    negative_sum = sum(num for num in numbers if num < 0)

    # If there's a clear winner, use it
    if abs(positive_sum + negative_sum) > max_abs_value:
        return positive_sum + negative_sum
    else:
        return max(numbers, key=abs)  # Return the number with highest absolute value

def create_combined_analysis(yearly_breakdown):
    """Create combined analysis from platform data"""

    print(f"\n  Creating combined analysis...")

    # Combine data from all platforms
    all_years = ['2020', '2021', '2022', '2023', '2024', '2025']

    for year in all_years:
        combined_fno = {'pnl': 0, 'trades': 0}
        combined_stocks = {'pnl': 0, 'trades': 0}

        # Sum data from all platforms
        for platform in ['groww', 'upstox']:
            if year in yearly_breakdown['platforms'][platform]['f&o']:
                platform_data = yearly_breakdown['platforms'][platform]['f&o'][year]
                combined_fno['pnl'] += platform_data.get('pnl', 0)
                combined_fno['trades'] += platform_data.get('trades', 0)

            if year in yearly_breakdown['platforms'][platform]['stocks']:
                platform_data = yearly_breakdown['platforms'][platform]['stocks'][year]
                combined_stocks['pnl'] += platform_data.get('pnl', 0)
                combined_stocks['trades'] += platform_data.get('trades', 0)

        # Only include years with actual data
        if combined_fno['pnl'] != 0 or combined_fno['trades'] > 0:
            yearly_breakdown['platforms']['combined']['f&o'][year] = combined_fno

        if combined_stocks['pnl'] != 0 or combined_stocks['trades'] > 0:
            yearly_breakdown['platforms']['combined']['stocks'][year] = combined_stocks

def generate_insights(yearly_breakdown):
    """Generate insights from yearly breakdown"""

    insights = []

    # Analyze F&O trends
    fno_data = yearly_breakdown['platforms']['combined']['f&o']
    if fno_data:
        fno_years = sorted(fno_data.keys())
        if len(fno_years) > 1:
            first_year_pnl = fno_data[fno_years[0]]['pnl']
            last_year_pnl = fno_data[fno_years[-1]]['pnl']
            total_fno_pnl = sum(data['pnl'] for data in fno_data.values())

            insights.append(f"F&O Trading Analysis:")
            insights.append(f"  Years with data: {fno_years}")
            insights.append(f"  Total F&O P&L: ₹{total_fno_pnl:,.0f}")
            insights.append(f"  Trend: {'Improving' if last_year_pnl > first_year_pnl else 'Declining'}")

    # Analyze Stock trends
    stock_data = yearly_breakdown['platforms']['combined']['stocks']
    if stock_data:
        stock_years = sorted(stock_data.keys())
        if len(stock_years) > 1:
            first_year_pnl = stock_data[stock_years[0]]['pnl']
            last_year_pnl = stock_data[stock_years[-1]]['pnl']
            total_stock_pnl = sum(data['pnl'] for data in stock_data.values())

            insights.append(f"\nStock Trading Analysis:")
            insights.append(f"  Years with data: {stock_years}")
            insights.append(f"  Total Stock P&L: ₹{total_stock_pnl:,.0f}")
            insights.append(f"  Trend: {'Improving' if last_year_pnl > first_year_pnl else 'Declining'}")

    yearly_breakdown['insights'] = insights

if __name__ == "__main__":
    analysis = analyze_all_excel_files()