import discord
from discord.ext import commands
import os, threading, time, re
from flask import Flask
from collections import defaultdict

app = Flask('')
TOKEN = os.getenv("TOKEN")
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

# --- MEMORIA ---
join_cache = []
msg_global = []
spam_cache = defaultdict(list)
is_defending = False
WHITELIST = [] # Pon aquí tus IDs de admin de confianza ej: [123456789]

@app.route('/')
def home(): return "INMARC SHIELD TOTAL - ANTI ALL ATTACKS LIVE"
def run_flask():
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))

async def blindar_servidor(guild, razon, atacante=None):
    global is_defending
    if is_defending: return
    is_defending = True
    print(f"🚨 ATAQUE DETECTADO: {razon}")
    try:
        await guild.edit(verification_level=discord.VerificationLevel.highest)
        for ch in guild.text_channels:
            try:
                await ch.edit(slowmode_delay=15)
                await ch.set_permissions(guild.default_role, send_messages=False)
            except: pass

        canal = guild.system_channel or guild.text_channels[0]
        if atacante:
            await canal.send(f"🛡️ **ATAQUE BLOQUEADO: {razon}**\nAtacante: {atacante.mention} `{atacante.id}` baneado.\nServidor en lockdown. Usa `!unlock`")
            try: await guild.ban(atacante, reason=f"INMARC Shield: {razon}")
            except: pass
        else:
            await canal.send(f"🛡️ **ATAQUE BLOQUEADO: {razon}**\nServidor en lockdown. Usa `!unlock`")
    except Exception as e:
        print(f"Error blindaje: {e}")

@bot.event
async def on_ready():
    print(f"✅ INMARC SHIELD TOTAL ACTIVO como {bot.user}")

# 1. ANTI-RAID Y ANTI-DDOS/FLOOD
@bot.event
async def on_member_join(member):
    now = time.time()
    join_cache.append(now)
    # Limpiar
    while join_cache and now - join_cache[0] > 10:
        join_cache.pop(0)
    if len(join_cache) >= 5:
        await blindar_servidor(member.guild, f"RAID - {len(join_cache)} joins en 10s")
        # Banear bots recién entrados
        for m in member.guild.members:
            if m.bot and m.id not in WHITELIST and (now - m.joined_at.timestamp() < 20):
                try: await m.guild.ban(m, reason="Anti-Raid: Bot masivo")
                except: pass

@bot.event
async def on_message(message):
    if message.author.bot or message.author.id in WHITELIST:
        return

    now = time.time()
    msg_global.append(now)
    while msg_global and now - msg_global[0] > 5:
        msg_global.pop(0)

    if len(msg_global) >= 25:
        await blindar_servidor(message.guild, f"FLOOD/DDOS - {len(msg_global)} msgs/5s")
        msg_global.clear()
        return

    # Anti-Spam individual
    spam_cache[message.author.id].append(now)
    spam_cache[message.author.id] = [t for t in spam_cache[message.author.id] if now - t < 4]
    if len(spam_cache[message.author.id]) >= 6:
        try:
            await message.author.timeout(duration=3600, reason="Anti-Spam")
            await message.channel.send(f"🤖 {message.author.mention} muteado 1h por spam.", delete_after=5)
        except: pass
        return

    # Anti @everyone + Anti Scam Links (Token grab)
    if ("@everyone" in message.content or "@here" in message.content) and not message.author.guild_permissions.moderate_members:
        try:
            await message.delete()
            await message.author.timeout(duration=3600, reason="Anti @everyone")
        except: pass
        return

    # Anti links de scam / nitro gratis / token grab
    scam_words = ["free nitro", "nitro gratis", "steam gift", "discord.gift", ".exe", "descarga esto"]
    if any(w in message.content.lower() for w in scam_words):
        try:
            await message.delete()
            await message.channel.send(f"⚠️ {message.author.mention} link sospechoso borrado (Anti-Scam/Token Grab).", delete_after=10)
        except: pass
        return

    await bot.process_commands(message)

# 2. ANTI-NUKE - Borrado de canales
@bot.event
async def on_guild_channel_delete(channel):
    try:
        async for entry in channel.guild.audit_logs(limit=1, action=discord.AuditLogAction.channel_delete):
            if entry.user.id not in WHITELIST and not entry.user.bot:
                await blindar_servidor(channel.guild, f"NUKE - Borrado de canal {channel.name}", entry.user)
    except: pass

@bot.event
async def on_guild_channel_create(channel):
    try:
        async for entry in channel.guild.audit_logs(limit=1, action=discord.AuditLogAction.channel_create):
            if entry.user.id not in WHITELIST and len(channel.guild.channels) > 50: # Creacion masiva
                await blindar_servidor(channel.guild, f"NUKE - Creación masiva de canales", entry.user)
    except: pass

# 3. ANTI-NUKE - Roles
@bot.event
async def on_guild_role_delete(role):
    try:
        async for entry in role.guild.audit_logs(limit=1, action=discord.AuditLogAction.role_delete):
            if entry.user.id not in WHITELIST and not entry.user.bot:
                await blindar_servidor(role.guild, f"NUKE - Borrado de rol {role.name}", entry.user)
    except: pass

# 4. ANTI-NUKE - Baneos masivos
@bot.event
async def on_member_ban(guild, user):
    try:
        async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.ban):
            if entry.user.id not in WHITELIST:
                # Si banea a 2 personas en 10 seg, es nuke
                # (simplificado: ban directo por seguridad)
                if not entry.user.bot:
                    await blindar_servidor(guild, f"NUKE - Baneo masivo", entry.user)
    except: pass

# 5. ANTI-WEBHOOK SPAM
@bot.event
async def on_webhooks_update(channel):
    try:
        async for entry in channel.guild.audit_logs(limit=1, action=discord.AuditLogAction.webhook_create):
            if entry.user.id not in WHITELIST and not entry.user.guild_permissions.administrator:
                # Borrar webhook creado por no-admin
                webhooks = await channel.webhooks()
                for wh in webhooks:
                    if wh.user and wh.user.id == entry.user.id:
                        await wh.delete(reason="Anti-Webhook Spam")
                await channel.send(f"🚫 Webhook no autorizado de {entry.user.mention} borrado.", delete_after=10)
    except: pass

@bot.command()
@commands.has_permissions(administrator=True)
async def unlock(ctx):
    global is_defending
    is_defending = False
    try:
        await ctx.guild.edit(verification_level=discord.VerificationLevel.low)
        for ch in ctx.guild.text_channels:
            try:
                await ch.edit(slowmode_delay=0)
                await ch.set_permissions(ctx.guild.default_role, send_messages=None)
            except: pass
        await ctx.send("🔓 Servidor restaurado.")
    except Exception as e:
        await ctx.send(f"Error: {e}")

@bot.command()
@commands.has_permissions(administrator=True)
async def whitelist(ctx, user: discord.Member):
    WHITELIST.append(user.id)
    await ctx.send(f"✅ {user} añadido a whitelist.")

if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    bot.run(TOKEN)
