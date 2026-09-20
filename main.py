import discord
from discord.ext import commands
import os, threading
from flask import Flask, request
import stripe

app = Flask('')
TOKEN = os.getenv("TOKEN")
stripe.api_key = os.getenv("STRIPE_SECRET")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

PRODUCTS = {
    "access": {"name": "LIMINAL ACCESS", "price": 499, "role": "Liminal"},
    "vip": {"name": "VIP REALM", "price": 999, "role": "VIP"},
    "founder": {"name": "FOUNDER'S KEY", "price": 1999, "role": "Founder"}
}

@app.route('/')
def home(): return "LIMINAL by INMARC - STORE LIVE"

@app.route('/webhook', methods=['POST'])
def webhook():
    print("Webhook recibido de Stripe")
    return "OK", 200

def run_flask():
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))

@bot.event
async def on_ready():
    print(f"✅ LIMINAL STORE ACTIVA como {bot.user}")

@bot.command()
async def tienda(ctx):
    embed = discord.Embed(title="INMARC STUDIOS // LIMINAL STORE", description="Pagos seguros con Stripe", color=0x7c3aed)
    for k, v in PRODUCTS.items():
        embed.add_field(name=f"{v['name']} - {v['price']/100}€", value=f"`!comprar {k}`", inline=False)
    await ctx.send(embed=embed)

@bot.command()
async def comprar(ctx, producto: str):
    producto = producto.lower()
    if producto not in PRODUCTS:
        await ctx.send("❌ Producto no existe. Usa `!tienda`")
        return
    p = PRODUCTS[producto]
    if not stripe.api_key:
        await ctx.send("❌ Stripe no configurado en Render.")
        return
    session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=[{'price_data': {'currency': 'eur','product_data': {'name': p['name']},'unit_amount': p['price']},'quantity': 1}],
        mode='payment',
        success_url='https://discord.com',
        cancel_url='https://discord.com',
        metadata={'user_id': str(ctx.author.id), 'role': p['role']}
    )
    await ctx.send(f"{ctx.author.mention} ✅ Paga tu {p['name']} aquí: {session.url}")

if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    bot.run(TOKEN)
