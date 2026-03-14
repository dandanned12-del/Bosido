import discord
from discord.ext import commands, tasks
from discord import app_commands
import sqlite3
import time
import os
import random
from datetime import datetime, timedelta

TOKEN = os.environ.get('DISCORD_TOKEN', '')
REGISTRATION_CHANNEL_ID = 1481140820223594630
DATE_CHANNEL_ID          = 1481495877003772034
MEMBERS_CHANNEL_ID       = 1481496307678970007
RULEBOOK_CHANNEL_ID      = 1481164110526939146
SUPPORT_CHANNEL_ID       = 1481328494272053248
CLAIM_CHANNEL_ID         = 1481328592490336388
WAR_CHANNEL_ID           = 1481325338544832666
GUIDE_CHANNEL_ID         = 1481166478735708230
WAR_GUIDE_CHANNEL_ID     = 1481325213105918076
BASE_ROLEPLAY_DATE = datetime(2020, 1, 1)

TICKET_STAFF_ROLES = {
    "Helper","Moderator","Main Moderator","Admin Assistant",
    "Main Administrator","Head Curator","War Curator",
    "Head Administrator","Coder","Co Owner"
}
WAR_ADMIN_ROLES = {"War Curator","Head Curator","Main Administrator","Head Administrator","Coder","Co Owner"}

MILITARY_EMOJIS = {
    "ОБТ":"<:obt:1482286883437412485>","БМП":"<:bmp:1482288964080500817>",
    "БТР":"<:btr:1482288994493661254>","БМД":"<:bmd:1482288925199433758>",
    "ПЗРК":"<:pzrk:1482289033928249405>","ПВО":"<:pvo:1482289074793484340>",
    "Бронемашина":"<:bronemashina:1482287089964814520>","Грузовик":"<:gruzovik:1482286958041628786>",
    "Артиллерия":"<:artilleriya:1482287106586837073>","САУ":"<:sau:1482289854514729003>",
    "ЗСУ":"<:zsu:1482289950564024433>","Ракета":"<:raketa:1482314491071955057>",
    "Пусковая установка":"<:pu:1482290345386577971>","Баллистическая ракета":"<:ballisticheskaya:1482290375740624916>",
    "РСЗО":"<:rszo:1482286978446921848>","Эсминец":"<:esminec:1482287074697678878>",
    "Крейсер":"<:kreiser:1482314120551337994>","Подводная лодка":"<:podlodka:1482314155594743839>",
    "Авианосец":"<:avianosec:1482314207340007445>","Фрегат":"<:fregat:1482287026937270404>",
    "Корабль госпиталь":"<:gospital:1482313982646816918>","Ударный вертолет":"<:udarvertolet:1482314246611271700>",
    "Вертолет":"<:vertolet:1482287050446077953>","Истребитель":"<:istrebitel:1482286919424544889>",
    "Грузовой самолет":"<:gruzovoi:1482314034362712085>","Истребитель 5 поколения":"<:5genjet:1482314281297907763>",
    "БПЛА":"<:bpla:1482314084639571969>","Пехотинец":"<:pehotinec:1482286940522024960>",
}

MILITARY_POWER = {
    "Пехотинец":1,"Грузовик":2,"Бронемашина":5,"БТР":8,"БМП":10,"БМД":10,
    "ПЗРК":12,"ПВО":30,"Артиллерия":20,"САУ":25,"ЗСУ":22,"ОБТ":35,
    "Ракета":40,"Пусковая установка":30,"РСЗО":45,"Баллистическая ракета":100,
    "Фрегат":60,"Корабль госпиталь":10,"Эсминец":80,"Крейсер":120,
    "Подводная лодка":130,"Авианосец":300,"Вертолет":25,"Ударный вертолет":50,
    "БПЛА":20,"Грузовой самолет":15,"Истребитель":70,"Истребитель 5 поколения":150,
}

GROUND_UNITS = {"Пехотинец","ОБТ","БМП","БТР","БМД","ПЗРК","ПВО","Бронемашина","Грузовик","Артиллерия","САУ","ЗСУ","Ракета","Пусковая установка","РСЗО","Баллистическая ракета"}
NAVAL_UNITS  = {"Эсминец","Крейсер","Подводная лодка","Авианосец","Фрегат","Корабль госпиталь"}
AIR_UNITS    = {"Ударный вертолет","Вертолет","Истребитель","Грузовой самолет","Истребитель 5 поколения","БПЛА"}

bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())

conn = sqlite3.connect("vpi_bot.db")
c = conn.cursor()

c.execute("""CREATE TABLE IF NOT EXISTS players (
user_id INTEGER PRIMARY KEY, country TEXT, balance REAL,
income_per_sec REAL, income_buffer REAL, last_income REAL)""")
c.execute("""CREATE TABLE IF NOT EXISTS countries (name TEXT PRIMARY KEY, taken INTEGER)""")
c.execute("""CREATE TABLE IF NOT EXISTS inventory (
user_id INTEGER, item TEXT, amount INTEGER, PRIMARY KEY(user_id,item))""")
c.execute("""CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)""")
c.execute("""CREATE TABLE IF NOT EXISTS tempbans (
user_id INTEGER PRIMARY KEY, guild_id INTEGER, unban_at REAL)""")
c.execute("""CREATE TABLE IF NOT EXISTS wars (
id INTEGER PRIMARY KEY AUTOINCREMENT,
attacker_id INTEGER, defender_id INTEGER,
attacker_country TEXT, defender_country TEXT,
status TEXT, guild_id INTEGER, created_at REAL)""")
conn.commit()

def get_setting(key):
    c.execute("SELECT value FROM settings WHERE key=?", (key,))
    row = c.fetchone()
    return row[0] if row else None

def set_setting(key, value):
    c.execute("INSERT OR REPLACE INTO settings VALUES (?,?)", (key, str(value)))
    conn.commit()

def get_current_roleplay_date():
    start = get_setting("game_start_time")
    if not start: return BASE_ROLEPLAY_DATE
    elapsed_days = int((time.time() - float(start)) / 60)
    return BASE_ROLEPLAY_DATE + timedelta(days=elapsed_days)

def get_inventory_amount(user_id, item):
    c.execute("SELECT amount FROM inventory WHERE user_id=? AND item=?", (user_id, item))
    row = c.fetchone()
    return row[0] if row else 0

def set_inventory(user_id, item, delta):
    c.execute("INSERT OR IGNORE INTO inventory VALUES (?,?,0)", (user_id, item))
    c.execute("UPDATE inventory SET amount=amount+? WHERE user_id=? AND item=?", (delta, user_id, item))
    conn.commit()

def update_income(user_id):
    c.execute("SELECT income_per_sec,income_buffer,last_income FROM players WHERE user_id=?", (user_id,))
    data = c.fetchone()
    if not data: return
    income_ps, buffer, last = data
    now = time.time()
    buffer += (now - last) * income_ps
    c.execute("UPDATE players SET income_buffer=?,last_income=? WHERE user_id=?", (buffer, now, user_id))
    conn.commit()

def get_mil_emoji(name):
    return MILITARY_EMOJIS.get(name, "🔫")

def has_war_role(interaction: discord.Interaction) -> bool:
    if interaction.user.id == interaction.guild.owner_id: return True
    return any(r.name in WAR_ADMIN_ROLES for r in interaction.user.roles)

# ----------------------------------------------------------------
# COUNTRY DATA
# ----------------------------------------------------------------

COUNTRY_FLAGS = {
    "Afghanistan":"🇦🇫","Albania":"🇦🇱","Algeria":"🇩🇿","Andorra":"🇦🇩","Angola":"🇦🇴","Antigua and Barbuda":"🇦🇬","Argentina":"🇦🇷","Armenia":"🇦🇲","Australia":"🇦🇺","Austria":"🇦🇹","Azerbaijan":"🇦🇿","Bahamas":"🇧🇸","Bahrain":"🇧🇭","Bangladesh":"🇧🇩","Barbados":"🇧🇧","Belarus":"🇧🇾","Belgium":"🇧🇪","Belize":"🇧🇿","Benin":"🇧🇯","Bhutan":"🇧🇹","Bolivia":"🇧🇴","Bosnia and Herzegovina":"🇧🇦","Botswana":"🇧🇼","Brazil":"🇧🇷","Brunei":"🇧🇳","Bulgaria":"🇧🇬","Burkina Faso":"🇧🇫","Burundi":"🇧🇮","Cabo Verde":"🇨🇻","Cambodia":"🇰🇭","Cameroon":"🇨🇲","Canada":"🇨🇦","Central African Republic":"🇨🇫","Chad":"🇹🇩","Chile":"🇨🇱","China":"🇨🇳","Colombia":"🇨🇴","Comoros":"🇰🇲","Congo":"🇨🇬","Costa Rica":"🇨🇷","Croatia":"🇭🇷","Cuba":"🇨🇺","Cyprus":"🇨🇾","Czech Republic":"🇨🇿","Denmark":"🇩🇰","Djibouti":"🇩🇯","Dominica":"🇩🇲","Dominican Republic":"🇩🇴","DR Congo":"🇨🇩","Ecuador":"🇪🇨","Egypt":"🇪🇬","El Salvador":"🇸🇻","Equatorial Guinea":"🇬🇶","Eritrea":"🇪🇷","Estonia":"🇪🇪","Eswatini":"🇸🇿","Ethiopia":"🇪🇹","Fiji":"🇫🇯","Finland":"🇫🇮","France":"🇫🇷","Gabon":"🇬🇦","Gambia":"🇬🇲","Georgia":"🇬🇪","Germany":"🇩🇪","Ghana":"🇬🇭","Greece":"🇬🇷","Grenada":"🇬🇩","Guatemala":"🇬🇹","Guinea":"🇬🇳","Guinea-Bissau":"🇬🇼","Guyana":"🇬🇾","Haiti":"🇭🇹","Honduras":"🇭🇳","Hungary":"🇭🇺","Iceland":"🇮🇸","India":"🇮🇳","Indonesia":"🇮🇩","Iran":"🇮🇷","Iraq":"🇮🇶","Ireland":"🇮🇪","Israel":"🇮🇱","Italy":"🇮🇹","Ivory Coast":"🇨🇮","Jamaica":"🇯🇲","Japan":"🇯🇵","Jordan":"🇯🇴","Kazakhstan":"🇰🇿","Kenya":"🇰🇪","Kiribati":"🇰🇮","Kuwait":"🇰🇼","Kyrgyzstan":"🇰🇬","Laos":"🇱🇦","Latvia":"🇱🇻","Lebanon":"🇱🇧","Lesotho":"🇱🇸","Liberia":"🇱🇷","Libya":"🇱🇾","Liechtenstein":"🇱🇮","Lithuania":"🇱🇹","Luxembourg":"🇱🇺","Madagascar":"🇲🇬","Malawi":"🇲🇼","Malaysia":"🇲🇾","Maldives":"🇲🇻","Mali":"🇲🇱","Malta":"🇲🇹","Marshall Islands":"🇲🇭","Mauritania":"🇲🇷","Mauritius":"🇲🇺","Mexico":"🇲🇽","Micronesia":"🇫🇲","Moldova":"🇲🇩","Monaco":"🇲🇨","Mongolia":"🇲🇳","Montenegro":"🇲🇪","Morocco":"🇲🇦","Mozambique":"🇲🇿","Myanmar":"🇲🇲","Namibia":"🇳🇦","Nauru":"🇳🇷","Nepal":"🇳🇵","Netherlands":"🇳🇱","New Zealand":"🇳🇿","Nicaragua":"🇳🇮","Niger":"🇳🇪","Nigeria":"🇳🇬","North Korea":"🇰🇵","North Macedonia":"🇲🇰","Norway":"🇳🇴","Oman":"🇴🇲","Pakistan":"🇵🇰","Palau":"🇵🇼","Palestine":"🇵🇸","Panama":"🇵🇦","Papua New Guinea":"🇵🇬","Paraguay":"🇵🇾","Peru":"🇵🇪","Philippines":"🇵🇭","Poland":"🇵🇱","Portugal":"🇵🇹","Qatar":"🇶🇦","Romania":"🇷🇴","Russia":"🇷🇺","Rwanda":"🇷🇼","Saint Kitts and Nevis":"🇰🇳","Saint Lucia":"🇱🇨","Saint Vincent and the Grenadines":"🇻🇨","Samoa":"🇼🇸","San Marino":"🇸🇲","Sao Tome and Principe":"🇸🇹","Saudi Arabia":"🇸🇦","Senegal":"🇸🇳","Serbia":"🇷🇸","Seychelles":"🇸🇨","Sierra Leone":"🇸🇱","Singapore":"🇸🇬","Slovakia":"🇸🇰","Slovenia":"🇸🇮","Solomon Islands":"🇸🇧","Somalia":"🇸🇴","South Africa":"🇿🇦","South Korea":"🇰🇷","South Sudan":"🇸🇸","Spain":"🇪🇸","Sri Lanka":"🇱🇰","Sudan":"🇸🇩","Suriname":"🇸🇷","Sweden":"🇸🇪","Switzerland":"🇨🇭","Syria":"🇸🇾","Taiwan":"🇹🇼","Tajikistan":"🇹🇯","Tanzania":"🇹🇿","Thailand":"🇹🇭","Timor-Leste":"🇹🇱","Togo":"🇹🇬","Tonga":"🇹🇴","Trinidad and Tobago":"🇹🇹","Tunisia":"🇹🇳","Turkey":"🇹🇷","Turkmenistan":"🇹🇲","Tuvalu":"🇹🇻","Uganda":"🇺🇬","Ukraine":"🇺🇦","United Arab Emirates":"🇦🇪","United Kingdom":"🇬🇧","United States":"🇺🇸","Uruguay":"🇺🇾","Uzbekistan":"🇺🇿","Vanuatu":"🇻🇺","Vatican City":"🇻🇦","Venezuela":"🇻🇪","Vietnam":"🇻🇳","Yemen":"🇾🇪","Zambia":"🇿🇲","Zimbabwe":"🇿🇼",
}

COUNTRY_NAMES_RU = {
    "Afghanistan":"Афганистан","Albania":"Албания","Algeria":"Алжир","Andorra":"Андорра","Angola":"Ангола","Antigua and Barbuda":"Антигуа и Барбуда","Argentina":"Аргентина","Armenia":"Армения","Australia":"Австралия","Austria":"Австрия","Azerbaijan":"Азербайджан","Bahamas":"Багамы","Bahrain":"Бахрейн","Bangladesh":"Бангладеш","Barbados":"Барбадос","Belarus":"Беларусь","Belgium":"Бельгия","Belize":"Белиз","Benin":"Бенин","Bhutan":"Бутан","Bolivia":"Боливия","Bosnia and Herzegovina":"Босния и Герцеговина","Botswana":"Ботсвана","Brazil":"Бразилия","Brunei":"Бруней","Bulgaria":"Болгария","Burkina Faso":"Буркина-Фасо","Burundi":"Бурунди","Cabo Verde":"Кабо-Верде","Cambodia":"Камбоджа","Cameroon":"Камерун","Canada":"Канада","Central African Republic":"ЦАР","Chad":"Чад","Chile":"Чили","China":"Китай","Colombia":"Колумбия","Comoros":"Коморы","Congo":"Конго","Costa Rica":"Коста-Рика","Croatia":"Хорватия","Cuba":"Куба","Cyprus":"Кипр","Czech Republic":"Чехия","Denmark":"Дания","Djibouti":"Джибути","Dominica":"Доминика","Dominican Republic":"Доминиканская Республика","DR Congo":"ДРК","Ecuador":"Эквадор","Egypt":"Египет","El Salvador":"Сальвадор","Equatorial Guinea":"Экв. Гвинея","Eritrea":"Эритрея","Estonia":"Эстония","Eswatini":"Эсватини","Ethiopia":"Эфиопия","Fiji":"Фиджи","Finland":"Финляндия","France":"Франция","Gabon":"Габон","Gambia":"Гамбия","Georgia":"Грузия","Germany":"Германия","Ghana":"Гана","Greece":"Греция","Grenada":"Гренада","Guatemala":"Гватемала","Guinea":"Гвинея","Guinea-Bissau":"Гвинея-Бисау","Guyana":"Гайана","Haiti":"Гаити","Honduras":"Гондурас","Hungary":"Венгрия","Iceland":"Исландия","India":"Индия","Indonesia":"Индонезия","Iran":"Иран","Iraq":"Ирак","Ireland":"Ирландия","Israel":"Израиль","Italy":"Италия","Ivory Coast":"Кот-д'Ивуар","Jamaica":"Ямайка","Japan":"Япония","Jordan":"Иордания","Kazakhstan":"Казахстан","Kenya":"Кения","Kiribati":"Кирибати","Kuwait":"Кувейт","Kyrgyzstan":"Кыргызстан","Laos":"Лаос","Latvia":"Латвия","Lebanon":"Ливан","Lesotho":"Лесото","Liberia":"Либерия","Libya":"Ливия","Liechtenstein":"Лихтенштейн","Lithuania":"Литва","Luxembourg":"Люксембург","Madagascar":"Мадагаскар","Malawi":"Малави","Malaysia":"Малайзия","Maldives":"Мальдивы","Mali":"Мали","Malta":"Мальта","Marshall Islands":"Маршалловы Острова","Mauritania":"Мавритания","Mauritius":"Маврикий","Mexico":"Мексика","Micronesia":"Микронезия","Moldova":"Молдова","Monaco":"Монако","Mongolia":"Монголия","Montenegro":"Черногория","Morocco":"Марокко","Mozambique":"Мозамбик","Myanmar":"Мьянма","Namibia":"Намибия","Nauru":"Науру","Nepal":"Непал","Netherlands":"Нидерланды","New Zealand":"Новая Зеландия","Nicaragua":"Никарагуа","Niger":"Нигер","Nigeria":"Нигерия","North Korea":"Северная Корея","North Macedonia":"Северная Македония","Norway":"Норвегия","Oman":"Оман","Pakistan":"Пакистан","Palau":"Палау","Palestine":"Палестина","Panama":"Панама","Papua New Guinea":"Папуа — Новая Гвинея","Paraguay":"Парагвай","Peru":"Перу","Philippines":"Филиппины","Poland":"Польша","Portugal":"Португалия","Qatar":"Катар","Romania":"Румыния","Russia":"Россия","Rwanda":"Руанда","Saint Kitts and Nevis":"Сент-Китс и Невис","Saint Lucia":"Сент-Люсия","Saint Vincent and the Grenadines":"Сент-Винсент","Samoa":"Самоа","San Marino":"Сан-Марино","Sao Tome and Principe":"Сан-Томе и Принсипи","Saudi Arabia":"Саудовская Аравия","Senegal":"Сенегал","Serbia":"Сербия","Seychelles":"Сейшелы","Sierra Leone":"Сьерра-Леоне","Singapore":"Сингапур","Slovakia":"Словакия","Slovenia":"Словения","Solomon Islands":"Соломоновы Острова","Somalia":"Сомали","South Africa":"ЮАР","South Korea":"Южная Корея","South Sudan":"Южный Судан","Spain":"Испания","Sri Lanka":"Шри-Ланка","Sudan":"Судан","Suriname":"Суринам","Sweden":"Швеция","Switzerland":"Швейцария","Syria":"Сирия","Taiwan":"Тайвань","Tajikistan":"Таджикистан","Tanzania":"Танзания","Thailand":"Таиланд","Timor-Leste":"Вост. Тимор","Togo":"Того","Tonga":"Тонга","Trinidad and Tobago":"Тринидад и Тобаго","Tunisia":"Тунис","Turkey":"Турция","Turkmenistan":"Туркменистан","Tuvalu":"Тувалу","Uganda":"Уганда","Ukraine":"Украина","United Arab Emirates":"ОАЭ","United Kingdom":"Великобритания","United States":"США","Uruguay":"Уругвай","Uzbekistan":"Узбекистан","Vanuatu":"Вануату","Vatican City":"Ватикан","Venezuela":"Венесуэла","Vietnam":"Вьетнам","Yemen":"Йемен","Zambia":"Замбия","Zimbabwe":"Зимбабве",
}

def ru(country): return COUNTRY_NAMES_RU.get(country, country)
def flag(country): return COUNTRY_FLAGS.get(country, "🏳️")
def display(country): return f"{flag(country)} {ru(country)}"

REGIONS = {
    "🌍 Африка — Запад":["Benin","Burkina Faso","Cabo Verde","Gambia","Ghana","Guinea","Guinea-Bissau","Ivory Coast","Liberia","Mali","Mauritania","Niger","Nigeria","Senegal","Sierra Leone","Togo"],
    "🌍 Африка — Север и Центр":["Algeria","Cameroon","Central African Republic","Chad","Comoros","Congo","DR Congo","Egypt","Equatorial Guinea","Gabon","Libya","Morocco","Sao Tome and Principe","Sudan","Tunisia"],
    "🌍 Африка — Восток и Юг":["Angola","Botswana","Burundi","Djibouti","Eritrea","Eswatini","Ethiopia","Kenya","Lesotho","Madagascar","Malawi","Mauritius","Mozambique","Namibia","Rwanda","Seychelles","Somalia","South Africa","South Sudan","Tanzania","Uganda","Zambia","Zimbabwe"],
    "🌎 Северная и Центральная Америка":["Antigua and Barbuda","Bahamas","Barbados","Belize","Canada","Costa Rica","Cuba","Dominica","Dominican Republic","El Salvador","Grenada","Guatemala","Haiti","Honduras","Jamaica","Mexico","Nicaragua","Panama","Saint Kitts and Nevis","Saint Lucia","Saint Vincent and the Grenadines","Trinidad and Tobago","United States"],
    "🌎 Южная Америка":["Argentina","Bolivia","Brazil","Chile","Colombia","Ecuador","Guyana","Paraguay","Peru","Suriname","Uruguay","Venezuela"],
    "🌏 Ближний Восток":["Bahrain","Cyprus","Iran","Iraq","Israel","Jordan","Kuwait","Lebanon","Oman","Palestine","Qatar","Saudi Arabia","Syria","Turkey","United Arab Emirates","Yemen"],
    "🌏 Южная и Центральная Азия":["Afghanistan","Armenia","Azerbaijan","Bangladesh","Bhutan","Georgia","India","Kazakhstan","Kyrgyzstan","Maldives","Nepal","Pakistan","Sri Lanka","Tajikistan","Turkmenistan","Uzbekistan"],
    "🌏 Восточная и Юго-Восточная Азия":["Brunei","Cambodia","China","Indonesia","Japan","Laos","Malaysia","Mongolia","Myanmar","North Korea","Philippines","Singapore","South Korea","Taiwan","Thailand","Timor-Leste","Vietnam"],
    "🌍 Европа — Запад и Север":["Andorra","Austria","Belgium","Denmark","Finland","France","Germany","Iceland","Ireland","Italy","Liechtenstein","Luxembourg","Malta","Monaco","Netherlands","Norway","Portugal","San Marino","Spain","Sweden","Switzerland","United Kingdom","Vatican City"],
    "🌍 Европа — Восток и Юг":["Albania","Belarus","Bosnia and Herzegovina","Bulgaria","Croatia","Czech Republic","Estonia","Greece","Hungary","Latvia","Lithuania","Moldova","Montenegro","North Macedonia","Poland","Romania","Russia","Serbia","Slovakia","Slovenia","Ukraine"],
    "🌊 Океания и Тихий океан":["Australia","Fiji","Kiribati","Marshall Islands","Micronesia","Nauru","New Zealand","Palau","Papua New Guinea","Samoa","Solomon Islands","Tonga","Tuvalu","Vanuatu"],
}

ALL_COUNTRIES = [cn for group in REGIONS.values() for cn in group]
for country in ALL_COUNTRIES:
    c.execute("INSERT OR IGNORE INTO countries VALUES (?,0)", (country,))
conn.commit()

INFRASTRUCTURE = {
    "ТРЦ":(120000,35,"Торговый развлекательный центр"),"Бизнес центр":(200000,55,"Деловой центр города"),
    "Полицейский участок":(25000,6,"Обеспечивает правопорядок"),"Больница":(40000,10,"Медицинское учреждение"),
    "Суд":(30000,8,"Судебная система"),"Пожарная часть":(20000,5,"Противопожарная служба"),
    "Школа":(22000,6,"Образовательное учреждение"),"Лаборатория":(300000,80,"Научно-исследовательский центр"),
    "Аэропорт":(500000,130,"Воздушный транспортный узел"),"Порт":(400000,100,"Морской торговый порт"),
    "Электростанция":(250000,60,"Источник электроэнергии для города"),
}
RESOURCES = {
    "Ферма":(10000,4,"Производство сельхозпродукции",None),"Шахта":(60000,18,"Добыча полезных ископаемых",None),
    "Поле":(6000,2,"Сельскохозяйственное поле",None),"Скот":(15000,5,"Животноводческое хозяйство",None),
    "Нефтебаза":(350000,95,"Нефтедобывающее производство",None),"Газовая скважина":(300000,80,"Добыча природного газа",None),
    "Электричество":(80000,25,"Продажа электроэнергии","Электростанция"),
}
MILITARY = {
    "Пехотинец":(1000,None,"Пехотный солдат"),
    "ОБТ":(12000,"ground","Основной боевой танк"),"БМП":(4500,"ground","Боевая машина пехоты"),
    "БТР":(3500,"ground","Бронетранспортёр"),"БМД":(4000,"ground","Боевая машина десанта"),
    "ПЗРК":(6000,"ground","Переносной зенитный ракетный комплекс"),"ПВО":(20000,"ground","Зенитный ракетный комплекс"),
    "Бронемашина":(2000,"ground","Бронированная разведывательная машина"),"Грузовик":(800,"ground","Военный грузовой автомобиль"),
    "Артиллерия":(8000,"ground","Буксируемая артиллерийская система"),"САУ":(11000,"ground","Самоходная артиллерийская установка"),
    "ЗСУ":(9000,"ground","Зенитная самоходная установка"),"Ракета":(25000,"ground","Тактическая крылатая ракета"),
    "Пусковая установка":(15000,"ground","Мобильная пусковая установка"),"РСЗО":(18000,"ground","Реактивная система залпового огня"),
    "Баллистическая ракета":(150000,"ground","Баллистическая ракета средней дальности"),
    "Эсминец":(120000,"sea","Многоцелевой боевой корабль"),"Крейсер":(250000,"sea","Тяжёлый ударный крейсер"),
    "Подводная лодка":(300000,"sea","Многоцелевая субмарина"),"Авианосец":(2000000,"sea","Авианесущий ударный корабль"),
    "Фрегат":(80000,"sea","Многоцелевой сторожевой корабль"),"Корабль госпиталь":(50000,"sea","Плавучий медицинский госпиталь"),
    "Ударный вертолет":(35000,"air","Вертолёт огневой поддержки"),"Вертолет":(20000,"air","Многоцелевой транспортный вертолёт"),
    "Истребитель":(60000,"air","Сверхзвуковой истребитель"),"Грузовой самолет":(30000,"air","Военно-транспортный самолёт"),
    "Истребитель 5 поколения":(200000,"air","Малозаметный стелс-истребитель"),"БПЛА":(15000,"air","Беспилотный летательный аппарат"),
}
MILITARY_CLASS_LABEL = {"ground":"🛡 Наземная техника","sea":"⚓ Морская техника","air":"✈️ Авиация"}
FACTORIES = {
    "Завод бронетехники":(800000,10,"ground","Производит наземную боевую технику"),
    "Верфь":(1200000,10,"sea","Производит морские суда всех классов"),
    "Авиазавод":(1000000,10,"air","Производит авиационную технику"),
}
FACTORY_CLASS_SLOT = {"ground":"slots_ground","sea":"slots_sea","air":"slots_air"}
ALL_MILITARY_ITEMS = set(MILITARY.keys())

# ----------------------------------------------------------------
# WAR HELPERS
# ----------------------------------------------------------------

def parse_units_string(text: str) -> dict:
    result = {}
    parts = [p.strip() for p in text.replace("\n",",").split(",") if p.strip()]
    for part in parts:
        tokens = part.split()
        if len(tokens) >= 2:
            for i, tok in enumerate(tokens):
                try:
                    amount = int(tok)
                    name = " ".join(tokens[:i] + tokens[i+1:]).strip()
                    if name in ALL_MILITARY_ITEMS:
                        result[name] = result.get(name,0) + amount
                        break
                except ValueError:
                    continue
    return result

def calc_power(units: dict) -> int:
    return sum(MILITARY_POWER.get(name,0)*amt for name,amt in units.items())

def calc_losses(units: dict, power_ratio: float, battle_type: str) -> dict:
    losses = {}
    valid = {"ground":GROUND_UNITS,"naval":NAVAL_UNITS,"air":AIR_UNITS}.get(battle_type, ALL_MILITARY_ITEMS)
    for name,amt in units.items():
        if name not in valid: continue
        base = random.uniform(0.15, 0.45)
        adjusted = min(base / max(0.3, power_ratio), 0.85)
        loss = max(0, round(amt * adjusted))
        if loss > 0: losses[name] = loss
    return losses

def apply_losses(user_id: int, losses: dict):
    for name,amount in losses.items():
        actual = min(amount, get_inventory_amount(user_id, name))
        if actual > 0: set_inventory(user_id, name, -actual)

def get_active_war(uid1, uid2):
    c.execute("""SELECT * FROM wars WHERE status='active'
                 AND ((attacker_id=? AND defender_id=?) OR (attacker_id=? AND defender_id=?))""",
              (uid1,uid2,uid2,uid1))
    return c.fetchone()

def losses_text(losses, units):
    if not losses: return "Потерь нет"
    return "\n".join(f"{get_mil_emoji(n)} {n}: −{v} (из {units.get(n,0)})" for n,v in losses.items())

async def run_battle(interaction, attacker, defender, attacker_units_str, defender_units_str, battle_type, title, color):
    if not has_war_role(interaction):
        await interaction.response.send_message("❌ Нет прав.", ephemeral=True); return
    if interaction.channel_id != WAR_CHANNEL_ID:
        await interaction.response.send_message("❌ Только в канале войны.", ephemeral=True); return
    if attacker.id == defender.id:
        await interaction.response.send_message("❌ Нельзя воевать с самим собой.", ephemeral=True); return

    row_a = c.execute("SELECT country FROM players WHERE user_id=?", (attacker.id,)).fetchone()
    row_d = c.execute("SELECT country FROM players WHERE user_id=?", (defender.id,)).fetchone()
    if not row_a or not row_d:
        await interaction.response.send_message("❌ Один из игроков не зарегистрирован.", ephemeral=True); return

    a_country = row_a[0]; d_country = row_d[0]
    if a_country == d_country:
        await interaction.response.send_message("❌ Нельзя начать битву между одной страной.", ephemeral=True); return

    a_units = parse_units_string(attacker_units_str)
    d_units = parse_units_string(defender_units_str)

    a_power = calc_power(a_units); d_power = calc_power(d_units)
    total = a_power + d_power or 1

    a_roll = random.randint(1, max(1, int(a_power/total*200)))
    d_roll = random.randint(1, max(1, int(d_power/total*200)))

    winner = attacker if a_roll >= d_roll else defender
    ratio_a = a_power / max(d_power,1); ratio_d = d_power / max(a_power,1)
    a_losses = calc_losses(a_units, ratio_a, battle_type)
    d_losses = calc_losses(d_units, ratio_d, battle_type)
    apply_losses(attacker.id, a_losses); apply_losses(defender.id, d_losses)

    embed = discord.Embed(title=title, color=color)
    embed.add_field(name=f"{display(a_country)} (Атака)", value=f"⚔️ Мощь: **{a_power}**\n🎲 Ролл: **{a_roll}**", inline=True)
    embed.add_field(name=f"{display(d_country)} (Оборона)", value=f"⚔️ Мощь: **{d_power}**\n🎲 Ролл: **{d_roll}**", inline=True)
    embed.add_field(name="\u200b", value="\u200b", inline=True)
    w_country = a_country if winner.id == attacker.id else d_country
    embed.add_field(name="🏆 Победитель сражения", value=display(w_country), inline=False)
    embed.add_field(name=f"💀 Потери {ru(a_country)}", value=losses_text(a_losses,a_units), inline=True)
    embed.add_field(name=f"💀 Потери {ru(d_country)}", value=losses_text(d_losses,d_units), inline=True)
    embed.set_footer(text="Потери списаны с инвентаря автоматически")
    await interaction.response.send_message(embed=embed)

# ----------------------------------------------------------------
# SLASH COMMANDS — WAR
# ----------------------------------------------------------------

@bot.tree.command(name="startgroundbattle", description="Начать наземное сражение")
@app_commands.describe(attacker="Атакующий",defender="Обороняющийся",attacker_units="Техника атакующего (пример: 100 ОБТ, 50 БМП)",defender_units="Техника обороняющегося")
async def startgroundbattle(interaction,attacker:discord.Member,defender:discord.Member,attacker_units:str,defender_units:str):
    await run_battle(interaction,attacker,defender,attacker_units,defender_units,"ground","🛡 Наземное сражение — Результат",0xe74c3c)

@bot.tree.command(name="startnavalbattle", description="Начать морское сражение")
@app_commands.describe(attacker="Атакующий",defender="Обороняющийся",attacker_units="Флот атакующего",defender_units="Флот обороняющегося")
async def startnavalbattle(interaction,attacker:discord.Member,defender:discord.Member,attacker_units:str,defender_units:str):
    await run_battle(interaction,attacker,defender,attacker_units,defender_units,"naval","⚓ Морское сражение — Результат",0x3498db)

@bot.tree.command(name="startairbattle", description="Начать воздушное сражение")
@app_commands.describe(attacker="Атакующий",defender="Обороняющийся",attacker_units="Авиация атакующего",defender_units="Авиация обороняющегося")
async def startairbattle(interaction,attacker:discord.Member,defender:discord.Member,attacker_units:str,defender_units:str):
    await run_battle(interaction,attacker,defender,attacker_units,defender_units,"air","✈️ Воздушное сражение — Результат",0x9b59b6)

@bot.tree.command(name="warend", description="Завершить войну")
@app_commands.describe(winner="Победитель",loser="Проигравший",outcome="Исход")
@app_commands.choices(outcome=[
    app_commands.Choice(name="Мирное соглашение (ничья)",value="peace"),
    app_commands.Choice(name="Поражение (победитель забирает всё)",value="defeat"),
])
async def warend(interaction,winner:discord.Member,loser:discord.Member,outcome:str):
    if not has_war_role(interaction):
        await interaction.response.send_message("❌ Нет прав.", ephemeral=True); return
    if interaction.channel_id != WAR_CHANNEL_ID:
        await interaction.response.send_message("❌ Только в канале войны.", ephemeral=True); return
    if winner.id == loser.id:
        await interaction.response.send_message("❌ Победитель и проигравший не могут быть одним человеком.", ephemeral=True); return

    row_w = c.execute("SELECT country FROM players WHERE user_id=?",(winner.id,)).fetchone()
    row_l = c.execute("SELECT country FROM players WHERE user_id=?",(loser.id,)).fetchone()
    if not row_w or not row_l:
        await interaction.response.send_message("❌ Один из игроков не зарегистрирован.", ephemeral=True); return

    w_country = row_w[0]; l_country = row_l[0]
    guild = interaction.guild
    await interaction.response.defer()

    c.execute("UPDATE wars SET status='ended' WHERE status='active' AND ((attacker_id=? AND defender_id=?) OR (attacker_id=? AND defender_id=?))",
              (winner.id,loser.id,loser.id,winner.id))
    conn.commit()

    if outcome == "peace":
        embed = discord.Embed(title="🕊️ Война завершена — Мирное соглашение",
            description=f"{display(w_country)} и {display(l_country)} заключили мир.\n\nОбе стороны сохраняют свои страны и инвентарь.",color=0x2ecc71)
        embed.set_footer(text=f"Решение: {interaction.user.display_name}")
        await interaction.followup.send(embed=embed)

    elif outcome == "defeat":
        c.execute("SELECT item,amount FROM inventory WHERE user_id=? AND amount>0",(loser.id,))
        loser_items = c.fetchall()
        transferred = []
        for item,amount in loser_items:
            if item.startswith("slots_"): continue
            set_inventory(winner.id,item,amount); set_inventory(loser.id,item,-amount)
            icon = get_mil_emoji(item) if item in ALL_MILITARY_ITEMS else "📦"
            transferred.append(f"• {icon} **{item}** — {amount}")

        c.execute("UPDATE countries SET taken=0 WHERE name=?",(l_country,))
        c.execute("DELETE FROM players WHERE user_id=?",(loser.id,))
        c.execute("DELETE FROM inventory WHERE user_id=?",(loser.id,))
        conn.commit()

        player_role = discord.utils.get(guild.roles,name="Player")
        unreg_role  = discord.utils.get(guild.roles,name="Unregistred")
        if player_role and player_role in loser.roles: await loser.remove_roles(player_role)
        if unreg_role: await loser.add_roles(unreg_role)
        try: await loser.edit(nick=None)
        except: pass

        embed = discord.Embed(title="⚔️ Война завершена — Полное поражение",color=0xe74c3c)
        embed.add_field(name="🏆 Победитель",value=f"{display(w_country)}\n{winner.mention}",inline=True)
        embed.add_field(name="💀 Побеждённый",value=f"{display(l_country)}\n{loser.mention}",inline=True)
        embed.add_field(name="\u200b",value="\u200b",inline=True)
        embed.add_field(name="📦 Передано победителю",value="\n".join(transferred)[:1024] if transferred else "Инвентарь был пуст",inline=False)
        embed.add_field(name="🔄 Последствия",value=f"• Страна **{ru(l_country)}** освобождена\n• Роль Player снята\n• Ник сброшен\n• Весь инвентарь передан победителю",inline=False)
        embed.set_footer(text=f"Решение: {interaction.user.display_name}")
        await interaction.followup.send(embed=embed)

# ----------------------------------------------------------------
# DECLARE WAR
# ----------------------------------------------------------------

@bot.command()
async def declarewar(ctx, target: discord.Member):
    if ctx.channel.id != WAR_CHANNEL_ID:
        await ctx.send("❌ Войну можно объявить только в канале войны."); return
    if ctx.author.id == target.id:
        await ctx.send("❌ Нельзя объявить войну самому себе."); return
    if target.bot:
        await ctx.send("❌ Нельзя объявить войну боту."); return

    row_a = c.execute("SELECT country FROM players WHERE user_id=?",(ctx.author.id,)).fetchone()
    row_d = c.execute("SELECT country FROM players WHERE user_id=?",(target.id,)).fetchone()
    if not row_a:
        await ctx.send("❌ Вы не зарегистрированы."); return
    if not row_d:
        await ctx.send("❌ Цель не зарегистрирована."); return

    a_country = row_a[0]; d_country = row_d[0]
    if a_country == d_country:
        await ctx.send("❌ Нельзя объявить войну своей же стране."); return

    if get_active_war(ctx.author.id, target.id):
        await ctx.send("❌ Война между этими странами уже идёт."); return

    c.execute("INSERT INTO wars (attacker_id,defender_id,attacker_country,defender_country,status,guild_id,created_at) VALUES (?,?,?,?,?,?,?)",
              (ctx.author.id,target.id,a_country,d_country,"active",ctx.guild.id,time.time()))
    conn.commit()

    embed = discord.Embed(title="⚔️ ВОЙНА ОБЪЯВЛЕНА",color=0xe74c3c)
    embed.add_field(name="🗡 Нападающий",value=f"{display(a_country)}\n{ctx.author.mention}",inline=True)
    embed.add_field(name="🛡 Обороняющийся",value=f"{display(d_country)}\n{target.mention}",inline=True)
    embed.add_field(name="\u200b",value="\u200b",inline=True)
    embed.add_field(name="📋 Дальнейшие действия",value=(
        "1. Оба игрока отправляют **War Curator** карту боёв\n"
        "2. War Curator запускает сражения:\n"
        "   `/startgroundbattle` — наземная\n"
        "   `/startnavalbattle` — морская\n"
        "   `/startairbattle` — воздушная\n"
        "3. По итогам войны — `/warend`"),inline=False)
    embed.set_footer(text=f"Объявлено: {datetime.now().strftime('%d.%m.%Y %H:%M')}")
    war_cur = discord.utils.get(ctx.guild.roles,name="War Curator")
    ping = war_cur.mention if war_cur else ""
    await ctx.send(ping, embed=embed)

# ----------------------------------------------------------------
# REGISTRATION UI
# ----------------------------------------------------------------

class CountrySelect(discord.ui.Select):
    def __init__(self, available_countries, user_id):
        self.user_id = user_id
        options = [discord.SelectOption(label=ru(cn), value=cn, emoji=flag(cn)) for cn in available_countries[:25]]
        super().__init__(placeholder="Выберите страну...", options=options, min_values=1, max_values=1)

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("Это не ваш выбор.", ephemeral=True); return
        chosen = self.values[0]
        user = interaction.user.id
        c.execute("SELECT country FROM players WHERE user_id=?",(user,))
        if c.fetchone():
            await interaction.response.edit_message(content="Вы уже зарегистрированы!", view=None); return
        c.execute("SELECT taken FROM countries WHERE name=?",(chosen,))
        row = c.fetchone()
        if not row or row[0]==1:
            await interaction.response.edit_message(content="Эта страна уже занята!", view=None); return
        c.execute("UPDATE countries SET taken=1 WHERE name=?",(chosen,))
        c.execute("INSERT INTO players VALUES (?,?,?,?,?,?)",(user,chosen,50000000,0,0,time.time()))
        conn.commit()
        member = interaction.user
        unr = discord.utils.get(member.guild.roles,name="Unregistred")
        plr = discord.utils.get(member.guild.roles,name="Player")
        if unr and unr in member.roles: await member.remove_roles(unr)
        if plr: await member.add_roles(plr)
        try: await member.edit(nick=f"{flag(chosen)} | {ru(chosen)}")
        except: pass
        await interaction.response.edit_message(content=f"{flag(chosen)} Вы теперь играете за **{ru(chosen)}**!\nСтартовый баланс: **50,000,000$**",view=None)

class CountryView(discord.ui.View):
    def __init__(self,available_countries,user_id):
        super().__init__(timeout=120)
        self.add_item(CountrySelect(available_countries,user_id))

class RegionSelect(discord.ui.Select):
    def __init__(self,user_id):
        self.user_id=user_id
        options=[discord.SelectOption(label=region) for region in REGIONS.keys()]
        super().__init__(placeholder="Выберите регион...",options=options,min_values=1,max_values=1)

    async def callback(self,interaction:discord.Interaction):
        if interaction.user.id!=self.user_id:
            await interaction.response.send_message("Это не ваш выбор.",ephemeral=True); return
        region=self.values[0]
        c.execute("SELECT name FROM countries WHERE taken=1")
        taken={row[0] for row in c.fetchall()}
        available=[cn for cn in REGIONS[region] if cn not in taken]
        if not available:
            await interaction.response.edit_message(content=f"В регионе **{region}** все страны заняты.",view=RegionView(self.user_id)); return
        await interaction.response.edit_message(content=f"Регион: **{region}**\nВыберите страну:",view=CountryView(available,self.user_id))

class RegionView(discord.ui.View):
    def __init__(self,user_id):
        super().__init__(timeout=120)
        self.add_item(RegionSelect(user_id))

class QuitConfirmView(discord.ui.View):
    def __init__(self,user_id,country):
        super().__init__(timeout=60)
        self.user_id=user_id; self.country=country

    @discord.ui.button(label="Да",style=discord.ButtonStyle.red)
    async def confirm_quit(self,interaction:discord.Interaction,button:discord.ui.Button):
        if interaction.user.id!=self.user_id:
            await interaction.response.send_message("Это не ваша кнопка.",ephemeral=True); return
        c.execute("UPDATE countries SET taken=0 WHERE name=?",(self.country,))
        c.execute("DELETE FROM players WHERE user_id=?",(self.user_id,))
        c.execute("DELETE FROM inventory WHERE user_id=?",(self.user_id,))
        conn.commit()
        member=interaction.user
        plr=discord.utils.get(member.guild.roles,name="Player")
        unr=discord.utils.get(member.guild.roles,name="Unregistred")
        if plr and plr in member.roles: await member.remove_roles(plr)
        if unr: await member.add_roles(unr)
        try: await member.edit(nick=None)
        except: pass
        await interaction.response.edit_message(content=f"Вы вышли из игры. Страна {display(self.country)} освобождена.",view=None)

    @discord.ui.button(label="Нет",style=discord.ButtonStyle.grey)
    async def cancel_quit(self,interaction:discord.Interaction,button:discord.ui.Button):
        if interaction.user.id!=self.user_id:
            await interaction.response.send_message("Это не ваша кнопка.",ephemeral=True); return
        await interaction.response.edit_message(content="Отменено. Вы остаётесь в игре.",view=None)

class RegisterView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🎮 Играть",style=discord.ButtonStyle.green,custom_id="reg_play")
    async def play(self,interaction:discord.Interaction,button:discord.ui.Button):
        user=interaction.user.id
        c.execute("SELECT country FROM players WHERE user_id=?",(user,))
        row=c.fetchone()
        if row:
            country=row[0]
            await interaction.response.send_message(
                f"Вы уже играете за {display(country)}.\n⚠️ Хотите выйти из игры? Весь прогресс будет потерян.",
                view=QuitConfirmView(user,country),ephemeral=True); return
        await interaction.response.send_message("Выберите регион:",view=RegionView(user),ephemeral=True)

    @discord.ui.button(label="🔴 Занятые страны",style=discord.ButtonStyle.red,custom_id="reg_taken")
    async def taken_list(self,interaction:discord.Interaction,button:discord.ui.Button):
        c.execute("SELECT co.name,p.user_id FROM countries co JOIN players p ON co.name=p.country WHERE co.taken=1 ORDER BY co.name")
        rows=c.fetchall()
        if not rows:
            await interaction.response.send_message("Пока нет занятых стран.",ephemeral=True); return
        embed=discord.Embed(title="🔴 Занятые страны",color=0xff4444)
        text=""
        for cn,uid in rows:
            text+=f"{flag(cn)} **{ru(cn)}** — <@{uid}>\n"
        embed.description=text
        embed.set_footer(text=f"Всего занято: {len(rows)} из {len(ALL_COUNTRIES)}")
        await interaction.response.send_message(embed=embed,ephemeral=True)

# ----------------------------------------------------------------
# TICKET / CLAIM
# ----------------------------------------------------------------

class CloseTicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    @discord.ui.button(label="🔒 Закрыть тикет",style=discord.ButtonStyle.red,custom_id="close_ticket")
    async def close_ticket(self,interaction:discord.Interaction,button:discord.ui.Button):
        await interaction.response.send_message("Закрываю тикет...",ephemeral=True)
        await interaction.channel.delete()

class OpenTicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    @discord.ui.button(label="🎫 Открыть тикет",style=discord.ButtonStyle.green,custom_id="open_ticket")
    async def open_ticket(self,interaction:discord.Interaction,button:discord.ui.Button):
        guild=interaction.guild; member=interaction.user
        safe_name=f"тикет-{member.name.lower().replace(' ','-')}"
        existing=discord.utils.get(guild.text_channels,name=safe_name)
        if existing:
            await interaction.response.send_message(f"У вас уже есть тикет: {existing.mention}",ephemeral=True); return
        overwrites={guild.default_role:discord.PermissionOverwrite(view_channel=False),member:discord.PermissionOverwrite(view_channel=True,send_messages=True,read_message_history=True),guild.me:discord.PermissionOverwrite(view_channel=True,send_messages=True,read_message_history=True)}
        for rn in TICKET_STAFF_ROLES:
            role=discord.utils.get(guild.roles,name=rn)
            if role: overwrites[role]=discord.PermissionOverwrite(view_channel=True,send_messages=True,read_message_history=True)
        if guild.owner: overwrites[guild.owner]=discord.PermissionOverwrite(view_channel=True,send_messages=True,read_message_history=True)
        ch=await guild.create_text_channel(name=safe_name,overwrites=overwrites,category=interaction.channel.category)
        embed=discord.Embed(title="🎫 Тикет открыт",description=f"Добро пожаловать, {member.mention}!\n\nОпишите вашу проблему.\nКогда вопрос решён — нажмите кнопку ниже.",color=0x5865F2)
        embed.set_footer(text="BHD Support")
        await ch.send(embed=embed,view=CloseTicketView())
        helper=discord.utils.get(guild.roles,name="Helper")
        if helper: await ch.send(f"{helper.mention} новый тикет от {member.mention}!")
        await interaction.response.send_message(f"✅ Тикет создан: {ch.mention}",ephemeral=True)

class CloseClaimView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    @discord.ui.button(label="🔒 Закрыть жалобу",style=discord.ButtonStyle.red,custom_id="close_claim")
    async def close_claim(self,interaction:discord.Interaction,button:discord.ui.Button):
        await interaction.response.send_message("Закрываю жалобу...",ephemeral=True)
        await interaction.channel.delete()

class ClaimFormModal(discord.ui.Modal,title="📋 Анкета жалобы"):
    accused=discord.ui.TextInput(label="На кого жалоба?",placeholder="Ник или @упоминание",max_length=100)
    reason=discord.ui.TextInput(label="Причина жалобы",placeholder="Опишите нарушение...",style=discord.TextStyle.paragraph,max_length=500)
    evidence=discord.ui.TextInput(label="Доказательства",placeholder="Ссылки на скриншоты, время...",style=discord.TextStyle.paragraph,max_length=500)
    witnesses=discord.ui.TextInput(label="Свидетели (если есть)",placeholder="Ники или 'нет'",max_length=200,required=False)

    async def on_submit(self,interaction:discord.Interaction):
        guild=interaction.guild; member=interaction.user
        safe_name=f"жалоба-{member.name.lower().replace(' ','-')}"
        existing=discord.utils.get(guild.text_channels,name=safe_name)
        if existing:
            await interaction.response.send_message(f"У вас уже есть жалоба: {existing.mention}",ephemeral=True); return
        overwrites={guild.default_role:discord.PermissionOverwrite(view_channel=False),member:discord.PermissionOverwrite(view_channel=True,send_messages=True,read_message_history=True),guild.me:discord.PermissionOverwrite(view_channel=True,send_messages=True,read_message_history=True)}
        for rn in TICKET_STAFF_ROLES:
            role=discord.utils.get(guild.roles,name=rn)
            if role: overwrites[role]=discord.PermissionOverwrite(view_channel=True,send_messages=True,read_message_history=True)
        if guild.owner: overwrites[guild.owner]=discord.PermissionOverwrite(view_channel=True,send_messages=True,read_message_history=True)
        ch=await guild.create_text_channel(name=safe_name,overwrites=overwrites,category=interaction.channel.category)
        embed=discord.Embed(title="📋 Жалоба подана",color=0xe74c3c)
        embed.add_field(name="👤 Заявитель",value=member.mention,inline=True)
        embed.add_field(name="🎯 На кого",value=self.accused.value,inline=True)
        embed.add_field(name="📝 Причина",value=self.reason.value,inline=False)
        embed.add_field(name="🔍 Доказательства",value=self.evidence.value,inline=False)
        embed.add_field(name="👥 Свидетели",value=self.witnesses.value or "Нет",inline=False)
        embed.set_footer(text="BHD Claims")
        await ch.send(embed=embed,view=CloseClaimView())
        pings=[discord.utils.get(guild.roles,name=rn) for rn in ["Moderator","Main Moderator"]]
        ping_str=" ".join(r.mention for r in pings if r)
        if ping_str: await ch.send(f"{ping_str} новая жалоба от {member.mention}!")
        await interaction.response.send_message(f"✅ Жалоба создана: {ch.mention}",ephemeral=True)

class OpenClaimView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    @discord.ui.button(label="📋 Подать жалобу",style=discord.ButtonStyle.red,custom_id="open_claim")
    async def open_claim(self,interaction:discord.Interaction,button:discord.ui.Button):
        await interaction.response.send_modal(ClaimFormModal())

@bot.command()
async def supportstart(ctx):
    if ctx.author.id!=ctx.guild.owner_id: return
    ch=bot.get_channel(SUPPORT_CHANNEL_ID)
    if not ch: await ctx.send("❌ Канал не найден."); return
    await ch.purge(limit=10,check=lambda m:m.author==bot.user)
    embed=discord.Embed(title="🎫 Поддержка BHD",description="Если у вас возникли вопросы — откройте тикет.\n\nНажмите кнопку ниже и бот создаст личный канал.",color=0x5865F2)
    embed.set_footer(text="BHD Support • Один тикет на пользователя")
    await ch.send(embed=embed,view=OpenTicketView())
    await ctx.message.delete()

@bot.command()
async def claimstart(ctx):
    if ctx.author.id!=ctx.guild.owner_id: return
    ch=bot.get_channel(CLAIM_CHANNEL_ID)
    if not ch: await ctx.send("❌ Канал не найден."); return
    await ch.purge(limit=10,check=lambda m:m.author==bot.user)
    embed=discord.Embed(title="📋 Подача жалоб — BHD",description="Здесь вы можете подать жалобу на другого игрока.\n\nНажмите кнопку ниже и заполните анкету.\n\n⚠️ **Ложные жалобы влекут наказание.**",color=0xe74c3c)
    embed.set_footer(text="BHD Claims • Один тикет на пользователя")
    await ch.send(embed=embed,view=OpenClaimView())
    await ctx.message.delete()

# ----------------------------------------------------------------
# GUIDES
# ----------------------------------------------------------------

@bot.command()
async def guidestart(ctx):
    if ctx.author.id != ctx.guild.owner_id: return
    ch = bot.get_channel(GUIDE_CHANNEL_ID)
    if not ch: await ctx.send("❌ Канал гайда не найден."); return
    await ch.purge(limit=20, check=lambda m: m.author == bot.user)

    e1 = discord.Embed(title="📖 Гайд новичка — BHD", description="Добро пожаловать на сервер **BHD** — военно-политической ролевой игры!\nЗдесь ты управляешь целым государством. Этот гайд поможет тебе разобраться с основами.", color=0x5865F2)
    e1.add_field(name="🌍 Шаг 1 — Регистрация", value="Перейди в канал регистрации и нажми кнопку **🎮 Играть**.\nВыбери регион и страну которой хочешь управлять.\nТы получишь стартовый баланс **50,000,000$** и роль **Player**.", inline=False)
    e1.add_field(name="💰 Шаг 2 — Экономика", value="Используй команду `!balance` чтобы увидеть свой баланс и доход.\nДля накопления средств покупай здания через магазин — они дают **пассивный доход** каждую секунду.\nНе забывай нажимать кнопку **Собрать доход** в команде `!balance`.", inline=False)
    await ch.send(embed=e1)

    e2 = discord.Embed(title="🏪 Магазин — Основы", color=0x27ae60)
    e2.add_field(name="Команды магазина", value="`!shop` — открыть магазин\n`!shop инфраструктура` — здания и объекты\n`!shop ресурсы` — природные ресурсы\n`!shop заводы` — военные заводы\n`!shop военная` — вся военная техника", inline=False)
    e2.add_field(name="Покупка", value="`!buy <название>` — купить 1 единицу\n`!buy <название> <количество>` — купить несколько\n\nПример: `!buy ТРЦ` или `!buy ОБТ 10`", inline=False)
    e2.add_field(name="💡 Совет", value="Начни с покупки **инфраструктуры** — она даёт постоянный доход.\nЗатем вкладывай в **ресурсы** и постепенно строй армию.", inline=False)
    await ch.send(embed=e2)

    e3 = discord.Embed(title="📦 Инвентарь и армия", color=0xf1c40f)
    e3.add_field(name="Команды", value="`!inv` или `!inventory` — посмотреть свой инвентарь\n`!inv @игрок` — посмотреть инвентарь другого игрока\n`!army` — посмотреть военную мощь\n`!army @игрок` — военная мощь другого игрока", inline=False)
    e3.add_field(name="⚔️ Военная техника", value="Для покупки **наземной техники** нужен **Завод бронетехники**\nДля **морской** — **Верфь**\nДля **авиации** — **Авиазавод**\n\nКаждый завод даёт **10 слотов** для покупки техники.\n**Пехотинец** — единственная единица без завода.", inline=False)
    await ch.send(embed=e3)

    e4 = discord.Embed(title="🤝 Дипломатия и ролеплей", color=0x9b59b6)
    e4.add_field(name="Основные принципы", value="• Ты управляешь **реальным государством** на карте мира\n• Можно заключать **союзы**, вести **торговлю**, создавать **альянсы**\n• Все переговоры ведутся в игровых каналах\n• Соблюдай **реализм** — твои действия должны соответствовать возможностям твоей страны", inline=False)
    e4.add_field(name="Советы по ролеплею", value="✅ Пиши от имени правительства своей страны\n✅ Объявляй о решениях официально\n✅ Реагируй на действия других стран\n❌ Не нарушай правила сервера\n❌ Не используй читы и баги", inline=False)
    e4.add_field(name="⚠️ Война", value="Войны объявляются через команду `!declarewar @игрок` в канале войны.\nПодробнее о войнах — смотри **военный гайд**.", inline=False)
    e4.set_footer(text="BHD • Желаем удачи в управлении государством!")
    await ch.send(embed=e4)
    await ctx.message.delete()


@bot.command()
async def warguidestart(ctx):
    if ctx.author.id != ctx.guild.owner_id: return
    ch = bot.get_channel(WAR_GUIDE_CHANNEL_ID)
    if not ch: await ctx.send("❌ Канал военного гайда не найден."); return
    await ch.purge(limit=20, check=lambda m: m.author == bot.user)

    e1 = discord.Embed(title="⚔️ Военный гайд — BHD", description="Полное руководство по системе войны на сервере BHD.", color=0xe74c3c)
    e1.add_field(name="📋 Как объявить войну", value="1. Перейди в **канал войны**\n2. Напиши `!declarewar @противник`\n3. Бот объявит о начале войны и уведомит **War Curator**\n\n⚠️ Нельзя объявить войну самому себе или незарегистрированному игроку.", inline=False)
    e1.add_field(name="🗺️ Подготовка к бою", value="После объявления войны **оба игрока** должны:\n• Составить **карту боёв** — список техники которую они хотят применить\n• Отправить её **War Curator** в личные сообщения\n• Указать тип сражения: наземное, морское или воздушное", inline=False)
    await ch.send(embed=e1)

    e2 = discord.Embed(title="🎲 Система сражений", color=0xe67e22)
    e2.add_field(name="Типы сражений", value="🛡 `/startgroundbattle` — **Наземное** (танки, пехота, артиллерия)\n⚓ `/startnavalbattle` — **Морское** (корабли, подводные лодки)\n✈️ `/startairbattle` — **Воздушное** (истребители, вертолёты, БПЛА)", inline=False)
    e2.add_field(name="Как работает ролл", value="Бот рассчитывает **военную мощь** каждой стороны на основе техники.\n\nЧем больше мощь — тем **выше максимальный ролл**.\nПобеждает тот у кого ролл выше.\n\nПример:\n• Атакующий: мощь 500 → ролл до 100\n• Обороняющийся: мощь 200 → ролл до 40\nАтакующий имеет явное преимущество, но не гарантированную победу.", inline=False)
    e2.add_field(name="💀 Потери", value="После каждого сражения **обе стороны несут потери**.\nЧем слабее твоя армия по сравнению с противником — тем **больше потерь**.\nПотери **автоматически списываются** с инвентаря.", inline=False)
    await ch.send(embed=e2)

    e3 = discord.Embed(title="📊 Очки военной мощи", color=0x3498db)
    e3.add_field(name="Пехота", value=f"{get_mil_emoji('Пехотинец')} Пехотинец — 1 очко", inline=True)
    e3.add_field(name="Наземная техника (выборка)", value=(
        f"{get_mil_emoji('Грузовик')} Грузовик — 2\n"
        f"{get_mil_emoji('БТР')} БТР — 8\n"
        f"{get_mil_emoji('БМП')} БМП — 10\n"
        f"{get_mil_emoji('ОБТ')} ОБТ — 35\n"
        f"{get_mil_emoji('Баллистическая ракета')} Балл. ракета — 100"), inline=True)
    e3.add_field(name="Флот и авиация (выборка)", value=(
        f"{get_mil_emoji('Фрегат')} Фрегат — 60\n"
        f"{get_mil_emoji('Эсминец')} Эсминец — 80\n"
        f"{get_mil_emoji('Авианосец')} Авианосец — 300\n"
        f"{get_mil_emoji('Истребитель')} Истребитель — 70\n"
        f"{get_mil_emoji('Истребитель 5 поколения')} Ист. 5 пок. — 150"), inline=True)
    await ch.send(embed=e3)

    e4 = discord.Embed(title="🏁 Завершение войны", color=0x2ecc71)
    e4.add_field(name="Команда `/warend`", value="War Curator или старший admin завершает войну командой `/warend`.\nНужно указать **победителя**, **проигравшего** и **исход**.", inline=False)
    e4.add_field(name="🕊️ Мирное соглашение", value="Война завершается **ничьёй**.\nОбе стороны сохраняют страны, инвентарь и прогресс.\nОбычно выбирается когда силы равны.", inline=False)
    e4.add_field(name="💀 Поражение", value="Проигравший **теряет всё**:\n• Страна освобождается\n• Весь инвентарь передаётся победителю\n• Роль Player снимается, выдаётся Unregistred\n• Ник сбрасывается\n\nПроигравший может зарегистрироваться снова и выбрать новую страну.", inline=False)
    e4.add_field(name="💡 Советы", value="• Строй **разнообразную армию** — наземная техника + флот + авиация\n• Не воюй без подготовки — сначала накопи достаточно техники\n• Заключай **военные союзы** с другими игроками\n• Следи за **военной мощью** противника через `!army @игрок`", inline=False)
    e4.set_footer(text="BHD • Удачи на полях сражений!")
    await ch.send(embed=e4)
    await ctx.message.delete()

# ----------------------------------------------------------------
# SHOP
# ----------------------------------------------------------------

ITEMS_PER_PAGE = 6

def build_shop_page(cat, page):
    if cat=="инфраструктура":
        items=list(INFRASTRUCTURE.items()); total=(len(items)+ITEMS_PER_PAGE-1)//ITEMS_PER_PAGE
        page=max(0,min(page,total-1)); chunk=items[page*ITEMS_PER_PAGE:(page+1)*ITEMS_PER_PAGE]
        embed=discord.Embed(title="🏗 Инфраструктура",description="Здания дают пассивный доход каждую секунду.",color=0x3498db)
        for name,(price,income,desc) in chunk:
            embed.add_field(name=f"🏢 {name}",value=f"💰 `{price:,}$`\n📈 +`{income}$/сек`\n_{desc}_",inline=True)
    elif cat=="ресурсы":
        items=list(RESOURCES.items()); total=(len(items)+ITEMS_PER_PAGE-1)//ITEMS_PER_PAGE
        page=max(0,min(page,total-1)); chunk=items[page*ITEMS_PER_PAGE:(page+1)*ITEMS_PER_PAGE]
        embed=discord.Embed(title="🌾 Ресурсы",description="Природные и промышленные ресурсы.",color=0x27ae60)
        for name,(price,income,desc,req) in chunk:
            req_line=f"\n⚠️ Требует: **{req}**" if req else ""
            embed.add_field(name=f"📦 {name}",value=f"💰 `{price:,}$`\n📈 +`{income}$/сек`\n_{desc}_{req_line}",inline=True)
    elif cat=="военная":
        all_items=[(name,price,cls,desc) for name,(price,cls,desc) in MILITARY.items()]
        total=(len(all_items)+ITEMS_PER_PAGE-1)//ITEMS_PER_PAGE
        page=max(0,min(page,total-1)); chunk=all_items[page*ITEMS_PER_PAGE:(page+1)*ITEMS_PER_PAGE]
        fn={"ground":"Завод бронетехники","sea":"Верфь","air":"Авиазавод"}
        ci={"ground":"🛡","sea":"⚓","air":"✈️"}
        classes=[cl for _,_,cl,_ in chunk if cl]
        classes=list(dict.fromkeys(classes))
        dt=" | ".join(f"{ci[cl]} {fn[cl]}" for cl in classes) if classes else "Не требует завода"
        embed=discord.Embed(title="⚔️ Военная техника",description=dt,color=0xe74c3c)
        for name,price,cls,desc in chunk:
            sn=f"\n{ci[cls]} {fn[cls]}" if cls else "\n✅ Без завода"
            embed.add_field(name=f"{get_mil_emoji(name)} {name}",value=f"💰 `{price:,}$`\n_{desc}_{sn}",inline=True)
    elif cat=="заводы":
        items=list(FACTORIES.items()); total=(len(items)+ITEMS_PER_PAGE-1)//ITEMS_PER_PAGE
        page=max(0,min(page,total-1)); chunk=items[page*ITEMS_PER_PAGE:(page+1)*ITEMS_PER_PAGE]
        fi={"ground":"🛡","sea":"⚓","air":"✈️"}
        embed=discord.Embed(title="🏭 Заводы",description="Каждый завод даёт **10 слотов** для покупки военной техники.",color=0xe67e22)
        for name,(price,slots,cls,desc) in chunk:
            embed.add_field(name=f"🏭 {name}",value=f"💰 `{price:,}$`\n🎰 +`{slots} слотов`\n{fi[cls]} {MILITARY_CLASS_LABEL[cls]}\n_{desc}_",inline=True)
    else:
        return None, 0
    embed.set_footer(text=f"Страница {page+1} / {total}  •  !buy <название> [кол-во]")
    return embed, total

class ShopView(discord.ui.View):
    def __init__(self,cat,page,total,user_id):
        super().__init__(timeout=120)
        self.cat=cat; self.page=page; self.total=total; self.user_id=user_id
        self._upd()
    def _upd(self):
        self.prev_btn.disabled=self.page==0
        self.next_btn.disabled=self.page>=self.total-1
    @discord.ui.button(label="◀ Назад",style=discord.ButtonStyle.secondary)
    async def prev_btn(self,interaction,button):
        if interaction.user.id!=self.user_id:
            await interaction.response.send_message("Это не ваш магазин.",ephemeral=True); return
        self.page-=1; embed,self.total=build_shop_page(self.cat,self.page); self._upd()
        await interaction.response.edit_message(embed=embed,view=self)
    @discord.ui.button(label="Вперёд ▶",style=discord.ButtonStyle.secondary)
    async def next_btn(self,interaction,button):
        if interaction.user.id!=self.user_id:
            await interaction.response.send_message("Это не ваш магазин.",ephemeral=True); return
        self.page+=1; embed,self.total=build_shop_page(self.cat,self.page); self._upd()
        await interaction.response.edit_message(embed=embed,view=self)

@bot.command()
async def shop(ctx, category: str = None):
    cats=["инфраструктура","ресурсы","военная","заводы"]
    if category is None or category.lower() not in cats:
        embed=discord.Embed(title="🏪 Магазин — BHD",color=0x2b2d31)
        embed.add_field(name="🏗 Инфраструктура",value="`!shop инфраструктура`",inline=True)
        embed.add_field(name="🌾 Ресурсы",value="`!shop ресурсы`",inline=True)
        embed.add_field(name="\u200b",value="\u200b",inline=True)
        embed.add_field(name="🏭 Заводы",value="`!shop заводы`",inline=True)
        embed.add_field(name="⚔️ Военная техника",value="`!shop военная`",inline=True)
        embed.add_field(name="\u200b",value="\u200b",inline=True)
        embed.set_footer(text="!buy <название> [кол-во]")
        await ctx.send(embed=embed); return
    cat=category.lower()
    embed,total=build_shop_page(cat,0)
    if embed is None: await ctx.send("❌ Категория не найдена."); return
    await ctx.send(embed=embed,view=ShopView(cat,0,total,ctx.author.id))

# ----------------------------------------------------------------
# BUY
# ----------------------------------------------------------------

ALL_ITEMS=list(INFRASTRUCTURE.keys())+list(RESOURCES.keys())+list(FACTORIES.keys())+list(MILITARY.keys())

def resolve_item(query):
    q=query.lower().strip()
    for name in ALL_ITEMS:
        if name.lower()==q: return name,[]
    matches=[name for name in ALL_ITEMS if name.lower().startswith(q)]
    if not matches: matches=[name for name in ALL_ITEMS if q in name.lower()]
    if len(matches)==1: return matches[0],[]
    return None,matches

@bot.command()
async def buy(ctx, *, args: str):
    parts=args.rsplit(" ",1)
    if len(parts)==2 and parts[1].isdigit(): raw_item,amount=parts[0],int(parts[1])
    else: raw_item,amount=args,1
    if amount<1: await ctx.send("Количество должно быть не менее 1."); return
    item,candidates=resolve_item(raw_item)
    if item is None:
        if candidates: await ctx.send("Найдено несколько совпадений:\n"+"\n".join(f"• **{n}**" for n in candidates))
        else: await ctx.send(f"❌ Товар **{raw_item}** не найден.")
        return
    user=ctx.author.id
    c.execute("SELECT balance FROM players WHERE user_id=?",(user,))
    row=c.fetchone()
    if not row: await ctx.send("Вы не зарегистрированы."); return
    balance=row[0]
    if item in INFRASTRUCTURE:
        price,income,desc=INFRASTRUCTURE[item]; cost=price*amount
        if balance<cost: await ctx.send(f"Недостаточно средств. Нужно **{cost:,}$**, есть **{int(balance):,}$**."); return
        c.execute("UPDATE players SET balance=balance-?,income_per_sec=income_per_sec+? WHERE user_id=?",(cost,income*amount,user))
        set_inventory(user,item,amount); conn.commit()
        await ctx.send(f"✅ Куплено **{amount}x {item}**. Доход: +**{income*amount}$/сек**."); return
    if item in RESOURCES:
        price,income,desc,req=RESOURCES[item]
        if req and get_inventory_amount(user,req)<1: await ctx.send(f"❌ Для покупки **{item}** нужна **{req}**."); return
        cost=price*amount
        if balance<cost: await ctx.send(f"Недостаточно средств. Нужно **{cost:,}$**, есть **{int(balance):,}$**."); return
        c.execute("UPDATE players SET balance=balance-?,income_per_sec=income_per_sec+? WHERE user_id=?",(cost,income*amount,user))
        set_inventory(user,item,amount); conn.commit()
        await ctx.send(f"✅ Куплено **{amount}x {item}**. Доход: +**{income*amount}$/сек**."); return
    if item in FACTORIES:
        price,slots,cls,desc=FACTORIES[item]; cost=price*amount
        if balance<cost: await ctx.send(f"Недостаточно средств. Нужно **{cost:,}$**, есть **{int(balance):,}$**."); return
        sk=FACTORY_CLASS_SLOT[cls]
        c.execute("UPDATE players SET balance=balance-? WHERE user_id=?",(cost,user))
        set_inventory(user,item,amount); set_inventory(user,sk,slots*amount); conn.commit()
        await ctx.send(f"✅ Куплен **{amount}x {item}**. Добавлено **{slots*amount}** слотов."); return
    if item in MILITARY:
        price,cls,desc=MILITARY[item]; emoji=get_mil_emoji(item)
        if cls is None:
            cost=price*amount
            if balance<cost: await ctx.send(f"Недостаточно средств. Нужно **{cost:,}$**, есть **{int(balance):,}$**."); return
            c.execute("UPDATE players SET balance=balance-? WHERE user_id=?",(cost,user))
            set_inventory(user,item,amount); conn.commit()
            await ctx.send(f"✅ Куплено **{amount}x {emoji} {item}** за **{cost:,}$**."); return
        sk=FACTORY_CLASS_SLOT[cls]; avail=get_inventory_amount(user,sk)
        if avail<amount:
            fn=next(n for n,(_,__,fc,___) in FACTORIES.items() if fc==cls)
            await ctx.send(f"❌ Недостаточно слотов.\nДоступно: **{avail}**, нужно: **{amount}**.\nКупите **{fn}**."); return
        cost=price*amount
        if balance<cost: await ctx.send(f"Недостаточно средств. Нужно **{cost:,}$**, есть **{int(balance):,}$**."); return
        c.execute("UPDATE players SET balance=balance-? WHERE user_id=?",(cost,user))
        set_inventory(user,item,amount); set_inventory(user,sk,-amount); conn.commit()
        await ctx.send(f"✅ Куплено **{amount}x {emoji} {item}** за **{cost:,}$**. Осталось слотов: **{avail-amount}**."); return
    await ctx.send(f"❌ Предмет **{item}** не найден.")

# ----------------------------------------------------------------
# BALANCE
# ----------------------------------------------------------------

class CollectButton(discord.ui.View):
    def __init__(self,user_id):
        super().__init__(timeout=None); self.user_id=user_id
    @discord.ui.button(label="Собрать доход",style=discord.ButtonStyle.green)
    async def collect(self,interaction,button):
        if interaction.user.id!=self.user_id:
            await interaction.response.send_message("Это не ваша кнопка.",ephemeral=True); return
        update_income(self.user_id)
        c.execute("SELECT income_buffer FROM players WHERE user_id=?",(self.user_id,))
        income=c.fetchone()[0]
        c.execute("UPDATE players SET balance=balance+?,income_buffer=0 WHERE user_id=?",(income,self.user_id))
        conn.commit()
        await interaction.response.send_message(f"Вы собрали **{int(income)}$**!",ephemeral=True)

@bot.command()
async def balance(ctx):
    user=ctx.author.id
    c.execute("SELECT balance,income_per_sec,income_buffer,country FROM players WHERE user_id=?",(user,))
    data=c.fetchone()
    if not data: await ctx.send("Вы не зарегистрированы."); return
    update_income(user)
    c.execute("SELECT balance,income_per_sec,income_buffer,country FROM players WHERE user_id=?",(user,))
    bal,income_ps,buffer,country=c.fetchone()
    embed=discord.Embed(title=f"{display(country)} — Экономика",color=0x00ff88)
    embed.add_field(name="Баланс",value=f"{int(bal):,}$")
    embed.add_field(name="Доход/сек",value=f"{income_ps}$")
    embed.add_field(name="Доступно к сбору",value=f"{int(buffer):,}$")
    await ctx.send(embed=embed,view=CollectButton(user))

# ----------------------------------------------------------------
# INVENTORY
# ----------------------------------------------------------------

INV_ITEMS_PER_PAGE=10

def get_inventory_pages(user_id):
    c.execute("SELECT item,amount FROM inventory WHERE user_id=? AND amount>0 ORDER BY item",(user_id,))
    rows=c.fetchall()
    infra,res,mil,fac,slots=[],[],[],[],[]
    for item,amount in rows:
        if item in INFRASTRUCTURE: infra.append(f"🏢 **{item}** — {amount}")
        elif item in RESOURCES: res.append(f"📦 **{item}** — {amount}")
        elif item in ALL_MILITARY_ITEMS: mil.append(f"{get_mil_emoji(item)} **{item}** — {amount}")
        elif item in FACTORIES: fac.append(f"🏭 **{item}** — {amount}")
        elif item.startswith("slots_"):
            sl={"slots_ground":"🛡 Слоты наземной","slots_sea":"⚓ Слоты морской","slots_air":"✈️ Слоты авиации"}
            slots.append(f"{sl.get(item,item)}: **{amount}**")
    all_lines=[]
    if infra: all_lines+=["**🏗 Инфраструктура**"]+infra
    if res: all_lines+=["**🌾 Ресурсы**"]+res
    if fac: all_lines+=["**🏭 Заводы**"]+fac
    if slots: all_lines+=["**🎰 Слоты**"]+slots
    if mil: all_lines+=["**⚔️ Военная техника**"]+mil
    pages=[]
    page=[]
    for line in all_lines:
        page.append(line)
        if len(page)>=INV_ITEMS_PER_PAGE:
            pages.append("\n".join(page)); page=[]
    if page: pages.append("\n".join(page))
    return pages if pages else ["Инвентарь пуст."]

def build_inv_embed(user_id,country,page_idx):
    pages=get_inventory_pages(user_id); total=len(pages)
    page_idx=max(0,min(page_idx,total-1))
    embed=discord.Embed(title=f"{display(country)} — Инвентарь",description=pages[page_idx],color=0xf1c40f)
    embed.set_footer(text=f"Страница {page_idx+1} / {total}")
    return embed,total

class InvView(discord.ui.View):
    def __init__(self,user_id,country,page,total):
        super().__init__(timeout=120)
        self.user_id=user_id; self.country=country; self.page=page; self.total=total; self._upd()
    def _upd(self):
        self.prev_btn.disabled=self.page==0; self.next_btn.disabled=self.page>=self.total-1
    @discord.ui.button(label="◀ Назад",style=discord.ButtonStyle.secondary)
    async def prev_btn(self,interaction,button):
        self.page-=1; embed,self.total=build_inv_embed(self.user_id,self.country,self.page); self._upd()
        await interaction.response.edit_message(embed=embed,view=self)
    @discord.ui.button(label="Вперёд ▶",style=discord.ButtonStyle.secondary)
    async def next_btn(self,interaction,button):
        self.page+=1; embed,self.total=build_inv_embed(self.user_id,self.country,self.page); self._upd()
        await interaction.response.edit_message(embed=embed,view=self)

@bot.command(aliases=["inventory"])
async def inv(ctx, member: discord.Member = None):
    target=member or ctx.author
    c.execute("SELECT country FROM players WHERE user_id=?",(target.id,))
    row=c.fetchone()
    if not row: await ctx.send("Игрок не зарегистрирован." if target!=ctx.author else "Вы не зарегистрированы."); return
    country=row[0]; embed,total=build_inv_embed(target.id,country,0)
    await ctx.send(embed=embed,view=InvView(target.id,country,0,total))

# ----------------------------------------------------------------
# ARMY
# ----------------------------------------------------------------

def build_mil_inv_embed(user_id,country):
    c.execute("SELECT item,amount FROM inventory WHERE user_id=? AND amount>0",(user_id,))
    rows=c.fetchall()
    mil_items=[(item,amt) for item,amt in rows if item in ALL_MILITARY_ITEMS]
    embed=discord.Embed(title=f"{display(country)} — Военный инвентарь",color=0xe74c3c)
    if not mil_items: embed.description="Военный инвентарь пуст."; return embed
    total_power=0; text=""
    for name,amt in sorted(mil_items):
        power=MILITARY_POWER.get(name,0)*amt; total_power+=power
        text+=f"{get_mil_emoji(name)} **{name}** — {amt} _(+{power} очков)_\n"
    embed.description=text; embed.set_footer(text=f"⚔️ Военная мощь: {total_power:,} очков")
    return embed

@bot.command()
async def army(ctx, member: discord.Member = None):
    target=member or ctx.author
    c.execute("SELECT country FROM players WHERE user_id=?",(target.id,))
    row=c.fetchone()
    if not row: await ctx.send("Игрок не зарегистрирован." if target!=ctx.author else "Вы не зарегистрированы."); return
    country=row[0]
    c.execute("SELECT item,amount FROM inventory WHERE user_id=? AND amount>0",(target.id,))
    rows=c.fetchall()
    mil_items=[(item,amt) for item,amt in rows if item in ALL_MILITARY_ITEMS]
    if not mil_items: await ctx.send(f"{display(country)} не имеет военной техники."); return
    total_power=sum(MILITARY_POWER.get(n,0)*a for n,a in mil_items)
    if total_power<100: tier="🪖 Ополчение"
    elif total_power<500: tier="⚔️ Регулярная армия"
    elif total_power<2000: tier="🛡 Боеспособная армия"
    elif total_power<5000: tier="💪 Сильная армия"
    elif total_power<15000: tier="🔥 Мощная армия"
    else: tier="☢️ Сверхдержава"
    embed=discord.Embed(title=f"{display(country)} — Военная мощь",description=f"**{tier}**\n⚔️ Очков мощи: **{total_power:,}**",color=0xe74c3c)
    ground,sea,air,inf=[],[],[],[]
    for name,amt in sorted(mil_items):
        cls=MILITARY.get(name,(None,None,None))[1]
        line=f"{get_mil_emoji(name)} {name} — **{amt}**"
        if cls=="ground": ground.append(line)
        elif cls=="sea": sea.append(line)
        elif cls=="air": air.append(line)
        else: inf.append(line)
    if inf: embed.add_field(name=f"{get_mil_emoji('Пехотинец')} Пехота",value="\n".join(inf),inline=False)
    if ground: embed.add_field(name="🛡 Наземная техника",value="\n".join(ground),inline=False)
    if sea: embed.add_field(name="⚓ Морская техника",value="\n".join(sea),inline=False)
    if air: embed.add_field(name="✈️ Авиация",value="\n".join(air),inline=False)
    uid=target.id; cntry=country
    class AV(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=120)
        @discord.ui.button(label="⚔️ Военный инвентарь",style=discord.ButtonStyle.red)
        async def mil_inv(self,interaction,button):
            await interaction.response.send_message(embed=build_mil_inv_embed(uid,cntry),ephemeral=True)
    await ctx.send(embed=embed,view=AV())

# ----------------------------------------------------------------
# ADMIN
# ----------------------------------------------------------------

ROLES_MUTE={"Moderator","Main Moderator","Admin Assistant","War Curator","Head Curator","Main Administrator","Head Administrator","Coder","Co Owner"}
ROLES_KICK={"Moderator","Main Moderator","Admin Assistant","War Curator","Head Curator","Main Administrator","Head Administrator","Coder","Co Owner"}
ROLES_BAN={"Main Moderator","Admin Assistant","War Curator","Head Curator","Main Administrator","Head Administrator","Coder","Co Owner"}
ROLES_MONEY={"Admin Assistant","War Curator","Head Curator","Main Administrator","Head Administrator","Coder","Co Owner"}
ROLES_ITEMS={"Main Administrator","Head Administrator","Coder","Co Owner"}
ROLES_RESET={"Main Administrator","Head Administrator","Coder","Co Owner"}
ROLES_ALL={"Head Administrator","Coder","Co Owner"}
ROLES_WARN={"Helper","Moderator","Main Moderator","Admin Assistant","War Curator","Head Curator","Main Administrator","Head Administrator","Coder","Co Owner"}

def staff_has(ctx,allowed_roles):
    if ctx.author.id==ctx.guild.owner_id: return True
    return any(r.name in allowed_roles for r in ctx.author.roles)

def parse_duration(s):
    s=s.strip().lower()
    if s.startswith("min"):
        try: return timedelta(minutes=int(s[3:]))
        except: return None
    if s.startswith("hour"):
        try: return timedelta(hours=int(s[4:]))
        except: return None
    if s.startswith("day"):
        try: return timedelta(days=int(s[3:]))
        except: return None
    return None

@bot.command()
async def warn(ctx,member:discord.Member,*,reason:str="Не указана"):
    if not staff_has(ctx,ROLES_WARN): return
    embed=discord.Embed(title="⚠️ Предупреждение",color=0xf1c40f)
    embed.add_field(name="Игрок",value=member.mention); embed.add_field(name="Причина",value=reason); embed.add_field(name="Выдал",value=ctx.author.mention)
    await ctx.send(embed=embed)
    try: await member.send(f"⚠️ Вы получили предупреждение на сервере **{ctx.guild.name}**.\nПричина: **{reason}**")
    except: pass

@bot.command()
async def mute(ctx,member:discord.Member,duration:str,*,reason:str="Не указана"):
    if not staff_has(ctx,ROLES_MUTE): return
    delta=parse_duration(duration)
    if not delta: await ctx.send("❌ Формат: `min30`, `hour2`, `day1`"); return
    try:
        await member.timeout(delta,reason=f"{reason} | {ctx.author}")
        embed=discord.Embed(title="🔇 Мут",color=0xe67e22)
        embed.add_field(name="Игрок",value=member.mention); embed.add_field(name="Срок",value=duration); embed.add_field(name="Причина",value=reason); embed.add_field(name="Выдал",value=ctx.author.mention)
        await ctx.send(embed=embed)
    except discord.Forbidden: await ctx.send("❌ Нет прав.")

@bot.command()
async def unmute(ctx,member:discord.Member):
    if not staff_has(ctx,ROLES_MUTE): return
    try: await member.timeout(None); await ctx.send(f"🔊 {member.mention} размучен.")
    except: await ctx.send("❌ Нет прав.")

@bot.command()
async def kick(ctx,member:discord.Member,*,reason:str="Не указана"):
    if not staff_has(ctx,ROLES_KICK): return
    try:
        await member.kick(reason=reason)
        embed=discord.Embed(title="👢 Кик",color=0xe67e22)
        embed.add_field(name="Игрок",value=str(member)); embed.add_field(name="Причина",value=reason); embed.add_field(name="Выдал",value=ctx.author.mention)
        await ctx.send(embed=embed)
    except: await ctx.send("❌ Нет прав.")

@bot.command()
async def ban(ctx,member:discord.Member,duration:str,*,reason:str="Не указана"):
    if not staff_has(ctx,ROLES_BAN): return
    delta=parse_duration(duration)
    if not delta: await ctx.send("❌ Формат: `min30`, `hour2`, `day1`"); return
    try:
        await member.ban(reason=reason)
        unban_at=time.time()+delta.total_seconds()
        c.execute("INSERT OR REPLACE INTO tempbans VALUES (?,?,?)",(member.id,ctx.guild.id,unban_at)); conn.commit()
        embed=discord.Embed(title="🔨 Бан",color=0xe74c3c)
        embed.add_field(name="Игрок",value=str(member)); embed.add_field(name="Срок",value=duration); embed.add_field(name="Причина",value=reason); embed.add_field(name="Выдал",value=ctx.author.mention)
        await ctx.send(embed=embed)
    except: await ctx.send("❌ Нет прав.")

@bot.command()
async def unban(ctx,user_id:int):
    if not staff_has(ctx,ROLES_BAN): return
    try:
        await ctx.guild.unban(discord.Object(id=user_id))
        c.execute("DELETE FROM tempbans WHERE user_id=?",(user_id,)); conn.commit()
        await ctx.send(f"✅ Пользователь `{user_id}` разбанен.")
    except: await ctx.send("❌ Не найден в банлисте.")

@bot.command()
async def addmoney(ctx,member:discord.Member,amount:float):
    if not staff_has(ctx,ROLES_MONEY): return
    c.execute("SELECT user_id FROM players WHERE user_id=?",(member.id,))
    if not c.fetchone(): await ctx.send("❌ Игрок не зарегистрирован."); return
    c.execute("UPDATE players SET balance=balance+? WHERE user_id=?",(amount,member.id)); conn.commit()
    await ctx.send(f"💰 {member.mention} начислено **{int(amount):,}$**.")

@bot.command()
async def takemoney(ctx,member:discord.Member,amount:float):
    if not staff_has(ctx,ROLES_MONEY): return
    c.execute("SELECT user_id FROM players WHERE user_id=?",(member.id,))
    if not c.fetchone(): await ctx.send("❌ Игрок не зарегистрирован."); return
    c.execute("UPDATE players SET balance=MAX(0,balance-?) WHERE user_id=?",(amount,member.id)); conn.commit()
    await ctx.send(f"💸 У {member.mention} снято **{int(amount):,}$**.")

@bot.command()
async def setmoney(ctx,member:discord.Member,amount:float):
    if not staff_has(ctx,ROLES_MONEY): return
    c.execute("SELECT user_id FROM players WHERE user_id=?",(member.id,))
    if not c.fetchone(): await ctx.send("❌ Игрок не зарегистрирован."); return
    c.execute("UPDATE players SET balance=? WHERE user_id=?",(amount,member.id)); conn.commit()
    await ctx.send(f"💵 Баланс {member.mention} установлен: **{int(amount):,}$**.")

@bot.command()
async def addincome(ctx,member:discord.Member,amount:float):
    if not staff_has(ctx,ROLES_MONEY): return
    c.execute("SELECT user_id FROM players WHERE user_id=?",(member.id,))
    if not c.fetchone(): await ctx.send("❌ Игрок не зарегистрирован."); return
    c.execute("UPDATE players SET income_per_sec=income_per_sec+? WHERE user_id=?",(amount,member.id)); conn.commit()
    await ctx.send(f"📈 {member.mention} добавлено **{amount}$/сек**.")

@bot.command()
async def takeincome(ctx,member:discord.Member,amount:float):
    if not staff_has(ctx,ROLES_MONEY): return
    c.execute("SELECT user_id FROM players WHERE user_id=?",(member.id,))
    if not c.fetchone(): await ctx.send("❌ Игрок не зарегистрирован."); return
    c.execute("UPDATE players SET income_per_sec=MAX(0,income_per_sec-?) WHERE user_id=?",(amount,member.id)); conn.commit()
    await ctx.send(f"📉 У {member.mention} снято **{amount}$/сек**.")

@bot.command()
async def additem(ctx,member:discord.Member,amount:int,*,item:str):
    if not staff_has(ctx,ROLES_ITEMS): return
    resolved,candidates=resolve_item(item)
    if resolved is None:
        if candidates: await ctx.send("Найдено несколько:\n"+"\n".join(f"• **{n}**" for n in candidates))
        else: await ctx.send(f"❌ Товар **{item}** не найден.")
        return
    c.execute("SELECT user_id FROM players WHERE user_id=?",(member.id,))
    if not c.fetchone(): await ctx.send("❌ Игрок не зарегистрирован."); return
    set_inventory(member.id,resolved,amount)
    await ctx.send(f"📦 {member.mention} получил **{amount}x {resolved}**.")

@bot.command()
async def takeinventory(ctx,member:discord.Member,amount:int,*,item:str):
    if not staff_has(ctx,ROLES_ITEMS): return
    resolved,candidates=resolve_item(item)
    if resolved is None:
        if candidates: await ctx.send("Найдено несколько:\n"+"\n".join(f"• **{n}**" for n in candidates))
        else: await ctx.send(f"❌ Товар **{item}** не найден.")
        return
    current=get_inventory_amount(member.id,resolved)
    if current==0: await ctx.send(f"❌ У {member.mention} нет **{resolved}**."); return
    remove=min(amount,current); set_inventory(member.id,resolved,-remove)
    await ctx.send(f"📤 У {member.mention} изъято **{remove}x {resolved}**.")

@bot.command()
async def clearinv(ctx,member:discord.Member):
    if not staff_has(ctx,ROLES_ITEMS): return
    c.execute("DELETE FROM inventory WHERE user_id=?",(member.id,)); conn.commit()
    await ctx.send(f"🗑️ Инвентарь {member.mention} очищен.")

@bot.command()
async def playerinfo(ctx,member:discord.Member=None):
    target=member or ctx.author
    if not staff_has(ctx,ROLES_WARN) and target!=ctx.author: return
    c.execute("SELECT country,balance,income_per_sec FROM players WHERE user_id=?",(target.id,))
    row=c.fetchone()
    if not row: await ctx.send("❌ Игрок не зарегистрирован."); return
    country,balance,income=row
    c.execute("SELECT COUNT(*) FROM inventory WHERE user_id=? AND amount>0",(target.id,))
    item_count=c.fetchone()[0]
    embed=discord.Embed(title=f"{display(country)} — Информация",color=0x5865F2)
    embed.set_thumbnail(url=target.display_avatar.url)
    embed.add_field(name="👤 Игрок",value=target.mention)
    embed.add_field(name="🌍 Страна",value=display(country))
    embed.add_field(name="💰 Баланс",value=f"{int(balance):,}$")
    embed.add_field(name="📈 Доход/сек",value=f"{income}$")
    embed.add_field(name="📦 Предметов",value=str(item_count))
    await ctx.send(embed=embed)

@bot.command()
async def reset(ctx,member:discord.Member):
    if not staff_has(ctx,ROLES_RESET): return
    c.execute("SELECT country FROM players WHERE user_id=?",(member.id,))
    row=c.fetchone()
    if not row: await ctx.send("❌ Игрок не зарегистрирован."); return
    country=row[0]
    c.execute("UPDATE countries SET taken=0 WHERE name=?",(country,))
    c.execute("DELETE FROM players WHERE user_id=?",(member.id,))
    c.execute("DELETE FROM inventory WHERE user_id=?",(member.id,))
    conn.commit()
    plr=discord.utils.get(ctx.guild.roles,name="Player"); unr=discord.utils.get(ctx.guild.roles,name="Unregistred")
    if plr and plr in member.roles: await member.remove_roles(plr)
    if unr: await member.add_roles(unr)
    try: await member.edit(nick=None)
    except: pass
    await ctx.send(f"🔄 {member.mention} сброшен. Страна **{ru(country)}** освобождена.")

@bot.command()
async def resetall(ctx):
    if not staff_has(ctx,ROLES_ALL): return
    c.execute("SELECT user_id,country FROM players"); players=c.fetchall()
    c.execute("UPDATE countries SET taken=0"); c.execute("DELETE FROM players"); c.execute("DELETE FROM inventory"); conn.commit()
    plr=discord.utils.get(ctx.guild.roles,name="Player"); unr=discord.utils.get(ctx.guild.roles,name="Unregistred")
    count=0
    for uid,_ in players:
        member=ctx.guild.get_member(uid)
        if member:
            if plr and plr in member.roles: await member.remove_roles(plr)
            if unr: await member.add_roles(unr)
            try: await member.edit(nick=None)
            except: pass
            count+=1
    await ctx.send(f"🔄 Сброшено **{count}** игроков.")

@bot.command()
async def cleaninventoryall(ctx):
    if not staff_has(ctx,ROLES_ALL): return
    c.execute("DELETE FROM inventory"); conn.commit()
    await ctx.send("🗑️ Инвентарь всех игроков очищен.")

@bot.command()
async def adminhelp(ctx):
    if not staff_has(ctx,ROLES_WARN): return
    embed=discord.Embed(title="🛠 Админ команды — BHD",color=0x5865F2)
    embed.add_field(name="👮 Модерация (Helper+)",value="`!warn @user причина`\n`!playerinfo @user`",inline=False)
    embed.add_field(name="🔇 Мут/Кик (Moderator+)",value="`!mute @user time причина`\n`!unmute @user`\n`!kick @user причина`",inline=False)
    embed.add_field(name="🔨 Бан (Main Moderator+)",value="`!ban @user time причина`\n`!unban user_id`",inline=False)
    embed.add_field(name="💰 Деньги (Admin Assistant+)",value="`!addmoney` `!takemoney` `!setmoney`\n`!addincome` `!takeincome`",inline=False)
    embed.add_field(name="📦 Предметы (Main Administrator+)",value="`!additem @user кол-во предмет`\n`!takeinventory @user кол-во предмет`\n`!clearinv @user`",inline=False)
    embed.add_field(name="🔄 Сброс (Main Administrator+)",value="`!reset @user`",inline=False)
    embed.add_field(name="☢️ Глобальные (Head Administrator+)",value="`!resetall` `!cleaninventoryall`",inline=False)
    embed.add_field(name="⚔️ Война (War Curator+)",value="`!declarewar @user`\n`/startgroundbattle` `/startnavalbattle` `/startairbattle`\n`/warend`",inline=False)
    await ctx.send(embed=embed)

# ----------------------------------------------------------------
# TASKS
# ----------------------------------------------------------------

@tasks.loop(seconds=60)
async def check_tempbans():
    now=time.time()
    c.execute("SELECT user_id,guild_id FROM tempbans WHERE unban_at<=?",(now,))
    rows=c.fetchall()
    for uid,gid in rows:
        guild=bot.get_guild(gid)
        if guild:
            try: await guild.unban(discord.Object(id=uid))
            except: pass
        c.execute("DELETE FROM tempbans WHERE user_id=?",(uid,))
    conn.commit()

@tasks.loop(seconds=60)
async def update_date_channel():
    channel=bot.get_channel(DATE_CHANNEL_ID)
    if not channel: return
    rp_date=get_current_roleplay_date()
    date_str=f"{rp_date.day}.{rp_date.month:02d}.{rp_date.year}"
    await channel.edit(name=f"〔🕰〕Date: {date_str}")

async def update_members_channel(guild):
    channel=bot.get_channel(MEMBERS_CHANNEL_ID)
    if channel: await channel.edit(name=f"〔👥〕Members: {guild.member_count}")

@bot.event
async def on_member_join(member):
    role=discord.utils.get(member.guild.roles,name="Unregistred")
    if role: await member.add_roles(role)
    await update_members_channel(member.guild)

@bot.event
async def on_member_remove(member):
    await update_members_channel(member.guild)

# ----------------------------------------------------------------
# RULEBOOK
# ----------------------------------------------------------------

RULEBOOK_SECTIONS=[
    {"title":"📜 ПРАВИЛА ВОЕННО-ПОЛИТИЧЕСКОГО RP СЕРВЕРА","color":0x5865F2,"description":"Добро пожаловать на сервер **BHD**.\nВнимательно ознакомьтесь с правилами.\n**Незнание правил не освобождает от ответственности.**",
     "fields":[("§1 · Основные положения","**1.1** Стратегическая ролевая игра.\n**1.2** Цель — интересная политическая игра.\n**1.3** Уважайте атмосферу игры.\n**1.4** Разрушение игры запрещено.\n**1.5** Незнание правил не освобождает от ответственности."),("§2 · Поведение","**2.1** Уважайте друг друга.\n**2.2** Оскорбления и токсичность запрещены.\n**2.3** Конфликты — только в рамках игры.\n**2.4** Провокации запрещены.\n**2.5** Решения администрации обязательны.")]},
    {"title":None,"color":0x2ecc71,"description":None,"fields":[("§3 · Аккаунты","**3.1** Один игрок — одна страна.\n**3.2** Мультиаккаунты запрещены.\n**3.3** Передача страны — только с разрешения.\n**3.4** Обход правил запрещён."),("§4 · Экономика","**4.1** Экономика — основа государства.\n**4.2** Все действия — через бота.\n**4.3** Скрипты запрещены.\n**4.4** Баги запрещено использовать."),("§5 · Армия","**5.1** Армия — через систему бота.\n**5.2** Нереальное накопление ограничивается.\n**5.3** Обход системы запрещён.")]},
    {"title":None,"color":0xe67e22,"description":None,"fields":[("§6 · Дипломатия","**6.1** Союзы допустимы.\n**6.2** Соглашения добровольны.\n**6.3** Нарушение договоров — часть игры."),("§7 · Войны","**7.1** Войны — часть игры.\n**7.2** Всё через систему бота.\n**7.3** Война вне системы запрещена."),("§8 · Бот","**8.1** Спам запрещён.\n**8.2** Взлом запрещён.\n**8.3** Об ошибках сообщайте в тикет.")]},
    {"title":None,"color":0xe74c3c,"description":None,"fields":[("§9 · Администрация","**9.1** Администрация следит за игрой.\n**9.2** Вмешательство при необходимости.\n**9.3** Решения окончательны.\n**9.4** Наказания: предупреждение, мут, бан, сброс."),("§10 · Цель","**10.1** Честная и интересная игра.\n**10.2** Уважайте других игроков.\n**10.3** Создавайте интересные ситуации.")]},
]

async def send_rulebook(channel):
    for section in RULEBOOK_SECTIONS:
        embed=discord.Embed(color=section["color"])
        if section["title"]: embed.title=section["title"]
        if section["description"]: embed.description=section["description"]
        for name,value in section["fields"]: embed.add_field(name=name,value=value,inline=False)
        await channel.send(embed=embed)

def is_owner():
    async def predicate(ctx): return ctx.author.id==ctx.guild.owner_id
    return commands.check(predicate)

@bot.command()
@is_owner()
async def rules(ctx):
    channel=bot.get_channel(RULEBOOK_CHANNEL_ID)
    if not channel: await ctx.send("❌ Канал правил не найден."); return
    await channel.purge(limit=50,check=lambda m:m.author==bot.user)
    await send_rulebook(channel); await ctx.message.delete()

@bot.command()
@is_owner()
async def regstart(ctx):
    channel=bot.get_channel(REGISTRATION_CHANNEL_ID)
    if not channel: await ctx.send("❌ Канал регистрации не найден."); return
    embed=discord.Embed(title="🌍 Регистрация — BHD",description="Нажмите **🎮 Играть**, чтобы выбрать страну.\nНажмите **🔴 Занятые страны**, чтобы увидеть занятых.",color=0x5865F2)
    await channel.send(embed=embed,view=RegisterView()); await ctx.message.delete()

# ----------------------------------------------------------------
# READY
# ----------------------------------------------------------------

@bot.event
async def on_ready():
    print(f"{bot.user} готов!")
    bot.add_view(RegisterView())
    bot.add_view(OpenTicketView()); bot.add_view(CloseTicketView())
    bot.add_view(OpenClaimView()); bot.add_view(CloseClaimView())
    if not get_setting("game_start_time"): set_setting("game_start_time",time.time())
    if not update_date_channel.is_running(): update_date_channel.start()
    if not check_tempbans.is_running(): check_tempbans.start()
    try:
        synced=await bot.tree.sync()
        print(f"Синхронизировано {len(synced)} слеш-команд")
    except Exception as e:
        print(f"Ошибка синхронизации: {e}")
    for guild in bot.guilds:
        await update_members_channel(guild)

if not TOKEN:
    print("ОШИБКА: DISCORD_TOKEN не установлен!")
else:
    bot.run(TOKEN)
