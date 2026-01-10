import telebot
from telebot import types
import yfinance as yf
import pandas_ta as ta
import os
from flask import Flask
from threading import Thread
import pandas as pd

# Render Keep Alive
app = Flask('')
@app.route('/')
def home(): return "Forex AI Bot is running!"

def run_flask():
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

# የአንተ መረጃ
TOKEN = '7311692566:AAGFv2P5ioA_s_45talCetYbJQynbTAlrvc'
ADMIN_ID = '449613656'
bot = telebot.TeleBot(TOKEN)

# --- ዋና ማውጫ ---
def main_menu():
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add('🇪🇺 EUR/USD', '🇬🇧 GBP/USD', '🇯🇵 USD/JPY', '🟡 GOLD (XAU/USD)', '₿ Bitcoin (BTC)', '🔄 ሌላ ምልክት ለመጻፍ')
    return markup

def get_detailed_analysis(symbol):
    try:
        # ምልክቶችን ማስተካከል
        symbol_map = {
            '🇪🇺 EUR/USD': 'EURUSD=X',
            '🇬🇧 GBP/USD': 'GBPUSD=X',
            '🇯🇵 USD/JPY': 'USDJPY=X',
            '🟡 GOLD (XAU/USD)': 'GC=F',
            '₿ Bitcoin (BTC)': 'BTC-USD'
        }
        search_symbol = symbol_map.get(symbol, symbol)
        
        # መረጃውን ከ Yahoo Finance ማምጣት (period ጨምረናል መረጃ እንዲበዛ)
        data = yf.download(search_symbol, period="5d", interval="15m", progress=False)
        
        if data.empty or len(data) < 30:
            return "❌ ስህተት፡ በቂ የገበያ መረጃ ማግኘት አልተቻለም። እባክዎ ጥቂት ቆይተው ይሞክሩ።"

        # Indicators ማስላት
        data['RSI'] = ta.rsi(data['Close'], length=14)
        data['EMA_20'] = ta.ema(data['Close'], length=20)
        
        # የመጨረሻዎቹን መስመሮች ማግኘት (ባዶ ካልሆኑ ብቻ)
        last_row = data.dropna(subset=['RSI', 'EMA_20']).iloc[-1]
        prev_row = data.dropna(subset=['RSI', 'EMA_20']).iloc[-2]
        
        last_price = float(last_row['Close'])
        last_rsi = float(last_row['RSI'])
        last_ema = float(last_row['EMA_20'])
        prev_price = float(prev_row['Close'])

        analysis = f"🎯 **የ {symbol} AI ትንታኔ**\n"
        analysis += "----------------------------------\n"
        analysis += f"💰 **ዋጋ:** `{last_price:.5f}`\n"
        analysis += f"📈 **RSI:** `{last_rsi:.2f}`\n"
        analysis += f"📊 **EMA (20):** `{last_ema:.5f}`\n\n"

        if last_rsi < 35:
            signal = "🟢 **BUY (Oversold)**\nገበያው በጣም ስለተሸጠ ዋጋው ሊጨምር ይችላል።"
        elif last_rsi > 65:
            signal = "🔴 **SELL (Overbought)**\nገበያው በጣም ስለተገዛ ዋጋው ሊቀንስ ይችላል።"
        elif last_price > last_ema and prev_price <= last_ema:
            signal = "🔵 **STRONG BUY**\nዋጋው ከ EMA በላይ ስለወጣ ወደ ላይ የመሄድ እድል አለው።"
        else:
            signal = "🟡 **NEUTRAL**\nገበያው ግልጽ አቅጣጫ አልያዘም።"

        analysis += f"💡 **የ AI ምክር:**\n{signal}"
        return analysis
    except Exception as e:
        return f"⚠️ ትንታኔውን ማዘጋጀት አልተቻለም። (Error: {str(e)})"

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "እንኳን ወደ Forex AI ቦት መጡ! 👋\nትንታኔ የሚፈልጉትን ጥንድ ይምረጡ።", reply_markup=main_menu())

@bot.message_handler(func=lambda m: m.text == '🔄 ሌላ ምልክት ለመጻፍ')
def ask_custom(message):
    bot.send_message(message.chat.id, "እባክዎ የምልክቱን ስም ይጻፉ (ለምሳሌ፦ `AUDUSD=X`)፡", reply_markup=types.ReplyKeyboardRemove())

@bot.message_handler(func=lambda m: True)
def handle_all(message):
    symbol = message.text
    bot.send_message(message.chat.id, f"🔍 የ {symbol} ገበያን በመተንተን ላይ ነኝ...")
    result = get_detailed_analysis(symbol)
    bot.send_message(message.chat.id, result, parse_mode='Markdown', reply_markup=main_menu())
    bot.send_message(ADMIN_ID, f"🔔 @{message.from_user.username} የ {symbol} ትንታኔ ጠይቋል።")

if __name__ == "__main__":
    Thread(target=run_flask).start()
    bot.infinity_polling()
