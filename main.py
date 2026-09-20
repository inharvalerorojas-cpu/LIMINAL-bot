import discord
from discord.ext import commands
import os, threading
from flask import Flask
import stripe

app = Flask('')
TOKEN = os.getenv("TOKEN")
stripe.api_key = os.getenv("STRIPE_SECRET")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

PRODUCTS = {
    "color": {"name": "Rol de Color Personalizado", "price": 199, "desc": "Tu nombre con el color que quieras"},
    "emoji": {"name": "Slot de Emoji Personalizado", "price": 99, "desc": "Añadimos tu emoji al server"},
    "sticker": {"name": "Sticker Personalizado", "price": 149, "desc": "Tu sticker en el server"},
    "vip": {"name": "Acceso VIP", "price": 499, "desc": "Acceso a canales VIP"},
    "sala": {"name": "Sala Privada de Voz", "price": 299, "desc": "Tu propia sala privada"},
    "boost": {"name": "Recompensa por Boost", "price": 399, "desc": "Recompensa por boostear el server"}
}

@app.route('/')
def home(): return "Discord General Store - LIVE"

@app.route('/webhook', methods=['POST'])
def webhook(): return "OK", 200

def run_flask():
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))

@bot.event
async def on_ready():
    print(f"✅ Tienda General ACTIVA como {bot.user}")

@bot.command()
async def tienda(ctx):
    embed = discord.Embed(title="🛒 TIENDA DEL SERVER", description="Objetos comunes - Pago con tarjeta", color=0x5865f2)
    for k, v in PRODUCTS.items():
        embed.add_field(name=f"{v['name']} - {v['price']/100}€", value=f"{v['desc']}\n`!comprar {k}`", inline=False)
    await ctx.send(embed=embed)

@bot.command()
async def comprar(ctx, producto: str):
    producto = producto.lower()
    if producto not in PRODUCTS:
        await ctx.send(f"❌ No existe. Usa `!tienda`\nDisponibles: {', '.join(PRODUCTS.keys())}")
        return
    p = PRODUCTS[producto]
    session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=[{'price_data': {'currency': 'eur','product_data': {'name': p['name']},'unit_amount': p['price']},'quantity': 1}],
        mode='payment',
        success_url='https://discord.com',
        cancel_url='https://discord.com',
        metadata={'user_id': str(ctx.author.id)}
    )
    await ctx.send(f"{ctx.author.mention} Paga tu **{p['name']}** aquí -> {session.url}")

if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    bot.run(TOKEN)
