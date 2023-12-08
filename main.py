import telebot
from datetime import datetime
import random
import json

# Inicializar o bot
bot = telebot.TeleBot("6336083371:AAEp2ueanhP_MYR4zcsI0ELBNFovq6XYmPI")  # Substitua pelo token real do seu bot

# ID do grupo onde as informações serão enviadas
GRUPO_ID = -1002124405057  # Substitua pelo ID real do seu grupo

# ID do grupo onde a mensagem de aceitação será enviada
ACEITACAO_GRUPO_ID = -1002049258074  # Substitua pelo ID real do seu grupo de aceitação

# Dicionário para armazenar temporariamente os dados do usuário
user_data = {}
# Dicionário para armazenar permanentemente os IDs de verificação
verification_ids = {}
# Dicionário simulando um banco de dados (em memória)
accepted_users = {}
# Dicionário simulando um banco de dados para o status de verificação
verification_status = {}

# Lista para armazenar permanentemente os usuários verificados
verified_usernames = []

# Load existing data from the database file
try:
    with open('database.json', 'r') as file:
        database = json.load(file)
except FileNotFoundError:
    database = {'accepted_users': {}, 'rejected_users': {}}

# Comando /start
@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "Nossa Verificação É Bem Simples! Ao Iniciar o Bot Com o Comando /verify, você irá responder algumas perguntas simples e aguardar até que a verificação seja concluída.")

# Comando /verify
@bot.message_handler(commands=['verify'])
def verify(message):
    bot.send_message(message.chat.id, "Por favor, diga seu nome completo")
    bot.register_next_step_handler(message, ask_age)

# Função para gerar ID de verificação
def generate_verification_id():
    return f"#{random.randint(10000, 99999)}"

# Função para perguntar a idade
def ask_age(message):
    nome = message.text
    bot.send_message(message.chat.id, "Sua Idade Real!")
    bot.register_next_step_handler(message, ask_video, nome)

# Função para perguntar pelo vídeo
def ask_video(message, nome):
    try:
        idade = int(message.text)
        if idade < 18:
            bot.send_message(message.chat.id, "Desculpe, você não tem idade suficiente para a verificação.")
            return
    except ValueError:
        bot.send_message(message.chat.id, "Por favor, insira uma idade válida.")
        return

    user_data[message.chat.id] = {'nome': nome, 'idade': idade}
    bot.send_message(message.chat.id, "Agora, por favor, envie-nos um vídeo dizendo: Olá Equipe HotVery, Me Chamo... E Desejo Ser Verificada Na Rede!")
    bot.register_next_step_handler(message, send_form)

# Função para enviar o formulário
def send_form(message):
    if message.video:
        user_id = message.chat.id
        user_video = message.video.file_id
        bot.send_video(GRUPO_ID, user_video)

        user_info = f"ID do usuário: {user_id}\n"
        user_info += f"Username: @{message.from_user.username}\n"
        user_info += f"Nome completo: {user_data[user_id]['nome']}\n"
        user_info += f"Idade: {user_data[user_id]['idade']}\n"

        verification_id = generate_verification_id()
        verification_ids[user_id] = verification_id
        accepted_users[user_id] = {'verification_id': verification_id, 'user_info': user_info}

        bot.send_message(GRUPO_ID, user_info)
        del user_data[user_id]

        bot.send_message(user_id, "Sua Solicitação foi Feita, Aguarde! Uma Resposta Será enviada em até 2 dias.")
    else:
        bot.send_message(message.chat.id, "Por favor, envie um vídeo da maneira solicitada para concluir a verificação.")
        bot.register_next_step_handler(message, send_form)

# Comando !aceito
@bot.message_handler(func=lambda message: message.text.lower().startswith('!aceito'))
def aceito(message):
    try:
        user_id_to_notify = int(message.text.split(' ')[1])

        if user_id_to_notify in verification_ids:
            verification_id = verification_ids[user_id_to_notify]
            user_info = accepted_users.get(user_id_to_notify)

            if user_info:
                formatted_message = (
                    f"{verification_id} - @{bot.get_chat(user_id_to_notify).username}\n"
                    f"✅ Conta verificada\n"
                    f"ℹ️ ID: {user_id_to_notify}\n"
                    f"Data da verificação: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                )
                bot.send_message(ACEITACAO_GRUPO_ID, formatted_message)

                bot.send_message(user_id_to_notify, "Parabéns, você foi aceito na Rede HotVery!")

                # Update verification status to 'aceito'
                verification_status[user_id_to_notify] = 'aceito'

                # Store username in verified_usernames
                verified_usernames.append(bot.get_chat(user_id_to_notify).username)

                # Save user as accepted in the database
                database['accepted_users'][bot.get_chat(user_id_to_notify).username] = {
                    'verification_id': verification_id,
                    'user_info': user_info
                }

                # Update the database file
                with open('database.json', 'w') as file:
                    json.dump(database, file, indent=2)
            else:
                bot.send_message(message.chat.id, "Mensagem de aceitação não encontrada para o usuário.")
        else:
            bot.send_message(message.chat.id, "Usuário não encontrado ou não verificado.")
    except (IndexError, ValueError):
        bot.send_message(message.chat.id, "Formato inválido. Use !aceito user_id")

# Comando !negado
@bot.message_handler(func=lambda message: message.text.lower().startswith('!negado'))
def negado(message):
    try:
        user_id_to_notify = int(message.text.split(' ')[1])

        if user_id_to_notify in verification_ids:
            bot.send_message(user_id_to_notify, "Infelizmente não foi possível concluir sua verificação. Tente novamente mais tarde. =(")

            # Update verification status to 'negado'
            verification_status[user_id_to_notify] = 'negado'

            # Save user as rejected in the database
            database['rejected_users'][bot.get_chat(user_id_to_notify).username] = {
                'verification_id': verification_ids[user_id_to_notify]
            }

            # Update the database file
            with open('database.json', 'w') as file:
                json.dump(database, file, indent=2)
        else:
            bot.send_message(message.chat.id, "Usuário não encontrado ou não verificado.")
    except (IndexError, ValueError):
        bot.send_message(message.chat.id, "Formato inválido. Use !negado user_id")

# Comando !verificar
@bot.message_handler(func=lambda message: message.text.lower().startswith('!verificar'))
def verificar(message):
    try:
        username_to_check = message.text.split(' ')[1]

        if username_to_check in database['accepted_users']:
            bot.send_message(message.chat.id, f"👤: @{username_to_check}\n《✅》Usuario Verificado")
        elif username_to_check in database['rejected_users']:
            bot.send_message(message.chat.id, f"👤: @{username_to_check}\n《❌》Usuario Não Verificado")
        else:
            bot.send_message(message.chat.id, f"👤: @{username_to_check}\n《❌》Usuario Não Verificado")
    except (IndexError, ValueError):
        bot.send_message(message.chat.id, "Formato inválido. Use !verificar @username")

# Iniciar o bot
bot.polling()
