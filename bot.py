import telebot
from telebot import types
import yfinance as yf
import os
from flask import Flask
from threading import Thread

# Render Port Fix (ለ 24 ሰዓት ስራ)
app = Flask('')
@app.route('/')
def home(): return "ICT AI Analyzer is Live!"

def run_flask():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

# ቦት Token
TOKEN = '7311692566:AAGFv2P5ioA_s_45talCetYbJQynbTAlrvc'
bot = telebot.TeleBot(TOKEN)

def get_combined_analysis(symbol):
    try:
        symbol_map = {
            '🇪🇺 EUR/USD': 'EURUSD=X', '🇬🇧 GBP/USD': 'GBPUSD=X',
            '🇯🇵 USD/JPY': 'USDJPY=X', '🟡 GOLD (XAU/USD)': 'GC=F',
            '₿ Bitcoin (BTC)': 'BTC-USD'
        }
        search_symbol = symbol_map.get(symbol, symbol)
        
        # ላለፉት 5 ቀናት የ 1 ሰዓት መረጃ (ለ ICT መረጃ አስፈላጊ ነው)
        data = yf.download(search_symbol, period="5d", interval="1h", progress=False)
        
        if data.empty: return "❌ መረጃ ማግኘት አልተቻለም።"

        # ስህተት እንዳይፈጠር ዳታውን ወደ List መቀየር
        prices = data['Close'].values.flatten().tolist()
        highs = data['High'].values.flatten().tolist()
        lows = data['Low'].values.flatten().tolist()
        
        last_price = prices[-1]
        
        # 1. ICT Liquidity Levels (የ 24 ሰዓት High/Low)
        bsl = max(highs[-24:]) # Buy Side Liquidity
        ssl = min(lows[-24:])  # Sell Side Liquidity
        
        # 2. Market Structure Shift (MSS/CHOCh)
        prev_high = highs[-2]
        prev_low = lows[-2]
        
        structure = "🔄 Ranging (Sideways)"
        if last_price > prev_high: 
            structure = "🚀 CHOCh/MSS (Bullish Shift)"
            signal = "🟢 **BUY SETUP**"
            sl, tp = ssl, bsl
        elif last_price < prev_low: 
            structure = "📉 CHOCh/MSS (Bearish Shift)"
            signal = "🔴 **SELL SETUP**"
            sl, tp = bsl, ssl
        else:
            signal = "🟡 **NEUTRAL (Wait for break)**"
            sl, tp = ssl, bsl

        # 3. RSI Calculation (Manual)
        gains = [max(prices[i] - prices[i-1], 0) for i in range(-14, 0)]
        losses = [max(prices[i-1] - prices[i], 0) for i in range(-14, 0)]
        avg_gain = sum(gains) / 14
        avg_loss = sum(losses) / 14 if sum(losses) != 0 else 0.001
        rsi = 100 - (100 / (1 + (avg_gain / avg_loss)))

        # መልእክቱን ማዘጋጀት
        msg = f"🎯 **የ {symbol} ICT AI ትንታኔ**\n"
        msg += "----------------------------------\n"
        msg += f"💰 **ዋጋ:** `{last_price:.5f}`\n"
        msg += f"🏗 **Structure:** `{structure}`\n"
        msg += f"📈 **RSI:** `{rsi:.2f}`\n\n"
        
        msg += f"🔝 **BSL (Target):** `{bsl:.5f}`\n"
        msg += f"⬇️ **SSL (Target):** `{ssl:.5f}`\n\n"
        
        msg += f"💡 **AI Signal:** {signal}\n"
        msg += f"🛑 **Stop Loss (SL):** `{sl:.5f}`\n"
        msg += f"🎯 **Take Profit (TP):** `{tp:.5f}`"
        
        return msg
    except Exception as e:
        return f"⚠️ ስህተት: {str(e)}"

@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add('🇪🇺 EUR/USD', '🇬🇧 GBP/USD', '🟡 GOLD (XAU/USD)', '₿ Bitcoin (BTC)', '🔄 ሌላ')
    bot.send_message(message.chat.id, "እንኳን ወደ ICT AI Analyzer በሰላም መጡ! 👋\nየገበያ ትንታኔ ለመጀመር ጥንድ ይምረጡ፡", reply_markup=markup)

@bot.message_handler(func=lambda m: True)
def handle_msg(message):
    bot.send_message(message.chat.id, f"🔍 የ {message.text} ICT መረጃዎችን በመተንተን ላይ ነኝ...")
    result = get_combined_analysis(message.text)
    bot.send_message(message.chat.id, result, parse_mode='Markdown')

if __name__ == "__main__":
    # Flask እና Bot በአንድ ላይ ማስነሳት
    Thread(target=run_flask).start()
    bot.infinity_polling(non_stop=True)
