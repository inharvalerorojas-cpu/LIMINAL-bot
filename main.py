import discord
from discord.ext import commands
import os, threading, time
from flask import Flask
from collections import defaultdict

app = Flask(__name__)
TOKEN = os.getenv("TOKEN")
STRIPE_LINK = os.getenv("STRIPE_LINK", "https://buy.stripe.com/test_123")

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

stats = {"raids": 0, "msgs": 0, "nukes": 0, "webhooks": 0}
join_cache, msg_global = [], []
spam_cache = defaultdict(list)
is_defending = False
WHITELIST = []

@app.route('/')
def home():
    html = f"""
    <!DOCTYPE html>
    <html><head><title>Liminal Shield - Anti Nuke System</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700&display=swap');
    body{{background:#0a0a0b;color:white;font-family:'Inter',sans-serif;margin:0;padding:20px;text-align:center}}
   .header{{padding:40px;background:linear-gradient(180deg,#1a1033 0%,#0a0a0b 100%);border-radius:20px}}
    h1{{color:#9147ff;font-size:42px;margin:0}} p{{color:#888}}
   .grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:20px;max-width:900px;margin:30px auto}}
   .card{{background:#16161a;padding:25px;border-radius:16px;border:1px solid #2a2a2e}}
   .card h2{{font-size:14px;color:#888;letter-spacing:1px;margin:0 0 10px 0}}
   .num{{font-size:36px;font-weight:700}}
   .btn{{background:#9147ff;color:white;padding:18px 40px;border-radius:12px;text-decoration:none;display:inline-block;font-weight:700;font-size:18px;margin-top:20px}}
   .btn:hover{{background:#772ce8}}
   .footer{{margin-top:50px;color:#444;font-size:12px}}
    </style>
    </head>
    <body>
    <div class="header">
    <h1>🛡️ LIMINAL SHIELD</h1>
    <p>Professional Anti-Nuke / Anti-Raid / Anti-Spam Protection</p>
    <p>24/7 Live Protection System</p>
    <a href="{STRIPE_LINK}" class="btn">BUY PRO - €4.99</a>
    </div>
    <div class="grid">
    <div class="card"><h2>RAIDS BLOCKED</h2><div class="num">{stats["raids"]}</div></div>
    <div class="card"><h2>MESSAGES SCANNED</h2><div class="num">{stats["msgs"]}</div></div>
    <div class="card"><h2>NUKES BLOCKED</h2><div class="num">{stats["nukes"]}</div></div>
    <div class="card"><h2>WEBHOOKS DELETED</h2><div class="num">{stats["webhooks"]}</div></div>
    </div>
    <div class="card" style="max-width:900px;margin:20px auto">
    <h2>HOW TO USE</h2>
    <p>Invite bot to your server and use <b style="color:#9147ff">/liminal</b> for private panel<br>
    <b>/lockdown</b> to lock server<br><b>/unlock</b> to restore server<br>All commands are private (ephemeral) - only you can see them.</p>
    </div>
    <div class="footer">INMARC Security © 2026 - Made in Terrassa, Spain</div>
    </body></html>
    """
    return html

def run_flask():
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))

async def blindar(guild, razon, atacante=None):
    global is_defending
    if is_defending: return
    is_defending = True
    if "RAID" in razon: stats["raids"] += 1
    if "NUKE" in razon: stats["nukes"] += 1
    print(f"ATTACK: {razon}")
    try:
        await guild.edit(verification_level=discord.VerificationLevel.highest)
        for ch in guild.text_channels:
            try:
                await ch.edit(slowmode_delay=15)
                await ch.set_permissions(guild.default_role, send_messages=False)
            except: pass
        canal = guild.system_channel or guild.text_channels[0]
        if atacante:
            try: await guild.ban(atacante, reason=razon)
            except: pass
        await canal.send(f"🛡️ ATTACK BLOCKED: {razon}. Use /unlock to restore")
    except: pass

@bot.event
async def on_ready():
    print(f"ONLINE {bot.user}")
    try:
        await bot.tree.sync()
        print("Slash synced")
    except Exception as e:
        print(e)

@bot.event
async def on_member_join(m):
    join_cache.append(time.time())
    while join_cache and time.time() - join_cache[0] > 10: join_cache.pop(0)
    if len(join_cache) >= 5: await blindar(m.guild, f"RAID - {len(join_cache)} joins/10s")

@bot.event
async def on_message(msg):
    if msg.author.bot:
        await bot.process_commands(msg)
        return
    stats["msgs"] += 1
    now = time.time()
    msg_global.append(now)
    while msg_global and now - msg_global[0] > 5: msg_global.pop(0)
    if len(msg_global) >= 25:
        await blindar(msg.guild, f"FLOOD - {len(msg_global)} msgs/5s"); msg_global.clear(); return
    spam_cache[msg.author.id].append(now)
    spam_cache[msg.author.id] = [t for t in spam_cache[msg.author.id] if now - t < 4]
    if len(spam_cache[msg.author.id]) >= 6:
        try: await msg.author.timeout(duration=3600, reason="spam")
        except: pass
        return
    await bot.process_commands(msg)

@bot.event
async def on_guild_channel_delete(ch):
    try:
        async for e in ch.guild.audit_logs(limit=1, action=discord.AuditLogAction.channel_delete):
            if e.user.id not in WHITELIST and not e.user.bot: await blindar(ch.guild, f"NUKE - Channel {ch.name} deleted", e.user)
    except: pass

@bot.event
async def on_guild_role_delete(role):
    try:
        async for e in role.guild.audit_logs(limit=1, action=discord.AuditLogAction.role_delete):
            if e.user.id not in WHITELIST and not e.user.bot: await blindar(role.guild, f"NUKE - Role {role.name} deleted", e.user)
    except: pass

@bot.event
async def on_webhooks_update(ch):
    try:
        async for e in ch.guild.audit_logs(limit=1, action=discord.AuditLogAction.webhook_create):
            if e.user.id not in WHITELIST and not e.user.guild_permissions.administrator:
                stats["webhooks"] += 1
                for wh in await ch.webhooks():
                    if wh.user and wh.user.id == e.user.id: await wh.delete(reason="Anti-Webhook")
    except: pass

# --- GHOST COMMANDS (PREFIX) ---
@bot.command()
@commands.has_permissions(administrator=True)
async def lockdown(ctx):
    try: await ctx.message.delete()
    except: pass
    global is_defending; is_defending = True
    await ctx.guild.edit(verification_level=discord.VerificationLevel.highest)
    for ch in ctx.guild.text_channels:
        try: await ch.edit(slowmode_delay=15); await ch.set_permissions(ctx.guild.default_role, send_messages=False)
        except: pass
    try: await ctx.author.send("🔒 Server locked (ghost mode). Only you see this. Use!unlock")
    except: pass

@bot.command()
@commands.has_permissions(administrator=True)
async def unlock(ctx):
    try: await ctx.message.delete()
    except: pass
    global is_defending; is_defending = False; join_cache.clear(); msg_global.clear()
    await ctx.guild.edit(verification_level=discord.VerificationLevel.low)
    for ch in ctx.guild.text_channels:
        try: await ch.edit(slowmode_delay=0); await ch.set_permissions(ctx.guild.default_role, overwrite=None)
        except: pass
    try: await ctx.author.send("🔓 Server restored. Only you see this.")
    except: pass

@bot.command()
async def liminal(ctx):
    try: await ctx.message.delete()
    except: pass
    embed = discord.Embed(title="🛡️ LIMINAL SHIELD PRO", color=0x9147ff, description="Private panel - Only you see this")
    embed.add_field(name="📊 Dashboard", value=f"Raids: {stats['raids']} | Scanned: {stats['msgs']}", inline=False)
    embed.add_field(name="💳 Buy PRO", value=f"[Stripe Link]({STRIPE_LINK})", inline=False)
    embed.add_field(name="Commands", value="/liminal /lockdown /unlock are 100% private (ephemeral)", inline=False)
    try: await ctx.author.send(embed=embed)
    except: await ctx.send(f"{ctx.author.mention} Enable DMs", delete_after=5)

# --- SLASH COMMANDS (100% PRIVATE) ---
@bot.tree.command(name="liminal", description="Private Liminal panel")
async def liminal_slash(interaction: discord.Interaction):
    embed = discord.Embed(title="🛡️ LIMINAL SHIELD PRO - Private", color=0x9147ff)
    embed.add_field(name="Stats", value=f"Raids: {stats['raids']} | Msgs: {stats['msgs']} | Nukes: {stats['nukes']}", inline=False)
    embed.add_field(name="Buy PRO - €4.99", value=f"[Click here - Stripe]({STRIPE_LINK})", inline=False)
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="lockdown", description="Lock server (ghost mode - only you see)")
async def lockdown_slash(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("No permission", ephemeral=True); return
    global is_defending; is_defending = True
    await interaction.guild.edit(verification_level=discord.VerificationLevel.highest)
    for ch in interaction.guild.text_channels:
        try: await ch.edit(slowmode_delay=15); await ch.set_permissions(interaction.guild.default_role, send_messages=False)
        except: pass
    await interaction.response.send_message("🔒 Server locked. Only you see this. Use /unlock to restore", ephemeral=True)

@bot.tree.command(name="unlock", description="Restore server (ghost mode)")
async def unlock_slash(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("No permission", ephemeral=True); return
    global is_defending; is_defending = False; join_cache.clear(); msg_global.clear()
    await interaction.guild.edit(verification_level=discord.VerificationLevel.low)
    for ch in interaction.guild.text_channels:
        try: await ch.edit(slowmode_delay=0); await ch.set_permissions(interaction.guild.default_role, overwrite=None)
        except: pass
    await interaction.response.send_message("🔓 Server restored. Only you see this.", ephemeral=True)

if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    bot.run(TOKEN)
