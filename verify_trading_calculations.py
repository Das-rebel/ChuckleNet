#!/usr/bin/env python3
"""
Verify Trading Calculations with Precision
Double-check all numbers and decimal accuracy
"""

import json

def load_and_verify_data():
    """Load and verify trading data calculations"""
    print("🔍 VERIFICATION OF TRADING CALCULATIONS")
    print("=" * 50)

    # Load the analysis results
    try:
        with open('/Users/Subho/comprehensive_trading_analysis_results.json', 'r') as f:
            results = json.load(f)
    except Exception as e:
        print(f"Error loading results: {e}")
        return

    # Extract F&O data
    fno_stats = results['fno_analysis']['stats']
    stock_stats = results['stock_analysis']['stats']

    # Convert to proper numbers
    fno_pnl = float(fno_stats['total_pnl'])
    stock_pnl = float(stock_stats['total_pnl'])
    fno_trades = int(fno_stats['num_trades'])
    stock_trades = int(stock_stats['num_trades'])

    print(f"📊 RAW DATA FROM EXCEL FILES:")
    print(f"\nF&O Trading:")
    print(f"  Total P&L: ₹{fno_pnl:,.2f}")
    print(f"  Number of Trades: {fno_trades:,}")
    print(f"  Winning Trades: {int(fno_stats['win_trades']):,}")
    print(f"  Losing Trades: {int(fno_stats['loss_trades']):,}")
    print(f"  Win Rate: {float(fno_stats['win_rate']):.2f}%")
    print(f"  Average Win: ₹{float(fno_stats['avg_win']):,.2f}")
    print(f"  Average Loss: ₹{float(fno_stats['avg_loss']):,.2f}")
    print(f"  Maximum Win: ₹{float(fno_stats['max_win']):,.2f}")
    print(f"  Maximum Loss: ₹{float(fno_stats['max_loss']):,.2f}")

    print(f"\nStock Trading:")
    print(f"  Total P&L: ₹{stock_pnl:,.2f}")
    print(f"  Number of Trades: {stock_trades:,}")
    print(f"  Winning Trades: {int(stock_stats['win_trades']):,}")
    print(f"  Losing Trades: {int(stock_stats['loss_trades']):,}")
    print(f"  Win Rate: {float(stock_stats['win_rate']):.2f}%")
    print(f"  Average Win: ₹{float(stock_stats['avg_win']):,.2f}")
    print(f"  Average Loss: ₹{float(stock_stats['avg_loss']):,.2f}")
    print(f"  Maximum Win: ₹{float(stock_stats['max_win']):,.2f}")
    print(f"  Maximum Loss: ₹{float(stock_stats['max_loss']):,.2f}")

    # Verify calculations
    print(f"\n✅ CALCULATION VERIFICATION:")

    # Verify combined P&L
    combined_pnl = fno_pnl + stock_pnl
    print(f"  Combined P&L: {fno_pnl:,.2f} + {stock_pnl:,.2f} = {combined_pnl:,.2f}")

    # Verify win rates
    fno_win_rate_calc = (int(fno_stats['win_trades']) / fno_trades) * 100
    stock_win_rate_calc = (int(stock_stats['win_trades']) / stock_trades) * 100

    print(f"\n  F&O Win Rate Verification:")
    print(f"    {int(fno_stats['win_trades']):,} / {fno_trades:,} * 100 = {fno_win_rate_calc:.2f}%")
    print(f"    Recorded: {float(fno_stats['win_rate']):.2f}%")
    print(f"    Match: {abs(fno_win_rate_calc - float(fno_stats['win_rate'])) < 0.01}")

    print(f"\n  Stock Win Rate Verification:")
    print(f"    {int(stock_stats['win_trades']):,} / {stock_trades:,} * 100 = {stock_win_rate_calc:.2f}%")
    print(f"    Recorded: {float(stock_stats['win_rate']):.2f}%")
    print(f"    Match: {abs(stock_win_rate_calc - float(stock_stats['win_rate'])) < 0.01}")

    # Verify trade counts
    fno_trades_verify = int(fno_stats['win_trades']) + int(fno_stats['loss_trades'])
    stock_trades_verify = int(stock_stats['win_trades']) + int(stock_stats['loss_trades'])

    print(f"\n  Trade Count Verification:")
    print(f"    F&O: {int(fno_stats['win_trades']):,} + {int(fno_stats['loss_trades']):,} = {fno_trades_verify:,} (Expected: {fno_trades:,})")
    print(f"    Stock: {int(stock_stats['win_trades']):,} + {int(stock_stats['loss_trades']):,} = {stock_trades_verify:,} (Expected: {stock_trades:,})")

    # Lakhs conversion (1 lakh = 100,000)
    fno_pnl_lakhs = fno_pnl / 100000
    stock_pnl_lakhs = stock_pnl / 100000
    combined_pnl_lakhs = combined_pnl / 100000

    print(f"\n💰 CONVERSION TO LAKHS:")
    print(f"  F&O P&L: ₹{fno_pnl:,.2f} = {fno_pnl_lakhs:,.2f} lakh")
    print(f"  Stock P&L: ₹{stock_pnl:,.2f} = {stock_pnl_lakhs:,.2f} lakh")
    print(f"  Combined: ₹{combined_pnl:,.2f} = {combined_pnl_lakhs:,.2f} lakh")

    # Create corrected summary
    print(f"\n🎯 CORRECTED SUMMARY:")
    print(f"=" * 40)
    print(f"F&O Trading:")
    print(f"  P&L: {fno_pnl_lakhs:,.2f} lakh ({'LOSS' if fno_pnl < 0 else 'PROFIT'})")
    print(f"  Trades: {fno_trades:,}")
    print(f"  Win Rate: {fno_win_rate_calc:.1f}%")
    print(f"")
    print(f"Stock Trading:")
    print(f"  P&L: {stock_pnl_lakhs:,.2f} lakh ({'PROFIT' if stock_pnl > 0 else 'LOSS'})")
    print(f"  Trades: {stock_trades:,}")
    print(f"  Win Rate: {stock_win_rate_calc:.1f}%")
    print(f"")
    print(f"Combined:")
    print(f"  Total P&L: {combined_pnl_lakhs:,.2f} lakh ({'LOSS' if combined_pnl < 0 else 'PROFIT'})")
    print(f"  Total Trades: {fno_trades + stock_trades:,}")

    # Professional improvement calculations
    print(f"\n💼 PROFESSIONAL IMPROVEMENT CALCULATION:")
    print(f"=" * 50)

    # Based on our earlier analysis - 75% improvement for F&O
    fno_improvement_pct = 0.75
    fno_current_loss = abs(fno_pnl)
    fno_improvement = fno_current_loss * fno_improvement_pct
    fno_professional_pnl = fno_pnl + fno_improvement

    print(f"F&O Improvement (75%):")
    print(f"  Current Loss: ₹{fno_current_loss:,.2f}")
    print(f"  Improvement: ₹{fno_improvement:,.2f}")
    print(f"  Professional Result: ₹{fno_professional_pnl:,.2f} ({fno_professional_pnl/100000:,.2f} lakh)")

    # Stock trading - already efficient
    stock_professional_pnl = stock_pnl  # No change needed

    # Combined professional results
    combined_professional = fno_professional_pnl + stock_professional_pnl
    combined_current = fno_pnl + stock_pnl
    total_improvement = combined_professional - combined_current

    print(f"\nCombined Professional Results:")
    print(f"  Current: {combined_current/100000:,.2f} lakh")
    print(f"  Professional: {combined_professional/100000:,.2f} lakh")
    print(f"  Total Improvement: {total_improvement/100000:,.2f} lakh")

    if combined_current != 0:
        improvement_pct = (total_improvement / abs(combined_current)) * 100
        print(f"  Improvement Percentage: {improvement_pct:.1f}%")

    # Monthly projections
    fno_months = 32  # Based on date range in file
    stock_months = 58  # Based on date range in file

    fno_monthly_current = fno_pnl / fno_months
    fno_monthly_professional = fno_professional_pnl / fno_months
    stock_monthly_current = stock_pnl / stock_months

    print(f"\n📅 MONTHLY PROJECTIONS:")
    print(f"=" * 30)
    print(f"F&O Monthly:")
    print(f"  Current: ₹{fno_monthly_current:,.2f} ({fno_monthly_current/100000:,.2f} lakh)")
    print(f"  Professional: ₹{fno_monthly_professional:,.2f} ({fno_monthly_professional/100000:,.2f} lakh)")
    print(f"  Monthly Improvement: ₹{(fno_monthly_professional - fno_monthly_current):,.2f}")

    print(f"\nStock Monthly:")
    print(f"  Current: ₹{stock_monthly_current:,.2f} ({stock_monthly_current/100000:,.2f} lakh)")
    print(f"  Professional: ₹{stock_monthly_current:,.2f} ({stock_monthly_current/100000:,.2f} lakh) (No change)")

    # Annual projections
    combined_monthly_professional = combined_professional / 12

    print(f"\n📈 ANNUAL PROJECTION:")
    print(f"  Professional Annual Result: ₹{combined_professional:,.2f} ({combined_professional/100000:,.1f} lakh)")
    print(f"  Monthly Average: ₹{combined_monthly_professional:,.2f} ({combined_monthly_professional/100000:,.1f} lakh)")

if __name__ == "__main__":
    load_and_verify_data()