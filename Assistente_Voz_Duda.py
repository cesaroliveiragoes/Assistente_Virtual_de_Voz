# Importar bibliotecas para utilizar no assistente de voz
import speech_recognition as sr #reconhecimento de fala
import pyttsx3 # para converter o texto em fala
import requests # para fazer requisição em http
import json # manipular json
import time # manipular tempo
from datetime import datetime # obter a data e hora atual do sistema

# AssistenteDuda é a classe que define a assistente virtual
# self. são os parâmetros que permite que o metodo acesse atributos da instancia atual, no caso, AssistenteDuda
class AssistenteDuda:
    def __init__(self, agenda_file, weather_api_key):
        self.agenda_file = agenda_file # arquivo onde os eventos serão salvos
        self.weather_api_key = weather_api_key # Chave API do OpenWeatherMap
        self.duda = pyttsx3.init() # Inicializar o mecanismo de fala
        self.duda.setProperty('rate', 162) # velocidade da fala
        self.duda.setProperty('volume', 2.0) # volume da fala
        self.duda.setProperty('voice', 'HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Speech\\Voices\\Tokens\\TTS_MS_PT-BR_MARIA_11.0') # definir o modelo da voz, nesse caso, a Maria do Windows
        self.reconhecedor = sr.Recognizer() # inicializar o reconhecedor de fala

    def ouvir_comando(self):
        with sr.Microphone() as mic: # Usar o microfone como entrada/captação de áudio
            self.reconhecedor.adjust_for_ambient_noise(mic, duration=2) # tratar o ruído ambiente
            print("Aguardando comando de voz...") # informar no prompt que está aguardando o comando de voz
            audio = self.reconhecedor.listen(mic, timeout=10) # ouvir o comando
            try:
                comando = self.reconhecedor.recognize_google(audio, language='pt-BR') # Reconhecer usando google
                print(f"Comando reconhecido: {comando}") # Exibir no prompt o comando recebido
                return comando.lower() # retornar o comando com letras minúsculas
            except sr.UnknownValueError:
                print("Não entendi o comando.") # mensagem de erro no prompt caso não conseguir captar a voz
                return ""
            except sr.RequestError:
                self.duda.say("Não consegui acessar o serviço de reconhecimento de voz.") # Mensagem de erro
                self.duda.runAndWait() # executar a fala
                return ""

    def obter_temperatura(self, cidade):
        url = f"http://api.openweathermap.org/data/2.5/weather?q={cidade}&appid={self.weather_api_key}&units=metric&lang=pt_br"
        response = requests.get(url) # requisição http para obter o clima do site da URL da OpenWeatherMap
        dados = response.json() # converter a resposta para um json

        if response.status_code == 200:
            temperatura = dados['main']['temp'] # obter a temperatura
            descricao = dados['weather'][0]['description'] #obter a descrição do clima
            resposta = f"A temperatura em {cidade} é de {temperatura} graus Celsius com {descricao}." # mensagem padronizada com a temperatura
        else:
            resposta = "Não consegui obter a temperatura. Por favor, tente novamente." # mensagem de erro

        return resposta # retornar a resposta da função

    def obter_hora_atual(self):
        agora = datetime.now() # data e hora atual
        hora = agora.strftime("%H:%M") # formatação
        resposta = f"São {hora} agora." # mensagem com a hora atual
        return resposta # retornar a resposta da função

    def responder_pergunta(self, pergunta):
        if "temperatura" in pergunta:
            cidade = "São Paulo"  # considerar cidade são paulo para facilitar o processamento
            resposta = self.obter_temperatura(cidade) # obter a função acima de temperatura
        elif "hora" in pergunta:
            resposta = self.obter_hora_atual() # obter a função de hora acima
        else:
            url = "http://localhost:11434/api/generate" # URL da api do Llama
            input_json = {"model": "llama3.1", "prompt": pergunta} # dados para requisição
            inicio = time.time()  # inicio do tempo
            response = requests.post(url, json=input_json) # outra requisição

            linhas = response.text.strip().split('\n') # dividir a resposta em linhas
            valores_response = [json.loads(linha).get('response') for linha in linhas]
            resposta_completa = ''.join(valores_response) # concatenar as respostas


            resposta = resposta_completa[:250] + '...' if len(resposta_completa) > 200 else resposta_completa # Truncar a resposta para 200 caracteres

            print("Tempo: ", time.time() - inicio) # Exibir o tempo de resposta

        print(f"Resposta: {resposta}") # Exibir a resposta no prompt
        self.duda.say(resposta) # Falar a resposta
        self.duda.runAndWait() # Executar a fala

    def salvar_arquivo(self, evento):
        with open(self.agenda_file, "a", encoding="utf-8") as file: # Abrir o arquivo em modo de anexação
            file.write(evento + "\n") # Salvar o evento no arquivo

    def ler_agenda(self):
        try:
            with open(self.agenda_file, "r", encoding="utf-8") as file: # Abrir o arquivo para leitura
                return file.read() # Ler e retornar o conteúdo do arquivo
        except FileNotFoundError:
            return "Nenhum evento encontrado." # Mensagem se o arquivo não for encontrado

    def executar(self):
        while True:
            self.duda.say("Diga Ok Duda para começar.") # Solicitar que o usuário diga "Ok Duda"
            self.duda.runAndWait()  # Executar a fala

            comando = self.ouvir_comando() # Ouvir o comando do usuário
            if "ok duda" in comando:
                self.duda.say("Diga Mestre, como posso ajudá-lo?") # Pedir o comando do usuário
                self.duda.runAndWait() # executar fala

                while True:
                    comando = self.ouvir_comando() # Ouvir o comando do usuário
                    if comando:
                        print(f"Você disse: {comando}")  # exibir o comando recebido no prompt

                        if "agendar evento" in comando:
                            self.duda.say("Ok, qual evento devo cadastrar?") # perguntar o evento a ser cadastrado
                            self.duda.runAndWait()

                            evento = self.ouvir_comando()
                            if evento:
                                self.salvar_arquivo(evento)
                                self.duda.say(f"Evento '{evento}' cadastrado com sucesso!") # confirma o cadastro
                                self.duda.runAndWait()
                            else:
                                self.duda.say("Não consegui entender o evento.") # mensagem de erro
                                self.duda.runAndWait() #executar a fala

                        elif "ler agenda" in comando:
                            conteudo_agenda = self.ler_agenda() # ler agenda
                            self.duda.say("Aqui está a sua agenda.") # informar que está lendo a agenda
                            self.duda.runAndWait() # executar a fala
                            self.duda.say(conteudo_agenda) # falar o conteudo da agenda
                            self.duda.runAndWait() # executar a fala

                        else:
                            self.responder_pergunta(comando)

                        while True:
                            self.duda.say("Deseja algo mais?") # pergunta se há mais inputs
                            self.duda.runAndWait() # executar a fala

                            resposta = self.ouvir_comando() # ouvir a resposta do usuário
                            if "não" in resposta:
                                self.duda.say("Até mais!") # se a reposta for não, a assistente se despede
                                self.duda.runAndWait()
                                return # encerra a execução
                            elif "sim" in resposta:
                                self.duda.say("O que mais deseja saber?") # pedir mais inputs
                                self.duda.runAndWait() # executar a fala
                                break # voltar para o loop para receber novos comandos
                            else:
                                self.duda.say("Desculpe, não entendi. Por favor, diga 'sim' ou 'não'.")
                                self.duda.runAndWait()
            else:
                self.duda.say("Por favor, diga 'Ok Duda' para começar.") # mensagem de erro para mensagens não reconhecidas
                self.duda.runAndWait() # executar a fala

if __name__ == "__main__":
    agenda_file = r"C:\Users\cesar\Desktop\FIAP\2-Ano\2 Semestre\Deep Learning & AI\agenda.txt" # diretório onde a agenda_file está salvo
    weather_api_key = "b2312a3612650c129498b6c7b10b0e8a"  # chave da api do OpenWeatherMap
    assistente = AssistenteDuda(agenda_file, weather_api_key)
    assistente.executar() # executar a fala
