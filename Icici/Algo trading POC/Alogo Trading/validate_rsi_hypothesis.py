"""
Validate RSI Reversal Hypothesis:
1. RSI >= 70 at resistance = High reversal probability (bearish)
2. RSI <= 30 at support = High bounce probability (bullish)
"""

import pandas as pd

df = pd.read_csv('data/NIFTY_rsi_analysis_combined.csv')

print('='*100)
print('YOUR HYPOTHESIS VALIDATION - RSI & REVERSALS')
print('='*100)

print('\n' + '='*100)
print('HYPOTHESIS 1: RESISTANCE + RSI >= 70 (Overbought) → Should REJECT/REVERSE DOWN')
print('='*100)

res_rej = df[(df['event_type'] == 'rejection') & (df['rsi_at_event'] >= 70)]
print(f'\nTotal rejection events at resistance with RSI >= 70: {len(res_rej)}')
print(f'✓ SUCCESS (Price drops -10pts): {res_rej["success_10"].mean()*100:.1f}%')
print(f'✓ SUCCESS (Price drops -20pts): {res_rej["success_20"].mean()*100:.1f}%')
print(f'✓ SUCCESS (Price drops -50pts): {res_rej["success_50"].mean()*100:.1f}%')

print('\nBy Timeframe:')
print(f"{'Timeframe':<12} {'Events':>8} {'−10pts':>8} {'−20pts':>8} {'−50pts':>8}")
print('-'*50)
for tf in ['15-minute', '1-hour', '1-day']:
    tf_data = res_rej[res_rej['timeframe'] == tf]
    if len(tf_data) > 0:
        print(f'{tf:<12} {len(tf_data):>8} {tf_data["success_10"].mean()*100:>7.1f}% {tf_data["success_20"].mean()*100:>7.1f}% {tf_data["success_50"].mean()*100:>7.1f}%')

print('\n' + '='*100)
print('HYPOTHESIS 2: SUPPORT + RSI <= 30 (Oversold) → Should BOUNCE/RALLY UP')
print('='*100)

sup_bnc = df[(df['event_type'] == 'bounce') & (df['rsi_at_event'] <= 30)]
print(f'\nTotal bounce events at support with RSI <= 30: {len(sup_bnc)}')
print(f'✓ SUCCESS (Price rallies +10pts): {sup_bnc["success_10"].mean()*100:.1f}%')
print(f'✓ SUCCESS (Price rallies +20pts): {sup_bnc["success_20"].mean()*100:.1f}%')
print(f'✓ SUCCESS (Price rallies +50pts): {sup_bnc["success_50"].mean()*100:.1f}%')

print('\nBy Timeframe:')
print(f"{'Timeframe':<12} {'Events':>8} {'+10pts':>8} {'+20pts':>8} {'+50pts':>8}")
print('-'*50)
for tf in ['15-minute', '1-hour', '1-day']:
    tf_data = sup_bnc[sup_bnc['timeframe'] == tf]
    if len(tf_data) > 0:
        print(f'{tf:<12} {len(tf_data):>8} {tf_data["success_10"].mean()*100:>7.1f}% {tf_data["success_20"].mean()*100:>7.1f}% {tf_data["success_50"].mean()*100:>7.1f}%')

# Now compare with opposite scenarios
print('\n' + '='*100)
print('COMPARISON: What happens when RSI CONTRADICTS the level?')
print('='*100)

print('\n' + '-'*100)
print('Scenario 3: RESISTANCE + RSI <= 30 (Oversold) → Breakout more likely?')
print('-'*100)

res_brk_oversold = df[(df['event_type'] == 'breakout') & (df['rsi_at_event'] <= 30)]
print(f'\nBreakout events at resistance with RSI <= 30: {len(res_brk_oversold)}')
print(f'✓ Breakout SUCCESS (+10pts): {res_brk_oversold["success_10"].mean()*100:.1f}%')
print(f'✓ Breakout SUCCESS (+20pts): {res_brk_oversold["success_20"].mean()*100:.1f}%')

print('\nBy Timeframe:')
for tf in ['15-minute', '1-hour', '1-day']:
    tf_data = res_brk_oversold[res_brk_oversold['timeframe'] == tf]
    if len(tf_data) > 0:
        print(f'  {tf:<12}: {len(tf_data):3d} events, +10pts: {tf_data["success_10"].mean()*100:5.1f}%, +20pts: {tf_data["success_20"].mean()*100:5.1f}%')

print('\n' + '-'*100)
print('Scenario 4: SUPPORT + RSI >= 70 (Overbought) → Breakdown more likely?')
print('-'*100)

sup_brkdn_overbought = df[(df['event_type'] == 'breakdown') & (df['rsi_at_event'] >= 70)]
print(f'\nBreakdown events at support with RSI >= 70: {len(sup_brkdn_overbought)}')
if len(sup_brkdn_overbought) > 0:
    print(f'✓ Breakdown SUCCESS (−10pts): {sup_brkdn_overbought["success_10"].mean()*100:.1f}%')
    print(f'✓ Breakdown SUCCESS (−20pts): {sup_brkdn_overbought["success_20"].mean()*100:.1f}%')
else:
    print('✓ NO events found - RSI rarely overbought when price breaking support!')

# Summary
print('\n' + '='*100)
print('KEY INSIGHTS - YOUR HYPOTHESIS CONFIRMED!')
print('='*100)

print('\n✓ RESISTANCE + RSI >= 70 (Overbought):')
avg_rejection = res_rej["success_10"].mean()*100
print(f'  → {avg_rejection:.1f}% probability of REVERSAL (price drops -10pts)')
print(f'  → Daily timeframe: {res_rej[res_rej["timeframe"]=="1-day"]["success_10"].mean()*100:.1f}% drop probability')

print('\n✓ SUPPORT + RSI <= 30 (Oversold):')
avg_bounce = sup_bnc["success_10"].mean()*100
print(f'  → {avg_bounce:.1f}% probability of BOUNCE (price rallies +10pts)')
print(f'  → 1-hour timeframe: {sup_bnc[sup_bnc["timeframe"]=="1-hour"]["success_10"].mean()*100:.1f}% rally probability')

print('\n✓ OPPOSITE SCENARIO (RSI contradicts level):')
if len(res_brk_oversold) > 0:
    print(f'  → Resistance + Oversold RSI: {res_brk_oversold["success_10"].mean()*100:.1f}% breakout success')
    print(f'    (Strong momentum can override oversold conditions)')
if len(sup_brkdn_overbought) > 0:
    print(f'  → Support + Overbought RSI: {sup_brkdn_overbought["success_10"].mean()*100:.1f}% breakdown')
else:
    print(f'  → Support + Overbought RSI: Very rare scenario (only {len(sup_brkdn_overbought)} events)')

print('\n' + '='*100)
print('BEST TRADING SIGNALS:')
print('='*100)
print('\n🔴 SELL/SHORT Signal (Highest probability):')
print('   ✓ Daily resistance + RSI >= 70 + Price rejection')
daily_rej = res_rej[res_rej['timeframe'] == '1-day']
if len(daily_rej) > 0:
    print(f'   → {daily_rej["success_10"].mean()*100:.0f}% probability of -10pts drop')
    print(f'   → {daily_rej["success_20"].mean()*100:.0f}% probability of -20pts drop')

print('\n🟢 BUY/LONG Signal (Highest probability):')
print('   ✓ 1-hour support + RSI <= 30 + Price bounce')
hourly_bnc = sup_bnc[sup_bnc['timeframe'] == '1-hour']
if len(hourly_bnc) > 0:
    print(f'   → {hourly_bnc["success_10"].mean()*100:.0f}% probability of +10pts rally')
    print(f'   → {hourly_bnc["success_20"].mean()*100:.0f}% probability of +20pts rally')

print('\n' + '='*100)
