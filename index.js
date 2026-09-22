const { Client, GatewayIntentBits, Partials, PermissionsBitField, EmbedBuilder, ApplicationCommandOptionType } = require('discord.js');

const TOKEN = process.env.TOKEN;
const CREATOR_ID = process.env.CREATOR_ID;

if (!TOKEN || !CREATOR_ID) {
  console.log("❌ FALTA TOKEN o CREATOR_ID en el Environment del host");
  process.exit(1);
}

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

// DB en memoria del PRO - 50 slots
const PRO_DB = new Map();

client.once('ready', async () => {
  console.log(`☾ Liminal FREE online como ${client.user.tag}`);

  // Registra comandos automáticamente
  const commands = [
    { name: 'setup', description: 'Activa la protección FREE de Liminal' },
    { 
      name: 'grant-pro', 
      description: 'SOLO CREADOR: Conceder PRO a un server',
      options: [{ name: 'server_id', description: 'ID del servidor', type: ApplicationCommandOptionType.String, required: true }]
    },
    { name: 'revoke-pro', description: 'SOLO CREADOR: Quitar PRO', options: [{ name: 'server_id', description: 'ID', type: ApplicationCommandOptionType.String, required: true }] },
    { name: 'raid-drill', description: 'PRO: Lanza un simulacro extremo mensual' }
  ];

  await client.application.commands.set(commands);
  console.log("✅ Comandos registrados");
});

// --- PROTECCIÓN FREE ---

client.on('channelCreate', async (channel) => {
  if (!channel.guild) return;
  try {
    const logs = await channel.guild.fetchAuditLogs({ type: 10, limit: 1 });
    const entry = logs.entries.first();
    if (!entry || !entry.executor || entry.executor.bot) return;
    if (entry.executor.id === channel.guild.ownerId) return;

    const member = await channel.guild.members.fetch(entry.executor.id).catch(()=>null);
    if (!member) return;

    // Si crea más de 1 canal rápido, lo consideramos raid
    await member.roles.set([], "Liminal FREE: Anti-Nuke").catch(()=>{});
    await channel.delete("Liminal FREE: Canal de raid detectado").catch(()=>{});
    
    const owner = await channel.guild.fetchOwner().catch(()=>null);
    if (owner) owner.send(`⚠️ **Liminal FREE bloqueó un intento en ${channel.guild.name}**\nUsuario: ${entry.executor.tag} creó ${channel.name}. Le quité los roles.`).catch(()=>{});
  } catch(e) {}
});

client.on('guildBanAdd', async (ban) => {
  try {
    const logs = await ban.guild.fetchAuditLogs({ type: 22, limit: 1 });
    const entry = logs.entries.first();
    if (!entry || !entry.executor || entry.executor.bot) return;
    
    const member = await ban.guild.members.fetch(entry.executor.id).catch(()=>null);
    if (member) {
      await member.roles.set([], "Liminal FREE: Anti-Ban Masivo").catch(()=>{});
      await ban.guild.members.unban(ban.user.id, "Liminal FREE: Revirtiendo ban").catch(()=>{});
    }
  } catch(e) {}
});

client.on('webhooksUpdate', async (channel) => {
  try {
    const webhooks = await channel.fetchWebhooks();
    webhooks.forEach(w => {
      if (w.owner.id !== client.user.id) w.delete("Liminal FREE: Webhook no autorizado").catch(()=>{});
    });
  } catch(e) {}
});

// --- COMANDOS ---

client.on('interactionCreate', async (interaction) => {
  if (!interaction.isChatInputCommand()) return;

  if (interaction.commandName === 'setup') {
    const embed = new EmbedBuilder()
      .setTitle("☾ Liminal Shield - FREE Activo")
      .setDescription("**Protección activa:**\n✅ Anti-Channel Nuke\n✅ Anti-Ban Masivo\n✅ Anti-Webhook Spam\n\n**PRO:** Solo 50 servidores. Solo por invitación directa del Creador.\nUsa `/raid-drill` si eres PRO.")
      .setColor(0x0a0a0a)
      .setFooter({ text: `Servidor: ${interaction.guild.name}` });
    return interaction.reply({ embeds: [embed] });
  }

  if (interaction.commandName === 'grant-pro') {
    if (interaction.user.id !== CREATOR_ID) return interaction.reply({ content: "⛔ No eres el Creador.", ephemeral: true });
    const id = interaction.options.getString('server_id');
    PRO_DB.set(id, true);
    return interaction.reply(`✅ PRO concedido a \`${id}\`. Slots usados: ${PRO_DB.size}/50`);
  }

  if (interaction.commandName === 'revoke-pro') {
    if (interaction.user.id !== CREATOR_ID) return interaction.reply({ content: "⛔ No eres el Creador.", ephemeral: true });
    const id = interaction.options.getString('server_id');
    PRO_DB.delete(id);
    return interaction.reply(`❌ PRO quitado a \`${id}\`. Slots usados: ${PRO_DB.size}/50`);
  }

  if (interaction.commandName === 'raid-drill') {
    if (!PRO_DB.has(interaction.guildId)) {
      return interaction.reply({ content: "⛔ **LIMINAL PRO requerido.**\nEsta función es solo para los 50 servidores elegidos por el Creador. No se puede comprar ni conseguir de otra forma.", ephemeral: true });
    }
    return interaction.reply({ content: "☾ **DRILL PRO EXTREMO** - Módulo pendiente.\nCuando quieras lo añadimos aquí. Si falla, el bot entra en MODO COMA.", ephemeral: true });
  }
});

client.login(TOKEN);
