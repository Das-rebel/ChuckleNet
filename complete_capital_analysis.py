#!/usr/bin/env python3
"""
Complete Capital Analysis with Both Excel Files
Calculate actual opportunity cost using real data from both trading files
"""

import pandas as pd
import numpy as np
import json
from datetime import datetime

def analyze_complete_trading_capital():
    """Analyze complete capital using both Excel files"""

    print("📊 COMPLETE CAPITAL ANALYSIS - ALL EXCEL FILES")
    print("=" * 60)

    # File paths
    file1 = '/Users/Subho/Downloads/F&O_PnL_Report_6917002522_2023-04-01_2025-08-05..xlsx'
    file2 = '/Users/Subho/Downloads/Stocks_PnL_Report_6917002522_01-04-2020_30-11-2024.xlsx'
    new_file = '/Users/Subho/Downloads/trade_20230401_20251115_347609.xlsx'

    # Analyze all files
    print(f"\n📋 Analyzing files:")
    print(f"  1. {file1}")
    print(f"  2. {file2}")
    print(f"  3. {new_file}")

    # Load existing P&L data
    try:
        with open('/Users/Subho/comprehensive_trading_analysis_results.json', 'r') as f:
            pnl_data = json.load(f)
    except:
        print("Error: P&L data not found")
        return

    # Analyze all three files
    analysis_results = {}

    # File 1: F&O Report
    analysis_results['f&o_report_1'] = analyze_excel_file_detailed(file1, "F&O Report 1")

    # File 2: Stocks Report
    analysis_results['stocks_report_1'] = analyze_excel_file_detailed(file2, "Stocks Report 1")

    # File 3: New Trade File
    analysis_results['new_trade_file'] = analyze_excel_file_detailed(new_file, "New Trade File")

    # Extract capital estimates
    capital_estimates = extract_capital_from_all_files(analysis_results)

    # Calculate complete opportunity cost
    complete_analysis = calculate_complete_opportunity_cost(capital_estimates, pnl_data)

    return complete_analysis

def analyze_excel_file_detailed(file_path, file_description):
    """Detailed analysis of individual Excel file"""

    print(f"\n🔍 Analyzing {file_description}...")
    print(f"  File: {file_path}")

    analysis = {
        'file_description': file_description,
        'file_path': file_path,
        'sheets': {},
        'capital_data': {}
    }

    try:
        # Get all sheets
        excel_file = pd.ExcelFile(file_path)
        sheet_names = excel_file.sheet_names
        print(f"  Available sheets: {sheet_names}")

        # Analyze each sheet
        for sheet_name in sheet_names:
            try:
                print(f"    Sheet: {sheet_name}")
                sheet_analysis = analyze_sheet_data(excel_file, sheet_name)
                analysis['sheets'][sheet_name] = sheet_analysis

            except Exception as e:
                print(f"    Error analyzing {sheet_name}: {e}")
                continue

    except Exception as e:
        print(f"  Error reading {file_description}: {e}")
        analysis['error'] = str(e)

    return analysis

def analyze_sheet_data(excel_file, sheet_name):
    """Analyze individual sheet data"""

    sheet_analysis = {
        'sheet_name': sheet_name,
        'data_shape': None,
        'columns': [],
        'numeric_columns': [],
        'capital_indicators': {},
        'sample_data': None
    }

    # Try different header rows
    for header_row in range(8):  # Try header rows 0-7
        try:
            df = pd.read_excel(excel_file, sheet_name=sheet_name, header=header_row)

            if len(df) > 0:
                sheet_analysis['data_shape'] = df.shape
                sheet_analysis['columns'] = list(df.columns)

                # Get numeric columns
                numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
                sheet_analysis['numeric_columns'] = numeric_cols

                # Analyze for capital indicators
                capital_indicators = analyze_capital_indicators(df, numeric_cols)
                sheet_analysis['capital_indicators'] = capital_indicators

                # Store sample data
                if len(df) > 0:
                    sheet_analysis['sample_data'] = df.head(5).to_dict()

                print(f"      Header row {header_row}: {df.shape} shape, {len(numeric_cols)} numeric columns")

                # If we found good data, break
                if len(numeric_cols) > 0:
                    break

        except Exception as e:
            continue

    return sheet_analysis

def analyze_capital_indicators(df, numeric_cols):
    """Analyze numeric columns for capital indicators"""

    indicators = {}

    for col in numeric_cols:
        if col in df.columns and df[col].notna().sum() > 3:  # At least 3 non-null values
            col_data = df[col].dropna()

            if len(col_data) > 0:
                max_val = col_data.max()
                min_val = col_data.min()
                mean_val = col_data.mean()
                total_abs = col_data.abs().sum()

                indicators[col] = {
                    'max': max_val,
                    'min': min_val,
                    'mean': mean_val,
                    'total_abs': total_abs,
                    'data_points': len(col_data)
                }

                # Classify the column
                if abs(max_val) > 1000000:  # > 10L - likely turnover/capital
                    indicators[col]['type'] = 'Large_Capital_Turnover'
                elif abs(max_val) > 100000:  # > 1L - likely position value/P&L
                    indicators[col]['type'] = 'Position_Value_PnL'
                elif abs(max_val) > 10000:  # > 10K - likely price/quantity
                    indicators[col]['type'] = 'Price_Quantity'
                else:
                    indicators[col]['type'] = 'Small_Value'

    return indicators

def extract_capital_from_all_files(all_analysis):
    """Extract capital estimates from all file analyses"""

    print(f"\n💰 EXTRACTING CAPITAL FROM ALL FILES")
    print("=" * 50)

    capital_estimates = {
        'by_file': {},
        'by_category': {
            'f&o_capital': 0,
            'stock_capital': 0,
            'total_capital': 0
        },
        'methodology': []
    }

    # Extract from each file
    for file_key, file_analysis in all_analysis.items():
        file_capital = extract_capital_from_file(file_analysis)
        capital_estimates['by_file'][file_key] = file_capital

        # Add to category totals
        if 'f&o' in file_key.lower():
            capital_estimates['by_category']['f&o_capital'] += file_capital['estimated_capital']
        elif 'stock' in file_key.lower():
            capital_estimates['by_category']['stock_capital'] += file_capital['estimated_capital']
        else:
            # Distribute unknown based on typical patterns
            capital_estimates['by_category']['f&o_capital'] += file_capital['estimated_capital'] * 0.7
            capital_estimates['by_category']['stock_capital'] += file_capital['estimated_capital'] * 0.3

        if file_capital['methodology']:
            capital_estimates['methodology'].extend(file_capital['methodology'])

    # Calculate totals
    capital_estimates['by_category']['total_capital'] = (
        capital_estimates['by_category']['f&o_capital'] +
        capital_estimates['by_category']['stock_capital']
    )

    # Display results
    print(f"\n📋 CAPITAL ESTIMATES BY FILE:")
    for file_key, estimate in capital_estimates['by_file'].items():
        print(f"  {file_key}:")
        print(f"    Estimated Capital: ₹{estimate['estimated_capital']:,.0f}")
        print(f"    Method: {estimate['method']}")
        print(f"    Key Indicators: {estimate['key_indicators']}")

    print(f"\n💰 TOTAL CAPITAL BY CATEGORY:")
    print(f"  F&O Trading Capital:   ₹{capital_estimates['by_category']['f&o_capital']:,.0f}")
    print(f"  Stock Trading Capital: ₹{capital_estimates['by_category']['stock_capital']:,.0f}")
    print(f"  Total Deployed Capital:  ₹{capital_estimates['by_category']['total_capital']:,.0f}")

    return capital_estimates

def extract_capital_from_file(file_analysis):
    """Extract capital estimate from single file analysis"""

    estimate = {
        'estimated_capital': 0,
        'method': '',
        'key_indicators': [],
        'methodology': []
    }

    # Look through all sheets for capital indicators
    for sheet_name, sheet_data in file_analysis.get('sheets', {}).items():
        if 'capital_indicators' in sheet_data:
            for col, indicators in sheet_data['capital_indicators'].items():
                if indicators['type'] == 'Large_Capital_Turnover':
                    # Large values - likely total turnover or capital
                    max_val = indicators['max']
                    if abs(max_val) > 0:
                        # Conservative estimate: assume this is annual turnover
                        # Capital ≈ Turnover / 10 (conservative multiple)
                        estimated_capital = abs(max_val) / 5  # Conservative
                        if estimated_capital > estimate['estimated_capital']:
                            estimate['estimated_capital'] = estimated_capital
                            estimate['method'] = f"Large turnover indicator: ₹{abs(max_val):,.0f} / 5"
                            estimate['key_indicators'].append(f"Sheet {sheet_name}, Col {col}: ₹{abs(max_val):,.0f}")

                elif indicators['type'] == 'Position_Value_PnL':
                    # Medium values - position values or P&L
                    max_val = indicators['max']
                    if abs(max_val) > 50000:  # Significant values
                        # This could be position value
                        estimated_capital = abs(max_val) * 10  # Conservative
                        if estimated_capital > estimate['estimated_capital']:
                            estimate['estimated_capital'] = estimated_capital
                            estimate['method'] = f"Position value indicator: ₹{abs(max_val):,.0f} × 10"
                            estimate['key_indicators'].append(f"Sheet {sheet_name}, Col {col}: ₹{abs(max_val):,.0f}")

    # If no good estimate, use conservative default
    if estimate['estimated_capital'] == 0:
        # Use minimum based on typical trading activity
        estimate['estimated_capital'] = 1000000  # ₹10L conservative
        estimate['method'] = "Conservative minimum estimate"

    return estimate

def calculate_complete_opportunity_cost(capital_estimates, pnl_data):
    """Calculate complete opportunity cost with all data"""

    print(f"\n📈 COMPLETE OPPORTUNITY COST CALCULATION")
    print("=" * 60)

    # Extract data
    total_capital = capital_estimates['by_category']['total_capital']
    fno_capital = capital_estimates['by_category']['f&o_capital']
    stock_capital = capital_estimates['by_category']['stock_capital']

    # Your actual P&L
    fno_stats = pnl_data['fno_analysis']['stats']
    stock_stats = pnl_data['stock_analysis']['stats']
    comparison = pnl_data['comparison']

    your_total_pnl = comparison['combined_pnl']  # -₹846,192
    fno_pnl = fno_stats['total_pnl']  # -₹2,637,173
    stock_pnl = stock_stats['total_pnl']  # ₹1,790,981

    # Trading periods
    fno_years = 29 / 12  # 29 months of F&O data
    stock_years = 58 / 12  # 58 months of stock data
    avg_years = (fno_years + stock_years) / 2

    # Market returns (conservative real averages)
    nifty_return = 12.0  # Conservative NIFTY return
    fd_return = 6.5     # Fixed deposit rate

    # Calculate market returns
    fno_market_return = fno_capital * (nifty_return / 100) * fno_years
    stock_market_return = stock_capital * (nifty_return / 100) * stock_years
    total_market_return = fno_market_return + stock_market_return

    fno_fd_return = fno_capital * (fd_return / 100) * fno_years
    stock_fd_return = stock_capital * (fd_return / 100) * stock_years
    total_fd_return = fno_fd_return + stock_fd_return

    # Opportunity costs
    opportunity_cost_vs_nifty = total_market_return - your_total_pnl
    opportunity_cost_vs_fd = total_fd_return - your_total_pnl

    # Annual costs
    your_annual_return = your_total_pnl / avg_years
    market_annual_return = total_market_return / avg_years
    fd_annual_return = total_fd_return / avg_years

    annual_opportunity_nifty = market_annual_return - your_annual_return
    annual_opportunity_fd = fd_annual_return - your_annual_return

    # Future projections
    years_projection = [5, 10, 15, 20]

    # Create complete analysis
    complete_analysis = {
        'analysis_timestamp': datetime.now().isoformat(),
        'capital_analysis': capital_estimates,
        'trading_performance': {
            'f_pnl': fno_pnl,
            's_pnl': stock_pnl,
            'total_pnl': your_total_pnl,
            'f_trades': fno_stats['num_trades'],
            's_trades': stock_stats['num_trades'],
            'f_win_rate': fno_stats['win_rate'],
            's_win_rate': stock_stats['win_rate']
        },
        'period_analysis': {
            'f_years': fno_years,
            's_years': stock_years,
            'avg_years': avg_years
        },
        'market_comparison': {
            'total_capital': total_capital,
            'f_capital': fno_capital,
            's_capital': stock_capital,
            'market_return_total': total_market_return,
            'fd_return_total': total_fd_return,
            'your_return_total': your_total_pnl,
            'opportunity_cost_nifty': opportunity_cost_vs_nifty,
            'opportunity_cost_fd': opportunity_cost_vs_fd
        },
        'annual_analysis': {
            'your_annual_return': your_annual_return,
            'market_annual_return': market_annual_return,
            'fd_annual_return': fd_annual_return,
            'annual_opportunity_nifty': annual_opportunity_nifty,
            'annual_opportunity_fd': annual_opportunity_fd
        },
        'future_projections': {}
    }

    # Calculate future projections
    for years in years_projection:
        complete_analysis['future_projections'][f'{years}_years'] = {
            'your_projected_loss': your_annual_return * years,
            'lost_market_returns': market_annual_return * years,
            'lost_fd_returns': fd_annual_return * years,
            'total_wealth_destruction': your_annual_return * years + market_annual_return * years
        }

    # Display results
    print(f"\n📊 COMPLETE ANALYSIS RESULTS:")
    print("=" * 50)

    print(f"\n💰 CAPITAL DEPLOYED:")
    print(f"  Total Capital:    ₹{total_capital:,.0f}")
    print(f"  F&O Capital:      ₹{fno_capital:,.0f}")
    print(f"  Stock Capital:    ₹{stock_capital:,.0f}")

    print(f"\n📈 YOUR TRADING RESULTS:")
    print(f"  F&O Trading:      ₹{fno_pnl:,.0f} ({fno_stats['num_trades']:,} trades)")
    print(f"  Stock Trading:    ₹{stock_pnl:,.0f} ({stock_stats['num_trades']:,} trades)")
    print(f"  Total Result:     ₹{your_total_pnl:,.0f}")

    print(f"\n🏆 MARKET COMPARISON:")
    print(f"  Market Return:    ₹{total_market_return:,.0f}")
    print(f"  FD Return:        ₹{total_fd_return:,.0f}")
    print(f"  Your Return:       ₹{your_total_pnl:,.0f}")

    print(f"\n🚨 OPPORTUNITY COST:")
    print(f"  vs NIFTY:         ₹{opportunity_cost_vs_nifty:,.0f}")
    print(f"  vs Fixed Deposits: ₹{opportunity_cost_vs_fd:,.0f}")

    print(f"\n📅 ANNUAL IMPACT:")
    print(f"  Your Annual Return:   ₹{your_annual_return:,.0f}")
    print(f"  Market Annual:        ₹{market_annual_return:,.0f}")
    print(f"  FD Annual:           ₹{fd_annual_return:,.0f}")
    print(f"  Annual Loss vs Market: ₹{annual_opportunity_nifty:,.0f}")

    print(f"\n🔮 FUTURE PROJECTIONS:")
    print("-" * 60)
    for years in years_projection:
        proj = complete_analysis['future_projections'][f'{years}_years']
        print(f"\n  In {years} years:")
        print(f"    Your Trading Loss:          ₹{proj['your_projected_loss']:,.0f}")
        print(f"    Lost Market Returns:          ₹{proj['lost_market_returns']:,.0f}")
        print(f"    Lost FD Returns:             ₹{proj['lost_fd_returns']:,.0f}")
        print(f"    Total Wealth Destruction:    ₹{proj['total_wealth_destruction']:,.0f}")

    # Percentage returns
    your_return_pct = (your_total_pnl / total_capital) * 100 if total_capital > 0 else 0
    market_return_pct = (total_market_return / total_capital) * 100 if total_capital > 0 else 0
    fd_return_pct = (total_fd_return / total_capital) * 100 if total_capital > 0 else 0

    print(f"\n📊 PERCENTAGE RETURNS:")
    print(f"  Your Return:    {your_return_pct:.1f}% over {avg_years:.1f} years")
    print(f"  Market Return:  {market_return_pct:.1f}% over {avg_years:.1f} years")
    print(f"  FD Return:      {fd_return_pct:.1f}% over {avg_years:.1f} years")
    print(f"  Underperformance: {market_return_pct - your_return_pct:.1f}%")

    # Save complete analysis
    with open('/Users/Subho/complete_capital_opportunity_analysis.json', 'w') as f:
        json.dump(complete_analysis, f, indent=2)

    print(f"\n📄 Complete analysis saved: complete_capital_opportunity_analysis.json")

    return complete_analysis

if __name__ == "__main__":
    results = analyze_complete_trading_capital()