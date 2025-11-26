import os
import mysql.connector
import smtplib
from email.message import EmailMessage
from datetime import datetime

# ----------------------------------------------------------
# 1️⃣ CARREGAR VARIÁVEIS DO GITHUB ACTIONS (env)
# ----------------------------------------------------------
MYSQL_HOST = os.getenv("MYSQL_HOST")
MYSQL_USER = os.getenv("MYSQL_USER")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")
MYSQL_DB = os.getenv("MYSQL_DB")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", 32386))  # Padrão 3306, Railway pode usar outro

EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")

# Email fixo que deve receber TODOS os alertas
EMAIL_DESTINO = "capricelima@gmail.com"  
# Ex.: seuemail@gmail.com

# ----------------------------------------------------------
# 2️⃣ CONECTAR AO MYSQL
# ----------------------------------------------------------
db = mysql.connector.connect(
    host=MYSQL_HOST,
    user=MYSQL_USER,
    password=MYSQL_PASSWORD,
    database=MYSQL_DB,
    port=MYSQL_PORT,
)

cursor = db.cursor(dictionary=True)

# ----------------------------------------------------------
# 3️⃣ BUSCAR ALIMENTOS NÃO ALERTADOS
# ----------------------------------------------------------
cursor.execute(
    "SELECT id, brand, type, expiration_date, alert_sent FROM products WHERE alert_sent = 0"
)
products = cursor.fetchall()

# Data atual (UTC)
today = datetime.utcnow().date()

# ----------------------------------------------------------
# 4️⃣ CONFIGURAR EMAIL (GMAIL)
# ----------------------------------------------------------
server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
server.login(EMAIL_USER, EMAIL_PASS)

# ----------------------------------------------------------
# 5️⃣ PROCESSAR ALIMENTOS
# ----------------------------------------------------------
for food in products:
    expiry_date = food["expiration_date"]

    # Converte string para date, se necessário
    if isinstance(expiry_date, str):
        try:
            expiry_date = datetime.strptime(expiry_date, "%Y-%m-%d").date()
        except ValueError:
            print(f" Data inválida para {food['type']}: {expiry_date}")
            continue  # pula para o próximo alimento

    diff_days = (expiry_date - today).days

    # Envia alerta se faltar entre 1 e 60 dias
    if 0 < diff_days <= 60:
        msg = EmailMessage()
        msg["Subject"] = f" Alerta: {food['type']} vence em {diff_days} dias"
        msg["From"] = EMAIL_USER
        msg["To"] = EMAIL_DESTINO
        msg.set_content(
            f"O alimento '{food['type']}' ({food['brand']}) está com a validade próxima.\n\n"
            f"Data de validade: {expiry_date}\n"
            f"Faltam {diff_days} dias para vencer."
        )

        try:
            server.send_message(msg)
            print(f" Email enviado para {EMAIL_DESTINO}: {food['type']}")

            # Atualiza alert_sent para não enviar novamente
            cursor.execute("UPDATE products SET alert_sent = 1 WHERE id = %s", (food["id"],))
            db.commit()

        except Exception as e:
            print(f" Erro ao enviar email do item {food['type']}: {e}")

# Fecha conexão com servidor e banco
server.quit()
cursor.close()
db.close()

print("✔️ Verificação concluída.")
