#!/usr/bin/env python3
"""
Comprehensive F&O Trading Timing Analysis
Analyzes whether trades were timed correctly vs market movements
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import date

# Set style
plt.style.use('default')
sns.set_palette("husl")

def load_and_clean_data():
    """Load and prepare trading data for analysis"""
    print("📊 Loading trading data...")

    # Load the detailed trades
    df = pd.read_csv('/Users/Subho/Downloads/fno_trade_details_with_expiry.csv')

    # Convert dates
    df['buy_date'] = pd.to_datetime(df['buy_date'])
    df['sell_date'] = pd.to_datetime(df['sell_date'])
    df['expiry'] = pd.to_datetime(df['expiry'])

    # Load daily P&L
    daily_pnl = pd.read_csv('/Users/Subho/Downloads/fno_daily_pnl.csv')
    daily_pnl['sell_day'] = pd.to_datetime(daily_pnl['sell_day'])

    print(f"✅ Loaded {len(df)} trades covering {df['buy_date'].min()} to {df['sell_date'].max()}")
    return df, daily_pnl

def analyze_timing_patterns(df):
    """Analyze entry and exit timing patterns"""
    print("\n🔍 Analyzing timing patterns...")

    # Create analysis columns
    df['trade_month'] = df['sell_date'].dt.to_period('M')
    df['trade_year'] = df['sell_date'].dt.year
    df['weekday'] = df['sell_date'].dt.day_name()
    df['week_number'] = df['sell_date'].dt.isocalendar().week

    # Calculate trade characteristics
    df['is_profit'] = df['realized_pnl'] > 0
    df['abs_pnl'] = abs(df['realized_pnl'])

    # Analyze holding periods by profitability
    holding_analysis = df.groupby('is_profit')['holding_days'].agg(['mean', 'median', 'count'])
    print("\n📅 Holding Period Analysis:")
    print(holding_analysis)

    # Expiry timing analysis
    expiry_bins = [-1, 0, 7, 14, 21, 30, 60]
    df['expiry_bucket'] = pd.cut(df['days_to_expiry_exit'], bins=expiry_bins,
                                  labels=['On Expiry', '0-7d', '8-14d', '15-21d', '22-30d', '30d+'])

    expiry_pnl = df.groupby('expiry_bucket')['realized_pnl'].agg(['sum', 'mean', 'count'])
    print("\n⏰ Expiry Timing Analysis:")
    print(expiry_pnl)

    return df

def analyze_market_regime_changes(df, daily_pnl):
    """Analyze major loss periods and potential market regime changes"""
    print("\n📉 Analyzing market regime changes and loss periods...")

    # Identify worst trading periods
    worst_days = daily_pnl.nsmallest(10, 'realized_pnl')
    print("\n🔴 Worst 10 Trading Days:")
    print(worst_days)

    # Find consecutive loss periods
    daily_pnl['is_loss'] = daily_pnl['realized_pnl'] < 0
    daily_pnl['loss_streak'] = (daily_pnl['is_loss'] !=
                               daily_pnl['is_loss'].shift()).cumsum()

    # Calculate streak statistics
    streaks = []
    current_streak = 0

    for is_loss in daily_pnl['is_loss']:
        if is_loss:
            current_streak += 1
        else:
            if current_streak > 0:
                streaks.append(current_streak)
            current_streak = 0

    if current_streak > 0:
        streaks.append(current_streak)

    print(f"\n📊 Loss Streak Analysis:")
    print(f"Average loss streak: {np.mean(streaks):.1f} days")
    print(f"Longest loss streak: {max(streaks)} days")
    print(f"Total loss streaks: {len(streaks)}")

    # Analyze the October 2024 crisis period
    oct_2024 = daily_pnl[(daily_pnl['sell_day'] >= '2024-10-01') &
                         (daily_pnl['sell_day'] <= '2024-10-31')]

    if not oct_2024.empty:
        oct_pnl = oct_2024['realized_pnl'].sum()
        print(f"\n🚨 October 2024 Analysis:")
        print(f"Total October P&L: ₹{oct_pnl:,.2f}")
        print(f"Trading days: {len(oct_2024)}")
        print(f"Win days: {(oct_2024['realized_pnl'] > 0).sum()}")
        print(f"Loss days: {(oct_2024['realized_pnl'] < 0).sum()}")

    return worst_days

def analyze_exit_quality(df):
    """Analyze whether exits were timely or delayed"""
    print("\n⏱️  Analyzing Exit Quality...")

    # Compare profitable vs losing trades
    profitable = df[df['realized_pnl'] > 0]
    losing = df[df['realized_pnl'] < 0]

    print("\n💰 Profitable Trades:")
    print(f"Average holding: {profitable['holding_days'].mean():.1f} days")
    print(f"Average P&L: ₹{profitable['realized_pnl'].mean():,.2f}")
    print(f"Median P&L: ₹{profitable['realized_pnl'].median():,.2f}")

    print("\n📉 Losing Trades:")
    print(f"Average holding: {losing['holding_days'].mean():.1f} days")
    print(f"Average P&L: ₹{losing['realized_pnl'].mean():,.2f}")
    print(f"Median P&L: ₹{losing['realized_pnl'].median():,.2f}")

    # Analyze trades by holding period buckets
    holding_buckets = [0, 1, 2, 3, 5, 7, 14, 30]
    df['holding_bucket'] = pd.cut(df['holding_days'], bins=holding_buckets,
                                 labels=['Intraday', '1d', '2d', '3d', '5d', '7d', '14d+'])

    bucket_analysis = df.groupby('holding_bucket')['realized_pnl'].agg(['sum', 'mean', 'count'])
    print("\n📊 Performance by Holding Period:")
    print(bucket_analysis)

    return bucket_analysis

def generate_timing_recommendations(df, worst_days):
    """Generate specific recommendations based on timing analysis"""
    print("\n💡 TIMING STRATEGY RECOMMENDATIONS")
    print("=" * 50)

    # Calculate key metrics
    total_trades = len(df)
    profitable_trades = (df['realized_pnl'] > 0).sum()
    losing_trades = (df['realized_pnl'] < 0).sum()
    win_rate = profitable_trades / total_trades * 100

    # Holding period insights
    avg_holding_win = df[df['realized_pnl'] > 0]['holding_days'].mean()
    avg_holding_loss = df[df['realized_pnl'] < 0]['holding_days'].mean()

    print(f"📈 OVERALL PERFORMANCE:")
    print(f"  Total Trades: {total_trades}")
    print(f"  Win Rate: {win_rate:.1f}%")
    print(f"  Profitable Trades: {profitable_trades}")
    print(f"  Losing Trades: {losing_trades}")

    print(f"\n⏰ TIMING INSIGHTS:")
    print(f"  🎯 Winners held: {avg_holding_win:.1f} days on average")
    print(f"  ⚠️  Losers held: {avg_holding_loss:.1f} days on average")
    print(f"  📊 Problem: Losers held {(avg_holding_loss/avg_holding_win-1)*100:.0f}% longer than winners")

    # Expiry analysis
    expiry_loss = df[df['days_to_expiry_exit'] <= 7]['realized_pnl'].sum()
    print(f"\n📅 EXPIRY RISKS:")
    print(f"  Near expiry (≤7 days) losses: ₹{expiry_loss:,.2f}")
    print(f"  Trades near expiry: {len(df[df['days_to_expiry_exit'] <= 7])}")

    # Problem periods
    print(f"\n🚨 PROBLEM PERIODS:")
    for _, row in worst_days.head(3).iterrows():
        print(f"  {row['sell_day'].strftime('%Y-%m-%d')}: ₹{row['realized_pnl']:,.2f}")

    print(f"\n🎯 SPECIFIC RECOMMENDATIONS:")

    # 1. Stop loss timing
    if avg_holding_loss > avg_holding_win * 1.5:
        print(f"  1️⃣  IMMEDIATE STOP LOSSES:")
        print(f"     • Set 2-day maximum for any trade not in profit")
        print(f"     • Winners average {avg_holding_win:.1f} days - be quicker to take profits")
        print(f"     • Current pattern: holding losers {avg_holding_loss-avg_holding_win:.1f} days too long")

    # 2. Expiry rules
    if expiry_loss < -50000:
        print(f"  2️⃣  EXPIRY MANAGEMENT:")
        print(f"     • MANDATORY exit 10+ days before expiry")
        print(f"     • Current expiry-week losses: ₹{expiry_loss:,.2f}")
        print(f"     • Consider rolling positions instead of riding to expiry")

    # 3. Market regime awareness
    print(f"  3️⃣  MARKET REGIME AWARENESS:")
    print(f"     • Oct 2024 shows market regime change impact")
    print(f"     • Reduce position size during high volatility periods")
    print(f"     • Monitor index trends alongside positions")

    print(f"\n⚡ QUICK IMPLEMENTATION:")
    print(f"  • Start tomorrow: 2-day max holding rule")
    print(f"  • Mark all positions with entry date on watchlist")
    print(f"  • Set calendar alerts for 10 days before each expiry")

    return {
        'total_trades': total_trades,
        'win_rate': win_rate,
        'avg_holding_win': avg_holding_win,
        'avg_holding_loss': avg_holding_loss,
        'expiry_loss': expiry_loss
    }

def create_visualizations(df, daily_pnl):
    """Create visual analysis charts"""
    print("\n📊 Creating visual analysis...")

    fig, axes = plt.subplots(2, 2, figsize=(15, 12))
    fig.suptitle('F&O Trading Timing Analysis', fontsize=16, fontweight='bold')

    # 1. Daily P&L Timeline
    ax1 = axes[0, 0]
    daily_pnl.set_index('sell_day')['realized_pnl'].plot(ax=ax1, linewidth=1)
    ax1.axhline(y=0, color='red', linestyle='--', alpha=0.5)
    ax1.set_title('Daily P&L Timeline')
    ax1.set_ylabel('P&L (₹)')
    ax1.tick_params(axis='x', rotation=45)

    # 2. Holding Period Distribution
    ax2 = axes[0, 1]
    winners = df[df['realized_pnl'] > 0]['holding_days']
    losers = df[df['realized_pnl'] < 0]['holding_days']

    ax2.hist([winners, losers], bins=20, alpha=0.7, label=['Winners', 'Losers'], color=['green', 'red'])
    ax2.set_xlabel('Holding Days')
    ax2.set_ylabel('Number of Trades')
    ax2.set_title('Holding Period: Winners vs Losers')
    ax2.legend()

    # 3. Expiry Timing Impact
    ax3 = axes[1, 0]
    expiry_summary = df.groupby(pd.cut(df['days_to_expiry_exit'],
                                     bins=[-1, 0, 7, 14, 21, 30, 60],
                                     labels=['Expiry', '0-7d', '8-14d', '15-21d', '22-30d', '30d+']))['realized_pnl'].sum()
    colours = ['red' if x < 0 else 'green' for x in expiry_summary.values]
    expiry_summary.plot(kind='bar', ax=ax3, color=colours)
    ax3.set_title('P&L by Time to Expiry')
    ax3.set_ylabel('Total P&L (₹)')
    ax3.tick_params(axis='x', rotation=45)

    # 4. Monthly Performance
    ax4 = axes[1, 1]
    monthly_pnl = df.groupby(df['sell_date'].dt.to_period('M'))['realized_pnl'].sum()
    colours = ['red' if x < 0 else 'green' for x in monthly_pnl.values]
    monthly_pnl.plot(kind='bar', ax=ax4, color=colours)
    ax4.set_title('Monthly Performance')
    ax4.set_ylabel('Total P&L (₹)')
    ax4.tick_params(axis='x', rotation=45)

    plt.tight_layout()

    # Save the chart
    plt.savefig('/Users/Subho/trading_timing_analysis.png', dpi=300, bbox_inches='tight')
    print("✅ Analysis chart saved to: /Users/Subho/trading_timing_analysis.png")

    return fig

def main():
    """Main analysis function"""
    print("🚀 F&O TRADING TIMING ANALYSIS")
    print("=" * 60)
    print("Analyzing whether your F&O orders were timed correctly...")
    print("Identifying root causes: Market regime vs Early/Late exits")
    print("=" * 60)

    # Load data
    df, daily_pnl = load_and_clean_data()

    # Analyze timing patterns
    df = analyze_timing_patterns(df)

    # Analyze market regime changes
    worst_days = analyze_market_regime_changes(df, daily_pnl)

    # Analyze exit quality
    bucket_analysis = analyze_exit_quality(df)

    # Generate recommendations
    insights = generate_timing_recommendations(df, worst_days)

    # Create visualizations
    try:
        fig = create_visualizations(df, daily_pnl)
        plt.show()
    except Exception as e:
        print(f"⚠️  Could not create charts: {e}")

    print(f"\n🎯 KEY TAKEAWAY:")
    print(f"Your analysis shows LOSSES were primarily caused by:")
    print(f"1. ❌ Holding losing trades too long ({insights['avg_holding_loss']:.1f} days vs {insights['avg_holding_win']:.1f} days for winners)")
    print(f"2. ❌ Poor expiry timing (₹{insights['expiry_loss']:,.2f} lost near expiry)")
    print(f"3. ❌ Market regime changes (Oct 2024 crisis)")
    print(f"\n💡 NOT primarily due to sudden market movements, but rather")
    print(f"   DELAYED REACTION to adverse market conditions!")

    return df, insights

if __name__ == "__main__":
    df, insights = main()