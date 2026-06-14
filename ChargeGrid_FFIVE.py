import customtkinter as ctk
import tkinter as tk
import json
import os
import time
import threading
from datetime import datetime
import random
import math

# UI
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

DATA_FILE = "ev_data.json"

class DataManager:

    # carrega os dados JSON. se o arquivo não existir, cria uma versão padrão.
    @staticmethod
    def load_data():
        # dados padrão caso seja a primeira execução
        if not os.path.exists(DATA_FILE):
            default_data = {"users": {}, "settings": {"coupons": {}, "chargers": {
                "Carregador 1": {"charge_speed_kw": 7.0, "max_time_min": 120, "price_per_kwh": 2.0,
                                 "dynamic_pricing": False, "rotation_active": False, "rotation_time_min": 30,
                                 "rotation_pct": 5.0}}}}
            DataManager.save_data(default_data)
            return default_data

        # lê os dados existentes
        with open(DATA_FILE, "r") as f:
            data = json.load(f)

            # prevenção de erros caso não haja uma das variáveis (feito para ajudar no debug)
            for ch_name, ch_data in data["settings"].get("chargers", {}).items():
                if "price_per_kwh" not in ch_data: ch_data["price_per_kwh"] = 2.0
                if "dynamic_pricing" not in ch_data: ch_data["dynamic_pricing"] = False
                if "rotation_active" not in ch_data: ch_data["rotation_active"] = False
                if "rotation_time_min" not in ch_data: ch_data["rotation_time_min"] = 30
                if "rotation_pct" not in ch_data: ch_data["rotation_pct"] = 5.0
            return data

    # salva os dados atuais.
    @staticmethod
    def save_data(data):
        with open(DATA_FILE, "w") as f:
            json.dump(data, f, indent=4)


class FakeModbusSimulator:
    # Inicializa o simulador Modbus associando uma função de callback para exibir as mensagens de log na interface.
    def __init__(self, logger_callback):
        self.logger_callback = logger_callback

    # Gera um sufixo aleatório de 2 bytes simulando o Checksum (CRC) de verificação de erros do protocolo Modbus.
    def _generate_fake_crc(self, payload):
        return f"{random.randint(0, 255):02X}{random.randint(0, 255):02X}"

    # Simula a Função Modbus 06 (Write Single Register) enviando uma requisição de escrita para o hardware e aguardando o ACK.
    def write_register(self, slave_id, register, value, description):
        # Monta o pacote de transmissão e gera um pacote de recepção idêntico (padrão da função 06)
        tx_payload = f"{slave_id:02X} 06 {register:04X} {int(value):04X}"
        tx_crc = self._generate_fake_crc(tx_payload)
        tx_msg = f"{tx_payload} {tx_crc[:2]} {tx_crc[2:]}"
        rx_msg = tx_msg

        # Envia log para a UI e simula atraso de rede
        self.logger_callback(f"[TX] {tx_msg}  -> (WRITE '{description}': {value})")
        time.sleep(0.2)
        self.logger_callback(f"[RX] {rx_msg}  <- (ACK SUCCESS)")

    # Simula a Função Modbus 03 (Read Holding Registers) enviando uma requisição de leitura ao hardware e retornando o valor simulado.
    def read_holding_registers(self, slave_id, register, count, simulated_value, description):
        # Monta a requisição do Mestre (TX)
        tx_payload = f"{slave_id:02X} 03 {register:04X} {count:04X}"
        tx_crc = self._generate_fake_crc(tx_payload)
        tx_msg = f"{tx_payload} {tx_crc[:2]} {tx_crc[2:]}"

        # Monta a resposta simulada do Escravo contendo os dados solicitados (RX)
        bytes_count = count * 2
        rx_payload = f"{slave_id:02X} 03 {bytes_count:02X} {int(simulated_value):04X}"
        rx_crc = self._generate_fake_crc(rx_payload)
        rx_msg = f"{rx_payload} {rx_crc[:2]} {rx_crc[2:]}"

        # Loga a transação e retorna o valor
        self.logger_callback(f"[TX] {tx_msg}  -> (READ '{description}')")
        time.sleep(0.1)
        self.logger_callback(f"[RX] {rx_msg}  <- (DATA RETURNED: {simulated_value})")
        return simulated_value


class ChargeGrid(ctk.CTk):
    # forma a janela principal do app, define o tamanho, carrega dados e decide se abre na tela de login ou direto no menu principal
    def __init__(self):
        super().__init__()
        self.title("Mockup App EvCharger")
        self.geometry("400x750")
        self.resizable(False, False)

        self.data = DataManager.load_data()
        self.current_user = None
        self.current_view = None
        self.charging_sessions = {}

        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.pack(expand=True, fill="both", padx=20, pady=20)

        active_user = self.data["settings"].get("active_session")
        if active_user and active_user in self.data["users"]:
            self.current_user = active_user
            self.show_main_screen()
        else:
            self.show_login_screen()

    # limpa a tela para aparecer uma nova
    def clear_screen(self):
        for widget in self.container.winfo_children():
            widget.destroy()
        self.current_view = None

    # ==========================================
    # TELAS DE LOGIN/CADASTRO
    # ==========================================

    # tela de login com campos para e-mail, senha e botões de navegação e autenticação
    def show_login_screen(self):
        self.clear_screen()
        title = ctk.CTkLabel(self.container, text="EvCharger App", font=("Arial", 28, "bold"))
        title.pack(pady=(50, 40))


        self.entry_email = ctk.CTkEntry(self.container, placeholder_text="E-mail", width=250)
        self.entry_email.pack(pady=10)
        self.entry_password = ctk.CTkEntry(self.container, placeholder_text="Senha", show="*", width=250)
        self.entry_password.pack(pady=10)

        self.lbl_error = ctk.CTkLabel(self.container, text="", text_color="red")
        self.lbl_error.pack()


        btn_login = ctk.CTkButton(self.container, text="Login", command=self.do_login, width=250)
        btn_login.pack(pady=10)
        btn_register = ctk.CTkButton(self.container, text="Cadastro", command=self.show_register_screen, width=250)
        btn_register.pack(pady=10)
        btn_close = ctk.CTkButton(self.container, text="Fechar", command=self.destroy, fg_color="#8B0000",hover_color="#5C0000", width=250)
        btn_close.pack(pady=(50, 0))

    # tela de cadastro com nome, email e senha.
    def show_register_screen(self):
        self.clear_screen()
        title = ctk.CTkLabel(self.container, text="Novo Cadastro", font=("Arial", 24, "bold"))
        title.pack(pady=(50, 40))


        entry_name = ctk.CTkEntry(self.container, placeholder_text="Nome", width=250)
        entry_name.pack(pady=10)
        entry_email = ctk.CTkEntry(self.container, placeholder_text="E-mail", width=250)
        entry_email.pack(pady=10)
        entry_pass = ctk.CTkEntry(self.container, placeholder_text="Senha", show="*", width=250)
        entry_pass.pack(pady=10)

        lbl_msg = ctk.CTkLabel(self.container, text="")
        lbl_msg.pack()

        # validação, verifica a existência prévia do e-mail e salva
        def register():
            name, email, password = entry_name.get(), entry_email.get(), entry_pass.get()
            email_exists = any(u == email for u in self.data["users"].keys())

            if not name or not email or not password:
                lbl_msg.configure(text="Preencha todos os campos.", text_color="red")
            elif email_exists:
                lbl_msg.configure(text="E-mail já cadastrado.", text_color="red")
            else:
                self.data["users"][email] = {"name": name, "password": password, "history": []}
                DataManager.save_data(self.data)
                self.show_login_screen()


        btn_save = ctk.CTkButton(self.container, text="Salvar", command=register, width=250)
        btn_save.pack(pady=20)
        btn_back = ctk.CTkButton(self.container, text="Voltar", command=self.show_login_screen, fg_color="transparent", width=250)
        btn_back.pack()

    # autenticação das credenciais digitadas, inicia a sessão e leva para a tela principal se tiverem certas
    def do_login(self):
        email = self.entry_email.get()
        password = self.entry_password.get()

        if email in self.data["users"] and self.data["users"][email]["password"] == password:
            self.current_user = email
            self.data["settings"]["active_session"] = email
            DataManager.save_data(self.data)
            self.show_main_screen()
        else:
            self.lbl_error.configure(text="Credenciais inválidas!")

    # desloga o usuário, e leva de volta para a tela de autenticação.
    def logout(self):
        self.current_user = None
        self.data["settings"]["active_session"] = None
        DataManager.save_data(self.data)
        self.show_login_screen()

    # ==========================================
    # TELA PRINCIPAL
    # ==========================================

    # Gera a tela principal do app e mostra opções (carregadores, histórico, configurações)
    def show_main_screen(self):
        self.clear_screen()
        user_name = self.data["users"][self.current_user]["name"]

        lbl_welcome = ctk.CTkLabel(self.container, text=f"Bem-vindo(a),\n{user_name}!", font=("Arial", 24, "bold"))
        lbl_welcome.pack(pady=(40, 50))

        btn_charge = ctk.CTkButton(self.container, text="Visualizar Carregadores", height=50, command=self.show_chargers_screen)
        btn_charge.pack(fill="x", pady=10)
        btn_history = ctk.CTkButton(self.container, text="Histórico de Cargas", height=50, command=self.show_history_screen)
        btn_history.pack(fill="x", pady=10)
        btn_settings = ctk.CTkButton(self.container, text="Configurações Globais", height=50, command=self.show_global_settings_screen)
        btn_settings.pack(fill="x", pady=10)
        btn_logout = ctk.CTkButton(self.container, text="Deslogar", height=40, fg_color="transparent", border_width=1, command=self.logout)
        btn_logout.pack(fill="x", pady=(50, 10))
        btn_exit = ctk.CTkButton(self.container, text="Sair", height=40, fg_color="transparent", border_width=1, text_color="red", border_color="red", hover_color="#5C0000", command=self.destroy)
        btn_exit.pack(fill="x", pady=(0, 0))

    # ==========================================
    # TELAS DOS CARREGADORES
    # ==========================================

    # cria a lista de carregadores cadastrados em grade, e permite criar novos ou apagar existentes
    def show_chargers_screen(self):
        self.clear_screen()
        self.current_view = "chargers"

        lbl_title = ctk.CTkLabel(self.container, text="Carregadores", font=("Arial", 24, "bold"))
        lbl_title.pack(pady=(10, 20))

        scroll = ctk.CTkScrollableFrame(self.container, fg_color="transparent")
        scroll.pack(expand=True, fill="both", pady=5)

        # proporções da grade
        scroll.grid_columnconfigure(0, weight=1)
        scroll.grid_columnconfigure(1, weight=1)

        # iteração
        row, col = 0, 0
        chargers = self.data["settings"]["chargers"]
        for charger_name in chargers.keys():
            self.draw_charger_card(scroll, charger_name, row, col)
            col += 1
            if col > 1:
                col = 0
                row += 1

        self.draw_add_charger_card(scroll, row, col)

        btn_back = ctk.CTkButton(self.container, text="Voltar", command=self.show_main_screen, fg_color="transparent")
        btn_back.pack(fill="x", pady=10)

    # desenha o visual do carregador na interface, mostrando nome, indicador de uso, e botões para iniciar carga ou configurar
    def draw_charger_card(self, parent, name, row, col):
        card = ctk.CTkFrame(parent, border_width=3, border_color="#555555", fg_color="#1a1a1a", corner_radius=0)
        card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")

        header = ctk.CTkFrame(card, fg_color="transparent")
        header.pack(fill="x", padx=5, pady=5)

        lbl_name = ctk.CTkLabel(header, text=name, font=("Arial", 12, "bold"))
        lbl_name.pack(side="left")

        btn_remove = ctk.CTkButton(header, text="X", width=20, height=20, fg_color="#8B0000", hover_color="#5C0000", command=lambda n=name: self.remove_charger(n))
        btn_remove.pack(side="right", padx=(5, 0))

        # se o carregador tem uma sessão ativa acender o sinal verde
        is_active = self.charging_sessions.get(name, {}).get("active", False)
        status_color = "#00FF00" if is_active else "#888888"
        lbl_status = ctk.CTkLabel(header, text="●", text_color=status_color, font=("Arial", 20))
        lbl_status.pack(side="right")

        # altera a funcionalidade do botão se tiver ativo ou não
        if is_active:
            btn_start = ctk.CTkButton(card, text="Ver Recarga", fg_color="#28a745", hover_color="#218838", command=lambda n=name: self.show_active_recharge_screen(n))
        else:
            btn_start = ctk.CTkButton(card, text="Iniciar recarga", command=lambda n=name: self.show_recharge_setup(n))
        btn_start.pack(fill="x", padx=10, pady=(10, 5))

        btn_config = ctk.CTkButton(card, text="Configurar", fg_color="transparent", border_width=1, command=lambda n=name: self.show_charger_config_screen(n))
        btn_config.pack(fill="x", padx=10, pady=(0, 10))

    # gera o botão para adicionar novos carregadores
    def draw_add_charger_card(self, parent, row, col):
        card = ctk.CTkFrame(parent, border_width=3, border_color="#555555", fg_color="#1a1a1a", corner_radius=0)
        card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")

        btn_add = ctk.CTkButton(card, text="Adicionar\nCarregador", fg_color="transparent", border_width=2, height=60, command=self.add_charger)
        btn_add.pack(expand=True, fill="both", padx=10, pady=20)

    # cria uma nova instância de carregador com parâmetros padrão no banco de dados
    def add_charger(self):
        # nome incrementando número
        count = len(self.data["settings"]["chargers"]) + 1
        new_name = f"Carregador {count}"
        while new_name in self.data["settings"]["chargers"]:
            count += 1
            new_name = f"Carregador {count}"

        self.data["settings"]["chargers"][new_name] = {"charge_speed_kw": 7.0, "max_time_min": 120,
                                                       "price_per_kwh": 2.0, "dynamic_pricing": False,
                                                       "rotation_active": False, "rotation_time_min": 30,
                                                       "rotation_pct": 5.0}
        DataManager.save_data(self.data)
        self.show_chargers_screen()

    # remove permanentemente um carregador selecionado da memória e do JSON, desde que ele não esteja executando uma sessão ativa de carga
    def remove_charger(self, name):
        if self.charging_sessions.get(name, {}).get("active", False):
            return

        if name in self.data["settings"]["chargers"]:
            del self.data["settings"]["chargers"][name]
            DataManager.save_data(self.data)
            self.show_chargers_screen()

    # ==========================================
    # CONFIGURAÇÃO INDIVIDUAL DO CARREGADOR
    # ==========================================

    # painel de parâmetros técnicos de um carregador específico, alterações possíveis: velocidade, preço base, tempo limite e regras de rotatividade
    def show_charger_config_screen(self, charger_name):
        self.clear_screen()
        config = self.data["settings"]["chargers"][charger_name]

        lbl_title = ctk.CTkLabel(self.container, text=f"Configurar {charger_name}", font=("Arial", 20, "bold"))
        lbl_title.pack(pady=(10, 15))

        # configurações de velocidade co carregador
        lbl_speed = ctk.CTkLabel(self.container, text=f"Velocidade: {config.get('charge_speed_kw', 7.0)} kW")
        lbl_speed.pack(anchor="w")
        slider_speed = ctk.CTkSlider(self.container, from_=7.0, to=22.0, number_of_steps=15)
        slider_speed.set(config.get("charge_speed_kw", 7.0))
        slider_speed.configure(command=lambda val: lbl_speed.configure(text=f"Velocidade: {val:.1f} kW"))
        slider_speed.pack(fill="x", pady=(0, 10))

        # configurações de tempo máximo
        lbl_time = ctk.CTkLabel(self.container, text="Tempo Máximo (min):")
        lbl_time.pack(anchor="w")
        entry_time = ctk.CTkEntry(self.container)
        entry_time.insert(0, str(config.get("max_time_min", 120)))
        entry_time.pack(fill="x", pady=(0, 10))

        # configurações de preço
        lbl_price = ctk.CTkLabel(self.container, text="Preço base por kWh (R$):")
        lbl_price.pack(anchor="w")
        entry_price = ctk.CTkEntry(self.container, placeholder_text="Ex: 2.0")
        entry_price.insert(0, str(config.get("price_per_kwh", 2.0)))
        entry_price.pack(fill="x", pady=(0, 10))

        # switch para regras de preço
        switch_dynamic_var = ctk.BooleanVar(value=config.get("dynamic_pricing", False))
        switch_dynamic = ctk.CTkSwitch(self.container, text="Ativar Tarifação Dinâmica (Pico/Demanda)",variable=switch_dynamic_var)
        switch_dynamic.pack(anchor="w", pady=(5, 5))

        # regras de rotação
        switch_rot_var = ctk.BooleanVar(value=config.get("rotation_active", False))
        switch_rot = ctk.CTkSwitch(self.container, text="Ativar Rotatividade", variable=switch_rot_var)
        switch_rot.pack(anchor="w", pady=(5, 5))

        frame_rot = ctk.CTkFrame(self.container, fg_color="transparent")
        frame_rot.pack(fill="x", pady=(0, 10))

        lbl_rot_time = ctk.CTkLabel(frame_rot, text="Após (min):")
        lbl_rot_time.pack(side="left")
        entry_rot_time = ctk.CTkEntry(frame_rot, width=50)
        entry_rot_time.insert(0, str(config.get("rotation_time_min", 30)))
        entry_rot_time.pack(side="left", padx=(5, 10))

        lbl_rot_pct = ctk.CTkLabel(frame_rot, text="Aumento (%/min):")
        lbl_rot_pct.pack(side="left")
        entry_rot_pct = ctk.CTkEntry(frame_rot, width=50)
        entry_rot_pct.insert(0, str(config.get("rotation_pct", 5.0)))
        entry_rot_pct.pack(side="left", padx=(5, 0))

        lbl_msg = ctk.CTkLabel(self.container, text="", text_color="red")
        lbl_msg.pack()

        # valida e atualiza a configuração interna no banco
        def save_config():
            try:
                max_t = int(entry_time.get())
                price_val = float(entry_price.get().replace(",", "."))
                rot_time_val = int(entry_rot_time.get())
                rot_pct_val = float(entry_rot_pct.get().replace(",", "."))

                if max_t <= 0 or price_val <= 0 or rot_time_val <= 0 or rot_pct_val <= 0: raise ValueError

                self.data["settings"]["chargers"][charger_name]["max_time_min"] = max_t
                self.data["settings"]["chargers"][charger_name]["charge_speed_kw"] = round(slider_speed.get(), 1)
                self.data["settings"]["chargers"][charger_name]["price_per_kwh"] = price_val
                self.data["settings"]["chargers"][charger_name]["dynamic_pricing"] = switch_dynamic_var.get()
                self.data["settings"]["chargers"][charger_name]["rotation_active"] = switch_rot_var.get()
                self.data["settings"]["chargers"][charger_name]["rotation_time_min"] = rot_time_val
                self.data["settings"]["chargers"][charger_name]["rotation_pct"] = rot_pct_val

                DataManager.save_data(self.data)
                self.show_chargers_screen()
            except ValueError:
                lbl_msg.configure(text="Valores inválidos! Verifique os campos.")

        btn_save = ctk.CTkButton(self.container, text="Salvar", command=save_config)
        btn_save.pack(fill="x", pady=10)
        btn_back = ctk.CTkButton(self.container, text="Cancelar", fg_color="transparent", command=self.show_chargers_screen)
        btn_back.pack(fill="x")

    # ==========================================
    # FLUXO DE RECARGA EM SEGUNDO PLANO
    # ==========================================

    # tarifação dinâmica baseada no horário atual (pico de demanda entre 18h e 21h) e na quantidade de estações em uso.
    def get_effective_price(self, charger_name):
        config = self.data["settings"]["chargers"][charger_name]
        base_price = config.get("price_per_kwh", 2.0)

        if not config.get("dynamic_pricing", False):
            return base_price

        # aplica a taxa no horário de pico
        current_hour = datetime.now().hour
        peak_multiplier = 1.0
        if 18 <= current_hour <= 21:
            peak_multiplier = 1.20

        # conta as sessões ativas nas threads para calcular e multiplicar a demanda
        active_chargers = sum(1 for session in self.charging_sessions.values() if session.get("active"))
        demand_multiplier = 1.0 + (0.10 * active_chargers)
        return base_price * peak_multiplier * demand_multiplier

    # tela de definir a recarga, entre limite por tempo ou por valor e aplica cupons
    def show_recharge_setup(self, charger_name):
        self.clear_screen()
        self.charge_mode = ctk.StringVar(value="time")
        config = self.data["settings"]["chargers"][charger_name]

        lbl_title = ctk.CTkLabel(self.container, text=f"Iniciar: {charger_name}", font=("Arial", 20, "bold"))
        lbl_title.pack(pady=(10, 10))

        # informa ao usuário as métricas dinâmicas ativas neste momento
        effective_price = self.get_effective_price(charger_name)
        status_text = f"Preço Base Atual: R$ {effective_price:.2f} / kWh"

        if config.get("dynamic_pricing", False):
            status_text += "\n(Tarifa Dinâmica Ativada)"

        if config.get("rotation_active", False):
            r_time = config.get("rotation_time_min", 30)
            r_pct = config.get("rotation_pct", 5.0)
            status_text += f"\n(Rotatividade: +{r_pct}% a cada min após {r_time}m)"

        lbl_price_info = ctk.CTkLabel(self.container, text=status_text, text_color="yellow")
        lbl_price_info.pack(pady=(0, 20))

        # alternar o modo de cálculo
        frame_mode = ctk.CTkFrame(self.container, fg_color="transparent")
        frame_mode.pack(fill="x")
        ctk.CTkRadioButton(frame_mode, text="Por Tempo (min)", variable=self.charge_mode, value="time").pack(side="left", padx=10)
        ctk.CTkRadioButton(frame_mode, text="Por Valor (R$)", variable=self.charge_mode, value="money").pack(side="right", padx=10)

        self.entry_value = ctk.CTkEntry(self.container, placeholder_text="Digite a quantidade:")
        self.entry_value.pack(fill="x", pady=(20, 10))
        self.entry_coupon = ctk.CTkEntry(self.container, placeholder_text="Cupom de Desconto (opcional)")
        self.entry_coupon.pack(fill="x", pady=10)

        self.lbl_feedback = ctk.CTkLabel(self.container, text="")
        self.lbl_feedback.pack()

        # função matemática, calcula o tempo final, o custo com penalidades de rotatividade incremental e o desconto do cupom
        def advance():
            mode = self.charge_mode.get()
            val_str = self.entry_value.get().replace(",", ".")
            coupon = self.entry_coupon.get().upper()

            try:
                input_value = float(val_str)
                if input_value <= 0: raise ValueError
            except ValueError:
                self.lbl_feedback.configure(text="Insira um valor numérico válido > 0", text_color="red")
                return

            power_kw = config.get("charge_speed_kw", 7.0)
            max_time = config.get("max_time_min", 120)
            price_kwh = self.get_effective_price(charger_name)

            rot_active = config.get("rotation_active", False)
            rot_time = config.get("rotation_time_min", 30)
            rot_pct = config.get("rotation_pct", 5.0) / 100.0

            energy_per_min = power_kw / 60
            cost_per_min = energy_per_min * price_kwh

            total_time_min = 0
            base_cost = 0.0

            # TEMPO
            if mode == "time":
                total_time_min = int(input_value)
                if total_time_min > max_time:
                    self.lbl_feedback.configure(text=f"Tempo excede o máximo ({max_time}m).", text_color="red")
                    return

                # se a rotatividade estiver ativa e o tempo passar da tolerância, aplica progressão aritmetrica
                if rot_active and total_time_min > rot_time:
                    n = total_time_min - rot_time
                    soma_pa = (n * (n + 1)) / 2
                    base_cost = (total_time_min * cost_per_min) + (cost_per_min * rot_pct * soma_pa)
                else:
                    base_cost = total_time_min * cost_per_min

                total_energy_kwh = energy_per_min * total_time_min

            # VALOR
            else:
                max_cost_without_rot = rot_time * cost_per_min if rot_active else float('inf')

                # se o dinheiro acabar antes de atingir a multa de rotatividade
                if not rot_active or input_value <= max_cost_without_rot:
                    total_time_min = int(input_value / cost_per_min)
                    base_cost = total_time_min * cost_per_min
                else:
                    # se o dinheiro precisar pagar a multa, aplica a Fórmula de Bhaskara para encontrar a raiz (minutos) que atinge aquele limite
                    a = (cost_per_min * rot_pct) / 2
                    b = cost_per_min * (1 + (rot_pct / 2))
                    c = (cost_per_min * rot_time) - input_value

                    delta = (b ** 2) - (4 * a * c)
                    if delta < 0:
                        self.lbl_feedback.configure(text="Erro de cálculo com esse valor.", text_color="red")
                        return

                    n = (-b + math.sqrt(delta)) / (2 * a)
                    total_time_min = rot_time + int(n)

                    # ajuste de consistência financeira arredondando para baixo e calculando o valor exato gasto
                    n_int = int(n)
                    soma_pa = (n_int * (n_int + 1)) / 2
                    base_cost = (total_time_min * cost_per_min) + (cost_per_min * rot_pct * soma_pa)

                # trava de segurança para impedir de passar do limite máximo configurado
                if total_time_min > max_time:
                    total_time_min = max_time
                    n_max = total_time_min - rot_time
                    soma_pa_max = (n_max * (n_max + 1)) / 2
                    base_cost = (total_time_min * cost_per_min) + (cost_per_min * rot_pct * soma_pa_max)

                if total_time_min == 0:
                    self.lbl_feedback.configure(text="Valor insuficiente para 1 minuto de carga.", text_color="red")
                    return

                total_energy_kwh = energy_per_min * total_time_min

            # etapa de desconto checando o cupom inserido se existe
            discount = 0
            if coupon:
                if coupon in self.data["settings"]["coupons"]:
                    discount = self.data["settings"]["coupons"][coupon]
                else:
                    self.lbl_feedback.configure(text="Cupom inválido!", text_color="red")
                    return

            final_cost = base_cost * (1 - discount)
            self.show_confirmation_screen(charger_name, total_time_min, total_energy_kwh, final_cost, coupon)

        btn_calc = ctk.CTkButton(self.container, text="Avançar", command=advance)
        btn_calc.pack(fill="x", pady=20)
        btn_back = ctk.CTkButton(self.container, text="Voltar", command=self.show_chargers_screen)
        btn_back.pack(fill="x")

    # tela com o resumo dos custos previstos da sessão e validação do meio de pagamento
    def show_confirmation_screen(self, charger_name, time_min, energy_kwh, final_cost, coupon):
        self.clear_screen()
        lbl_title = ctk.CTkLabel(self.container, text="Resumo da Sessão", font=("Arial", 20, "bold"))
        lbl_title.pack(pady=(20, 20))

        frame_info = ctk.CTkFrame(self.container)
        frame_info.pack(fill="x", pady=10, ipadx=10, ipady=10)

        ctk.CTkLabel(frame_info, text=f"Tempo Estimado: {time_min} min").pack(anchor="w")
        ctk.CTkLabel(frame_info, text=f"Energia Entregue: {energy_kwh:.2f} kWh").pack(anchor="w")
        ctk.CTkLabel(frame_info, text=f"Total a Pagar: R$ {final_cost:.2f}", font=("Arial", 16, "bold"),text_color="green").pack(anchor="w", pady=(10, 0))

        ctk.CTkLabel(self.container, text="Cartão de Crédito (16 dígitos):").pack(anchor="w", pady=(20, 0))
        entry_cc = ctk.CTkEntry(self.container)
        entry_cc.pack(fill="x", pady=(5, 10))

        lbl_err = ctk.CTkLabel(self.container, text="", text_color="red")
        lbl_err.pack()

        # verifica se o número de cartão digitado possui 16 dígitos
        def validate():
            cc_clean = entry_cc.get().replace(" ", "")
            if cc_clean.isdigit() and len(cc_clean) == 16:
                self.start_background_simulation(charger_name, time_min, energy_kwh, final_cost, coupon)
            else:
                lbl_err.configure(text="Cartão inválido! Digite 16 números.")

        btn_confirm = ctk.CTkButton(self.container, text="Confirmar e Iniciar", command=validate)
        btn_confirm.pack(fill="x", pady=10)
        btn_back = ctk.CTkButton(self.container, text="Voltar", fg_color="transparent", command=lambda: self.show_recharge_setup(charger_name))
        btn_back.pack(fill="x")

    # inicializa a sessão ativa na memória da aplicação e dispara uma thread paralela para executar a comunicação Modbus simulada
    def start_background_simulation(self, charger_name, total_mins, total_energy, final_cost, coupon):
        self.charging_sessions[charger_name] = {"active": True, "progress": 0.0,
                                                "logs": [f"Conectando {charger_name}...\nSessão liberada.\n"],
                                                "total_mins": total_mins, "completed": False}

        # disparo assíncrono para não travar a main thread de interface gráfica
        sim_thread = threading.Thread(target=self.run_simulation_thread, args=(charger_name, total_mins, total_energy, final_cost, coupon))
        sim_thread.daemon = True
        sim_thread.start()

        self.show_active_recharge_screen(charger_name)

    # loop executado em uma Thread separada. comandos iniciais Modbus, executa leituras cíclicas simulando os minutos passando e finaliza gravando o histórico
    def run_simulation_thread(self, charger_name, total_mins, total_energy, final_cost, coupon):
        # função helper que injeta dados de log na tela do usuário
        def log_to_ui(msg):
            session = self.charging_sessions.get(charger_name)
            if session and session.get("active"):
                session["logs"].append(msg)
                self.after(0, self.update_active_ui_if_visible, charger_name, session["progress"], msg)

        log_to_ui("\n--- INICIANDO PROTOCOLO MODBUS ---")
        modbus = FakeModbusSimulator(logger_callback=log_to_ui)
        slave_id = 1
        power_kw = self.data["settings"]["chargers"][charger_name]["charge_speed_kw"]

        # 1 Etapa Modbus: Set Target Minutes, Energy e dar Start
        modbus.write_register(slave_id, 0x0100, total_mins, "SetTargetMinutes")
        modbus.write_register(slave_id, 0x0102, int(total_energy * 100), "SetTargetEnergy")
        modbus.write_register(slave_id, 0x0001, 1, "StartChargerContactor")
        log_to_ui("----------------------------------\n")

        # 2 Etapa Modbus: simulação temporal do progresso
        current_min = 1
        while current_min <= total_mins and self.charging_sessions.get(charger_name, {}).get("active"):
            energy = power_kw / 60
            progress = current_min / total_mins

            hardware_min = modbus.read_holding_registers(slave_id, 0x0200, 1, current_min, "ReadCurrentMin")
            ui_msg = f"  >> Sessão UI: {hardware_min}/{total_mins} min | +{energy:.3f} kWh"
            self.charging_sessions[charger_name]["progress"] = progress
            log_to_ui(ui_msg + "\n")

            current_min += 1
            time.sleep(1.5)

        # 3 Etapa Modbus: finalização
        if self.charging_sessions.get(charger_name, {}).get("active"):
            log_to_ui("--- FINALIZANDO SESSÃO MODBUS ---")
            modbus.write_register(slave_id, 0x0001, 0, "StopChargerContactor")

            self.charging_sessions[charger_name]["completed"] = True
            self.charging_sessions[charger_name]["logs"].append("\nRECARGA CONCLUÍDA COM SUCESSO!")

            session_data = {"date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "charger": charger_name,
                            "time_min": total_mins, "energy_kwh": total_energy, "final_cost": final_cost,
                            "coupon": coupon}
            self.data["users"][self.current_user]["history"].append(session_data)
            DataManager.save_data(self.data)
            self.after(0, self.finish_active_ui_if_visible, charger_name)

    # tela do console/terminal em tempo real, as mensagens geradas pela simualação Modbus aparece
    def show_active_recharge_screen(self, charger_name):
        self.clear_screen()
        self.current_view = f"charging_{charger_name}"

        session = self.charging_sessions.get(charger_name)
        if not session:
            self.show_chargers_screen()
            return

        lbl_title = ctk.CTkLabel(self.container, text=f"Recarga - {charger_name}", font=("Arial", 20, "bold"))
        lbl_title.pack(pady=(20, 10))

        self.progress_bar = ctk.CTkProgressBar(self.container)
        self.progress_bar.pack(fill="x", pady=10)
        self.progress_bar.set(session["progress"])

        self.terminal = ctk.CTkTextbox(self.container, height=200, fg_color="#1E1E1E", text_color="#00FF00", font=("Courier New", 12))
        self.terminal.pack(fill="both", expand=True, pady=10)

        self.terminal.insert("end", "\n".join(session["logs"]) + "\n")
        self.terminal.see("end")
        self.terminal.configure(state="disabled")

        self.btn_finish = ctk.CTkButton(self.container, text="Finalizar / Voltar", command=lambda: self.close_active_session(charger_name))
        self.btn_finish.pack(fill="x", pady=20)

        if not session["completed"]:
            self.btn_finish.configure(text="Voltar aos Carregadores")

    # barra de progresso e inserção de uma nova linha no terminal se o usuário estiver com a tela do console aberta
    def update_active_ui_if_visible(self, charger_name, progress, msg):
        if self.current_view == f"charging_{charger_name}":
            if hasattr(self, 'progress_bar') and self.progress_bar.winfo_exists():
                self.progress_bar.set(progress)
            if hasattr(self, 'terminal') and self.terminal.winfo_exists():
                self.terminal.configure(state="normal")
                self.terminal.insert("end", msg + "\n")
                self.terminal.see("end")
                self.terminal.configure(state="disabled")

    # finaliza a recarga e modifica os botões da tela
    def finish_active_ui_if_visible(self, charger_name):
        if self.current_view == f"charging_{charger_name}":
            if hasattr(self, 'terminal') and self.terminal.winfo_exists():
                self.terminal.configure(state="normal")
                self.terminal.insert("end", "\nRECARGA CONCLUÍDA COM SUCESSO!\n")
                self.terminal.see("end")
                self.terminal.configure(state="disabled")
            if hasattr(self, 'btn_finish') and self.btn_finish.winfo_exists():
                self.btn_finish.configure(text="Concluir e Voltar")

    # fecha o monitoramento e apaga os resíduos da sessão
    def close_active_session(self, charger_name):
        session = self.charging_sessions.get(charger_name)
        if session and session.get("completed"):
            del self.charging_sessions[charger_name]
        self.show_chargers_screen()

    # ==========================================
    # CONFIGURAÇÕES GLOBAIS (SÓ CUPOM NO MOMENTO)
    # ==========================================

    # tela de configurações globais focado no cupom
    def show_global_settings_screen(self):
        self.clear_screen()
        lbl_title = ctk.CTkLabel(self.container, text="Gerenciar Cupons", font=("Arial", 20, "bold"))
        lbl_title.pack(pady=(10, 10))

        self.coupon_scroll = ctk.CTkScrollableFrame(self.container, height=150)
        self.coupon_scroll.pack(fill="x", pady=5)
        self.render_coupons_list()

        frame_add = ctk.CTkFrame(self.container, fg_color="transparent")
        frame_add.pack(fill="x", pady=5)
        self.entry_new_code = ctk.CTkEntry(frame_add, placeholder_text="Código", width=140)
        self.entry_new_code.pack(side="left", padx=(0, 5))
        self.entry_new_disc = ctk.CTkEntry(frame_add, placeholder_text="Desconto %", width=100)
        self.entry_new_disc.pack(side="left", padx=5)

        btn_add = ctk.CTkButton(frame_add, text="Add", width=60, command=self.add_coupon_logic)
        btn_add.pack(side="right")

        self.lbl_settings_msg = ctk.CTkLabel(self.container, text="")
        self.lbl_settings_msg.pack()

        btn_save = ctk.CTkButton(self.container, text="Voltar", command=self.show_main_screen)
        btn_save.pack(side="bottom", fill="x", pady=10)

    # vê os cupons armazenados no banco de dados e mostra eles, permitindo exclusão
    def render_coupons_list(self):
        for widget in self.coupon_scroll.winfo_children():
            widget.destroy()
        coupons = self.data["settings"]["coupons"]
        if not coupons:
            ctk.CTkLabel(self.coupon_scroll, text="Nenhum cupom ativo.", text_color="gray").pack()
            return
        for code, discount in coupons.items():
            row = ctk.CTkFrame(self.coupon_scroll, fg_color="#2A2D2E", corner_radius=5)
            row.pack(fill="x", pady=2, padx=2)
            ctk.CTkLabel(row, text=f"🎟 {code} (-{int(discount * 100)}%)").pack(side="left", padx=10, pady=5)
            btn_del = ctk.CTkButton(row, text="X", width=30, fg_color="#8B0000", hover_color="#5C0000", command=lambda c=code: self.remove_coupon_logic(c))
            btn_del.pack(side="right", padx=10, pady=5)

    # validação dos dados para o novo cupom e registra no JSON.
    def add_coupon_logic(self):
        code = self.entry_new_code.get().strip().upper()
        disc_raw = self.entry_new_disc.get().strip()
        if not code or not disc_raw or not disc_raw.isdigit():
            self.lbl_settings_msg.configure(text="Preencha código e desconto numérico!", text_color="red")
            return
        if code in self.data["settings"]["coupons"]:
            self.lbl_settings_msg.configure(text="Cupom já existe!", text_color="red")
            return
        disc = float(disc_raw) / 100.0
        if disc <= 0 or disc >= 1:
            self.lbl_settings_msg.configure(text="Desconto deve ser entre 1 e 99", text_color="red")
            return
        self.data["settings"]["coupons"][code] = disc
        DataManager.save_data(self.data)
        self.entry_new_code.delete(0, 'end')
        self.entry_new_disc.delete(0, 'end')
        self.render_coupons_list()

    # deletar cupom
    def remove_coupon_logic(self, code_to_remove):
        if code_to_remove in self.data["settings"]["coupons"]:
            del self.data["settings"]["coupons"][code_to_remove]
            DataManager.save_data(self.data)
            self.render_coupons_list()

    # ==========================================
    # TELAS DE HISTÓRICO E GRÁFICOS
    # ==========================================

    # tela de históricos e seleção de gráficos
    def show_history_screen(self):
        self.clear_screen()
        lbl_title = ctk.CTkLabel(self.container, text="Menu de Histórico", font=("Arial", 20, "bold"))
        lbl_title.pack(pady=(20, 20))

        ctk.CTkLabel(self.container, text="Geral", font=("Arial", 16, "bold"), text_color="#1f6aa5").pack(anchor="w", pady=(10, 5))

        btn_geral_lista = ctk.CTkButton(self.container, text="Histórico Geral (Lista)", command=lambda: self.show_history_list(None))
        btn_geral_lista.pack(fill="x", pady=5)
        btn_geral_graf = ctk.CTkButton(self.container, text="Gráficos Gerais", command=lambda: self.show_history_graphs(None))
        btn_geral_graf.pack(fill="x", pady=5)

        ctk.CTkLabel(self.container, text="Por Carregador", font=("Arial", 16, "bold"), text_color="#1f6aa5").pack(anchor="w", pady=(20, 5))

        chargers = list(self.data["settings"]["chargers"].keys())
        self.selected_charger = ctk.StringVar(value=chargers[0] if chargers else "Nenhum Carregador")

        drop_chargers = ctk.CTkOptionMenu(self.container, variable=self.selected_charger, values=chargers if chargers else ["Nenhum Carregador"])
        drop_chargers.pack(fill="x", pady=10)

        btn_esp_lista = ctk.CTkButton(self.container, text="Ver Lista do Carregador", fg_color="transparent", border_width=1, command=lambda: self.show_history_list(self.selected_charger.get()))
        btn_esp_lista.pack(fill="x", pady=5)
        btn_esp_graf = ctk.CTkButton(self.container, text="Ver Gráficos do Carregador", fg_color="transparent", border_width=1, command=lambda: self.show_history_graphs(self.selected_charger.get()))
        btn_esp_graf.pack(fill="x", pady=5)

        btn_back = ctk.CTkButton(self.container, text="Voltar à Tela Principal", command=self.show_main_screen, fg_color="transparent", text_color="gray")
        btn_back.pack(fill="x", side="bottom", pady=20)

    # filtra registros de recarga do usuário e exibeem formato de lista como pilha
    def show_history_list(self, charger_filter):
        self.clear_screen()
        title_text = "Histórico Geral" if not charger_filter else f"Histórico: {charger_filter}"
        lbl_title = ctk.CTkLabel(self.container, text=title_text, font=("Arial", 20, "bold"))
        lbl_title.pack(pady=(20, 10))

        history = self.data["users"][self.current_user].get("history", [])

        if charger_filter and charger_filter != "Nenhum Carregador":
            history = [s for s in history if s.get("charger") == charger_filter]

        total_spent = sum(s['final_cost'] for s in history)
        total_energy = sum(s['energy_kwh'] for s in history)

        lbl_stats = ctk.CTkLabel(self.container, text=f"Total Gasto: R$ {total_spent:.2f} | Energia: {total_energy:.2f} kWh", text_color="gray")
        lbl_stats.pack(pady=(0, 10))

        scroll = ctk.CTkScrollableFrame(self.container)
        scroll.pack(expand=True, fill="both", pady=10)

        if not history:
            ctk.CTkLabel(scroll, text="Nenhuma recarga encontrada para esta seleção.").pack(pady=20)
        else:
            for session in reversed(history):
                frame = ctk.CTkFrame(scroll, fg_color="#2A2D2E", corner_radius=10)
                frame.pack(fill="x", pady=5, padx=5)

                info = f"Data: {session['date']} | {session.get('charger', 'Desconhecido')}\n"
                info += f"Tempo: {session['time_min']} min  |  Energia: {session['energy_kwh']:.2f} kWh\n"
                info += f"Valor Pago: R$ {session['final_cost']:.2f}"
                if session.get('coupon'):
                    info += f" (Cupom: {session['coupon']})"

                ctk.CTkLabel(frame, text=info, justify="left").pack(padx=10, pady=10, anchor="w")

        btn_back = ctk.CTkButton(self.container, text="Voltar ao Menu", command=self.show_history_screen)
        btn_back.pack(fill="x", pady=10)

    # tela de seleção dos gráficos
    def show_history_graphs(self, charger_filter):
        self.clear_screen()
        title_text = "Gráficos Gerais" if not charger_filter else f"Gráficos: {charger_filter}"
        lbl_title = ctk.CTkLabel(self.container, text=title_text, font=("Arial", 20, "bold"))
        lbl_title.pack(pady=(10, 10))

        self.graph_type = ctk.StringVar(value="cost")

        frame_mode = ctk.CTkFrame(self.container, fg_color="transparent")
        frame_mode.pack(fill="x", pady=5)

        rb_cost = ctk.CTkRadioButton(frame_mode, text="Valor (R$)", variable=self.graph_type, value="cost", command=lambda: self.render_bar_chart(charger_filter))
        rb_cost.pack(side="left", padx=20)
        rb_time = ctk.CTkRadioButton(frame_mode, text="Tempo (min)", variable=self.graph_type, value="time", command=lambda: self.render_bar_chart(charger_filter))
        rb_time.pack(side="right", padx=20)

        # widget frame pro Canvas operar
        self.graph_container = ctk.CTkFrame(self.container, height=350)
        self.graph_container.pack(expand=True, fill="both", pady=15)
        self.graph_container.pack_propagate(False)

        btn_back = ctk.CTkButton(self.container, text="Voltar ao Menu", command=self.show_history_screen)
        btn_back.pack(fill="x", pady=10)

        self.render_bar_chart(charger_filter)

    # canvas do Tkinter para processar as últimas 6 recargas e desenhar um gráfico de linhas
    def render_bar_chart(self, charger_filter):

        for widget in self.graph_container.winfo_children():
            widget.destroy()

        history = self.data["users"][self.current_user].get("history", [])
        if charger_filter and charger_filter != "Nenhum Carregador":
            history = [s for s in history if s.get("charger") == charger_filter]

        if not history:
            ctk.CTkLabel(self.graph_container, text="Dados insuficientes para gerar gráfico.").pack(expand=True)
            return

        history_slice = history[-6:]
        mode = self.graph_type.get()
        values = [s['final_cost'] if mode == "cost" else s['time_min'] for s in history_slice]
        max_val = max(values) if max(values) > 0 else 1

        canvas_bg = "#242424"
        canvas = tk.Canvas(self.graph_container, bg=canvas_bg, highlightthickness=0)
        canvas.pack(expand=True, fill="both", padx=10, pady=10)

        # atualizar a renderização antes da leitura de dimensões para impedir problemas do frame
        self.graph_container.update_idletasks()
        width = canvas.winfo_width()
        height = canvas.winfo_height()

        if width <= 10 or height <= 10:
            width = 380
            height = 300

        margin_x = 45
        margin_y = 35
        usable_width = width - margin_x - 20
        usable_height = height - (2 * margin_y)
        line_color = "#1f6aa5" if mode == "cost" else "#28a745"

        # desenho das grades horizontais e marcadores do eixo Y
        for i in range(5):
            y_line = height - margin_y - (i * usable_height / 4)
            canvas.create_line(margin_x, y_line, width - 10, y_line, fill="#444444", dash=(2, 2))
            val_y = (max_val / 4) * i
            lbl_y = f"R$ {val_y:.0f}" if mode == "cost" else f"{val_y:.0f}m"
            canvas.create_text(margin_x - 10, y_line, text=lbl_y, fill="gray", font=("Arial", 10), anchor="e")

        points = []
        num_points = len(values)
        step_x = usable_width / (num_points - 1) if num_points > 1 else usable_width / 2

        # conversão dos dados de tempo/dinheiro das sessões para as coordenadas da tela
        for i, val in enumerate(values):
            x = margin_x + (i * step_x) if num_points > 1 else width / 2
            y = height - margin_y - ((val / max_val) * usable_height)
            points.append((x, y))
            canvas.create_text(x, height - margin_y + 20, text=f"{i}", fill="gray", font=("Arial", 10))

        if len(points) > 1:
            for i in range(len(points) - 1):
                x1, y1 = points[i]
                x2, y2 = points[i + 1]
                canvas.create_line(x1, y1, x2, y2, fill=line_color, width=2.5)

        for i, (x, y) in enumerate(points):
            r = 4
            canvas.create_oval(x - r, y - r, x + r, y + r, fill="#ffffff", outline=line_color, width=2)
            val_txt = f"{values[i]:.0f}"
            canvas.create_text(x, y - 15, text=val_txt, fill="white", font=("Arial", 10, "bold"))


if __name__ == "__main__":
    app = ChargeGrid()
    app.mainloop()