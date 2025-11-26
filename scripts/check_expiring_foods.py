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

EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")

# Email fixo que deve receber TODOS os alertas
EMAIL_DESTINO = os.getenv("EMAIL_DESTINO")  
# Ex.: seuemail@gmail.com

# ----------------------------------------------------------
# 2️⃣ CONECTAR AO MYSQL
# ----------------------------------------------------------
db = mysql.connector.connect(
    host=os.getenv("MYSQL_HOST"),
    user=os.getenv("MYSQL_USER"),
    password=os.getenv("MYSQL_PASSWORD"),
    database=os.getenv("MYSQL_DB"),
    port=os.getenv("MYSQL_PORT"),   # IMPORTANTE: Railway usa porta customizada
)


cursor = db.cursor(dictionary=True)

# ----------------------------------------------------------
# 3️⃣ BUSCAR ALIMENTOS NÃO ALERTADOS
# ----------------------------------------------------------
cursor.execute("SELECT id, brand, type, expiration_date, alert_sent FROM products WHERE alert_sent = 0")
foods = cursor.fetchall()

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

    if isinstance(expiry_date, str):
        expiry_date = datetime.strptime(expiry_date, "%Y-%m-%d").date()

    diff_days = (expiry_date - today).days

    if 0 < diff_days <= 60:
        msg = EmailMessage()
        msg["Subject"] = f"⚠️ Alerta: {food['type']} vence em {diff_days} dias"
        msg["From"] = EMAIL_USER
        msg["To"] = EMAIL_DESTINO
        msg.set_content(
            f"O alimento '{food['type']}' está com a validade próxima.\n\n"
            f"Data de validade: {expiration_date}\n"
            f"Faltam {diff_days} dias para vencer."
        )

        try:
            server.send_message(msg)
            print(f"✅ Email enviado para {EMAIL_DESTINO}: {food['type']}")

            cursor.execute("UPDATE products SET alert_sent = 1 WHERE id = %s", (food["id"],))
            db.commit()

        except Exception as e:
            print(f"❌ Erro ao enviar email do item {food['type']}: {e}")

server.quit()
cursor.close()
db.close()

print("✔️ Verificação concluída.")

