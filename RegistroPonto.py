from datetime import datetime as dt, time
import face_recognition as reconhecedor
import colored
import secrets
import random
import simpy
import json

FOTOS_VISITANTES = [
    "faces/todoMundo1.png",
    "faces/todoMundo2.jpg",
    "faces/todoMundo3.jpg",
    "faces/todoMundo4.jpg",
    "faces/todoMundo5.jpg",
    "faces/todoMundo6.jpg"
]
HORARIOS_TRABALHO = {
    'Chandler': {'inicio': '7:00', 'fim': '10:00'},
    'Joey': {'inicio': '8:00', 'fim': '17:00'},
    'Ross': {'inicio': '8:00', 'fim': '10:00'},
    'Phoebe': {'inicio': '7:00', 'fim': '17:00'}
    
    
}
ARQUIVO_DE_CONFIGURACAO = "configuracao.json"

PROBABILIDADE_DE_RECONHECIMENTO = 85
PROBABILIDADE_DE_ENTRADA = 50
PROBABILIDADE_DE_SAIDA = 50

TEMPO_MEDIO_DE_REGISTRO = 80

TEMPO_DE_DETECCAO_DE_FUNCIONARIOS = 50
TEMPO_DE_DETECCAO_DE_ENTRADA = 30
TEMPO_DE_DETECCAO_DE_SAIDA = 20

configuracao = None
funcionarios_reconhecidos = {}

def preparar():
    global configuracao

    configuracao = None
    try:
        with open(ARQUIVO_DE_CONFIGURACAO, "r", encoding='utf-8') as arquivo:
            configuracao = json.load(arquivo)
            if configuracao:
                print("arquivo de configuracao carregado")
            arquivo.close()
    except Exception as e:
        print(f"erro lendo configuração: {str(e)}")
        
#reconhece o funcionario
def reconhecer_funcionarios(ambiente_de_simulacao):
    global configuracao

    print("realizando reconhecimento de funcionarios...")
    for funcionario in configuracao["funcionarios"]:
        codificacoes_conhecidas = []

        for foto in funcionario["fotos"]:
            imagem = reconhecedor.load_image_file(foto)
            codificacao = reconhecedor.face_encodings(imagem)[0]
            codificacoes_conhecidas.append(codificacao)

        for foto in FOTOS_VISITANTES:
            imagem = reconhecedor.load_image_file(foto)
            codificacao = reconhecedor.face_encodings(imagem)[0]

            reconhecimentos = reconhecedor.compare_faces(codificacoes_conhecidas, codificacao)
            if True in reconhecimentos:
                funcionario["tempo_para_reconhecer"] = TEMPO_MEDIO_DE_REGISTRO

                id_atendimento = secrets.token_hex(nbytes=32).upper()
                funcionarios_reconhecidos[id_atendimento] = funcionario

                funcionario["horario_entrada"] = ambiente_de_simulacao.now

                imprimir_dados_do_funcionario(ambiente_de_simulacao, funcionario)

                yield ambiente_de_simulacao.timeout(TEMPO_DE_DETECCAO_DE_FUNCIONARIOS)


def imprimir_dados_do_funcionario(ambiente_de_simulacao, funcionario):
    print(colored.fg('black'), colored.bg('white'), f"funcionario reconhecido em {ambiente_de_simulacao.now}", colored.attr('reset'))
    print(colored.fg('black'), colored.bg('green'), f"nome: {funcionario['nome']}", colored.attr('reset'))
    print(colored.fg('black'), colored.bg('green'), f"idade: {funcionario['idade']}", colored.attr('reset'))
    print(colored.fg('black'), colored.bg('green'), f"cargo: {funcionario['cargo']}", colored.attr('reset'))


#registra a entrada
def registrar_entrada_e_saida(ambiente_de_simulacao):
    global funcionarios_reconhecidos

    while True:
        print(f"Tentando registrar a entrada e saída de um funcionário {ambiente_de_simulacao.now}")

        if len(funcionarios_reconhecidos) > 0:
            for codigo_funcionario, funcionario in list(funcionarios_reconhecidos.items()):
                horario_entrada = dt.combine(dt.now().date(), time(7, 0))  # Exemplo de horário fictício (8:00 AM)
                horario_saida = dt.combine(dt.now().date(), time(10, 0))  # Exemplo de horário fictício (5:00 PM)
                nome_funcionario = funcionario['nome']

                if nome_funcionario in HORARIOS_TRABALHO:
                    horario_inicio = dt.strptime(HORARIOS_TRABALHO[nome_funcionario]['inicio'], '%H:%M').time()
                    horario_fim = dt.strptime(HORARIOS_TRABALHO[nome_funcionario]['fim'], '%H:%M').time()

                    if horario_inicio <= horario_entrada.time() <= horario_fim:
                        print(f"{nome_funcionario} entrou no horário correto: {horario_entrada}")
                    else:
                        print(f"{nome_funcionario} entrou fora do horário de trabalho: {horario_entrada}")

                    if horario_inicio <= horario_saida.time() <= horario_fim:
                        print(f"{nome_funcionario} saiu no horário correto: {horario_saida}")
                    else:
                        print(f"{nome_funcionario} saiu fora do horário de trabalho: {horario_saida}")

                    funcionario["horario_entrada"] = horario_entrada
                    funcionario["horario_saida"] = horario_saida
                    verificar_pendencia(funcionario)

                else:
                    print(f"Não foi possível encontrar o horário de trabalho para {nome_funcionario}")

                del funcionarios_reconhecidos[codigo_funcionario]
                break

        yield ambiente_de_simulacao.timeout(TEMPO_DE_DETECCAO_DE_ENTRADA)

# Verifica se o funcionário possui falta ou pendência
def verificar_pendencia(funcionario):
    nome_funcionario = funcionario['nome']
    horario_entrada = funcionario.get('horario_entrada')
    horario_saida = funcionario.get('horario_saida')

    if nome_funcionario and horario_entrada and horario_saida:
        if nome_funcionario in HORARIOS_TRABALHO:
            horario_inicio = dt.strptime(HORARIOS_TRABALHO[nome_funcionario]['inicio'], '%H:%M').time()
            horario_fim = dt.strptime(HORARIOS_TRABALHO[nome_funcionario]['fim'], '%H:%M').time()

            if horario_inicio <= horario_entrada.time() <= horario_fim:
                print(f"{nome_funcionario} cumpriu o horário de trabalho.")
            else:
                print(f"{nome_funcionario} possui falta ou entrou/saiu em horario diferente")
        else:
            print(f"Não foi possível encontrar o horário de trabalho para {nome_funcionario}")
    else:
        print(f"{nome_funcionario} possui pendência de registro de entrada/saída.")

if __name__ == "__main__":
    preparar()

    ambiente_de_simulacao = simpy.Environment()
    ambiente_de_simulacao.process(reconhecer_funcionarios(ambiente_de_simulacao))
    ambiente_de_simulacao.process(registrar_entrada_e_saida(ambiente_de_simulacao))
    #ambiente_de_simulacao.process(registrar_saida(ambiente_de_simulacao))
    ambiente_de_simulacao.run(until=250)
