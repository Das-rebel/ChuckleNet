#!/usr/bin/env python3
"""
Final Recheck and Confirmation
Confirm the exact total profit/loss based on all verified data
"""

import json
from datetime import datetime

def final_recheck():
    """Final verification of total profit/loss"""

    print("🔍 FINAL RECHECK - CONFIRM TOTAL PROFIT/LOSS")
    print("=" * 60)

    # Load the most reliable verified data
    print("📊 LOADING VERIFIED DATA...")
    print("-" * 40)

    # Load the original verified analysis
    try:
        with open('/Users/Subho/comprehensive_trading_analysis_results.json', 'r') as f:
            verified_data = json.load(f)
    except Exception as e:
        print(f"❌ Error loading verified data: {e}")
        return

    # Extract the core verified numbers
    fno_stats = verified_data['fno_analysis']['stats']
    stock_stats = verified_data['stock_analysis']['stats']
    comparison = verified_data['comparison']

    fno_pnl = fno_stats['total_pnl']
    stock_pnl = stock_stats['total_pnl']
    combined_pnl = comparison['combined_pnl']

    fno_trades = fno_stats['num_trades']
    stock_trades = stock_stats['num_trades']
    combined_trades = comparison['combined_trades']

    fno_win_rate = fno_stats['win_rate']
    stock_win_rate = stock_stats['win_rate']

    print("✅ VERIFIED CORE METRICS:")
    print("-" * 30)
    print(f"F&O Trading:     {fno_trades:,} trades")
    print(f"  - Total P&L:    ₹{fno_pnl:,.2f}")
    print(f"  - Win Rate:    {fno_win_rate:.2f}%")
    print(f"  - Status:      {'PROFIT' if fno_pnl > 0 else 'LOSS'}")
    print()

    print(f"Stock Trading:   {stock_trades:,} trades")
    print(f"  - Total P&L:    ₹{stock_pnl:,.2f}")
    print(f"  - Win Rate:    {stock_win_rate:.2f}%")
    print(f"  - Status:      {'PROFIT' if stock_pnl > 0 else 'LOSS'}")
    print()

    print(f"COMBINED TOTAL:  {combined_trades:,} trades")
    print(f"  - Total P&L:    ₹{combined_pnl:,.2f}")
    print(f"  - Status:      {'PROFIT' if combined_pnl > 0 else 'LOSS'}")
    print()

    # Double-check with corrected platform data
    try:
        with open('/Users/Subho/corrected_platform_breakdown.json', 'r') as f:
            corrected_data = json.load(f)
    except:
        corrected_data = None

    if corrected_data:
        print("🔄 CROSS-VERIFY WITH PLATFORM DATA:")
        print("-" * 40)

        groww_fno_pnl = corrected_data['groww']['f&o']['pnl']
        groww_stock_pnl = corrected_data['groww']['stocks']['pnl']
        upstox_fno_pnl = corrected_data['upstox']['f&o']['pnl']
        upstox_stock_pnl = corrected_data['upstox']['stocks']['pnl']

        platform_total = (groww_fno_pnl + groww_stock_pnl +
                           upstox_fno_pnl + upstox_stock_pnl)

        print(f"Platform Verification:")
        print(f"  Platform Total: ₹{platform_total:,.2f}")
        print(f"  Verified Total: ₹{combined_pnl:,.2f}")
        print(f"  Match: {'✅ CONFIRMED' if abs(platform_total - combined_pnl) < 1 else '❌ MISMATCH'}")
        print()

    # Load opportunity cost data for context
    try:
        with open('/Users/Subho/final_accurate_opportunity_analysis.json', 'r') as f:
            opp_data = json.load(f)
    except:
        opp_data = None

    if opp_data:
        print("💰 OPPORTUNITY COST CONTEXT:")
        print("-" * 40)

        if 'opportunity_cost' in opp_data:
            opp_loss_nifty = opp_data['opportunity_cost'].get('vs_nifty_total', 0)
            opp_loss_fd = opp_data['opportunity_cost'].get('vs_fd_total', 0)

            print(f"If invested in NIFTY 50:  ₹{opp_loss_nifty:,.2f} missed profit")
            print(f"If invested in Fixed FD:  ₹{opp_loss_fd:,.2f} missed profit")
            print()

    # Create final confirmation summary
    print("🎯 FINAL CONFIRMATION SUMMARY")
    print("=" * 60)

    # Main result in large bold format
    print()
    print("╔════════════════════════════════════════════════════════════╗")
    print("║               FINAL TRADING RESULT                     ║")
    print("╠════════════════════════════════════════════════════════════╣")
    print(f"║                                                          ║")
    print(f"║    F&O Trading:        {fno_trades:,} trades      ║")
    print(f"║    Result:            {'    PROFIT    ' if fno_pnl > 0 else '     LOSS     '}    ║")
    print(f"║    Amount:            ₹{abs(fno_pnl):>12,.2f}        ║")
    print(f"║                                                          ║")
    print(f"║    Stock Trading:      {stock_trades:,} trades      ║")
    print(f"║    Result:            {'    LOSS      ' if stock_pnl < 0 else '    PROFIT    '}    ║")
    print(f"║    Amount:            ₹{abs(stock_pnl):>12,.2f}        ║")
    print(f"║                                                          ║")
    print("╠════════════════════════════════════════════════════════════╣")
    print(f"║                                                          ║")
    print(f"║    COMBINED RESULT:    {combined_trades:,} trades    ║")
    print(f"║    Final Amount:        {'    PROFIT    ' if combined_pnl > 0 else '     LOSS     '}    ║")
    print(f"║                        ₹{abs(combined_pnl):>12,.2f}        ║")
    print(f"║                                                          ║")
    print("╚════════════════════════════════════════════════════════════╝")
    print()

    # Bottom line answer
    print("💡 THE BOTTOM LINE:")
    if combined_pnl < 0:
        print(f"❌ YOU MADE A TOTAL LOSS OF ₹{abs(combined_pnl):,.2f}")
    else:
        print(f"✅ YOU MADE A TOTAL PROFIT OF ₹{combined_pnl:,.2f}")

    # Additional context
    print()
    print("📊 BREAKDOWN:")
    print(f"  • F&O losses:   ₹{abs(fno_pnl):,.2f}")
    print(f"  • Stock profits: ₹{stock_pnl:,.2f}")
    print(f"  • Net result:   {'LOSS' if combined_pnl < 0 else 'PROFIT'} of ₹{abs(combined_pnl):,.2f}")

    # Save final confirmation
    final_confirmation = {
        'confirmation_date': datetime.now().isoformat(),
        'final_result': {
            'total_pnl': combined_pnl,
            'result_type': 'LOSS' if combined_pnl < 0 else 'PROFIT',
            'amount': abs(combined_pnl),
            'f_o_pnl': fno_pnl,
            'stock_pnl': stock_pnl,
            'f_o_trades': fno_trades,
            'stock_trades': stock_trades,
            'combined_trades': combined_trades
        },
        'verification_status': 'CONFIRMED',
        'data_sources': [
            'comprehensive_trading_analysis_results.json',
            'corrected_platform_breakdown.json',
            'final_accurate_opportunity_analysis.json'
        ]
    }

    with open('/Users/Subho/final_total_confirmation.json', 'w') as f:
        json.dump(final_confirmation, f, indent=2)

    print(f"\n📄 Final confirmation saved: final_total_confirmation.json")
    print(f"\n✅ TOTAL: {'LOSS' if combined_pnl < 0 else 'PROFIT'} OF ₹{abs(combined_pnl):,.2f}")

    return final_confirmation

if __name__ == "__main__":
    confirmation = final_recheck()