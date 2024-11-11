import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl
import tkinter as tk
from tkinter import ttk, messagebox
import time
import matplotlib
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt

# Use o backend TkAgg para integração com Tkinter
matplotlib.use("TkAgg")


class InterfaceControleFuzzy:
    def __init__(self, raiz):
        self.raiz = raiz
        self.raiz.title("Sistema de Controle Fuzzy - Chuveiro Inteligente")
        self.raiz.state('zoomed')  # Maximiza a janela

        # Parâmetros das funções de pertinência
        self.parametros_erro_valores = {
            'muito_negativo': [-30, -30, -15],
            'negativo': [-20, -10, 0],
            'neutro': [-5, 0, 5],
            'positivo': [0, 10, 20],
            'muito_positivo': [15, 30, 30]
        }

        self.parametros_var_valores = {
            'diminuindo': [-10, -10, 0],
            'estavel': [-2, 0, 2],
            'aumentando': [0, 10, 10]
        }

        # Criação do sistema fuzzy
        self.configurar_sistema_fuzzy()

        # Variáveis de simulação
        self.temperatura_atual = 20.0  # Inicializa em 20°C
        self.temperatura_desejada = 25.0  # Inicializa em 25°C
        self.ultimo_tempo = time.time()
        self.historico_temp = [self.temperatura_atual]
        self.historico_potencia = [0.0]

        # Flag para controlar o estado da simulação
        self.executando = False

        # Configuração da interface
        self.configurar_interface()

    def configurar_sistema_fuzzy(self):
        # Universos de discurso
        self.erro_temperatura = ctrl.Antecedent(np.arange(-30, 31, 1), 'erro_temperatura')
        self.variacao_temp = ctrl.Antecedent(np.arange(-10, 11, 1), 'variacao_temperatura')
        self.potencia = ctrl.Consequent(np.arange(0, 101, 1), 'potencia')

        # Funções de pertinência para Erro de Temperatura
        for termo, params in self.parametros_erro_valores.items():
            self.erro_temperatura[termo] = fuzz.trimf(self.erro_temperatura.universe, params)

        # Funções de pertinência para Variação de Temperatura
        for termo, params in self.parametros_var_valores.items():
            self.variacao_temp[termo] = fuzz.trimf(self.variacao_temp.universe, params)

        # Funções de pertinência para Potência
        self.potencia['baixa'] = fuzz.trimf(self.potencia.universe, [0, 0, 50])
        self.potencia['media'] = fuzz.trimf(self.potencia.universe, [25, 50, 75])
        self.potencia['alta'] = fuzz.trimf(self.potencia.universe, [50, 100, 100])

        # Regras Corretas
        self.regras = [
            # Regras para Erro Muito Negativo (desired << actual) -> diminuir potência
            ctrl.Rule(self.erro_temperatura['muito_negativo'] & self.variacao_temp['diminuindo'], self.potencia['baixa']),
            ctrl.Rule(self.erro_temperatura['muito_negativo'] & self.variacao_temp['estavel'], self.potencia['baixa']),
            ctrl.Rule(self.erro_temperatura['muito_negativo'] & self.variacao_temp['aumentando'], self.potencia['baixa']),

            # Regras para Erro Negativo (desired < actual)
            ctrl.Rule(self.erro_temperatura['negativo'] & self.variacao_temp['diminuindo'], self.potencia['media']),
            ctrl.Rule(self.erro_temperatura['negativo'] & self.variacao_temp['estavel'], self.potencia['media']),
            ctrl.Rule(self.erro_temperatura['negativo'] & self.variacao_temp['aumentando'], self.potencia['baixa']),

            # Regras para Erro Neutro (desired ≈ actual)
            ctrl.Rule(self.erro_temperatura['neutro'] & self.variacao_temp['diminuindo'], self.potencia['media']),
            ctrl.Rule(self.erro_temperatura['neutro'] & self.variacao_temp['estavel'], self.potencia['media']),
            ctrl.Rule(self.erro_temperatura['neutro'] & self.variacao_temp['aumentando'], self.potencia['media']),

            # Regras para Erro Positivo (desired > actual)
            ctrl.Rule(self.erro_temperatura['positivo'] & self.variacao_temp['diminuindo'], self.potencia['alta']),
            ctrl.Rule(self.erro_temperatura['positivo'] & self.variacao_temp['estavel'], self.potencia['media']),
            ctrl.Rule(self.erro_temperatura['positivo'] & self.variacao_temp['aumentando'], self.potencia['baixa']),

            # Regras para Erro Muito Positivo (desired >> actual)
            ctrl.Rule(self.erro_temperatura['muito_positivo'] & self.variacao_temp['diminuindo'], self.potencia['alta']),
            ctrl.Rule(self.erro_temperatura['muito_positivo'] & self.variacao_temp['estavel'], self.potencia['alta']),
            ctrl.Rule(self.erro_temperatura['muito_positivo'] & self.variacao_temp['aumentando'], self.potencia['alta']),
        ]

        self.sistema_ctrl = ctrl.ControlSystem(self.regras)
        self.simulacao = ctrl.ControlSystemSimulation(self.sistema_ctrl)

    def configurar_interface(self):
        # Criação do notebook (sistema de abas)
        self.notebook = ttk.Notebook(self.raiz)
        self.notebook.pack(fill='both', expand=True, padx=5, pady=5)

        # Criação das abas
        self.abas = {}
        nomes_abas = [
            "Simulação em Tempo Real",
            "Sistema Fuzzy Interno",
            "Regras e Informações",
            "Verificação das Regras",
            "Variáveis e Processos"
        ]
        for nome in nomes_abas:
            aba = ttk.Frame(self.notebook)
            self.notebook.add(aba, text=nome)
            self.abas[nome] = aba

        # Configuração de cada aba
        self.configurar_aba_simulacao()
        self.configurar_aba_fuzzy_interno()
        self.configurar_aba_regras_info()
        self.configurar_aba_verificacao_regras()
        self.configurar_aba_variaveis_processos()

    def configurar_aba_simulacao(self):
        aba = self.abas["Simulação em Tempo Real"]

        # Frame de controles
        frame_controles = ttk.LabelFrame(aba, text="Controles")
        frame_controles.pack(fill='x', padx=5, pady=5)

        # Controle de Temperatura Desejada
        ttk.Label(frame_controles, text="Temperatura Desejada:").pack(side='left', padx=5)

        # Exibir a temperatura desejada
        self.label_temp_desejada = ttk.Label(frame_controles, text=f"{self.temperatura_desejada:.1f}°C")
        self.label_temp_desejada.pack(side='left', padx=5)

        # Criar a escala após criar o label_temp_desejada
        self.escala_temp_desejada = ttk.Scale(
            frame_controles, from_=0, to=50, orient='horizontal',
            command=self.atualizar_temp_desejada
        )
        self.escala_temp_desejada.pack(side='left', padx=5, fill='x', expand=True)
        self.escala_temp_desejada.set(self.temperatura_desejada)

        # Botões de Iniciar, Parar e Resetar Simulação
        frame_botoes = ttk.Frame(frame_controles)
        frame_botoes.pack(side='left', padx=5)

        self.botao_iniciar = ttk.Button(frame_botoes, text="Iniciar Simulação", command=self.iniciar_simulacao)
        self.botao_iniciar.pack(side='left', padx=2)

        self.botao_parar = ttk.Button(frame_botoes, text="Parar Simulação", command=self.parar_simulacao, state='disabled')
        self.botao_parar.pack(side='left', padx=2)

        self.botao_reset = ttk.Button(frame_botoes, text="Resetar Simulação", command=self.reset_simulacao, state='disabled')
        self.botao_reset.pack(side='left', padx=2)

        # Barra de Progresso para Potência
        frame_progresso = ttk.LabelFrame(aba, text="Indicador de Potência")
        frame_progresso.pack(fill='x', padx=5, pady=5)

        self.barra_potencia = ttk.Progressbar(frame_progresso, orient='horizontal', length=400, mode='determinate')
        self.barra_potencia.pack(padx=10, pady=10)
        self.barra_potencia['maximum'] = 100
        self.barra_potencia['value'] = 0

        # Frame para informações de simulação
        frame_info = ttk.LabelFrame(aba, text="Informações da Simulação")
        frame_info.pack(fill='both', expand=True, padx=5, pady=5)

        # Label para exibir a temperatura atual
        self.label_temp_atual_sim = ttk.Label(frame_info, text=f"Temperatura Atual: {self.temperatura_atual:.1f}°C", font=("Arial", 14))
        self.label_temp_atual_sim.pack(pady=10)

        # Label para exibir o erro de temperatura
        self.label_erro_sim = ttk.Label(frame_info, text=f"Erro de Temperatura: {0.0:.1f}°C", font=("Arial", 14))
        self.label_erro_sim.pack(pady=10)

        # Criação dos gráficos
        self.fig, (self.ax_temp, self.ax_pot) = plt.subplots(2, 1, figsize=(8, 6))
        self.fig.tight_layout(pad=3.0)

        # Gráfico de Temperatura
        self.ax_temp.set_title("Histórico de Temperatura")
        self.ax_temp.set_xlabel("Tempo (s)")
        self.ax_temp.set_ylabel("Temperatura (°C)")
        self.line_temp, = self.ax_temp.plot([], [], color='red')

        # Gráfico de Potência
        self.ax_pot.set_title("Histórico de Potência Aplicada")
        self.ax_pot.set_xlabel("Tempo (s)")
        self.ax_pot.set_ylabel("Potência (%)")
        self.line_pot, = self.ax_pot.plot([], [], color='blue')

        # Integração dos gráficos com Tkinter
        self.canvas = FigureCanvasTkAgg(self.fig, master=frame_info)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill='both', expand=True)

    def configurar_aba_fuzzy_interno(self):
        aba = self.abas["Sistema Fuzzy Interno"]

        frame_info = ttk.LabelFrame(aba, text="Funções de Pertinência")
        frame_info.pack(fill='both', expand=True, padx=5, pady=5)

        # Texto para exibir as funções de pertinência
        self.texto_fuzzy = tk.Text(frame_info, wrap=tk.WORD, height=15)
        self.texto_fuzzy.pack(fill='both', expand=True, padx=5, pady=5)
        self.texto_fuzzy.config(state='disabled')
        self.atualizar_fuzzy_interno()

        # Frame para editar funções de pertinência
        frame_editar = ttk.LabelFrame(aba, text="Editar Funções de Pertinência")
        frame_editar.pack(fill='both', expand=True, padx=5, pady=5)

        # Tabelas para Erro de Temperatura
        frame_erro = ttk.LabelFrame(frame_editar, text="Erro de Temperatura")
        frame_erro.pack(side='left', fill='both', expand=True, padx=5, pady=5)

        self.parametros_erro = {}
        termos_erro = ['muito_negativo', 'negativo', 'neutro', 'positivo', 'muito_positivo']
        for i, termo in enumerate(termos_erro):
            ttk.Label(frame_erro, text=termo).grid(row=i, column=0, padx=5, pady=2, sticky='e')
            # Obtém os parâmetros atuais
            a, b, c = self.parametros_erro_valores[termo]
            # Adiciona spinboxes para editar os parâmetros
            ttk.Label(frame_erro, text=f"a:").grid(row=i, column=1, padx=5, pady=2, sticky='e')
            spin_a = tk.Spinbox(frame_erro, from_=-30, to=30, increment=1, width=5)
            spin_a.grid(row=i, column=2, padx=5, pady=2, sticky='w')
            spin_a.delete(0, 'end')
            spin_a.insert(0, a)

            ttk.Label(frame_erro, text=f"b:").grid(row=i, column=3, padx=5, pady=2, sticky='e')
            spin_b = tk.Spinbox(frame_erro, from_=-30, to=30, increment=1, width=5)
            spin_b.grid(row=i, column=4, padx=5, pady=2, sticky='w')
            spin_b.delete(0, 'end')
            spin_b.insert(0, b)

            ttk.Label(frame_erro, text=f"c:").grid(row=i, column=5, padx=5, pady=2, sticky='e')
            spin_c = tk.Spinbox(frame_erro, from_=-30, to=30, increment=1, width=5)
            spin_c.grid(row=i, column=6, padx=5, pady=2, sticky='w')
            spin_c.delete(0, 'end')
            spin_c.insert(0, c)

            self.parametros_erro[termo] = [spin_a, spin_b, spin_c]

        # Tabelas para Variação de Temperatura
        frame_var = ttk.LabelFrame(frame_editar, text="Variação de Temperatura")
        frame_var.pack(side='left', fill='both', expand=True, padx=5, pady=5)

        self.parametros_var = {}
        termos_var = ['diminuindo', 'estavel', 'aumentando']
        for i, termo in enumerate(termos_var):
            ttk.Label(frame_var, text=termo).grid(row=i, column=0, padx=5, pady=2, sticky='e')
            # Obtém os parâmetros atuais
            a, b, c = self.parametros_var_valores[termo]
            # Adiciona spinboxes para editar os parâmetros
            ttk.Label(frame_var, text=f"a:").grid(row=i, column=1, padx=5, pady=2, sticky='e')
            spin_a = tk.Spinbox(frame_var, from_=-10, to=10, increment=1, width=5)
            spin_a.grid(row=i, column=2, padx=5, pady=2, sticky='w')
            spin_a.delete(0, 'end')
            spin_a.insert(0, a)

            ttk.Label(frame_var, text=f"b:").grid(row=i, column=3, padx=5, pady=2, sticky='e')
            spin_b = tk.Spinbox(frame_var, from_=-10, to=10, increment=1, width=5)
            spin_b.grid(row=i, column=4, padx=5, pady=2, sticky='w')
            spin_b.delete(0, 'end')
            spin_b.insert(0, b)

            ttk.Label(frame_var, text=f"c:").grid(row=i, column=5, padx=5, pady=2, sticky='e')
            spin_c = tk.Spinbox(frame_var, from_=-10, to=10, increment=1, width=5)
            spin_c.grid(row=i, column=6, padx=5, pady=2, sticky='w')
            spin_c.delete(0, 'end')
            spin_c.insert(0, c)

            self.parametros_var[termo] = [spin_a, spin_b, spin_c]

        # Botão para Aplicar Alterações
        self.botao_aplicar = ttk.Button(frame_editar, text="Aplicar Alterações", command=self.aplicar_alteracoes_fuzzy)
        self.botao_aplicar.pack(pady=10)

    def configurar_aba_regras_info(self):
        aba = self.abas["Regras e Informações"]

        # Frame para valores crisp
        frame_crisp = ttk.LabelFrame(aba, text="Valores Crisp")
        frame_crisp.pack(fill='x', padx=5, pady=5)

        self.label_temp_atual_crisp = ttk.Label(frame_crisp, text="Temperatura Atual: 0°C")
        self.label_temp_atual_crisp.pack(anchor='w', padx=5, pady=2)

        self.label_variacao_crisp = ttk.Label(frame_crisp, text="Variação: 0°C/s")
        self.label_variacao_crisp.pack(anchor='w', padx=5, pady=2)

        self.label_potencia_crisp = ttk.Label(frame_crisp, text="Potência: 0%")
        self.label_potencia_crisp.pack(anchor='w', padx=5, pady=2)

        # Frame para exibir as regras
        frame_regras = ttk.LabelFrame(aba, text="Base de Regras")
        frame_regras.pack(fill='both', expand=True, padx=5, pady=5)

        self.texto_regras = tk.Text(frame_regras, wrap=tk.WORD, height=25)
        self.texto_regras.pack(fill='both', expand=True, padx=5, pady=5)
        self.texto_regras.config(state='disabled')

        # Inserir as regras
        regras_texto = [
            "Regras do Sistema Fuzzy:",
            "",
            "1. SE erro_muito_negativo E variação_diminuindo ENTÃO potência_baixa",
            "2. SE erro_muito_negativo E variação_estavel ENTÃO potência_baixa",
            "3. SE erro_muito_negativo E variação_aumentando ENTÃO potência_baixa",
            "",
            "4. SE erro_negativo E variação_diminuindo ENTÃO potência_media",
            "5. SE erro_negativo E variação_estavel ENTÃO potência_media",
            "6. SE erro_negativo E variação_aumentando ENTÃO potência_baixa",
            "",
            "7. SE erro_neutro E variação_diminuindo ENTÃO potência_media",
            "8. SE erro_neutro E variação_estavel ENTÃO potência_media",
            "9. SE erro_neutro E variação_aumentando ENTÃO potência_media",
            "",
            "10. SE erro_positivo E variação_diminuindo ENTÃO potência_alta",
            "11. SE erro_positivo E variação_estavel ENTÃO potência_media",
            "12. SE erro_positivo E variação_aumentando ENTÃO potência_baixa",
            "",
            "13. SE erro_muito_positivo E variação_diminuindo ENTÃO potência_alta",
            "14. SE erro_muito_positivo E variação_estavel ENTÃO potência_alta",
            "15. SE erro_muito_positivo E variação_aumentando ENTÃO potência_alta",
        ]
        self.texto_regras.config(state='normal')
        self.texto_regras.insert('1.0', "\n".join(regras_texto))
        self.texto_regras.config(state='disabled')

    def configurar_aba_verificacao_regras(self):
        aba = self.abas["Verificação das Regras"]

        frame_regras_ativas = ttk.LabelFrame(aba, text="Regras Ativas")
        frame_regras_ativas.pack(fill='both', expand=True, padx=5, pady=5)

        self.texto_regras_ativas = tk.Text(frame_regras_ativas, wrap=tk.WORD, height=25)
        self.texto_regras_ativas.pack(fill='both', expand=True, padx=5, pady=5)
        self.texto_regras_ativas.config(state='disabled')

    def configurar_aba_variaveis_processos(self):
        aba = self.abas["Variáveis e Processos"]

        # Frame para variáveis de entrada e fuzzificação
        frame_fuzzificacao = ttk.LabelFrame(aba, text="Variáveis de Entrada e Fuzzificação")
        frame_fuzzificacao.pack(fill='both', expand=True, padx=5, pady=5)

        self.texto_fuzzificacao = tk.Text(frame_fuzzificacao, wrap=tk.WORD, height=15)
        self.texto_fuzzificacao.pack(fill='both', expand=True, padx=5, pady=5)
        self.texto_fuzzificacao.config(state='disabled')

        # Frame para processo de defuzzificação
        frame_defuzzificacao = ttk.LabelFrame(aba, text="Processo de Defuzzificação")
        frame_defuzzificacao.pack(fill='both', expand=True, padx=5, pady=5)

        self.texto_defuzzificacao = tk.Text(frame_defuzzificacao, wrap=tk.WORD, height=10)
        self.texto_defuzzificacao.pack(fill='both', expand=True, padx=5, pady=5)
        self.texto_defuzzificacao.config(state='disabled')

    def iniciar_simulacao(self):
        if not self.executando:
            self.executando = True
            self.botao_iniciar.config(state='disabled')
            self.botao_parar.config(state='normal')
            self.botao_reset.config(state='normal')
            self.atualizar()

    def parar_simulacao(self):
        if self.executando:
            self.executando = False
            self.botao_iniciar.config(state='normal')
            self.botao_parar.config(state='disabled')
            self.botao_reset.config(state='normal')

    def reset_simulacao(self):
        # Resetando as variáveis de simulação
        self.temperatura_atual = 20.0
        self.temperatura_desejada = 25.0
        self.historico_temp = [self.temperatura_atual]
        self.historico_potencia = [0.0]
        self.ultimo_tempo = time.time()

        # Atualizando os widgets
        self.label_temp_desejada.config(text=f"{self.temperatura_desejada:.1f}°C")
        self.escala_temp_desejada.set(self.temperatura_desejada)
        self.label_temp_atual_sim.config(text=f"Temperatura Atual: {self.temperatura_atual:.1f}°C")
        self.label_erro_sim.config(text=f"Erro de Temperatura: {0.0:.1f}°C")
        self.label_temp_atual_crisp.config(text=f"Temperatura Atual: {self.temperatura_atual:.1f}°C")
        self.label_variacao_crisp.config(text=f"Variação: 0°C/s")
        self.label_potencia_crisp.config(text=f"Potência: 0%")
        self.barra_potencia['value'] = 0

        # Resetando os gráficos
        self.line_temp.set_data([], [])
        self.ax_temp.set_xlim(-100, 0)
        self.ax_temp.set_ylim(0, 50)
        self.ax_temp.figure.canvas.draw()

        self.line_pot.set_data([], [])
        self.ax_pot.set_xlim(-100, 0)
        self.ax_pot.set_ylim(0, 100)
        self.ax_pot.figure.canvas.draw()

        # Atualizando os textos de fuzzificação e defuzzificação
        self.atualizar_fuzzy_interno()
        self.atualizar_variaveis_processos_interface(0.0, 0.0, 0.0)
        self.atualizar_verificacao_regras(0.0, 0.0, 0.0)

        # Desativar o botão Reset se a simulação não estiver executando
        if not self.executando:
            self.botao_reset.config(state='disabled')

    def atualizar_temp_desejada(self, valor):
        self.temperatura_desejada = float(valor)
        self.label_temp_desejada.config(text=f"{self.temperatura_desejada:.1f}°C")

    def atualizar_temperatura(self, potencia):
        tempo_atual = time.time()
        delta_t = tempo_atual - self.ultimo_tempo

        # Limitar delta_t para evitar grandes variações
        delta_t = min(delta_t, 1.0)  # Limita delta_t a no máximo 1 segundo

        # Ajuste no fator ambiental para simular troca de calor com o ambiente
        fator_ambiente = -0.05 * (self.temperatura_atual - 20)  # Reduzido para suavizar a variação
        delta_temp = (potencia / 100.0 * 2.0) * delta_t + fator_ambiente * delta_t  # Ajuste no ganho da potência

        # Debugging: Print dos valores de delta_temp
        print(f"Potência: {potencia:.2f}%, Fator Ambiente: {fator_ambiente:.2f}, Delta Temp: {delta_temp:.2f}")

        self.temperatura_atual += delta_temp
        self.ultimo_tempo = tempo_atual
        return delta_temp

    def atualizar_graficos_simulacao(self):
        # Atualiza os gráficos com os históricos
        tempos = np.arange(-len(self.historico_temp)+1, 1, 1)

        # Atualiza o gráfico de temperatura
        self.line_temp.set_data(tempos, self.historico_temp)
        self.ax_temp.set_xlim(min(tempos), max(tempos))
        self.ax_temp.set_ylim(0, 50)
        self.ax_temp.figure.canvas.draw()

        # Atualiza o gráfico de potência
        self.line_pot.set_data(tempos, self.historico_potencia)
        self.ax_pot.set_xlim(min(tempos), max(tempos))
        self.ax_pot.set_ylim(0, 100)
        self.ax_pot.figure.canvas.draw()

    def atualizar_fuzzy_interno(self):
        # Atualiza as informações das funções de pertinência na aba "Sistema Fuzzy Interno"
        info_fuzzy = "Funções de Pertinência para Erro de Temperatura:\n"
        for termo, params in self.parametros_erro_valores.items():
            info_fuzzy += f"  - {termo}: {params}\n"

        info_fuzzy += "\nFunções de Pertinência para Variação de Temperatura:\n"
        for termo, params in self.parametros_var_valores.items():
            info_fuzzy += f"  - {termo}: {params}\n"

        info_fuzzy += "\nFunções de Pertinência para Potência:\n"
        for termo in self.potencia.terms:
            info_fuzzy += f"  - {termo}: {self.potencia[termo].mf.tolist()}\n"

        self.texto_fuzzy.config(state='normal')
        self.texto_fuzzy.delete('1.0', tk.END)
        self.texto_fuzzy.insert('1.0', info_fuzzy)
        self.texto_fuzzy.config(state='disabled')

    def atualizar_valores_crisp(self, erro, variacao, potencia):
        self.label_temp_atual_crisp.config(text=f"Temperatura Atual: {self.temperatura_atual:.1f}°C")
        self.label_variacao_crisp.config(text=f"Variação: {variacao:.2f}°C/s")
        self.label_potencia_crisp.config(text=f"Potência: {potencia:.1f}%")
        self.barra_potencia['value'] = potencia

    def atualizar_verificacao_regras(self, erro, variacao, potencia):
        # Atualiza as regras ativas e suas forças de disparo
        regras_ativas = []
        for i, regra in enumerate(self.regras, start=1):
            # Acessa os termos dos antecedentes usando term1 e term2
            termo_erro = regra.antecedent.term1
            termo_var = regra.antecedent.term2

            # Calcula os graus de pertinência
            grau_erro = fuzz.interp_membership(self.erro_temperatura.universe, self.erro_temperatura[termo_erro.label].mf, erro)
            grau_var = fuzz.interp_membership(self.variacao_temp.universe, self.variacao_temp[termo_var.label].mf, variacao)

            # Calcula a força de disparo como o mínimo dos graus de pertinência
            firing_strength = min(grau_erro, grau_var)

            if firing_strength > 0:
                regras_ativas.append(f"Regra {i}: Força de Disparo = {firing_strength:.2f}")

        # Atualiza o texto na aba de verificação das regras
        self.texto_regras_ativas.config(state='normal')
        self.texto_regras_ativas.delete('1.0', tk.END)
        if regras_ativas:
            self.texto_regras_ativas.insert('1.0', "\n".join(regras_ativas))
        else:
            self.texto_regras_ativas.insert('1.0', "Nenhuma regra ativa.")
        self.texto_regras_ativas.config(state='disabled')

    def atualizar_variaveis_processos_interface(self, erro, variacao, potencia):
        # Atualiza as variáveis de entrada e seus graus de pertinência
        info_fuzzificacao = f"Erro de Temperatura: {erro:.1f}°C\n"
        info_fuzzificacao += f"  - muito_negativo: {fuzz.interp_membership(self.erro_temperatura.universe, self.erro_temperatura['muito_negativo'].mf, erro):.2f}\n"
        info_fuzzificacao += f"  - negativo: {fuzz.interp_membership(self.erro_temperatura.universe, self.erro_temperatura['negativo'].mf, erro):.2f}\n"
        info_fuzzificacao += f"  - neutro: {fuzz.interp_membership(self.erro_temperatura.universe, self.erro_temperatura['neutro'].mf, erro):.2f}\n"
        info_fuzzificacao += f"  - positivo: {fuzz.interp_membership(self.erro_temperatura.universe, self.erro_temperatura['positivo'].mf, erro):.2f}\n"
        info_fuzzificacao += f"  - muito_positivo: {fuzz.interp_membership(self.erro_temperatura.universe, self.erro_temperatura['muito_positivo'].mf, erro):.2f}\n\n"

        info_fuzzificacao += f"Variação de Temperatura: {variacao:.2f}°C/s\n"
        info_fuzzificacao += f"  - diminuindo: {fuzz.interp_membership(self.variacao_temp.universe, self.variacao_temp['diminuindo'].mf, variacao):.2f}\n"
        info_fuzzificacao += f"  - estavel: {fuzz.interp_membership(self.variacao_temp.universe, self.variacao_temp['estavel'].mf, variacao):.2f}\n"
        info_fuzzificacao += f"  - aumentando: {fuzz.interp_membership(self.variacao_temp.universe, self.variacao_temp['aumentando'].mf, variacao):.2f}\n"

        self.texto_fuzzificacao.config(state='normal')
        self.texto_fuzzificacao.delete('1.0', tk.END)
        self.texto_fuzzificacao.insert('1.0', info_fuzzificacao)
        self.texto_fuzzificacao.config(state='disabled')

        # Atualiza o processo de defuzzificação
        info_defuzzificacao = f"Potência Defuzzificada: {potencia:.2f}%\n"
        info_defuzzificacao += f"Agregação das Contribuições das Regras:\n"
        info_defuzzificacao += f"  - Resultado: {potencia:.2f}%"

        self.texto_defuzzificacao.config(state='normal')
        self.texto_defuzzificacao.delete('1.0', tk.END)
        self.texto_defuzzificacao.insert('1.0', info_defuzzificacao)
        self.texto_defuzzificacao.config(state='disabled')

    def aplicar_alteracoes_fuzzy(self):
        # Coleta os novos parâmetros para Erro de Temperatura
        for termo, spins in self.parametros_erro.items():
            try:
                a = float(spins[0].get())
                b = float(spins[1].get())
                c = float(spins[2].get())
                # Atualiza os valores das funções de pertinência
                self.parametros_erro_valores[termo] = [a, b, c]
                self.erro_temperatura[termo].mf = fuzz.trimf(self.erro_temperatura.universe, [a, b, c])
            except ValueError:
                messagebox.showerror("Erro", f"Valores inválidos para a função de pertinência '{termo}'. Certifique-se de inserir números válidos.")
                return

        # Coleta os novos parâmetros para Variação de Temperatura
        for termo, spins in self.parametros_var.items():
            try:
                a = float(spins[0].get())
                b = float(spins[1].get())
                c = float(spins[2].get())
                # Atualiza os valores das funções de pertinência
                self.parametros_var_valores[termo] = [a, b, c]
                self.variacao_temp[termo].mf = fuzz.trimf(self.variacao_temp.universe, [a, b, c])
            except ValueError:
                messagebox.showerror("Erro", f"Valores inválidos para a função de pertinência '{termo}'. Certifique-se de inserir números válidos.")
                return

        # Atualiza o sistema fuzzy com as novas funções de pertinência
        self.configurar_sistema_fuzzy()
        self.simulacao = ctrl.ControlSystemSimulation(self.sistema_ctrl)

        # Atualiza as informações na interface
        self.atualizar_fuzzy_interno()
        messagebox.showinfo("Sucesso", "Funções de pertinência atualizadas com sucesso!")

    def atualizar(self):
        if self.executando:
            # Calcula o erro de temperatura
            erro = self.temperatura_desejada - self.temperatura_atual
            print(f"Erro: {erro:.1f}°C")

            # Calcula a variação de temperatura
            if len(self.historico_temp) > 1:
                variacao = self.historico_temp[-1] - self.historico_temp[-2]
            else:
                variacao = 0.0
            print(f"Variação de Temperatura: {variacao:.2f}°C/s")

            # Atualiza o sistema fuzzy com os valores atuais
            self.simulacao.input['erro_temperatura'] = erro
            self.simulacao.input['variacao_temperatura'] = variacao

            try:
                self.simulacao.compute()
                potencia = self.simulacao.output['potencia']
                print(f"Potência Calculada: {potencia:.2f}%")
            except Exception as e:
                print(f"Erro na computação fuzzy: {e}")
                potencia = 50.0  # Valor padrão em caso de erro

            # Atualiza a temperatura
            self.atualizar_temperatura(potencia)

            # Atualiza históricos
            self.historico_temp.append(self.temperatura_atual)
            self.historico_potencia.append(potencia)

            # Mantém apenas os últimos 100 pontos
            if len(self.historico_temp) > 100:
                self.historico_temp.pop(0)
                self.historico_potencia.pop(0)

            # Atualiza interfaces
            self.atualizar_graficos_simulacao()
            self.label_temp_atual_sim.config(text=f"Temperatura Atual: {self.temperatura_atual:.1f}°C")
            self.label_erro_sim.config(text=f"Erro de Temperatura: {erro:.1f}°C")
            self.atualizar_valores_crisp(erro, variacao, potencia)
            self.atualizar_verificacao_regras(erro, variacao, potencia)
            self.atualizar_variaveis_processos_interface(erro, variacao, potencia)

            # Agenda próxima atualização (a cada 1000 ms)
            self.raiz.after(1000, self.atualizar)


def main():
    raiz = tk.Tk()
    app = InterfaceControleFuzzy(raiz)
    raiz.mainloop()


if __name__ == "__main__":
    main()
