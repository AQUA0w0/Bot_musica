import discord
from discord import app_commands
from discord.ext import commands
import wavelink
import os
from dotenv import load_dotenv

# Carregar variáveis do .env
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# Configuração do bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Evento quando o bot está pronto
@bot.event
async def on_ready():
    print(f"🎵 Bot de Música {bot.user} está online!")
    try:
        await bot.tree.sync()  # Sincronizar comandos Slash
        print("✅ Comandos Slash sincronizados!")
    except Exception as e:
        print(f"Erro ao sincronizar comandos: {e}")
    
    bot.loop.create_task(connect_lavalink())

# Conectar ao servidor Lavalink público (Correção aplicada)
async def connect_lavalink():
    node = wavelink.Node(uri="https://lavalink.voidnodes.com", password="youshallnotpass")
    await wavelink.Pool.connect(client=bot, nodes=[node])

# 🎵 Comando Slash para tocar música
@bot.tree.command(name="play", description="Toca uma música do YouTube ou Spotify.")
async def play(interaction: discord.Interaction, search: str):
    user = interaction.user
    if not user.voice:
        await interaction.response.send_message("❌ Você precisa estar em um canal de voz para usar este comando.", ephemeral=True)
        return

    if not interaction.guild.voice_client:
        vc: wavelink.Player = await user.voice.channel.connect(cls=wavelink.Player)
    else:
        vc: wavelink.Player = interaction.guild.voice_client

    track = await wavelink.YouTubeTrack.search(query=search, return_first=True)
    
    if not track:
        await interaction.response.send_message("❌ Nenhuma música encontrada.", ephemeral=True)
        return

    if vc.is_playing():
        vc.queue.put(track)
        await interaction.response.send_message(f"📥 **{track.title}** foi adicionado à fila!")
    else:
        await vc.play(track)
        await interaction.response.send_message(f"🎶 **Tocando agora:** {track.title}")

# ⏸️ Comando Slash para pausar música
@bot.tree.command(name="pause", description="Pausa a música atual.")
async def pause(interaction: discord.Interaction):
    vc: wavelink.Player = interaction.guild.voice_client
    if vc and vc.is_playing():
        await vc.pause()
        await interaction.response.send_message("⏸ Música pausada.")
    else:
        await interaction.response.send_message("❌ Não há música tocando no momento.", ephemeral=True)

# ▶️ Comando Slash para retomar música
@bot.tree.command(name="resume", description="Retoma a música pausada.")
async def resume(interaction: discord.Interaction):
    vc: wavelink.Player = interaction.guild.voice_client
    if vc and vc.is_paused():
        await vc.resume()
        await interaction.response.send_message("▶ Música retomada.")
    else:
        await interaction.response.send_message("❌ Nenhuma música pausada para retomar.", ephemeral=True)

# ⏭️ Comando Slash para pular música
@bot.tree.command(name="skip", description="Pula para a próxima música na fila.")
async def skip(interaction: discord.Interaction):
    vc: wavelink.Player = interaction.guild.voice_client
    if vc and vc.is_playing():
        await vc.stop()
        await interaction.response.send_message("⏭ Música pulada.")
    else:
        await interaction.response.send_message("❌ Não há música tocando para pular.", ephemeral=True)

# ⏹️ Comando Slash para parar música e sair do canal
@bot.tree.command(name="stop", description="Para a música e remove o bot do canal de voz.")
async def stop(interaction: discord.Interaction):
    vc: wavelink.Player = interaction.guild.voice_client
    if vc:
        await vc.disconnect()
        await interaction.response.send_message("👋 Sai do canal de voz.")
    else:
        await interaction.response.send_message("❌ Não estou conectado a um canal de voz.", ephemeral=True)

# 🎶 Comando Slash para mostrar a fila de músicas
@bot.tree.command(name="queue", description="Mostra as músicas na fila.")
async def queue(interaction: discord.Interaction):
    vc: wavelink.Player = interaction.guild.voice_client
    if not vc or vc.queue.is_empty:
        await interaction.response.send_message("❌ A fila está vazia.", ephemeral=True)
        return

    queue_list = "\n".join([f"{i+1}. {track.title}" for i, track in enumerate(vc.queue)])
    await interaction.response.send_message(f"🎵 **Fila de músicas:**\n{queue_list}")

# Rodar o bot
bot.run(TOKEN)