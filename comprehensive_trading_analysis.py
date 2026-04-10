#!/usr/bin/env python3
"""
Comprehensive Trading Analysis for F&O and Stock Data
Analyzes both Excel files and creates visualizations
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json

def analyze_excel_file(file_path, file_type):
    """Analyze Excel file with flexible structure detection"""
    print(f"\n📊 Analyzing {file_type} data from {file_path.split('/')[-1]}...")

    try:
        # Load all sheets to find the right one
        excel_file = pd.ExcelFile(file_path)
        print(f"Available sheets: {excel_file.sheet_names}")

        df = None
        selected_sheet = None

        for sheet_name in excel_file.sheet_names:
            try:
                temp_df = pd.read_excel(file_path, sheet_name=sheet_name)
                print(f"\nSheet '{sheet_name}' - Shape: {temp_df.shape}")
                print(f"Columns: {list(temp_df.columns)}")

                # Look for data rows (skip header rows with NaN)
                # Find first row with substantial data
                data_start_row = None
                for idx, row in temp_df.iterrows():
                    non_null_count = row.notna().sum()
                    if non_null_count >= 3:  # At least 3 non-null values
                        data_start_row = idx
                        break

                if data_start_row is not None:
                    # Read again with header row detected
                    if data_start_row > 0:
                        temp_df = pd.read_excel(file_path, sheet_name=sheet_name,
                                               header=data_start_row)

                    # Remove completely empty rows
                    temp_df = temp_df.dropna(how='all')
                    temp_df = temp_df.dropna(axis=1, how='all')

                    if len(temp_df) > 5:  # Need substantial data
                        df = temp_df
                        selected_sheet = sheet_name
                        print(f"Selected sheet: {sheet_name}")
                        print(f"Data shape after cleaning: {df.shape}")
                        print(f"Cleaned columns: {list(df.columns)}")
                        break

            except Exception as e:
                print(f"Error reading sheet {sheet_name}: {e}")
                continue

        if df is None:
            print(f"No valid data found in {file_type} file")
            return None, None

        # Display sample data
        print(f"\nSample data from {selected_sheet}:")
        print(df.head())

        # Try to identify P&L column
        pnl_columns = []
        for col in df.columns:
            col_str = str(col).lower()
            if any(keyword in col_str for keyword in ['p&l', 'pnl', 'profit', 'loss', 'realized']):
                pnl_columns.append(col)
            # Also check if any sample values look like P&L
            if len(df) > 0:
                sample_values = df[col].dropna().head(5).astype(str)
                for val in sample_values:
                    if any(keyword in val.lower() for keyword in ['p&l', 'pnl', 'profit', 'loss']):
                        if col not in pnl_columns:
                            pnl_columns.append(col)
                        break

        print(f"\nPotential P&L columns: {pnl_columns}")

        # Try to identify date columns
        date_columns = []
        for col in df.columns:
            if df[col].dtype == 'object':
                # Try to convert to datetime
                try:
                    pd.to_datetime(df[col].dropna().head())
                    date_columns.append(col)
                except:
                    pass
            elif pd.api.types.is_datetime64_any_dtype(df[col]):
                date_columns.append(col)

        print(f"Potential date columns: {date_columns}")

        return df, {
            'file_type': file_type,
            'sheet': selected_sheet,
            'pnl_columns': pnl_columns,
            'date_columns': date_columns
        }

    except Exception as e:
        print(f"Error loading {file_type} file: {e}")
        return None, None

def analyze_trading_patterns(df, metadata):
    """Analyze trading patterns from the data"""
    print(f"\n🔍 Analyzing {metadata['file_type']} trading patterns...")

    # Find P&L column
    pnl_col = None
    if metadata['pnl_columns']:
        for col in metadata['pnl_columns']:
            if col in df.columns:
                pnl_col = col
                break

    if pnl_col is None:
        print("No P&L column found")
        return None

    # Clean P&L data - remove non-numeric values
    df[pnl_col] = pd.to_numeric(df[pnl_col], errors='coerce')
    df = df.dropna(subset=[pnl_col])

    print(f"Using P&L column: {pnl_col}")
    print(f"Cleaned data shape: {df.shape}")

    # Basic statistics
    total_pnl = df[pnl_col].sum()
    num_trades = len(df)
    win_trades = (df[pnl_col] > 0).sum()
    loss_trades = (df[pnl_col] < 0).sum()
    win_rate = (win_trades / num_trades) * 100 if num_trades > 0 else 0

    avg_win = df[df[pnl_col] > 0][pnl_col].mean() if win_trades > 0 else 0
    avg_loss = df[df[pnl_col] < 0][pnl_col].mean() if loss_trades > 0 else 0
    max_win = df[pnl_col].max()
    max_loss = df[pnl_col].min()

    print(f"\n📈 {metadata['file_type'].upper()} TRADING STATISTICS:")
    print(f"  Total P&L: ₹{total_pnl:,.2f}")
    print(f"  Number of Trades: {num_trades}")
    print(f"  Win Rate: {win_rate:.1f}%")
    print(f"  Winning Trades: {win_trades}")
    print(f"  Losing Trades: {loss_trades}")
    print(f"  Average Win: ₹{avg_win:,.2f}")
    print(f"  Average Loss: ₹{abs(avg_loss):,.2f}")
    print(f"  Maximum Win: ₹{max_win:,.2f}")
    print(f"  Maximum Loss: ₹{abs(max_loss):,.2f}")

    # Look for time patterns if date column exists
    date_col = None
    if metadata['date_columns']:
        for col in metadata['date_columns']:
            if col in df.columns:
                date_col = col
                df[col] = pd.to_datetime(df[col], errors='coerce')
                break

    timeline_analysis = None
    if date_col:
        timeline_analysis = create_timeline_analysis(df, pnl_col, date_col)

    return {
        'total_pnl': total_pnl,
        'num_trades': num_trades,
        'win_rate': win_rate,
        'win_trades': win_trades,
        'loss_trades': loss_trades,
        'avg_win': avg_win,
        'avg_loss': avg_loss,
        'max_win': max_win,
        'max_loss': max_loss,
        'pnl_col': pnl_col,
        'date_col': date_col,
        'timeline_analysis': timeline_analysis
    }

def create_timeline_analysis(df, pnl_col, date_col):
    """Create timeline analysis"""
    print(f"\n📅 Creating timeline analysis using {date_col}...")

    # Sort by date
    df_sorted = df.sort_values(date_col)

    # Calculate cumulative P&L
    df_sorted['cumulative_pnl'] = df_sorted[pnl_col].cumsum()

    # Monthly analysis
    df_sorted['year_month'] = df_sorted[date_col].dt.to_period('M')
    monthly_stats = df_sorted.groupby('year_month').agg({
        pnl_col: ['sum', 'count'],
        'cumulative_pnl': 'last'
    }).round(2)

    print(f"\n📊 MONTHLY BREAKDOWN:")
    for period, row in monthly_stats.iterrows():
        monthly_pnl = row[(pnl_col, 'sum')]
        trade_count = row[(pnl_col, 'count')]
        cumulative = row[('cumulative_pnl', 'last')]

        print(f"  {period}:")
        print(f"    Monthly P&L: ₹{monthly_pnl:,.2f}")
        print(f"    Trades: {trade_count}")
        print(f"    Cumulative: ₹{cumulative:,.2f}")

    # Best and worst months
    monthly_pnl_series = monthly_stats[(pnl_col, 'sum')]
    if len(monthly_pnl_series) > 0:
        best_month = monthly_pnl_series.max()
        worst_month = monthly_pnl_series.min()
        best_month_period = monthly_pnl_series.idxmax()
        worst_month_period = monthly_pnl_series.idxmin()

        print(f"\n🏆 BEST MONTH: {best_month_period} - ₹{best_month:,.2f}")
        print(f"📉 WORST MONTH: {worst_month_period} - ₹{worst_month:,.2f}")

        return {
            'monthly_stats': monthly_stats,
            'best_month': (best_month_period, best_month),
            'worst_month': (worst_month_period, worst_month),
            'data_range': (df_sorted[date_col].min(), df_sorted[date_col].max())
        }

    return None

def create_comparison_visualization(fno_stats, stock_stats):
    """Create comparison visualization between F&O and Stock trading"""
    print("\n📊 COMPREHENSIVE TRADING COMPARISON")
    print("=" * 50)

    print(f"\n🎯 PERFORMANCE COMPARISON:")
    print(f"{'Metric':<20} {'F&O Trading':<15} {'Stock Trading':<15} {'Difference':<15}")
    print("-" * 65)

    def safe_get(stats, key, default=0):
        return stats.get(key, default) if stats else default

    metrics = [
        ('Total P&L (₹)', 'total_pnl', 'total_pnl'),
        ('Number of Trades', 'num_trades', 'num_trades'),
        ('Win Rate (%)', 'win_rate', 'win_rate'),
        ('Winning Trades', 'win_trades', 'win_trades'),
        ('Average Win (₹)', 'avg_win', 'avg_win'),
        ('Average Loss (₹)', 'avg_loss', 'avg_loss'),
        ('Max Win (₹)', 'max_win', 'max_win'),
        ('Max Loss (₹)', 'max_loss', 'max_loss')
    ]

    for label, fno_key, stock_key in metrics:
        fno_val = safe_get(fno_stats, fno_key)
        stock_val = safe_get(stock_stats, stock_key)

        if isinstance(fno_val, float):
            fno_display = f"{fno_val:,.2f}"
        else:
            fno_display = str(fno_val)

        if isinstance(stock_val, float):
            stock_display = f"{stock_val:,.2f}"
        else:
            stock_display = str(stock_val)

        if isinstance(fno_val, (int, float)) and isinstance(stock_val, (int, float)):
            diff = fno_val - stock_val
            diff_display = f"{diff:,.2f}"
        else:
            diff_display = "N/A"

        print(f"{label:<20} {fno_display:<15} {stock_display:<15} {diff_display:<15}")

    # Combined analysis
    combined_pnl = safe_get(fno_stats, 'total_pnl') + safe_get(stock_stats, 'total_pnl')
    combined_trades = safe_get(fno_stats, 'num_trades') + safe_get(stock_stats, 'num_trades')

    print(f"\n📈 COMBINED PERFORMANCE:")
    print(f"  Total Combined P&L: ₹{combined_pnl:,.2f}")
    print(f"  Total Combined Trades: {combined_trades}")

    if fno_stats and stock_stats:
        fno_contribution = (fno_stats['total_pnl'] / combined_pnl) * 100 if combined_pnl != 0 else 0
        stock_contribution = (stock_stats['total_pnl'] / combined_pnl) * 100 if combined_pnl != 0 else 0

        print(f"  F&O Contribution: {fno_contribution:.1f}%")
        print(f"  Stock Contribution: {stock_contribution:.1f}%")

def create_text_charts(fno_stats, stock_stats):
    """Create text-based charts"""
    print("\n📈 TEXT-BASED VISUALIZATIONS")
    print("=" * 40)

    # P&L Comparison Chart
    print(f"\n💰 P&L COMPARISON CHART:")
    fno_pnl = fno_stats['total_pnl'] if fno_stats else 0
    stock_pnl = stock_stats['total_pnl'] if stock_stats else 0

    max_pnl = max(abs(fno_pnl), abs(stock_pnl))
    if max_pnl > 0:
        fno_bars = int((abs(fno_pnl) / max_pnl) * 20)
        stock_bars = int((abs(stock_pnl) / max_pnl) * 20)

        print(f"F&O Trading:  {'█' * fno_bars}{' ' * (20 - fno_bars)} ₹{fno_pnl:,.0f}")
        print(f"Stock Trading: {'█' * stock_bars}{' ' * (20 - stock_bars)} ₹{stock_pnl:,.0f}")

    # Win Rate Comparison
    print(f"\n📊 WIN RATE COMPARISON:")
    fno_wr = fno_stats['win_rate'] if fno_stats else 0
    stock_wr = stock_stats['win_rate'] if stock_stats else 0

    print(f"F&O Trading:  {'█' * int(fno_wr)}{' ' * (100 - int(fno_wr))} {fno_wr:.1f}%")
    print(f"Stock Trading: {'█' * int(stock_wr)}{' ' * (100 - int(stock_wr))} {stock_wr:.1f}%")

    # Timeline charts if available
    print(f"\n📅 PERFORMANCE TIMELINE:")
    if fno_stats and fno_stats.get('timeline_analysis'):
        timeline = fno_stats['timeline_analysis']
        print(f"F&O Trading Period: {timeline['data_range'][0]} to {timeline['data_range'][1]}")
        print(f"Best Month: {timeline['best_month'][0]} (₹{timeline['best_month'][1]:,.0f})")
        print(f"Worst Month: {timeline['worst_month'][0]} (₹{timeline['worst_month'][1]:,.0f})")

    if stock_stats and stock_stats.get('timeline_analysis'):
        timeline = stock_stats['timeline_analysis']
        print(f"Stock Trading Period: {timeline['data_range'][0]} to {timeline['data_range'][1]}")
        print(f"Best Month: {timeline['best_month'][0]} (₹{timeline['best_month'][1]:,.0f})")
        print(f"Worst Month: {timeline['worst_month'][0]} (₹{timeline['worst_month'][1]:,.0f})")

def simulate_professional_improvements(fno_stats, stock_stats):
    """Simulate professional improvements for both F&O and Stock trading"""
    print("\n💼 PROFESSIONAL IMPROVEMENT SIMULATION")
    print("=" * 40)

    def simulate_improvement(stats, asset_type):
        if not stats:
            return None

        original_pnl = stats['total_pnl']

        # Apply improvement factors based on our earlier analysis
        improvement_factor = 1.0

        # F&O has higher volatility, so more room for improvement
        if asset_type == 'F&O':
            expiry_saving = abs(original_pnl) * 0.3 if original_pnl < 0 else 0
            time_saving = abs(original_pnl) * 0.25 if original_pnl < 0 else 0
            atr_saving = abs(original_pnl) * 0.2 if original_pnl < 0 else 0
            total_saving = expiry_saving + time_saving + atr_saving
        else:  # Stock trading - usually less volatile
            expiry_saving = 0  # Stocks don't have expiry
            time_saving = abs(original_pnl) * 0.15 if original_pnl < 0 else 0
            atr_saving = abs(original_pnl) * 0.1 if original_pnl < 0 else 0
            total_saving = time_saving + atr_saving

        professional_pnl = original_pnl + total_saving
        improvement = professional_pnl - original_pnl

        print(f"\n{asset_type} Trading:")
        print(f"  Current P&L: ₹{original_pnl:,.2f}")
        print(f"  Professional P&L: ₹{professional_pnl:,.2f}")
        print(f"  Improvement: ₹{improvement:,.2f}")

        if original_pnl != 0:
            improvement_pct = (improvement / abs(original_pnl)) * 100
            print(f"  Improvement Percentage: {improvement_pct:.1f}%")

        return {
            'original_pnl': original_pnl,
            'professional_pnl': professional_pnl,
            'improvement': improvement,
            'improvement_pct': improvement_pct if original_pnl != 0 else 0
        }

    fno_improvement = simulate_improvement(fno_stats, 'F&O')
    stock_improvement = simulate_improvement(stock_stats, 'Stocks')

    # Combined improvement
    if fno_improvement and stock_improvement:
        combined_original = fno_improvement['original_pnl'] + stock_improvement['original_pnl']
        combined_professional = fno_improvement['professional_pnl'] + stock_improvement['professional_pnl']
        combined_improvement = combined_professional - combined_original

        print(f"\n🎯 COMBINED IMPACT:")
        print(f"  Current Combined P&L: ₹{combined_original:,.2f}")
        print(f"  Professional Combined P&L: ₹{combined_professional:,.2f}")
        print(f"  Total Combined Improvement: ₹{combined_improvement:,.2f}")

        if combined_original != 0:
            combined_improvement_pct = (combined_improvement / abs(combined_original)) * 100
            print(f"  Combined Improvement Percentage: {combined_improvement_pct:.1f}%")

        return fno_improvement, stock_improvement, {
            'combined_original': combined_original,
            'combined_professional': combined_professional,
            'combined_improvement': combined_improvement,
            'combined_improvement_pct': combined_improvement_pct if combined_original != 0 else 0
        }

    return fno_improvement, stock_improvement, None

def save_comprehensive_results(fno_stats, stock_stats, fno_metadata, stock_metadata, improvements):
    """Save comprehensive analysis results"""
    print("\n💾 Saving comprehensive analysis results...")

    results = {
        'analysis_date': datetime.now().isoformat(),
        'fno_analysis': {
            'metadata': fno_metadata,
            'stats': fno_stats
        },
        'stock_analysis': {
            'metadata': stock_metadata,
            'stats': stock_stats
        },
        'comparison': {
            'combined_pnl': (fno_stats['total_pnl'] if fno_stats else 0) + (stock_stats['total_pnl'] if stock_stats else 0),
            'combined_trades': (fno_stats['num_trades'] if fno_stats else 0) + (stock_stats['num_trades'] if stock_stats else 0)
        },
        'improvements': improvements
    }

    # Save as JSON
    with open('/Users/Subho/comprehensive_trading_analysis_results.json', 'w') as f:
        json.dump(results, f, indent=2, default=str)

    print("✅ Comprehensive results saved to: /Users/Subho/comprehensive_trading_analysis_results.json")

def main():
    """Main analysis function"""
    print("🚀 COMPREHENSIVE TRADING DATA ANALYSIS")
    print("=" * 60)
    print("Analyzing both F&O and Stock trading data")
    print("=" * 60)

    # Analyze F&O data
    fno_file = '/Users/Subho/Downloads/F&O_PnL_Report_6917002522_2023-04-01_2025-11-10..xlsx'
    fno_df, fno_metadata = analyze_excel_file(fno_file, 'F&O')
    fno_stats = analyze_trading_patterns(fno_df, fno_metadata) if fno_df is not None and not fno_df.empty else None

    # Analyze Stock data
    stock_file = '/Users/Subho/Downloads/Stocks_PnL_Report_6917002522_01-04-2020_30-11-2024.xlsx'
    stock_df, stock_metadata = analyze_excel_file(stock_file, 'Stocks')
    stock_stats = analyze_trading_patterns(stock_df, stock_metadata) if stock_df is not None and not stock_df.empty else None

    # Create visualizations
    create_comparison_visualization(fno_stats, stock_stats)
    create_text_charts(fno_stats, stock_stats)

    # Simulate improvements
    improvements = simulate_professional_improvements(fno_stats, stock_stats)

    # Save results
    save_comprehensive_results(fno_stats, stock_stats, fno_metadata, stock_metadata, improvements)

    print(f"\n🎯 ANALYSIS COMPLETE!")
    print(f"📊 F&O File: {fno_file}")
    print(f"📈 Stock File: {stock_file}")
    print(f"📋 Results saved to: /Users/Subho/comprehensive_trading_analysis_results.json")

    return fno_stats, stock_stats, improvements

if __name__ == "__main__":
    fno_stats, stock_stats, improvements = main()