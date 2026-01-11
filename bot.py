import telebot
from telebot import types
import yfinance as yf
import os
from flask import Flask
from threading import Thread

# Render Port Fix (Flask)
app = Flask('')
@app.route('/')
def home(): return "Forex AI Bot is Live!"

def run_flask():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

# ቦት መረጃ
TOKEN = '7311692566:AAGFv2P5ioA_s_45talCetYbJQynbTAlrvc'
bot = telebot.TeleBot(TOKEN)

def get_market_analysis(symbol):
    try:
        symbol_map = {
            '🇪🇺 EUR/USD': 'EURUSD=X', '🇬🇧 GBP/USD': 'GBPUSD=X',
            '🇯🇵 USD/JPY': 'USDJPY=X', '🟡 GOLD (XAU/USD)': 'GC=F',
            '₿ Bitcoin (BTC)': 'BTC-USD'
        }
        search_symbol = symbol_map.get(symbol, symbol)
        
        # መረጃ ማምጣት
        ticker = yf.Ticker(search_symbol)
        df = ticker.history(period="2d", interval="15m")
        
        if df.empty: return "❌ መረጃ ማግኘት አልተቻለም።"

        prices = df['Close'].tolist()
        last_price = prices[-1]
        
        # 1. የገበያ አዝማሚያ (Trend)
        trend = "📈 UP" if last_price > prices[0] else "📉 DOWN"
        
        # 2. RSI ስሌት (Manual - 14 period)
        gains = []
        losses = []
        for i in range(1, 15):
            diff = prices[-i] - prices[-(i+1)]
            gains.append(max(diff, 0))
            losses.append(max(-diff, 0))
        
        avg_gain = sum(gains) / 14
        avg_loss = sum(losses) / 14 if sum(losses) != 0 else 0.0001
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        # መልእክቱን ማዘጋጀት
        msg = f"🎯 **የ {symbol} AI ትንታኔ**\n"
        msg += "----------------------------------\n"
        msg += f"💰 ዋጋ: `{last_price:.5f}`\n"
        msg += f"📊 Trend: {trend}\n"
        msg += f"📈 RSI: `{rsi:.2f}`\n\n"

        if rsi < 35:
            msg += "💡 **AI ምክር:** 🟢 **BUY (Oversold)**\nገበያው ሊጨምር ስለሚችል ለመግዛት አመቺ ነው።"
        elif rsi > 65:
            msg += "💡 **AI ምክር:** 🔴 **SELL (Overbought)**\nገበያው ሊቀንስ ስለሚችል ለመሸጥ አመቺ ነው።"
        else:
            msg += "💡 **AI ምክር:** 🟡 **NEUTRAL**\nገበያው ግልጽ አቅጣጫ አልያዘም።"
        
        return msg
    except Exception as e:
        return f"⚠️ ስህተት ተከስቷል: {str(e)}"

@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add('🇪🇺 EUR/USD', '🇬🇧 GBP/USD', '🟡 GOLD (XAU/USD)', '₿ Bitcoin (BTC)', '🔄 ሌላ')
    bot.send_message(message.chat.id, "እንኳን ወደ Forex AI ቦት መጡ! 👋\nትንታኔ ይምረጡ፡", reply_markup=markup)

@bot.message_handler(func=lambda m: True)
def handle_msg(message):
    bot.send_message(message.chat.id, "🔍 በመተንተን ላይ ነኝ... እባክዎ ይጠብቁ።")
    result = get_market_analysis(message.text)
    bot.send_message(message.chat.id, result, parse_mode='Markdown')

if __name__ == "__main__":
    Thread(target=run_flask).start()
    bot.infinity_polling()
