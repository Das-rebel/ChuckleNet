#!/usr/bin/env python3
"""
Platform Loss Summary
Calculate exact loss/profit by platform
"""

import json

def calculate_platform_losses():
    """Calculate and display platform-wise losses"""

    # Load corrected platform data
    with open('/Users/Subho/corrected_platform_breakdown.json', 'r') as f:
        platform_data = json.load(f)

    print("📊 PLATFORM-WISE LOSS BREAKDOWN")
    print("=" * 60)

    # Calculate Upstox totals
    upstox_fno_pnl = platform_data['upstox']['f&o']['pnl']
    upstox_stock_pnl = platform_data['upstox']['stocks']['pnl']
    upstox_fno_trades = platform_data['upstox']['f&o']['trades']
    upstox_stock_trades = platform_data['upstox']['stocks']['trades']
    upstox_total = upstox_fno_pnl + upstox_stock_pnl
    upstox_total_trades = upstox_fno_trades + upstox_stock_trades

    # Calculate Groww totals
    groww_fno_pnl = platform_data['groww']['f&o']['pnl']
    groww_stock_pnl = platform_data['groww']['stocks']['pnl']
    groww_fno_trades = platform_data['groww']['f&o']['trades']
    groww_stock_trades = platform_data['groww']['stocks']['trades']
    groww_total = groww_fno_pnl + groww_stock_pnl
    groww_total_trades = groww_fno_trades + groww_stock_trades

    # Display results
    print("🔴 UPSTOX PLATFORM")
    print("-" * 30)
    print(f"F&O Trading:   {upstox_fno_trades:,.0f} trades")
    print(f"  P&L:         ₹{abs(upstox_fno_pnl):,.2f} {'PROFIT' if upstox_fno_pnl > 0 else 'LOSS'}")
    print()
    print(f"Stock Trading: {upstox_stock_trades:,.0f} trades")
    print(f"  P&L:         ₹{upstox_stock_pnl:,.2f} {'PROFIT' if upstox_stock_pnl > 0 else 'LOSS'}")
    print()
    print(f"📈 UPSTOX TOTAL: {upstox_total_trades:,.0f} trades")
    print(f"   Net P&L:     ₹{abs(upstox_total):,.2f} {'PROFIT' if upstox_total > 0 else 'LOSS'}")
    print()

    print("🟢 GROWW PLATFORM")
    print("-" * 30)
    print(f"F&O Trading:   {groww_fno_trades:,.0f} trades")
    print(f"  P&L:         ₹{abs(groww_fno_pnl):,.2f} {'PROFIT' if groww_fno_pnl > 0 else 'LOSS'}")
    print()
    print(f"Stock Trading: {groww_stock_trades:,.0f} trades")
    print(f"  P&L:         ₹{groww_stock_pnl:,.2f} {'PROFIT' if groww_stock_pnl > 0 else 'LOSS'}")
    print()
    print(f"📈 GROWW TOTAL: {groww_total_trades:,.0f} trades")
    print(f"   Net P&L:     ₹{groww_total:,.2f} {'PROFIT' if groww_total > 0 else 'LOSS'}")
    print()

    # Summary table
    print("📋 PLATFORM COMPARISON TABLE")
    print("=" * 80)
    print("PLATFORM   │   F&O P&L    │  STOCK P&L   │   TOTAL P&L   │  RESULT")
    print("───────────┼─────────────┼─────────────┼──────────────┼─────────")
    print(f"UPSTOX     │  ₹{abs(upstox_fno_pnl):>9,.2f}  │  ₹{upstox_stock_pnl:>9,.2f}  │  ₹{abs(upstox_total):>10,.2f}  │  {'PROFIT' if upstox_total > 0 else 'LOSS'}")
    print(f"GROWW      │  ₹{abs(groww_fno_pnl):>9,.2f}  │  ₹{groww_stock_pnl:>9,.2f}  │  ₹{abs(groww_total):>10,.2f}  │  {'PROFIT' if groww_total > 0 else 'LOSS'}")
    print()

    # Bottom line
    combined_total = upstox_total + groww_total

    print("💡 BOTTOM LINE ANSWER:")
    print("=" * 40)
    if upstox_total < 0:
        print(f"🔴 UPSTOX LOSS: ₹{abs(upstox_total):,.2f}")
    else:
        print(f"🟢 UPSTOX PROFIT: ₹{upstox_total:,.2f}")

    if groww_total < 0:
        print(f"🔴 GROWW LOSS: ₹{abs(groww_total):,.2f}")
    else:
        print(f"🟢 GROWW PROFIT: ₹{groww_total:,.2f}")

    print(f"📊 COMBINED: {'LOSS' if combined_total < 0 else 'PROFIT'} of ₹{abs(combined_total):,.2f}")

    return {
        'upstox': {
            'fno_pnl': upstox_fno_pnl,
            'stock_pnl': upstox_stock_pnl,
            'total_pnl': upstox_total,
            'result': 'LOSS' if upstox_total < 0 else 'PROFIT'
        },
        'groww': {
            'fno_pnl': groww_fno_pnl,
            'stock_pnl': groww_stock_pnl,
            'total_pnl': groww_total,
            'result': 'LOSS' if groww_total < 0 else 'PROFIT'
        },
        'combined_total': combined_total
    }

if __name__ == "__main__":
    platform_summary = calculate_platform_losses()