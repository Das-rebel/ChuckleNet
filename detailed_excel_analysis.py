#!/usr/bin/env python3
"""
Detailed Excel File Analysis for Actual Capital Calculation
Extract real position sizes, turnover, and capital requirements from your trading files
"""

import pandas as pd
import numpy as np
from datetime import datetime
import json

def analyze_excel_files_detailed():
    """Detailed analysis of Excel files to extract actual capital data"""

    print("📋 DETAILED EXCEL FILE ANALYSIS")
    print("=" * 50)

    # File paths
    fno_file = '/Users/Subho/Downloads/F&O_PnL_Report_6917002522_2023-04-01_2025-08-05..xlsx'
    stock_file = '/Users/Subho/Downloads/Stocks_PnL_Report_6917002522_01-04-2020_30-11-2024.xlsx'

    # Analyze F&O file in detail
    fno_analysis = analyze_fno_file_detailed(fno_file)

    # Analyze Stock file in detail
    stock_analysis = analyze_stock_file_detailed(stock_file)

    # Calculate actual opportunity cost
    opportunity_cost_analysis = calculate_actual_opportunity_cost(fno_analysis, stock_analysis)

    return opportunity_cost_analysis

def analyze_fno_file_detailed(file_path):
    """Analyze F&O file with detailed data extraction"""

    print("\n📊 F&O FILE DETAILED ANALYSIS")
    print("-" * 40)

    fno_data = {}

    try:
        # Read the Trade Level sheet with different header row attempts
        for header_row in [0, 1, 2, 3, 4, 5]:
            try:
                print(f"  Trying header row {header_row}...")
                df = pd.read_excel(file_path, sheet_name='Trade Level', header=header_row)

                print(f"  Columns found: {list(df.columns)}")
                print(f"  Sample data:")
                print(df.head(2).to_string())

                # Look for numerical columns that might contain capital data
                numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
                print(f"  Numeric columns: {numeric_cols}")

                if len(numeric_cols) > 0:
                    # Analyze each numeric column
                    for col in numeric_cols:
                        if df[col].notna().sum() > 10:  # At least 10 non-null values
                            max_val = df[col].max()
                            min_val = df[col].min()
                            mean_val = df[col].mean()
                            std_val = df[col].std()

                            print(f"\n    Column '{col}':")
                            print(f"      Max: {max_val:,.2f}")
                            print(f"      Min: {min_val:,.2f}")
                            print(f"      Mean: {mean_val:,.2f}")
                            print(f"      Std: {std_val:,.2f}")

                            # Try to identify what this column represents
                            if abs(max_val) > 1000000:  # Large values might be turnover
                                print(f"      Possibly: Total Turnover/Value")
                            elif abs(max_val) > 100000:  # Medium values might be P&L or margin
                                print(f"      Possibly: P&L or Margin")
                            elif abs(max_val) < 10000:  # Small values might be quantity
                                print(f"      Possibly: Quantity or Price")

                            # Store top values for analysis
                            top_values = df[col].nlargest(10)
                            print(f"      Top 10 values: {top_values.tolist()}")

                    fno_data['trade_level'] = {
                        'header_row': header_row,
                        'columns': list(df.columns),
                        'numeric_columns': numeric_cols,
                        'data_shape': df.shape,
                        'sample_data': df.head(5).to_dict()
                    }

                    break  # Found good data

            except Exception as e:
                print(f"    Error with header row {header_row}: {e}")
                continue

        # Try Contract Level sheet
        try:
            print(f"\n  Analyzing Contract Level sheet...")
            for header_row in [0, 1, 2]:
                try:
                    df_contract = pd.read_excel(file_path, sheet_name='Contract Level', header=header_row)
                    print(f"  Contract Level Columns: {list(df_contract.columns)}")

                    numeric_cols = df_contract.select_dtypes(include=[np.number]).columns.tolist()
                    print(f"  Contract Level Numeric: {numeric_cols}")

                    if len(numeric_cols) > 0:
                        fno_data['contract_level'] = {
                            'header_row': header_row,
                            'columns': list(df_contract.columns),
                            'numeric_columns': numeric_cols,
                            'data_shape': df_contract.shape,
                            'sample_data': df_contract.head(3).to_dict()
                        }
                        break

                except Exception as e:
                    print(f"    Error with Contract Level header {header_row}: {e}")

        except Exception as e:
            print(f"  Error reading Contract Level: {e}")

    except Exception as e:
        print(f"Error analyzing F&O file: {e}")

    return fno_data

def analyze_stock_file_detailed(file_path):
    """Analyze Stock file with detailed data extraction"""

    print("\n📈 STOCK FILE DETAILED ANALYSIS")
    print("-" * 40)

    stock_data = {}

    try:
        # Read the Trade Level sheet
        for header_row in [0, 1, 2, 3, 4, 5]:
            try:
                print(f"  Trying header row {header_row}...")
                df = pd.read_excel(file_path, sheet_name='Trade Level', header=header_row)

                print(f"  Columns found: {list(df.columns)}")
                print(f"  Sample data:")
                print(df.head(2).to_string())

                # Look for numerical columns
                numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
                print(f"  Numeric columns: {numeric_cols}")

                if len(numeric_cols) > 0:
                    # Analyze each numeric column
                    for col in numeric_cols:
                        if df[col].notna().sum() > 5:  # At least 5 non-null values
                            max_val = df[col].max()
                            min_val = df[col].min()
                            mean_val = df[col].mean()

                            print(f"\n    Column '{col}':")
                            print(f"      Max: {max_val:,.2f}")
                            print(f"      Min: {min_val:,.2f}")
                            print(f"      Mean: {mean_val:,.2f}")

                            # Calculate total absolute values as estimate of turnover
                            total_abs = df[col].abs().sum()
                            if total_abs > 0:
                                print(f"      Total Absolute: {total_abs:,.0f}")

                            # Identify potential position sizes
                            if abs(max_val) > 100000:  # Large values
                                print(f"      Possibly: Position Value / Turnover")
                                if total_abs > 0:
                                    estimated_total_turnover = total_abs * 2  # Assume each position has buy and sell
                                    print(f"      Estimated Total Turnover: ₹{estimated_total_turnover:,.0f}")

                    stock_data['trade_level'] = {
                        'header_row': header_row,
                        'columns': list(df.columns),
                        'numeric_columns': numeric_cols,
                        'data_shape': df.shape,
                        'sample_data': df.head(5).to_dict()
                    }
                    break

            except Exception as e:
                print(f"    Error with header row {header_row}: {e}")
                continue

        # Try Scrip Level sheet
        try:
            print(f"\n  Analyzing Scrip Level sheet...")
            for header_row in [0, 1, 2]:
                try:
                    df_scrip = pd.read_excel(file_path, sheet_name='Scrip Level', header=header_row)
                    print(f"  Scrip Level Columns: {list(df_scrip.columns)}")

                    numeric_cols = df_scrip.select_dtypes(include=[np.number]).columns.tolist()
                    print(f"  Scrip Level Numeric: {numeric_cols}")

                    if len(numeric_cols) > 0:
                        stock_data['scrip_level'] = {
                            'header_row': header_row,
                            'columns': list(df_scrip.columns),
                            'numeric_columns': numeric_cols,
                            'data_shape': df_scrip.shape,
                            'sample_data': df_scrip.head(3).to_dict()
                        }
                        break

                except Exception as e:
                    print(f"    Error with Scrip Level header {header_row}: {e}")

        except Exception as e:
            print(f"  Error reading Scrip Level: {e}")

    except Exception as e:
        print(f"Error analyzing Stock file: {e}")

    return stock_data

def calculate_actual_opportunity_cost(fno_analysis, stock_analysis):
    """Calculate actual opportunity cost based on extracted data"""

    print("\n💰 ACTUAL OPPORTUNITY COST CALCULATION")
    print("=" * 50)

    # Load P&L data
    try:
        with open('/Users/Subho/comprehensive_trading_analysis_results.json', 'r') as f:
            pnl_data = json.load(f)
    except:
        print("Error: P&L data not found")
        return

    your_actual_pnl = pnl_data['comparison']['combined_pnl']  # -₹846,192

    # Extract real capital estimates from the data
    actual_capital_estimates = extract_real_capital_from_data(fno_analysis, stock_analysis)

    # Calculate opportunity costs
    opportunity_costs = {}

    # Use conservative estimates based on extracted data
    if actual_capital_estimates['total_capital_min'] > 0:
        total_capital = actual_capital_estimates['total_capital_min']

        # Market return calculations (based on actual periods)
        fno_years = 29 / 12  # April 2023 - August 2025
        stock_years = 58 / 12  # April 2020 - November 2024

        nifty_cagr = 12.0  # Conservative
        fd_cagr = 6.0      # Conservative

        fno_market_return = actual_capital_estimates['fno_capital'] * (nifty_cagr/100) * fno_years
        stock_market_return = actual_capital_estimates['stock_capital'] * (nifty_cagr/100) * stock_years
        total_market_return = fno_market_return + stock_market_return

        fno_fd_return = actual_capital_estimates['fno_capital'] * (fd_cagr/100) * fno_years
        stock_fd_return = actual_capital_estimates['stock_capital'] * (fd_cagr/100) * stock_years
        total_fd_return = fno_fd_return + stock_fd_return

        opportunity_cost_vs_nifty = total_market_return - your_actual_pnl
        opportunity_cost_vs_fd = total_fd_return - your_actual_pnl

        # Annual costs
        avg_years = (fno_years + stock_years) / 2
        annual_nifty_cost = opportunity_cost_vs_nifty / avg_years
        annual_fd_cost = opportunity_cost_vs_fd / avg_years

        opportunity_costs = {
            'total_capital_actual': total_capital,
            'fno_capital': actual_capital_estimates['fno_capital'],
            'stock_capital': actual_capital_estimates['stock_capital'],
            'actual_pnl': your_actual_pnl,
            'market_return_nifty': total_market_return,
            'fd_return': total_fd_return,
            'opportunity_cost_vs_nifty': opportunity_cost_vs_nifty,
            'opportunity_cost_vs_fd': opportunity_cost_vs_fd,
            'annual_opportunity_cost_nifty': annual_nifty_cost,
            'annual_opportunity_cost_fd': annual_fd_cost,
            'period_years': avg_years
        }

        print(f"\n📊 ACTUAL CAPITAL ANALYSIS RESULTS:")
        print(f"=" * 50)
        print(f"Total Capital Deployed: ₹{total_capital:,.0f}")
        print(f"  F&O Capital: ₹{actual_capital_estimates['fno_capital']:,.0f}")
        print(f"  Stock Capital: ₹{actual_capital_estimates['stock_capital']:,.0f}")
        print(f"\nYour Actual P&L: ₹{your_actual_pnl:,.0f}")
        print(f"Market Return (NIFTY): ₹{total_market_return:,.0f}")
        print(f"Fixed Deposit Return: ₹{total_fd_return:,.0f}")
        print(f"\nOpportunity Cost:")
        print(f"  vs NIFTY: ₹{opportunity_cost_vs_nifty:,.0f}")
        print(f"  vs Fixed Deposits: ₹{opportunity_cost_vs_fd:,.0f}")
        print(f"\nAnnual Opportunity Cost:")
        print(f"  vs NIFTY: ₹{annual_nifty_cost:,.0f} per year")
        print(f"  vs Fixed Deposits: ₹{annual_fd_cost:,.0f} per year")

    # Save detailed analysis
    complete_analysis = {
        'analysis_timestamp': datetime.now().isoformat(),
        'fno_analysis': fno_analysis,
        'stock_analysis': stock_analysis,
        'capital_estimates': actual_capital_estimates,
        'opportunity_costs': opportunity_costs
    }

    with open('/Users/Subho/detailed_capital_analysis.json', 'w') as f:
        json.dump(complete_analysis, f, indent=2)

    print(f"\n📄 Detailed analysis saved: detailed_capital_analysis.json")

    return complete_analysis

def extract_real_capital_from_data(fno_analysis, stock_analysis):
    """Extract real capital estimates from the analyzed data"""

    capital_estimates = {
        'fno_capital': 0,
        'stock_capital': 0,
        'total_capital_min': 0,
        'methodology': []
    }

    # F&O capital estimation
    if 'trade_level' in fno_analysis:
        fno_data = fno_analysis['trade_level']

        # Look for large numerical values that might represent position values
        for col in fno_data.get('numeric_columns', []):
            if col in fno_data.get('sample_data', {}):
                values = list(fno_data['sample_data'][col].values())
                if values:
                    max_val = max(abs(v) for v in values if v is not None and not pd.isna(v))
                    if max_val > 100000:  # Significant position value
                        estimated_fno_capital = max_val * 10  # Conservative estimate
                        capital_estimates['fno_capital'] = max(capital_estimates['fno_capital'], estimated_fno_capital)
                        capital_estimates['methodology'].append(f"F&O capital from {col}: ₹{estimated_fno_capital:,.0f}")

    # Stock capital estimation
    if 'trade_level' in stock_analysis:
        stock_data = stock_analysis['trade_level']

        for col in stock_data.get('numeric_columns', []):
            if col in stock_data.get('sample_data', {}):
                values = list(stock_data['sample_data'][col].values())
                if values:
                    max_val = max(abs(v) for v in values if v is not None and not pd.isna(v))
                    if max_val > 50000:  # Significant position value
                        estimated_stock_capital = max_val * 5  # Conservative estimate
                        capital_estimates['stock_capital'] = max(capital_estimates['stock_capital'], estimated_stock_capital)
                        capital_estimates['methodology'].append(f"Stock capital from {col}: ₹{estimated_stock_capital:,.0f}")

    # If no good estimates, fall back to P&L-based calculation
    if capital_estimates['fno_capital'] == 0:
        # Use the known P&L max loss method
        capital_estimates['fno_capital'] = 230280 / 0.01  # ₹2.3 crore minimum
        capital_estimates['methodology'].append("F&O capital from max loss (1% risk): ₹23,028,000")

    if capital_estimates['stock_capital'] == 0:
        capital_estimates['stock_capital'] = 24858 / 0.01  # ₹24.9 lakh minimum
        capital_estimates['methodology'].append("Stock capital from max loss (1% risk): ₹2,485,800")

    capital_estimates['total_capital_min'] = capital_estimates['fno_capital'] + capital_estimates['stock_capital']

    return capital_estimates

if __name__ == "__main__":
    results = analyze_excel_files_detailed()