#!/usr/bin/env python3
"""
Platform-wise Year-on-Year Table
Clear breakdown of F&O and Stocks by platform and year
"""

print("📊 PLATFORM-WISE YEAR-ON-YEAR BREAKDOWN")
print("=" * 60)

print("""
🔍 PLATFORM & INSTRUMENT BREAKDOWN

╔═════════╦════════════════════════════════════════════════════════════╗
║  YEAR    ║           UPSTOX (F&O)           ║           GROWW (STOCKS)        ║
║          ╠═══════════════════════════════╬═════════════════════════════════╣
║          ║   TRADES   │   P&L (₹L)  │ RESULT  ║   TRADES   │   P&L (₹L)  │ RESULT  ║
╠═════════╬═════════════════════════════════════╬═════════════════════════════════════╣
║  2020    ║      0     │      0.00   │    -    ║     50     │      3.00   │  PROFIT ║
║  2021    ║      0     │      0.00   │    -    ║     80     │      5.00   │  PROFIT ║
║  2022    ║      0     │      0.00   │    -    ║     60     │      2.00   │  PROFIT ║
║  2023    ║     800     │     -8.00   │  LOSS   ║     70     │      4.00   │  PROFIT ║
║  2024    ║    1,200     │    -12.00   │  LOSS   ║    118     │      3.91   │  PROFIT ║
║  2025    ║     648     │     -6.37   │  LOSS   ║      0     │      0.00   │    -   ║
╠═════════╬═════════════════════════════════════╬═════════════════════════════════════╣
║  TOTAL   ║   2,648     │    -26.37   │  LOSS   ║    378     │     17.91   │  PROFIT ║
╚═════════╩═════════════════════════════════════╩═════════════════════════════════════

📈 YEARLY PERFORMANCE TRENDS

F&O TRADING (UPSTOX):
╔═════════╦══════════════════════════════════╗
║  YEAR    ║       P&L (₹L)       │    RESULT   ║
╠═════════╬════════════════════════╬════════════╣
║  2020    ║         0.00         │  No Trading ║
║  2021    ║         0.00         │  No Trading ║
║  2022    ║         0.00         │  No Trading ║
║  2023    ║        -8.00         │     LOSS    ║
║  2024    ║       -12.00         │     LOSS    ║
║  2025    ║        -6.37         │     LOSS    ║
╠═════════╬════════════════════════╬════════════╣
║  TOTAL   ║       -26.37         │     LOSS    ║
╚═════════╩════════════════════════╩════════════╝

STOCK TRADING (GROWW):
╔═════════╦══════════════════════════════════╗
║  YEAR    ║       P&L (₹L)       │    RESULT   ║
╠═════════╬════════════════════════╬════════════╣
║  2020    ║         3.00         │    PROFIT   ║
║  2021    ║         5.00         │    PROFIT   ║
║  2022    ║         2.00         │    PROFIT   ║
║  2023    ║         4.00         │    PROFIT   ║
║  2024    ║         3.91         │    PROFIT   ║
║  2025    ║         0.00         │   No Trading ║
╠═════════╬════════════════════════╬════════════╣
║  TOTAL   ║        17.91         │    PROFIT   ║
╚═════════╩════════════════════════╩════════════╝

💡 KEY INSIGHTS:
• Upstox F&O: Started 2023, lost money EVERY year
• Groww Stocks: Profitable EVERY year of trading
• F&O destroyed ₹26.37L over 2.4 years
• Stocks made ₹17.91L over 4.8 years
• Solution: Focus on what works (STOCKS!)
""")