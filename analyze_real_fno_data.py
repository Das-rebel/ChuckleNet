#!/usr/bin/env python3
"""
Analyze Real F&O Data and Create Visualizations
Based on your actual F&O P&L Excel file
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json

def load_fno_excel_data():
    """Load your actual F&O Excel data"""
    print("📊 Loading your real F&O Excel data...")

    try:
        # Try different sheet names that might contain the data
        excel_file = '/Users/Subho/Downloads/F&O_PnL_Report_6917002522_2023-04-01_2025-11-10..xlsx'

        # First, let's see what sheets are available
        xl = pd.ExcelFile(excel_file)
        print(f"Available sheets: {xl.sheet_names}")

        # Try to load the main data sheet (likely first sheet or one with common names)
        df = None
        for sheet_name in xl.sheet_names:
            try:
                df = pd.read_excel(excel_file, sheet_name=sheet_name)
                print(f"Successfully loaded sheet: {sheet_name}")
                print(f"Shape: {df.shape}")
                print(f"Columns: {list(df.columns)}")
                break
            except Exception as e:
                print(f"Failed to load sheet {sheet_name}: {e}")
                continue

        if df is None:
            print("Could not load any sheet successfully")
            return None, None

        # Display sample data
        print("\nSample data:")
        print(df.head())

        return df, excel_file

    except Exception as e:
        print(f"Error loading Excel file: {e}")
        return None, None

def analyze_fno_patterns(df):
    """Analyze patterns in F&O data"""
    print("\n🔍 Analyzing F&O trading patterns...")

    # Convert date columns if they exist
    date_columns = ['Date', 'Trade Date', 'Buy Date', 'Sell Date', 'Exit Date', 'date']
    for col in date_columns:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')
            print(f"Converted {col} to datetime")

    # Identify P&L column
    pnl_columns = ['P&L', 'PnL', 'Realized P&L', 'Profit & Loss', 'profit_loss', 'realized_pnl']
    pnl_col = None
    for col in pnl_columns:
        if col in df.columns:
            pnl_col = col
            print(f"Found P&L column: {col}")
            break

    if pnl_col is None:
        print("No P&L column found. Available columns:", df.columns.tolist())
        return None

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

    print(f"\n📈 F&O TRADING STATISTICS:")
    print(f"  Total P&L: ₹{total_pnl:,.2f}")
    print(f"  Number of Trades: {num_trades}")
    print(f"  Win Rate: {win_rate:.1f}%")
    print(f"  Winning Trades: {win_trades}")
    print(f"  Losing Trades: {loss_trades}")
    print(f"  Average Win: ₹{avg_win:,.2f}")
    print(f"  Average Loss: ₹{avg_loss:,.2f}")
    print(f"  Maximum Win: ₹{max_win:,.2f}")
    print(f"  Maximum Loss: ₹{max_loss:,.2f}")

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
        'pnl_col': pnl_col
    }

def create_timeline_analysis(df, stats):
    """Create timeline analysis if date column exists"""
    print("\n📅 Creating timeline analysis...")

    # Find date column
    date_col = None
    for col in df.columns:
        if any(keyword in col.lower() for keyword in ['date', 'time']):
            if pd.api.types.is_datetime64_any_dtype(df[col]):
                date_col = col
                break

    if date_col is None:
        print("No date column found for timeline analysis")
        return None

    # Sort by date
    df_sorted = df.sort_values(date_col)
    pnl_col = stats['pnl_col']

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
        'date_col': date_col
    }

def identify_trading_patterns(df, stats):
    """Identify specific trading patterns"""
    print("\n🔍 Identifying trading patterns...")

    pnl_col = stats['pnl_col']

    # Large trades analysis
    large_win_threshold = stats['avg_win'] * 2
    large_loss_threshold = stats['avg_loss'] * 2

    large_wins = df[df[pnl_col] > large_win_threshold]
    large_losses = df[df[pnl_col] < large_loss_threshold]

    print(f"\n💰 LARGE TRADES ANALYSIS:")
    print(f"  Large Wins (>{large_win_threshold:,.2f}): {len(large_wins)} trades")
    print(f"  Large Losses (<{large_loss_threshold:,.2f}): {len(large_losses)} trades")

    if len(large_wins) > 0:
        print(f"  Total from Large Wins: ₹{large_wins[pnl_col].sum():,.2f}")
        print(f"  Average Large Win: ₹{large_wins[pnl_col].mean():,.2f}")

    if len(large_losses) > 0:
        print(f"  Total from Large Losses: ₹{large_losses[pnl_col].sum():,.2f}")
        print(f"  Average Large Loss: ₹{large_losses[pnl_col].mean():,.2f}")

    # Look for other patterns
    patterns = {}

    # Check if there are other categorical columns
    categorical_cols = df.select_dtypes(include=['object']).columns
    for col in categorical_cols:
        if col not in [pnl_col, stats.get('date_col', '')] and df[col].nunique() < 20:
            pattern_analysis = df.groupby(col)[pnl_col].agg(['sum', 'count', 'mean'])
            patterns[col] = pattern_analysis.sort_values('sum', ascending=False)

    if patterns:
        print(f"\n📊 PATTERNS BY CATEGORY:")
        for category, pattern_data in patterns.items():
            print(f"\n  {category}:")
            for value, row in pattern_data.head().iterrows():
                print(f"    {value}: ₹{row['sum']:,.2f} ({row['count']} trades, avg ₹{row['mean']:,.2f})")

    return {
        'large_wins': large_wins,
        'large_losses': large_losses,
        'patterns': patterns
    }

def simulate_professional_improvements(df, stats):
    """Simulate how professional improvements would affect your real data"""
    print("\n💼 Simulating professional trading improvements...")

    pnl_col = stats['pnl_col']
    improved_df = df.copy()

    # Apply professional improvements based on our earlier analysis
    improvements = []
    total_improvement = 0

    for idx, row in df.iterrows():
        original_pnl = row[pnl_col]
        professional_pnl = original_pnl
        improvement_reasons = []

        # 1. Expiry Management (30% of trades assumed near expiry)
        if np.random.random() < 0.3:  # Simulate 30% near expiry
            if original_pnl < 0:
                expiry_saving = abs(original_pnl) * 0.7  # Save 70%
                professional_pnl += expiry_saving
                improvement_reasons.append(f"Expiry: ₹{expiry_saving:,.2f}")
                total_improvement += expiry_saving

        # 2. Time-based Stops (25% of losing trades held too long)
        if original_pnl < 0 and np.random.random() < 0.25:
            time_saving = abs(original_pnl) * 0.5  # Save 50%
            professional_pnl += time_saving
            improvement_reasons.append(f"Time stop: ₹{time_saving:,.2f}")
            total_improvement += time_saving

        # 3. ATR Position Sizing (apply to 40% of trades)
        if np.random.random() < 0.4:
            if original_pnl < 0:
                atr_saving = abs(original_pnl) * 0.3  # Save 30%
                professional_pnl += atr_saving
                improvement_reasons.append(f"ATR sizing: ₹{atr_saving:,.2f}")
                total_improvement += atr_saving

        improvements.append({
            'original_pnl': original_pnl,
            'professional_pnl': professional_pnl,
            'improvement': professional_pnl - original_pnl,
            'reasons': improvement_reasons
        })

    improved_pnl_total = sum([imp['professional_pnl'] for imp in improvements])
    original_pnl_total = stats['total_pnl']

    print(f"\n📈 PROFESSIONAL IMPROVEMENT SIMULATION:")
    print(f"  Original Total P&L: ₹{original_pnl_total:,.2f}")
    print(f"  Professional Total P&L: ₹{improved_pnl_total:,.2f}")
    print(f"  Total Improvement: ₹{improved_pnl_total - original_pnl_total:,.2f}")
    print(f"  Improvement Percentage: {((improved_pnl_total - original_pnl_total) / abs(original_pnl_total) * 100) if original_pnl_total != 0 else 0:.1f}%")

    return {
        'original_total': original_pnl_total,
        'professional_total': improved_pnl_total,
        'total_improvement': improved_pnl_total - original_pnl_total,
        'improvements': improvements
    }

def create_visualization_summary(stats, timeline_data, pattern_data, improvement_data):
    """Create a text-based visualization summary"""
    print("\n📊 VISUALIZATION SUMMARY:")
    print("=" * 50)

    print(f"\n🎯 OVERALL PERFORMANCE:")
    print(f"  Total P&L: ₹{stats['total_pnl']:,.2f}")
    print(f"  Number of Trades: {stats['num_trades']}")
    print(f"  Win Rate: {stats['win_rate']:.1f}%")
    print(f"  Average Win: ₹{stats['avg_win']:,.2f}")
    print(f"  Average Loss: ₹{abs(stats['avg_loss']):,.2f}")

    if timeline_data:
        print(f"\n📅 TIMELINE INSIGHTS:")
        print(f"  Best Month: {timeline_data['best_month'][0]} (₹{timeline_data['best_month'][1]:,.2f})")
        print(f"  Worst Month: {timeline_data['worst_month'][0]} (₹{timeline_data['worst_month'][1]:,.2f})")

        # Simple monthly trend
        monthly_stats = timeline_data['monthly_stats']
        pnl_col = stats['pnl_col']
        monthly_pnl = monthly_stats[(pnl_col, 'sum')]

        positive_months = (monthly_pnl > 0).sum()
        negative_months = (monthly_pnl <= 0).sum()

        print(f"  Profitable Months: {positive_months}/{len(monthly_pnl)} ({positive_months/len(monthly_pnl)*100:.1f}%)")

    if pattern_data:
        print(f"\n🔍 PATTERN INSIGHTS:")
        print(f"  Large Wins: {len(pattern_data['large_wins'])} trades")
        print(f"  Large Losses: {len(pattern_data['large_losses'])} trades")

        if len(pattern_data['large_wins']) > 0:
            large_win_total = pattern_data['large_wins'][pnl_col].sum()
            print(f"  Impact from Large Wins: ₹{large_win_total:,.2f}")

        if len(pattern_data['large_losses']) > 0:
            large_loss_total = pattern_data['large_losses'][pnl_col].sum()
            print(f"  Impact from Large Losses: ₹{abs(large_loss_total):,.2f}")

    if improvement_data:
        print(f"\n💼 PROFESSIONAL IMPROVEMENT POTENTIAL:")
        print(f"  Current P&L: ₹{improvement_data['original_total']:,.2f}")
        print(f"  With Professional Tools: ₹{improvement_data['professional_total']:,.2f}")
        print(f"  Potential Improvement: ₹{improvement_data['total_improvement']:,.2f}")

        if improvement_data['original_total'] != 0:
            improvement_pct = (improvement_data['total_improvement'] / abs(improvement_data['original_total'])) * 100
            print(f"  Improvement Percentage: {improvement_pct:.1f}%")

def save_analysis_results(stats, timeline_data, pattern_data, improvement_data):
    """Save analysis results to files"""
    print("\n💾 Saving analysis results...")

    # Save detailed analysis
    results = {
        'basic_stats': stats,
        'timeline_analysis': timeline_data,
        'pattern_analysis': pattern_data,
        'improvement_simulation': improvement_data,
        'analysis_date': datetime.now().isoformat()
    }

    # Save as JSON
    with open('/Users/Subho/fno_analysis_results.json', 'w') as f:
        json.dump(results, f, indent=2, default=str)

    print("✅ Results saved to: /Users/Subho/fno_analysis_results.json")

    # Save as CSV if dataframe is available
    try:
        if improvement_data and len(improvement_data['improvements']) > 0:
            improvement_df = pd.DataFrame(improvement_data['improvements'])
            improvement_df.to_csv('/Users/Subho/fno_improvement_simulation.csv', index=False)
            print("✅ Improvement simulation saved to: /Users/Subho/fno_improvement_simulation.csv")
    except Exception as e:
        print(f"Could not save CSV: {e}")

def main():
    """Main analysis function"""
    print("🚀 REAL F&O DATA ANALYSIS & VISUALIZATION")
    print("=" * 50)
    print("Analyzing your actual F&O Excel data")
    print("=" * 50)

    # Load the data
    df, excel_file = load_fno_excel_data()

    if df is None:
        print("❌ Could not load F&O data. Please check the Excel file.")
        return

    # Analyze patterns
    stats = analyze_fno_patterns(df)

    if stats is None:
        print("❌ Could not analyze F&O patterns.")
        return

    # Timeline analysis
    timeline_data = create_timeline_analysis(df, stats)

    # Pattern analysis
    pattern_data = identify_trading_patterns(df, stats)

    # Simulate professional improvements
    improvement_data = simulate_professional_improvements(df, stats)

    # Create visualization summary
    create_visualization_summary(stats, timeline_data, pattern_data, improvement_data)

    # Save results
    save_analysis_results(stats, timeline_data, pattern_data, improvement_data)

    print(f"\n🎯 ANALYSIS COMPLETE!")
    print(f"📊 Data file: {excel_file}")
    print(f"📈 Detailed results saved to JSON and CSV files")

    return df, stats, improvement_data

if __name__ == "__main__":
    df, stats, improvement_data = main()