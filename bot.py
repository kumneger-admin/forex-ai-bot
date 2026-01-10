import telebot
from telebot import types
import yfinance as yf
import os
from flask import Flask
from threading import Thread

# Render Port Fix
app = Flask('')
@app.route('/')
def home(): return "Forex ICT AI Bot is Live!"

def run_flask():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

TOKEN = '7311692566:AAGFv2P5ioA_s_45talCetYbJQynbTAlrvc'
bot = telebot.TeleBot(TOKEN)

def get_ict_analysis(symbol):
    try:
        symbol_map = {
            '🇪🇺 EUR/USD': 'EURUSD=X', '🇬🇧 GBP/USD': 'GBPUSD=X',
            '🇯🇵 USD/JPY': 'USDJPY=X', '🟡 GOLD (XAU/USD)': 'GC=F',
            '₿ Bitcoin (BTC)': 'BTC-USD'
        }
        search_symbol = symbol_map.get(symbol, symbol)
        
        # ላለፉት 5 ቀናት የ 1 ሰዓት መረጃ ማምጣት
        df = yf.download(search_symbol, period="5d", interval="1h", progress=False)
        if df.empty or len(df) < 24: return "❌ መረጃ ማግኘት አልተቻለም።"

        prices = df['Close'].tolist()
        highs = df['High'].tolist()
        lows = df['Low'].tolist()
        
        last_price = prices[-1]
        
        # 1. Liquidity Levels (የ 24 ሰዓት ከፍተኛ እና ዝቅተኛ)
        bsl = max(highs[-24:]) # Buy Side Liquidity
        ssl = min(lows[-24:])  # Sell Side Liquidity
        
        # 2. MSS / CHOCh Logic (ቀለል ያለ)
        # ዋጋው ካለፈው ከፍተኛ ከበለጠ CHOCh (Bullish)
        # ዋጋው ካለፈው ዝቅተኛ ካለፈ CHOCh (Bearish)
        prev_high = highs[-2]
        prev_low = lows[-2]
        
        structure = "🔄 Ranging"
        if last_price > prev_high: structure = "🚀 CHOCh/MSS (Bullish)"
        elif last_price < prev_low: structure = "📉 CHOCh/MSS (Bearish)"

        # 3. Stop Loss (SL) እና Take Profit (TP)
        if "Bullish" in structure:
            sl = ssl # ከ Liquidity በታች
            tp = bsl # ወደ Liquidity መጠጋት
            signal = "🟢 **BUY SETUP**"
        else:
            sl = bsl # ከ Liquidity በላይ
            tp = ssl # ወደ Liquidity መጠጋት
            signal = "🔴 **SELL SETUP**"

        msg = f"🎯 **የ {symbol} ICT ትንታኔ**\n"
        msg += "----------------------------------\n"
        msg += f"💰 **ዋጋ:** `{last_price:.5f}`\n"
        msg += f"🏗 **Structure:** `{structure}`\n\n"
        
        msg += f"🔝 **BSL:** `{bsl:.5f}`\n"
        msg += f"⬇️ **SSL:** `{ssl:.5f}`\n\n"
        
        msg += f"💡 **Signal:** {signal}\n"
        msg += f"🛑 **SL:** `{sl:.5f}`\n"
        msg += f"🎯 **TP:** `{tp:.5f}`\n"
        
        return msg
    except Exception as e:
        return f"⚠️ ስህተት: {str(e)}"

@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add('🇪🇺 EUR/USD', '🇬🇧 GBP/USD', '🟡 GOLD (XAU/USD)', '₿ Bitcoin (BTC)', '🔄 ሌላ')
    bot.send_message(message.chat.id, "እንኳን ወደ ICT AI ቦት መጡ! ትንታኔ ይምረጡ፦", reply_markup=markup)

@bot.message_handler(func=lambda m: True)
def handle_msg(message):
    bot.send_message(message.chat.id, "🔍 የ ICT ትንታኔ በመስራት ላይ ነኝ...")
    result = get_ict_analysis(message.text)
    bot.send_message(message.chat.id, result, parse_mode='Markdown')

if __name__ == "__main__":
    Thread(target=run_flask).start()
    bot.infinity_polling()
