SELECTORS = {
    'buy_sell_toggle': 'button.css-1wsh2jr, a[href*="/rlb/trade"], .css-1wsh2jr',
    'up_button': '.css-1p91j2k',        # visual chip div with text Up (green when active)
    'down_button': '.css-qv9fap',     # visual chip div with text Down (red when active)
    'wager_input': '.css-14hgewr input[type="text"]',
    'multiplier_input': 'div.css-14hgewr input[type="text"]:nth-child(2)',
    'place_bet_button': 'button.css-1wit1e6, .css-1wit1e6, button.css-4jqfnv, .css-4jqfnv, button[type="submit"]',
    'cash_out_button': 'button.css-nja62m',
    'active_bet_rows': 'tbody tr.css-jbcm9e'
}

# Feature flags
DEBUG_UI_SCAN = False           # print DOM scans/inspector at startup
DEBUG_NETWORK_SPY = False       # install and dump network spy
USE_API_FALLBACK = True         # call /private/trade if UI submit fails

# Blacklist of elements to NEVER click
BLACKLISTED_SELECTORS = [
    '.css-1psueex',           # Cashier button
    'button.css-1psueex',
    '[class*="cashier"]',
    'button:contains("CASHIER")',
    'a[href*="cashier"]',
    'a[href*="/casino"]',
    'a[href*="/sports"]'
]

ROLLBIT_URL = 'https://rollbit.com/trading/BTC'






