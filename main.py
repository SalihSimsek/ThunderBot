import os
import json
import random
import asyncio
import aiohttp
from dotenv import load_dotenv
import discord
from discord.ext import commands
from discord import app_commands
import time
from datetime import timedelta
import yt_dlp
from keep_alive import keep_alive
from dotenv import load_dotenv
keep_alive()  # önce çalıştır
# PYNACL DAHİLDİR


load_dotenv()
TOKEN = os.getenv("TOKEN")
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "ayarlar.json")
AUTO_FILE = os.path.join(BASE_DIR, "otoyanit.json")
POINTS_FILE = os.path.join(BASE_DIR, "puanlar.json")
ECON_FILE = os.path.join(BASE_DIR, "economy.json")
MARKET_FILE = os.path.join(BASE_DIR, "market.json")
SAVE_LOCK = asyncio.Lock()
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="t!", intents=intents, help_command=None)
guild_settings = {}
user_points = {}
auto_replies = {}

economy_data = {}   # kullanıcı -> { balance, inventory, last_daily }
# Global market_data yerine
market_data = {}  # Sunucu ID -> market items şeklinde olacak

# Varsayılan market ürünleri
default_items = [
    {"id": "Dikkat", "name": "dikkat", "price": 100000, "desc": "Bu ürünü satın almayınız..."},
]


def _convert_loaded(raw):
    converted = {}
    for k, v in raw.items():
        try:
            gid = int(k)
        except:
            gid = k
        converted[gid] = {}
        for gname, settings in v.items():
            s = dict(settings)
            if isinstance(s.get("used"), list):
                s["used"] = set(s["used"])
            converted[gid][gname] = s
    return converted


def load_all():
    global guild_settings, user_points, economy_data, market_data, auto_replies

    # guild ayarları
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                raw = json.load(f)
            guild_settings = _convert_loaded(raw)
        except Exception as e:
            print("LOAD DATA ERROR:", e)
            guild_settings = {}
    else:
        guild_settings = {}

    # puanlar
    if os.path.exists(POINTS_FILE):
        try:
            with open(POINTS_FILE, "r", encoding="utf-8") as f:
                user_points = json.load(f)
        except Exception as e:
            print("LOAD POINTS ERROR:", e)
            user_points = {}
    else:
        user_points = {}

    # ekonomi (ACoin)
    if os.path.exists(ECON_FILE):
        try:
            with open(ECON_FILE, "r", encoding="utf-8") as f:
                economy_data = json.load(f)
        except Exception as e:
            print("LOAD ECON ERRO/R:", e)
            economy_data = {}
    else:
        economy_data = {}

    # market (ürünler)
    if os.path.exists(MARKET_FILE):
        try:
            with open(MARKET_FILE, "r", encoding="utf-8") as f:
                market_data = json.load(f)
        except Exception as e:
            print("LOAD MARKET ERROR:", e)
            market_data = {}
    else:
        market_data = {}

    # oto yanıtlar
    if os.path.exists(AUTO_FILE):
        try:
            with open(AUTO_FILE, "r", encoding="utf-8") as f:
                auto_replies = json.load(f)
        except Exception as e:
            print("LOAD AUTOYANIT ERROR:", e)
            auto_replies = {}
    else:
        auto_replies = {}


async def save_all():
    async with SAVE_LOCK:
        # guild_settings kaydet
        dump = {}
        for gid, games in guild_settings.items():
            k = str(gid)
            dump[k] = {}
            for gname, settings in games.items():
                s = {}
                for kk, vv in settings.items():
                    if isinstance(vv, set):
                        s[kk] = list(vv)
                    else:
                        s[kk] = vv
                dump[k][gname] = s
        try:
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(dump, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print("SAVE DATA ERROR:", e)

        # user_points kaydet
        try:
            with open(POINTS_FILE, "w", encoding="utf-8") as f:
                json.dump(user_points, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print("SAVE POINTS ERROR:", e)

        # economy kaydet
        try:
            with open(ECON_FILE, "w", encoding="utf-8") as f:
                json.dump(economy_data, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print("SAVE ECON ERROR:", e)

        # market kaydet
        try:
            with open(MARKET_FILE, "w", encoding="utf-8") as f:
                json.dump(market_data, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print("SAVE MARKET ERROR:", e)

        # oto yanıtlar kaydet
        try:
            with open(AUTO_FILE, "w", encoding="utf-8") as f:
                json.dump(auto_replies, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print("SAVE AUTOYANIT ERROR:", e)


async def fetch_word():
    vercel = "https://rastgelekelime.vercel.app/api/word"
    github_raw = "https://raw.githubusercontent.com/EnesKeremAYDIN/npm-rastgelekelime/main/data/turkce-1.txt"
    try:
        async with aiohttp.ClientSession() as s:
            try:
                async with s.get(vercel, timeout=5) as r:
                    if r.status == 200:
                        text = (await r.text()).strip()
                        text = text.strip('"[] \n\r')
                        if text:
                            return text.lower()
            except:
                pass
            try:
                async with s.get(github_raw, timeout=6) as r2:
                    if r2.status == 200:
                        txt = await r2.text()
                        words = [w.strip() for w in txt.splitlines() if w.strip()]
                        if words:
                            return random.choice(words).lower()
            except:
                pass
    except:
        pass
    fallback = ["python","discord","oyun","bot","kod","yazılım","bilgisayar","müzik","oyuncu","tasarım","şehir","kitap","kalem"]
    return random.choice(fallback)

def create_embed(title, desc, color=discord.Color.blue()):
    return discord.Embed(title=title, description=desc, color=color)

@bot.event
async def on_ready():
    load_all()
    try:
        await bot.tree.sync()
    except Exception as e:
        print("SYNC ERROR", e)
    await bot.change_presence(status=discord.Status.online, activity=discord.Game(name="✨ /help - t! ile kullan"))
    print("Bot hazır:", bot.user)

async def kurulum_logic(ctx, oyun: str, kanal: discord.TextChannel, sifirlamali: str):
    if not getattr(ctx.author, "guild_permissions", None) or not ctx.author.guild_permissions.administrator:
        return await ctx.send(embed=create_embed("⛔ Yetki Hatası","Bu komutu sadece yöneticiler kullanabilir.", discord.Color.red()))
    if sifirlamali is None or sifirlamali.lower() not in ("evet","hayır"):
        return await ctx.send(embed=create_embed("❌ Hata","Son parametre `sıfırlamalı` zorunlu: `evet` veya `hayır`", discord.Color.red()))
    gid = ctx.guild.id
    if gid not in guild_settings:
        guild_settings[gid] = {}
    key = oyun.lower()
    base = {"aktif": True, "kanal_id": kanal.id, "sıfırlamalı": sifirlamali.lower()}
    if key == "boom":
        base["son_sayi"] = 0
        guild_settings[gid]["boom"] = base
        msg = f"💣 Boom kuruldu {kanal.mention} Sıfırlamalı: {sifirlamali}"
        print(f"[{ctx.guild.name}] Boom kuruldu. sıfırlamalı={sifirlamali}")
    elif key == "say":
        base["son_sayi"] = 0
        guild_settings[gid]["say"] = base
        msg = f"🔢 Say kuruldu {kanal.mention} Sıfırlamalı: {sifirlamali}"
        print(f"[{ctx.guild.name}] Say kuruldu. sıfırlamalı={sifirlamali}")
    elif key == "kelime_bilmece":
        w = await fetch_word()
        base["kelime"] = w
        guild_settings[gid]["kelime_bilmece"] = base
        msg = f"📝 Kelime Bilmece kuruldu {kanal.mention} Sıfırlamalı: {sifirlamali}"
        print(f"[{ctx.guild.name}] kelime_bilmece kelime: {w}")
    elif key == "sayi":
        n = random.randint(1,20)
        base["sayi"] = n
        guild_settings[gid]["sayi"] = base
        msg = f"🎯 Sayı oyunu kuruldu {kanal.mention} Sıfırlamalı: {sifirlamali}"
        print(f"[{ctx.guild.name}] sayi seçildi: {n}")
    elif key == "kelime_turetme":
        w = await fetch_word()
        base["son_kelime"] = w
        base["used"] = set([w])
        guild_settings[gid]["kelime_turetme"] = base
        msg = f"🧩 Kelime Türetme kuruldu {kanal.mention} İlk kelime: {w} Sıfırlamalı: {sifirlamali}"
        print(f"[{ctx.guild.name}] kelime_turetme ilk kelime: {w}")
    else:
        return await ctx.send(embed=create_embed("❌ Hata","Geçersiz oyun! seçenekler: boom, say, kelime_bilmece, sayi, kelime_turetme", discord.Color.red()))
    await save_all()
    await ctx.send(embed=create_embed("✅ Kurulum Tamamlandı", msg, discord.Color.green()))
    await kanal.send(embed=create_embed(f"🎮 {key.upper()} başladı","Oyun kuruldu! Kurallara göre oynayın.", discord.Color.purple()))

async def sifirla_logic(ctx, oyun: str, kanal: discord.TextChannel):
    if not getattr(ctx.author, "guild_permissions", None) or not ctx.author.guild_permissions.administrator:
        return await ctx.send(embed=create_embed("⛔ Yetki Hatası","Bu komutu sadece yöneticiler kullanabilir.", discord.Color.red()))
    gid = ctx.guild.id
    key = oyun.lower()
    if gid not in guild_settings or key not in guild_settings[gid]:
        return await ctx.send(embed=create_embed("❌ Hata",f"{kanal.mention} kanalında {key} kurulu değil.", discord.Color.red()))
    if guild_settings[gid][key]["kanal_id"] != kanal.id:
        return await ctx.send(embed=create_embed("❌ Hata",f"{key} bu kanalda kurulu değil.", discord.Color.red()))
    del guild_settings[gid][key]
    if not guild_settings[gid]:
        del guild_settings[gid]
    await save_all()
    await ctx.send(embed=create_embed("✅ Oyun Kaldırıldı", f"{key} kaldırıldı.", discord.Color.orange()))
    print(f"[{ctx.guild.name}] {key} kaldırıldı")

async def fabrika_reset_logic(ctx):
    if not getattr(ctx.author, "guild_permissions", None) or not ctx.author.guild_permissions.administrator:
        return await ctx.send(embed=create_embed("⛔ Yetki Hatası","Bu komutu sadece yöneticiler kullanabilir.", discord.Color.red()))
    gid = ctx.guild.id
    if gid in guild_settings:
        del guild_settings[gid]
        await save_all()
    await ctx.send(embed=create_embed("♻️ Fabrika Reset","Sunucu ayarları sıfırlandı.", discord.Color.red()))
    print(f"[{ctx.guild.name}] fabrika reset")

async def help_logic(ctx):
    act = bot.activity.name if getattr(bot, "activity", None) else "Aktivite yok"
    e = create_embed("📖 Yardım Menüsü", "Komutların listesi", discord.Color.blue())

    # Oyunlar
    e.add_field(name="🎮 Oyunlar", value=(
        "`/kurulum <oyun> <kanal> <sıfırlamalı>`\n"
        "`/sifirla <oyun> <kanal>`\n"
        "`/fabrika_reset`\n"
        "`/oyna <oyun>`"
    ), inline=False)

    # Puan
    e.add_field(name="📊 Puan & Liderlik", value=(
        "`/puan`\n"
        "`/liderlik-tablosu`"
    ), inline=False)

    # Ekonomi
    e.add_field(name="💰 Ekonomi", value=(
        "`/gunluk`\n"
        "`/bakiye [kullanıcı]`\n"
        "`/market`\n"
        "`/satinal <ürün>`\n"
        "`/sat <id>`\n"
        "`/takas <kullanıcı> <senin item> <onun item>`\n"
        "`/gonder <kullanıcı> <id>`\n"
        "`/paraver <kullanıcı> <miktar>`\n"
        "`/envanter [kullanıcı]`\n"
        "`/urun-ekle <id> <fiyat> <isim> <açıklama>`\n"
        "`/market_ekle <id> <fiyat> <isim>|<açıklama>`\n"
        "`/market_sil <id>`"
    ), inline=False)

    # Moderasyon
    e.add_field(name="🔧 Moderasyon", value=(
        "`/ban <kullanıcı> [sebep]`\n"
        "`/kick <kullanıcı> [sebep]`\n"
        "`/mute <kullanıcı> [dk]`\n"
        "`/otoyanit <tetik> <cevap> [mute]`\n"
        "`/otoyanitsil <id>`\n"
        "`/marketsil <id>`"
    ), inline=False)

    # Müzik
    e.add_field(name="🎵 Müzik", value="`/çal <YouTube linki>`", inline=False)

    # Diğer
    e.add_field(name="🤖 Diğer", value=(
        "`/ping`\n"
        "`/ai <metin>`\n"
        "`/credit`"
    ), inline=False)

    e.set_footer(text=f"Şu an: {act}")
    await ctx.send(embed=e)


@bot.command()
async def ping(ctx):
    latency = round(bot.latency * 1000)
    await ctx.send(f"Pong! 🏓 {latency}ms")

async def oyna_logic(ctx, oyun: str):
    gid = ctx.guild.id
    if gid not in guild_settings:
        return await ctx.send(embed=create_embed("⚠️ Hata","Önce kurulum yapmalısın.", discord.Color.red()))
    ayarlar = guild_settings[gid]
    key = oyun.lower()
    if key not in ayarlar:
        return await ctx.send(embed=create_embed("❌ Hata", f"{key} kurulmamış.", discord.Color.red()))
    if key == "boom":
        ayarlar["boom"]["aktif"] = True
        ayarlar["boom"]["son_sayi"] = 0
        msg = "Boom başladı"
    elif key == "say":
        ayarlar["say"]["aktif"] = True
        ayarlar["say"]["son_sayi"] = 0
        msg = "Say başladı"
    elif key == "kelime_bilmece":
        yeni = await fetch_word()
        ayarlar["kelime_bilmece"]["aktif"] = True
        ayarlar["kelime_bilmece"]["kelime"] = yeni
        msg = "Kelime Bilmece başladı"
        print(f"[{ctx.guild.name}] kelime_bilmece yeni kelime: {yeni}")
    elif key == "sayi":
        ayarlar["sayi"]["aktif"] = True
        ayarlar["sayi"]["sayi"] = random.randint(1,20)
        msg = "Sayı oyunu başladı"
        print(f"[{ctx.guild.name}] sayi yeni: {ayarlar['sayi']['sayi']}")
    elif key == "kelime_turetme":
        if "son_kelime" not in ayarlar["kelime_turetme"]:
            w = await fetch_word()
            ayarlar["kelime_turetme"]["son_kelime"] = w
            ayarlar["kelime_turetme"]["used"] = set([w])
            print(f"[{ctx.guild.name}] kelime_turetme ilk: {w}")
        ayarlar["kelime_turetme"]["aktif"] = True
        msg = f"Kelime Türetme başladı: {ayarlar['kelime_turetme']['son_kelime']}"
    else:
        msg = "Geçersiz oyun"
    await save_all()
    await ctx.send(embed=create_embed("🎲 Oyun Başladı", msg, discord.Color.purple()))

@bot.tree.command(name="kurulum", description="Belirtilen oyunu belirtilen kanala kurar (Yönetici)")
async def kurulum_slash(interaction: discord.Interaction, oyun: str, kanal: discord.TextChannel, sıfırlamalı: str):
    class Ctx:
        def __init__(self, interaction):
            self.guild = interaction.guild
            self.author = interaction.user
            async def s(embed=None):
                await interaction.response.send_message(embed=embed)
            self.send = s
    await kurulum_logic(Ctx(interaction), oyun, kanal, sıfırlamalı)

@bot.tree.command(name="sifirla", description="Belirtilen oyunu belirtilen kanaldan kaldırır (Yönetici)")
async def sifirla_slash(interaction: discord.Interaction, oyun: str, kanal: discord.TextChannel):
    class Ctx:
        def __init__(self, interaction):
            self.guild = interaction.guild
            self.author = interaction.user
            async def s(embed=None):
                await interaction.response.send_message(embed=embed)
            self.send = s
    await sifirla_logic(Ctx(interaction), oyun, kanal)
auto_replies = {}  # id -> {'trigger': ..., 'response': ..., 'mute': dakika}

@bot.command(name="otoyanit")
async def otoyanit_cmd(ctx, tetik: str, cevap: str, mute: int = None):
    reply_id = str(len(auto_replies) + 1)
    auto_replies[reply_id] = {'trigger': tetik, 'response': cevap, 'mute': mute}
    await ctx.send(f"Oto yanıt eklendi! ID: {reply_id}")

@bot.command(name="otoyanitsil")
async def otoyanitsil_cmd(ctx, reply_id: str):
    if reply_id in auto_replies:
        del auto_replies[reply_id]
        await ctx.send(f"Oto yanıt silindi! ID: {reply_id}")
    else:
        await ctx.send("Bu ID ile oto yanıt yok.")

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    for reply in auto_replies.values():
        if reply['trigger'] in message.content:
            cevap = reply['response']
            cevap = cevap.replace("UserName", message.author.mention)
            cevap = cevap.replace("User", message.author.display_name)
            await message.channel.send(cevap)
            # Mute özelliği
            if reply.get('mute'):
                mute_role = discord.utils.get(message.guild.roles, name="Muted")
                if not mute_role:
                    mute_role = await message.guild.create_role(name="Muted")
                    for channel in message.guild.channels:
                        await channel.set_permissions(mute_role, send_messages=False, speak=False)
                await message.author.add_roles(mute_role)
                await asyncio.sleep(reply['mute'] * 60)
                await message.author.remove_roles(mute_role)
            break
    await bot.process_commands(message)

# Slash versiyonu
@bot.tree.command(name="otoyanit", description="Otomatik yanıt ekle")
@app_commands.describe(tetik="Tetikleyici kelime", cevap="Verilecek cevap", mute="Susturma süresi (dk, opsiyonel)")
async def otoyanit_slash(interaction: discord.Interaction, tetik: str, cevap: str, mute: int = None):
    reply_id = str(len(auto_replies) + 1)
    auto_replies[reply_id] = {'trigger': tetik, 'response': cevap, 'mute': mute}
    await interaction.response.send_message(f"Oto yanıt eklendi! ID: {reply_id}")

@bot.tree.command(name="otoyanitsil", description="Otomatik yanıtı sil")
@app_commands.describe(reply_id="Yanıt ID")
async def otoyanitsil_slash(interaction: discord.Interaction, reply_id: str):
    if reply_id in auto_replies:
        del auto_replies[reply_id]
        await interaction.response.send_message(f"Oto yanıt silindi! ID: {reply_id}")
    else:
        await interaction.response.send_message("Bu ID ile oto yanıt yok.")
@bot.command(name="çal")
async def cal_cmd(ctx, url: str):
    if ctx.author.voice is None:
        return await ctx.send("Bir ses kanalında olmalısın!")
    channel = ctx.author.voice.channel
    if ctx.voice_client is None:
        await channel.connect()
    vc = ctx.voice_client

    ydl_opts = {'format': 'bestaudio', 'noplaylist': True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        audio_url = info['url']
    vc.stop()
    vc.play(discord.FFmpegPCMAudio(audio_url))
    await ctx.send(f"Şu an çalıyor: {info['title']}")

@bot.command(name="marketsil")
@commands.has_permissions(administrator=True)
async def marketsil_cmd(ctx, item_id: str):
    gid = str(ctx.guild.id)
    if gid not in market_data:
        return await ctx.send("Market yok.")
    for i, item in enumerate(market_data[gid]):
        if item["id"] == item_id:
            del market_data[gid][i]
            await save_all()
            return await ctx.send(f"{item['name']} marketten silindi.")
    await ctx.send("Ürün bulunamadı.")

@bot.tree.command(name="marketsil", description="Market ürününü sil (Yönetici)")
@app_commands.describe(item_id="Silinecek ürünün ID'si")
async def marketsil_slash(interaction: discord.Interaction, item_id: str):
    gid = str(interaction.guild.id)
    if gid not in market_data:
        return await interaction.response.send_message("Market yok.")
    for i, item in enumerate(market_data[gid]):
        if item["id"] == item_id:
            del market_data[gid][i]
            await save_all()
            return await interaction.response.send_message(f"{item['name']} marketten silindi.")
    await interaction.response.send_message("Ürün bulunamadı.")

@bot.tree.command(name="çal", description="Bir YouTube linki çal")
@app_commands.describe(url="YouTube video linki")
async def cal_slash(interaction: discord.Interaction, url: str):
    if interaction.user.voice is None:
        return await interaction.response.send_message("Bir ses kanalında olmalısın!")

    channel = interaction.user.voice.channel
    if interaction.guild.voice_client is None:
        await channel.connect()
    vc = interaction.guild.voice_client

    # İlk embed: yükleniyor
    embed_loading = discord.Embed(
        title="🎵 Müziğiniz yükleniyor...",
        description="Lütfen bekleyin...",
        color=discord.Color.orange()
    )
    embed_loading.set_thumbnail(url="https://cdn.discordapp.com/emojis/1398733526886514849.gif?size=44&quality=lossless")
    msg = await interaction.response.send_message(embed=embed_loading)
    msg = await interaction.original_response()

    # yt_dlp ile bilgi çek
    ydl_opts = {'format': 'bestaudio', 'noplaylist': True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        audio_url = info['url']
        title = info.get("title", "Bilinmeyen Başlık")
        duration = info.get("duration", 0)  # saniye

    # Çalmaya başla
    vc.stop()
    vc.play(discord.FFmpegPCMAudio(audio_url))

    # Embed güncelle
    embed_playing = discord.Embed(
        title="✅ Şarkı Çalıyor",
        description=f"**{title}**",
        color=discord.Color.green()
    )
    if "thumbnail" in info:
        embed_playing.set_thumbnail(url=info["thumbnail"])
    embed_playing.add_field(name="Süre", value=f"{duration//60}:{duration%60:02d}", inline=True)
    await msg.edit(embed=embed_playing)

    # Kullanıcı çıkarsa DM gönder
    def check(member, before, after):
        return member == interaction.user and before.channel is not None and after.channel is None

    try:
        await bot.wait_for("voice_state_update", check=lambda m, b, a: check(m, b, a), timeout=duration+10)
        # DM gönder
        elapsed = vc.source.read() if hasattr(vc.source, "read") else 0
        embed_dm = discord.Embed(
            title="🎶 Dinleme Bilgisi",
            description=f"**{title}** çalmayı bıraktı.",
            color=discord.Color.blue()
        )
        embed_dm.add_field(name="Toplam Süre", value=f"{duration//60}:{duration%60:02d}", inline=True)
        # Çalınan süreyi tam hesaplamak zor, o yüzden yaklaşık süre
        embed_dm.add_field(name="Çalınan Süre", value="Tahmini: Kanalda olduğun süre", inline=True)
        await interaction.user.send(embed=embed_dm)
    except asyncio.TimeoutError:
        pass


@bot.tree.command(name="fabrika_reset", description="Tüm sunucu ayarlarını sıfırlar (Yönetici)")
async def fabrika_reset_slash(interaction: discord.Interaction):
    class Ctx:
        def __init__(self, interaction):
            self.guild = interaction.guild
            self.author = interaction.user
            async def s(embed=None):
                await interaction.response.send_message(embed=embed)
            self.send = s
    await fabrika_reset_logic(Ctx(interaction))

@bot.tree.command(name="help", description="Yardım menüsünü gösterir")
async def help_slash(interaction: discord.Interaction):
    class Ctx:
        def __init__(self, interaction):
            self.guild = interaction.guild
            self.author = interaction.user
            async def s(embed=None):
                await interaction.response.send_message(embed=embed)
            self.send = s
    await help_logic(Ctx(interaction))

@bot.tree.command(name="oyna", description="Bir oyun başlatır: boom, say, kelime_bilmece, sayi, kelime_turetme")
async def oyna_slash(interaction: discord.Interaction, oyun: str):
    class Ctx:
        def __init__(self, interaction):
            self.guild = interaction.guild
            self.author = interaction.user
            async def s(embed=None):
                await interaction.response.send_message(embed=embed)
            self.send = s
    await oyna_logic(Ctx(interaction), oyun)

@bot.command()
@commands.has_permissions(administrator=True)
async def kurulum(ctx, oyun: str, kanal: discord.TextChannel, sıfırlamalı: str):
    await kurulum_logic(ctx, oyun, kanal, sıfırlamalı)

@bot.command()
@commands.has_permissions(administrator=True)
async def sifirla(ctx, oyun: str, kanal: discord.TextChannel):
    await sifirla_logic(ctx, oyun, kanal)
# Market yönetimi için yeni komutlar ekleyelim
@bot.command()
@commands.has_permissions(administrator=True)
async def market_ekle(ctx, item_id: str, fiyat: int, *, isim_ve_aciklama: str):
    """Markete yeni ürün ekler"""
    try:
        isim, aciklama = isim_ve_aciklama.split('|')
    except:
        return await ctx.send("❌ Format: !market_ekle <id> <fiyat> <isim>|<açıklama>")

    gid = str(ctx.guild.id)
    if gid not in market_data:
        market_data[gid] = default_items.copy()
    
    # Aynı ID'li ürün var mı kontrol
    for item in market_data[gid]:
        if item["id"] == item_id:
            return await ctx.send("❌ Bu ID'li ürün zaten var!")
    
    yeni_item = {
        "id": item_id,
        "name": isim.strip(),
        "price": fiyat,
        "desc": aciklama.strip()
    }
    
    market_data[gid].append(yeni_item)
    await save_all()
    await ctx.send(f"✅ Yeni ürün eklendi: {isim}")

@bot.command()
@commands.has_permissions(administrator=True) 
async def market_sil(ctx, item_id: str):
    """Marketten ürün siler"""
    gid = str(ctx.guild.id)
    if gid not in market_data:
        return await ctx.send("❌ Bu sunucuda market kurulu değil!")
        
    for i, item in enumerate(market_data[gid]):
        if item["id"] == item_id:
            del market_data[gid][i]
            await save_all()
            return await ctx.send(f"✅ Ürün silindi: {item['name']}")
            
    await ctx.send("❌ Bu ID'li ürün bulunamadı!")

# Market gösterme komutunu güncelle
@bot.command(name="market")
async def market_cmd(ctx):
    gid = str(ctx.guild.id)
    if gid not in market_data:
        market_data[gid] = default_items.copy()
        
    items = market_data[gid]
    if not items:
        return await ctx.send("❌ Market boş!")
        
    embed = discord.Embed(title="🏪 Market", color=discord.Color.blue())
    for item in items:
        embed.add_field(
            name=f"{item['name']} - {item['price']} ACoin",
            value=f"ID: {item['id']}\n{item['desc']}",
            inline=False
        )
    await ctx.send(embed=embed)

# find_market_item fonksiyonunu güncelle
def find_market_item(guild_id, query):
    """Markette ürün arar"""
    gid = str(guild_id)
    if gid not in market_data:
        market_data[gid] = default_items.copy()
        
    q = str(query).lower()
    for item in market_data[gid]:
        if item["id"].lower() == q or item["name"].lower() == q:
            return item
    return None
@bot.command()
@commands.has_permissions(administrator=True)
async def fabrika_reset(ctx):
    await fabrika_reset_logic(ctx)

@bot.command()
async def help(ctx):
    await help_logic(ctx)

@bot.command()
async def oyna(ctx, oyun: str):
    await oyna_logic(ctx, oyun)

def add_points(user_id, amount):
    uid = str(user_id)
    user_points.setdefault(uid, 0)
    user_points[uid] += amount

def get_points(user_id):
    return user_points.get(str(user_id), 0)
# --------------- Economy helpers ---------------
def ensure_account(gid, user_id):
    gid = str(gid)
    uid = str(user_id)
    if gid not in economy_data:
        economy_data[gid] = {"users": {}, "market": {}}
    if uid not in economy_data[gid]["users"]:
        economy_data[gid]["users"][uid] = {"balance": 0, "inventory": [], "last_daily": 0}
    return economy_data[gid]["users"][uid]

# Economy helpers düzeltmeleri
def get_coins(gid, user_id):
    """Kullanıcının coin miktarını döndürür"""
    uid = str(user_id)
    account = ensure_account(gid, uid)
    return account.get("balance", 0)

def add_coins(gid, user_id, amount):
    """Kullanıcıya coin ekler"""
    uid = str(user_id)
    account = ensure_account(gid, uid)
    account["balance"] += amount
    
def deduct_coins(gid, user_id, amount):
    """Kullanıcıdan coin düşer"""
    uid = str(user_id)
    account = ensure_account(gid, uid)
    if account["balance"] < amount:
        return False
    account["balance"] -= amount
    return True

# Envanter işlemleri için fonksiyonları düzelt
def get_inventory(gid, user_id):
    """Kullanıcının envanterini döndürür"""
    uid = str(user_id)
    account = ensure_account(gid, uid)
    return account.get("inventory", [])

def add_item_to_user(gid, user_id, item_id):
    """Kullanıcının envanterine ürün ekler"""
    uid = str(user_id)
    account = ensure_account(gid, uid)
    if "inventory" not in account:
        account["inventory"] = []
    account["inventory"].append(item_id)

# Market item bulma fonksiyonunu düzelt
def find_market_item(guild_id, query):
    """Markette ürün arar"""
    gid = str(guild_id)
    if gid not in market_data:
        market_data[gid] = default_items.copy()
        
    q = str(query).lower()
    for item in market_data[gid]:
        if item["id"].lower() == q or item["name"].lower() == q:
            return item
    return None

@bot.tree.command(name="puan", description="Puanını gösterir")
async def puan_slash(interaction: discord.Interaction):
    p = get_points(interaction.user.id)
    await interaction.response.send_message(f"🏆 Puanın: {p}")
# ---------------- Economy commands ----------------

# GÜNLÜK (prefix)
@bot.command(name="gunluk")
async def gunluk_cmd(ctx):
    uid = str(ctx.author.id)
    acc = ensure_account(uid)
    now = int(time.time())
    last = int(acc.get("last_daily", 0))
    if now - last < 86400:
        rem = 86400 - (now - last)
        hrs = rem // 3600
        mins = (rem % 3600) // 60
        await ctx.send(embed=create_embed("⏳ Zaten aldın", f"{ctx.author.mention} günlük ödülünü zaten almışsın.\nKalan: {hrs} saat {mins} dakika", discord.Color.orange()))
        return
    add_coins(uid, 100)
    economy_data[uid]["last_daily"] = now
    await save_all()
    await ctx.send(embed=create_embed("🎁 Günlük Ödül", f"{ctx.author.mention} +100 ACoin! Şu bakiye: {get_coins(uid)} ACoin", discord.Color.green()))
# Günlük komutunu düzeltme 
@bot.tree.command(name="gunluk", description="Günlük ACoin al")
async def gunluk_slash(interaction: discord.Interaction):
    gid = interaction.guild.id
    uid = interaction.user.id
    acc = ensure_account(gid, uid)
    now = int(time.time())
    last = int(acc.get("last_daily", 0))
    
    if now - last < 86400:
        rem = 86400 - (now - last)
        hrs = rem // 3600
        mins = (rem % 3600) // 60
        await interaction.response.send_message(
            embed=create_embed("⏳ Zaten aldın", 
            f"{interaction.user.mention} günlük ödülünü zaten almışsın.\nKalan: {hrs} saat {mins} dakika", 
            discord.Color.orange())
        )
        return
        
    add_coins(gid, uid, 100)
    acc["last_daily"] = now
    await save_all()
    await interaction.response.send_message(
        embed=create_embed("🎁 Günlük Ödül", 
        f"{interaction.user.mention} +100 ACoin! Şu bakiye: {get_coins(gid, uid)} ACoin",
        discord.Color.green())
    )

# BAKİYE (prefix)
@bot.command(name="bakiye")
async def bakiye_cmd(ctx, member: discord.Member = None):
    member = member or ctx.author
    bal = get_coins(member.id)
    inv = get_inventory(member.id)
    e = create_embed(f"💰 {member.display_name} - Bakiye", f"**{bal} ACoin**", discord.Color.blue())
    e.add_field(name="Envanter", value=", ".join(inv[:20]) if inv else "Boş", inline=False)
    await ctx.send(embed=e)
# Market slash command ekleme
@bot.tree.command(name="market", description="Marketteki ürünleri gösterir")
async def market_slash(interaction: discord.Interaction):
    gid = str(interaction.guild.id)
    if gid not in market_data:
        market_data[gid] = default_items.copy()
        
    items = market_data[gid]
    if not items:
        return await interaction.response.send_message("❌ Market boş!")
        
    embed = discord.Embed(title="🏪 Market", color=discord.Color.blue())
    for item in items:
        embed.add_field(
            name=f"{item['name']} - {item['price']} ACoin",
            value=f"ID: {item['id']}\n{item['desc']}",
            inline=False
        )
    await interaction.response.send_message(embed=embed)

# Bakiye slash komutunu düzelt
@bot.tree.command(name="bakiye", description="Bir kullanıcının ACoin bakiyesini gösterir")
async def bakiye_slash(interaction: discord.Interaction, kullanici: discord.Member = None):
    user = kullanici or interaction.user
    gid = interaction.guild.id
    bal = get_coins(gid, user.id)
    inv = get_inventory(gid, user.id)  # guild_id eklendi
    e = create_embed(f"💰 {user.display_name} - Bakiye", f"**{bal} ACoin**", discord.Color.blue())
    e.add_field(name="Envanter", value=", ".join(inv[:20]) if inv else "Boş", inline=False)
    await interaction.response.send_message(embed=e)


@bot.command(name="satinal")
async def satinal_cmd(ctx, *, item_query: str):
    gid = ctx.guild.id
    item = find_market_item(gid, item_query)
    if not item:
        await ctx.send(embed=create_embed("❌ Hata", f"Ürün bulunamadı: {item_query}", discord.Color.red()))
        return
    price = int(item['price'])
    if get_coins(gid, ctx.author.id) < price:
        await ctx.send(embed=create_embed("❌ Yetersiz bakiye", f"Bu ürün {price} ACoin. Bakiye: {get_coins(gid, ctx.author.id)}", discord.Color.red()))
        return
    deduct_coins(gid, ctx.author.id, price)
    add_item_to_user(gid, ctx.author.id, item['id'])
    await save_all()
    await ctx.send(embed=create_embed("✅ Satın alındı", f"{ctx.author.mention} başarıyla **{item['name']}** aldı. Kalan bakiye: {get_coins(gid, ctx.author.id)} ACoin", discord.Color.green()))








# 1. Market Ürünlerini Satma (envanterden sat)
@bot.command(name="sat")
async def sat_cmd(ctx, item_id: str):
    gid = ctx.guild.id
    uid = ctx.author.id
    inv = get_inventory(gid, uid)
    if item_id not in inv:
        return await ctx.send(embed=create_embed("❌ Hata", "Bu ürüne sahip değilsin.", discord.Color.red()))
    item = find_market_item(gid, item_id)
    if not item:
        return await ctx.send(embed=create_embed("❌ Hata", "Ürün markette bulunamadı.", discord.Color.red()))
    inv.remove(item_id)
    add_coins(gid, uid, int(item["price"] // 2))  # Yarı fiyatına sat
    await save_all()
    await ctx.send(embed=create_embed("✅ Satıldı", f"{item['name']} satıldı. {item['price']//2} ACoin kazandın.", discord.Color.green()))

# 2. Kullanıcılar Arası Takas (envanterden item takası)
@bot.command(name="takas")
async def takas_cmd(ctx, alici: discord.Member, kendi_item: str, alici_item: str):
    gid = ctx.guild.id
    veren_id = ctx.author.id
    alan_id = alici.id

    veren_inv = get_inventory(gid, veren_id)
    alan_inv = get_inventory(gid, alan_id)

    if kendi_item not in veren_inv:
        return await ctx.send(embed=create_embed("❌ Hata", "Kendi envanterinde bu ürün yok.", discord.Color.red()))
    if alici_item not in alan_inv:
        return await ctx.send(embed=create_embed("❌ Hata", f"{alici.display_name} envanterinde bu ürün yok.", discord.Color.red()))

    # Takas işlemi
    veren_inv.remove(kendi_item)
    alan_inv.remove(alici_item)
    veren_inv.append(alici_item)
    alan_inv.append(kendi_item)
    await save_all()
    await ctx.send(embed=create_embed("🔄 Takas Başarılı", f"{ctx.author.mention} ↔️ {alici.mention}\n"
        f"{ctx.author.display_name}: {kendi_item} ➡️ {alici.display_name}\n"
        f"{alici.display_name}: {alici_item} ➡️ {ctx.author.display_name}", discord.Color.purple()))

# 3. Bir Kişiye Ürün Gönderme (envanterden)
@bot.command(name="gonder")
async def gonder_cmd(ctx, alici: discord.Member, item_id: str):
    gid = ctx.guild.id
    veren_id = ctx.author.id
    alan_id = alici.id

    if veren_id == alan_id:
        return await ctx.send(embed=create_embed("❌ Hata", "Kendine ürün gönderemezsin.", discord.Color.red()))

    veren_inv = get_inventory(gid, veren_id)
    alan_inv = get_inventory(gid, alan_id)

    if item_id not in veren_inv:
        return await ctx.send(embed=create_embed("❌ Hata", "Bu ürüne sahip değilsin.", discord.Color.red()))

    veren_inv.remove(item_id)
    alan_inv.append(item_id)
    await save_all()
    await ctx.send(embed=create_embed("🎁 Ürün Gönderildi", f"{ctx.author.mention} → {alici.mention}: {item_id}", discord.Color.orange()))
@bot.tree.command(name="satinal", description="Marketten ürün satın al")
async def satinal_slash(interaction: discord.Interaction, urun: str):
    gid = interaction.guild.id
    item = find_market_item(gid, urun)
    if not item:
        await interaction.response.send_message(embed=create_embed("❌ Hata", f"Ürün bulunamadı: {urun}", discord.Color.red()))
        return
    price = int(item['price'])
    if get_coins(gid, interaction.user.id) < price:
        await interaction.response.send_message(embed=create_embed("❌ Yetersiz bakiye", f"Bu ürün {price} ACoin. Bakiye: {get_coins(gid, interaction.user.id)}", discord.Color.red()))
        return
    deduct_coins(gid, interaction.user.id, price)
    add_item_to_user(gid, interaction.user.id, item['id'])
    await save_all()
    await interaction.response.send_message(embed=create_embed("✅ Satın alındı", f"{interaction.user.mention} başarıyla **{item['name']}** aldı. Kalan bakiye: {get_coins(gid, interaction.user.id)} ACoin", discord.Color.green()))
@bot.tree.command(name="sat", description="Envanterindeki bir ürünü sat (yarı fiyatına)")
@app_commands.describe(item_id="Satmak istediğin ürünün ID'si")
async def sat_slash(interaction: discord.Interaction, item_id: str):
    gid = interaction.guild.id
    uid = interaction.user.id
    inv = get_inventory(gid, uid)
    if item_id not in inv:
        return await interaction.response.send_message(embed=create_embed("❌ Hata", "Bu ürüne sahip değilsin.", discord.Color.red()))
    item = find_market_item(gid, item_id)
    if not item:
        return await interaction.response.send_message(embed=create_embed("❌ Hata", "Ürün markette bulunamadı.", discord.Color.red()))
    inv.remove(item_id)
    add_coins(gid, uid, int(item["price"] // 2))
    await save_all()
    await interaction.response.send_message(embed=create_embed("✅ Satıldı", f"{item['name']} satıldı. {item['price']//2} ACoin kazandın.", discord.Color.green()))

@bot.tree.command(name="takas", description="Bir kullanıcıyla envanterden ürün takası yap")
@app_commands.describe(alici="Takas yapılacak kullanıcı", kendi_item="Senin vereceğin ürünün ID'si", alici_item="Alacağın ürünün ID'si")
async def takas_slash(interaction: discord.Interaction, alici: discord.Member, kendi_item: str, alici_item: str):
    gid = interaction.guild.id
    veren_id = interaction.user.id
    alan_id = alici.id

    veren_inv = get_inventory(gid, veren_id)
    alan_inv = get_inventory(gid, alan_id)

    if kendi_item not in veren_inv:
        return await interaction.response.send_message(embed=create_embed("❌ Hata", "Kendi envanterinde bu ürün yok.", discord.Color.red()))
    if alici_item not in alan_inv:
        return await interaction.response.send_message(embed=create_embed("❌ Hata", f"{alici.display_name} envanterinde bu ürün yok.", discord.Color.red()))

    veren_inv.remove(kendi_item)
    alan_inv.remove(alici_item)
    veren_inv.append(alici_item)
    alan_inv.append(kendi_item)
    await save_all()
    await interaction.response.send_message(embed=create_embed("🔄 Takas Başarılı", f"{interaction.user.mention} ↔️ {alici.mention}\n"
        f"{interaction.user.display_name}: {kendi_item} ➡️ {alici.display_name}\n"
        f"{alici.display_name}: {alici_item} ➡️ {interaction.user.display_name}", discord.Color.purple()))

@bot.tree.command(name="gonder", description="Bir kullanıcıya envanterinden ürün gönder")
@app_commands.describe(alici="Ürünü göndereceğin kullanıcı", item_id="Göndermek istediğin ürünün ID'si")
async def gonder_slash(interaction: discord.Interaction, alici: discord.Member, item_id: str):
    gid = interaction.guild.id
    veren_id = interaction.user.id
    alan_id = alici.id

    if veren_id == alan_id:
        return await interaction.response.send_message(embed=create_embed("❌ Hata", "Kendine ürün gönderemezsin.", discord.Color.red()))

    veren_inv = get_inventory(gid, veren_id)
    alan_inv = get_inventory(gid, alan_id)

    if item_id not in veren_inv:
        return await interaction.response.send_message(embed=create_embed("❌ Hata", "Bu ürüne sahip değilsin.", discord.Color.red()))

    veren_inv.remove(item_id)
    alan_inv.append(item_id)
    await save_all()
    await interaction.response.send_message(embed=create_embed("🎁 Ürün Gönderildi", f"{interaction.user.mention} → {alici.mention}: {item_id}", discord.Color.orange()))
# TAKAS / GÖNDER (prefix)
@bot.command(name="paraver")
async def takas_cmd(ctx, member: discord.Member, miktar: int):
    if miktar <= 0:
        return await ctx.send(embed=create_embed("❌ Hata", "Miktar pozitif olmalı.", discord.Color.red()))
    if get_coins(ctx.author.id) < miktar:
        return await ctx.send(embed=create_embed("❌ Yetersiz bakiye", f"{ctx.author.mention} bakiye yetersiz.", discord.Color.red()))
    deduct_coins(ctx.author.id, miktar)
    add_coins(member.id, miktar)
    await save_all()
    await ctx.send(embed=create_embed("✅ Başarılı", f"{ctx.author.mention} {member.mention} kullanıcısına {miktar} ACoin gönderdi.", discord.Color.green()))

# Ban
@bot.command(name="ban")
@commands.has_permissions(ban_members=True)
async def ban_cmd(ctx, member: discord.Member, *, reason="Sebep belirtilmedi"):
    await member.ban(reason=reason)
    await ctx.send(f"{member.mention} sunucudan banlandı. Sebep: {reason}")

@bot.tree.command(name="ban", description="Bir kullanıcıyı sunucudan banlar")
@app_commands.describe(member="Banlanacak kullanıcı", reason="Sebep")
async def ban_slash(interaction: discord.Interaction, member: discord.Member, reason: str = "Sebep belirtilmedi"):
    await member.ban(reason=reason)
    await interaction.response.send_message(f"{member.mention} sunucudan banlandı. Sebep: {reason}")

# Kick
@bot.command(name="kick")
@commands.has_permissions(kick_members=True)
async def kick_cmd(ctx, member: discord.Member, *, reason="Sebep belirtilmedi"):
    await member.kick(reason=reason)
    await ctx.send(f"{member.mention} sunucudan atıldı. Sebep: {reason}")

@bot.tree.command(name="kick", description="Bir kullanıcıyı sunucudan atar")
@app_commands.describe(member="Atılacak kullanıcı", reason="Sebep")
async def kick_slash(interaction: discord.Interaction, member: discord.Member, reason: str = "Sebep belirtilmedi"):
    await member.kick(reason=reason)
    await interaction.response.send_message(f"{member.mention} sunucudan atıldı. Sebep: {reason}")

# Mute (rol ile)
@bot.command(name="mute")
@commands.has_permissions(manage_roles=True)
async def mute_cmd(ctx, member: discord.Member, dakika: int = 5):
    mute_role = discord.utils.get(ctx.guild.roles, name="Muted")
    if not mute_role:
        mute_role = await ctx.guild.create_role(name="Muted")
        for channel in ctx.guild.channels:
            await channel.set_permissions(mute_role, send_messages=False, speak=False)
    await member.add_roles(mute_role)
    await ctx.send(f"{member.mention} {dakika} dakika susturuldu.")
    await asyncio.sleep(dakika * 60)
    await member.remove_roles(mute_role)
    await ctx.send(f"{member.mention} susturulması kaldırıldı.")


@bot.tree.command(name="mute", description="Bir kullanıcıyı susturur")
@app_commands.describe(member="Susturulacak kullanıcı", dakika="Kaç dakika susturulacak")
async def mute_slash(interaction: discord.Interaction, member: discord.Member, dakika: int = 5):
    mute_role = discord.utils.get(interaction.guild.roles, name="Muted")
    if not mute_role:
        mute_role = await interaction.guild.create_role(name="Muted")
        for channel in interaction.guild.channels:
            await channel.set_permissions(mute_role, send_messages=False, speak=False)
    await member.add_roles(mute_role)
    await interaction.response.send_message(f"{member.mention} {dakika} dakika susturuldu.")
    await asyncio.sleep(dakika * 60)
    await member.remove_roles(mute_role)
    await interaction.followup.send(f"{member.mention} susturulması kaldırıldı.")

# TAKAS (slash)
@bot.tree.command(name="paraver", description="Başka bir kullanıcıya ACoin gönder")
async def takas_slash(interaction: discord.Interaction, kullanici: discord.Member, miktar: int):
    if miktar <= 0:
        return await interaction.response.send_message(embed=create_embed("❌ Hata", "Miktar pozitif olmalı.", discord.Color.red()))
    if get_coins(interaction.user.id) < miktar:
        return await interaction.response.send_message(embed=create_embed("❌ Yetersiz bakiye", f"{interaction.user.mention} bakiye yetersiz.", discord.Color.red()))
    deduct_coins(interaction.user.id, miktar)
    add_coins(kullanici.id, miktar)
    await save_all()
    await interaction.response.send_message(embed=create_embed("✅ Başarılı", f"{interaction.user.mention} {kullanici.mention} kullanıcısına {miktar} ACoin gönderdi.", discord.Color.green()))


@bot.command(name="envanter")
async def envanter_cmd(ctx, member: discord.Member = None):
    member = member or ctx.author
    gid = ctx.guild.id
    inv = get_inventory(gid, member.id)
    if not inv:
        return await ctx.send(embed=create_embed("🎒 Envanter", f"{member.mention} envanteri boş.", discord.Color.blue()))
    lines = []
    for i,it in enumerate(inv,1):
        item = find_market_item(gid, it) or {"name":it, "id":it}
        lines.append(f"{i}. {item.get('name')} ({item.get('id')})")
    await ctx.send(embed=create_embed(f"🎒 {member.display_name} Envanteri", "\n".join(lines), discord.Color.blue()))

@bot.tree.command(name="envanter", description="Kullanıcının envanterini gösterir")
async def envanter_slash(interaction: discord.Interaction, kullanici: discord.Member = None):
    user = kullanici or interaction.user
    gid = interaction.guild.id  # <-- eksikti, ekle
    inv = get_inventory(gid, user.id)  # <-- düzeltildi
    if not inv:
        return await interaction.response.send_message(embed=create_embed("🎒 Envanter", f"{user.mention} envanteri boş.", discord.Color.blue()))
    lines = []
    for i,it in enumerate(inv,1):
        item = find_market_item(gid, it) or {"name":it, "id":it}  # <-- find_market_item da düzeltildi
        lines.append(f"{i}. {item.get('name')} ({item.get('id')})")
    await interaction.response.send_message(embed=create_embed(f"🎒 {user.display_name} Envanteri", "\n".join(lines), discord.Color.blue()))
@bot.command(name="urun-ekle")
@commands.has_permissions(administrator=True)
async def urun_ekle_cmd(ctx, urun_id: str, fiyat: int, isim: str, *, aciklama: str = ""):
    if find_market_item(urun_id):
        return await ctx.send(embed=create_embed("❌ Hata", "Bu id zaten var.", discord.Color.red()))
    market_data.append({"id": urun_id.lower(), "name": isim, "price": fiyat, "desc": aciklama})
    await save_all()
    await ctx.send(embed=create_embed("✅ Ürün eklendi", f"{isim} ({urun_id}) başarıyla eklendi.", discord.Color.green()))

# Ürün ekleme komutunu düzelt
@bot.tree.command(name="urun-ekle", description="Market'e ürün ekle (Yönetici)")
@app_commands.describe(urun_id="Ürün id'si", fiyat="Fiyat", isim="Görünen isim", aciklama="Açıklama")
async def urun_ekle_slash(interaction: discord.Interaction, urun_id: str, fiyat: int, isim: str, aciklama: str = ""):
    if not interaction.user.guild_permissions.administrator:
        return await interaction.response.send_message(embed=create_embed("⛔ Yetki Hatası","Bu komutu sadece yöneticiler kullanabilir.", discord.Color.red()))
    
    gid = str(interaction.guild.id)
    if gid not in market_data:
        market_data[gid] = default_items.copy()
        
    if find_market_item(interaction.guild.id, urun_id):  # guild_id eklendi
        return await interaction.response.send_message(embed=create_embed("❌ Hata", "Bu id zaten var.", discord.Color.red()))
        
    market_data[gid].append({
        "id": urun_id.lower(),
        "name": isim,
        "price": fiyat,
        "desc": aciklama
    })
    await save_all()
    await interaction.response.send_message(embed=create_embed("✅ Ürün eklendi", f"{isim} ({urun_id}) başarıyla eklendi.", discord.Color.green()))
    
@bot.command()
async def puan(ctx):
    p = get_points(ctx.author.id)
    await ctx.send(f"🏆 Puanın: {p}")

@bot.tree.command(name="liderlik-tablosu", description="Liderlik tablosunu gösterir")
async def lider_slash(interaction: discord.Interaction):
    items = sorted(user_points.items(), key=lambda x: x[1], reverse=True)[:10]
    e = create_embed("🏆 Liderlik Tablosu", "", discord.Color.gold())
    rank = 1
    for uid, score in items:
        try:
            user = await bot.fetch_user(int(uid))
            name = f"{user.name}#{user.discriminator}"
        except:
            name = f"U:{uid}"
        e.add_field(name=f"{rank}. {name}", value=f"{score} puan", inline=False)
        rank += 1
    await interaction.response.send_message(embed=e)

@bot.command(name="liderlik-tablosu")
async def lider_cmd(ctx):
    items = sorted(user_points.items(), key=lambda x: x[1], reverse=True)[:10]
    e = create_embed("🏆 Liderlik Tablosu", "", discord.Color.gold())
    rank = 1
    for uid, score in items:
        try:
            user = await bot.fetch_user(int(uid))
            name = f"{user.name}#{user.discriminator}"
        except:
            name = f"U:{uid}"
        e.add_field(name=f"{rank}. {name}", value=f"{score} puan", inline=False)
        rank += 1
    await ctx.send(embed=e)

# ----------------- Credit -----------------
@bot.tree.command(name="credit", description="Bot credit bilgisi")
async def credit(interaction: discord.Interaction):
    guild_name = interaction.guild.name if interaction.guild else "Bilinmeyen Sunucu"
    embed = discord.Embed(title="Bot Credit", color=discord.Color.blue())
    embed.add_field(name="Bot İsmi", value="**ThunderBot**", inline=False)
    embed.add_field(name="Sunucu Adı", value=f"{guild_name}", inline=False)
    embed.add_field(name="Geliştiren Kişi", value="neighboth", inline=False)  # buraya senin ismin
    embed.add_field(name="Geliştirici Sunucu", value="[Discord Sunucusu](https://discord.gg/TWF9qc3576)", inline=False)
    embed.add_field(name="Telif Hakkı", value="*© 2025 ThunderBot. Tüm hakları saklıdır.*", inline=False)
    await interaction.response.send_message(embed=embed)

@bot.command(name="credit")
async def credit_prefix(ctx):
    guild_name = ctx.guild.name if ctx.guild else "Bilinmeyen Sunucu"
    embed = discord.Embed(title="Bot Credit", color=discord.Color.blue())
    embed.add_field(name="Bot İsmi", value="**ThunderBot**", inline=False)
    embed.add_field(name="Sunucu Adı", value=f"{guild_name}", inline=False)
    embed.add_field(name="Geliştiren Kişi", value="neighboth", inline=False)  # buraya senin ismin
    embed.add_field(name="Geliştirici Sunucu", value="[Discord Sunucusu](https://discord.gg/TWF9qc3576)", inline=False)
    embed.add_field(name="Telif Hakkı", value="*© 2025 ThunderBot. Tüm hakları saklıdır.*", inline=False)
    await ctx.send(embed=embed)

@bot.tree.command(name="ping", description="Botun pingini gösterir")
async def ping(interaction: discord.Interaction):
    latency = round(bot.latency * 1000)  # ms cinsinden
    await interaction.response.send_message(f"Pong! 🏓 {latency}ms")

@bot.tree.command(name="ai", description="AI cevabı al")
async def ai_slash(interaction: discord.Interaction, metin: str):
    url = f"https://text.pollinations.ai/{metin}"
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(url, timeout=10) as r:
                if r.status == 200:
                    text = await r.text()
                else:
                    text = f"Hata: {r.status}"
    except Exception as e:
        text = f"Hata: {e}"
    e = create_embed("AI Cevap", text, discord.Color.green())
    await interaction.response.send_message(embed=e)

@bot.command()
async def ai(ctx, *, metin: str):
    url = f"https://text.pollinations.ai/{metin}"
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(url, timeout=10) as r:
                if r.status == 200:
                    text = await r.text()
                else:
                    text = f"Hata: {r.status}"
    except Exception as e:
        text = f"Hata: {e}"
    e = create_embed("AI Cevap", text, discord.Color.green())
    await ctx.send(embed=e)
@bot.event
async def on_message(message: discord.Message):
    if message.author.bot or not message.guild:
        return await bot.process_commands(message)

    gid = message.guild.id
    if gid not in guild_settings:
        return await bot.process_commands(message)

    ayarlar = guild_settings[gid]

    for key, settings in list(ayarlar.items()):
        if message.channel.id != settings.get("kanal_id"):
            continue
        if not settings.get("aktif", False):
            continue

        sifir = settings.get("sıfırlamalı", "evet")

        # BOOM
        if key == "boom":
            content = message.content.strip()
            try:
                num = int(content)
                expected = settings.get("son_sayi", 0) + 1
                if num == expected and expected % 5 != 0:
                    settings["son_sayi"] = num
                    await save_all()
                    try:
                        await message.add_reaction("✅")
                    except:
                        pass
                else:
                    try:
                        await message.add_reaction("❌")
                    except:
                        pass
                    if sifir == "evet":
                        settings["son_sayi"] = 0
                        await save_all()
                        await message.channel.send(embed=create_embed("❌ Yanlış!", f"{message.author.mention} yanlış yazdı! Oyun sıfırlandı! Beklenen: {expected if expected%5!=0 else 'Boom'}", discord.Color.red()))
                    else:
                        await message.channel.send(embed=create_embed("⚠️ Yanlış ama devam", f"{message.author.mention} yanlış yazdı! Beklenen: {expected if expected%5!=0 else 'Boom'} (Sıfırlama kapalı)", discord.Color.orange()))

            except ValueError:
                if content.lower() == "boom":
                    expected = settings.get("son_sayi", 0) + 1
                    if expected % 5 == 0:
                        settings["son_sayi"] = expected
                        await save_all()
                        try:
                            await message.add_reaction("✅")
                        except:
                            pass
                    else:
                        try:
                            await message.add_reaction("❌")
                        except:
                            pass
                        if sifir == "evet":
                            settings["son_sayi"] = 0
                            await save_all()
                            await message.channel.send(embed=create_embed("❌ Yanlış Boom!", f"{message.author.mention} oyun sıfırlandı!", discord.Color.red()))
                        else:
                            await message.channel.send(embed=create_embed("⚠️ Yanlış Boom!", f"{message.author.mention} yanlış 'Boom' yazdı! (Sıfırlama kapalı)", discord.Color.orange()))

        # SAY
        elif key == "say":
            content = message.content.strip()
            if content.isdigit():
                num = int(content)
                expected = settings.get("son_sayi", 0) + 1
                if num == expected:
                    settings["son_sayi"] = num
                    await save_all()
                    try:
                        await message.add_reaction("✅")
                    except:
                        pass
                else:
                    try:
                        await message.add_reaction("❌")
                    except:
                        pass
                    if sifir == "evet":
                        settings["son_sayi"] = 0
                        await save_all()
                        await message.channel.send(embed=create_embed("❌ Yanlış Sayı!", f"{message.author.mention} oyun sıfırlandı! Beklenen: {expected}", discord.Color.red()))
                    else:
                        await message.channel.send(embed=create_embed("⚠️ Yanlış Sayı!", f"{message.author.mention} yanlış sayı yazdı! Beklenen: {expected} (Sıfırlama kapalı)", discord.Color.orange()))

        # KELIME BILMECE
        elif key == "kelime_bilmece":
            guess = message.content.strip().lower()
            hedef = settings.get("kelime", "").lower()
            if not hedef:
                continue
            if guess == hedef:
                try:
                    await message.add_reaction("✅")
                except:
                    pass
                add_points(message.author.id, 1000)
                await save_all()
                await message.channel.send(embed=create_embed("✅ Doğru!", f"{message.author.mention} kelimeyi bildi: **{hedef}** (+1000 puan)", discord.Color.green()))
                yeni = await fetch_word()
                settings["kelime"] = yeni
                await save_all()
                print(f"[{message.guild.name}] kelime_bilmece yeni kelime: {yeni}")
                await message.channel.send(embed=create_embed("📝 Yeni Kelime", "Yeni kelime belirlendi, hadi bakalım!", discord.Color.purple()))
            else:
                try:
                    await message.add_reaction("❌")
                except:
                    pass
                await message.channel.send(embed=create_embed("❌ Yanlış Tahmin!", f"{message.author.mention} yanlış tahmin etti. Tekrar dene!", discord.Color.red()))

        # SAYIYI BIL
        elif key == "sayi":
            content = message.content.strip()
            if content.isdigit():
                tahmin = int(content)
                hedef = settings.get("sayi")
                if tahmin == hedef:
                    try:
                        await message.add_reaction("✅")
                    except:
                        pass
                    add_points(message.author.id, 100)
                    await save_all()
                    await message.channel.send(embed=create_embed("🎉 Doğru Tahmin!", f"{message.author.mention} sayıyı bildi! (+100 puan) (**{tahmin}**)", discord.Color.gold()))
                    yeni = random.randint(1, 20)
                    settings["sayi"] = yeni
                    await save_all()
                    print(f"[{message.guild.name}] sayi yeni: {yeni}")
                    await message.channel.send(embed=create_embed("🎯 Yeni Sayı", "Yeni bir sayı tutuldu, tahmin etmeye devam edin!", discord.Color.purple()))
                else:
                    try:
                        await message.add_reaction("❌")
                    except:
                        pass
                    if sifir == "evet":
                        settings["sayi"] = random.randint(1, 20)
                        await save_all()
                        await message.channel.send(embed=create_embed("❌ Yanlış Tahmin!", f"{message.author.mention} yanlış tahmin etti. Yeni sayı tutuldu. (Sıfırlama)", discord.Color.red()))
                    else:
                        await message.channel.send(embed=create_embed("⚠️ Yanlış Tahmin!", f"{message.author.mention} yanlış tahmin etti. (Sıfırlama kapalı)", discord.Color.orange()))

        # KELIME TURETME
        elif key == "kelime_turetme":
            content = message.content.strip().lower()
            if not content.isalpha():
                continue
            son = settings.get("son_kelime", "").lower()
            if not son:
                continue
            expected = son[-1]
            used = settings.get("used", set())
            if content[0] == expected and content not in used:
                try:
                    await message.add_reaction("✅")
                except:
                    pass
                add_points(message.author.id, 100)
                if not isinstance(settings.get("used"), set):
                    settings["used"] = set(settings.get("used", []))
                settings["used"].add(content)
                settings["son_kelime"] = content
                await save_all()
                await message.channel.send(embed=create_embed("✅ Doğru!", f"{message.author.mention} uygun kelime yazdı: **{content}** (+100 puan)", discord.Color.green()))
            else:
                try:
                    await message.add_reaction("❌")
                except:
                    pass
                if sifir == "evet":
                    yeni = await fetch_word()
                    settings["son_kelime"] = yeni
                    settings["used"] = set([yeni])
                    await save_all()
                    await message.channel.send(embed=create_embed("❌ Yanlış!", f"{message.author.mention} uymayan kelime yazdı. Oyun sıfırlandı. Yeni kelime: **{yeni}**", discord.Color.red()))
                    print(f"[{message.guild.name}] kelime_turetme sıfırlandı, yeni: {yeni}")
                else:
                    await message.channel.send(embed=create_embed("⚠️ Yanlış!", f"{message.author.mention} uymayan kelime yazdı. (Sıfırlama kapalı) Beklenen ilk harf: **{expected}**", discord.Color.orange()))

    await bot.process_commands(message)


if not TOKEN:
    print("HATA: DISCORD_TOKEN ortam değişkeni yok.")
else:
    bot.run(TOKEN)
