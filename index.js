require('dotenv').config();
const { Client, GatewayIntentBits, Partials, PermissionsBitField, EmbedBuilder } = require('discord.js');

const client = new Client({
  intents: [
    GatewayIntentBits.Guilds,
    GatewayIntentBits.GuildMembers,
    GatewayIntentBits.GuildBans,
    GatewayIntentBits.GuildWebhooks,
    GatewayIntentBits.GuildModeration
  ],
  partials: [Partials.GuildMember]
});

const CREATOR_ID = process.env.CREATOR_ID;
const PRO_DB = new Map(); // Aquí van los 50 PRO. Ej: PRO_DB.set("ID_SERVER", true)
const TRUSTED = new Map(); // Anti-nuke whitelist por server

// --- CONFIG FREE ---
const LIMITS = {
  CHANNEL_CREATE: 3, // max 3 canales en 10s
  BAN: 2
};

client.on('ready', () => {
  console.log(`☾ Liminal FREE online como ${client.user.tag}`);
});

// --- PROTECCIÓN ANTI-NUKE FREE ---

// 1. Anti Channel Create / Delete
client.on('channelCreate', async (channel) => {
  const guild = channel.guild;
  if (!guild) return;
  const logs = await guild.fetchAuditLogs({ type: 10, limit: 1 }); // 10 = ChannelCreate
  const entry = logs.entries.first();
  if (!entry ||!entry.executor || entry.executor.bot) return;

  const execId = entry.executor.id;
  if (TRUSTED.get(guild.id)?.includes(execId)) return;
  if (execId === guild.ownerId) return;

  // Castigo FREE: Quita permisos al raider
  try {
    const member = await guild.members.fetch(execId);
    if (member.permissions.has(PermissionsBitField.Flags.Administrator)) {
      await member.roles.set([], "Liminal: Raid detectado");
      channel.guild.channels.cache.forEach(c => {
        if (c.name.startsWith("raid-test") || c.id === channel.id) return;
      });
      await channel.delete("Liminal: Canal de raid").catch(()=>{});

      const owner = await guild.fetchOwner();
      owner.send(`⚠️ **Liminal bloqueó un raid en ${guild.name}**. Usuario: ${entry.executor.tag} intentó crear canales. Le quité todos los roles.`).catch(()=>{});
    }
  } catch(e) {}
});

// 2. Anti Ban
client.on('guildBanAdd', async (ban) => {
  const guild = ban.guild;
  const logs = await guild.fetchAuditLogs({ type: 22, limit: 1 }); // 22 = MemberBanAdd
  const entry = logs.entries.first();
  if (!entry ||!entry.executor || entry.executor.bot) return;

  const execId = entry.executor.id;
  if (TRUSTED.get(guild.id)?.includes(execId)) return;

  try {
    const member = await guild.members.fetch(execId);
    if (member) {
      await member.roles.set([], "Liminal: Ban masivo detectado");
      await guild.members.unban(ban.user.id, "Liminal: Revirtiendo ban de raid").catch(()=>{});
    }
  } catch(e) {}
});

// 3. Anti Webhook
client.on('webhooksUpdate', async (channel) => {
  const guild = channel.guild;
  const logs = await guild.fetchAuditLogs({ type: 50, limit: 1 }); // 50 = WebhookCreate
  const entry = logs.entries.first();
  if (!entry ||!entry.executor || entry.executor.bot) return;

  try {
    const webhooks = await channel.fetchWebhooks();
    webhooks.forEach(w => w.delete("Liminal: Webhook no autorizado").catch(()=>{}));
  } catch(e) {}
});

// --- COMANDOS FREE ---
client.on('interactionCreate', async (interaction) => {
  if (!interaction.isChatInputCommand()) return;

  // Comando solo para ti
  if (interaction.commandName === 'grant-pro') {
    if (interaction.user.id!== CREATOR_ID) return interaction.reply({ content: "No eres el Creador.", ephemeral: true });
    const serverId = interaction.options.getString('server_id');
    PRO_DB.set(serverId, true);
    return interaction.reply(`✅ PRO concedido a ${serverId}. Quedan ${50 - PRO_DB.size}/50`);
  }

  if (interaction.commandName === 'setup') {
    const embed = new EmbedBuilder()
     .setTitle("☾ Liminal Shield - FREE Activado")
     .setDescription("Protección básica activa:\n✅ Anti-Channel Nuke\n✅ Anti-Ban Mass\n✅ Anti-Webhook Spam\n\n**PRO:** Solo por invitación del Creador. 50 slots totales.")
     .setColor(0x0a0a0a);
    return interaction.reply({ embeds: [embed] });
  }

  if (interaction.commandName === 'raid-drill') {
    // BLOQUEO FREE - Solo si es PRO
    if (!PRO_DB.has(interaction.guildId)) {
      return interaction.reply({ content: "⛔ Esta función es LIMINAL PRO - Solo por invitación del Creador. No se puede comprar.", ephemeral: true });
    }
    // Aquí irá la lógica PRO extrema que hablamos después
    return interaction.reply("Modo PRO detectado. Lógica de drill extremo pendiente de añadir.");
  }
});

client.login(process.env.TOKEN);
