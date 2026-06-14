# ChargeGrid APP 

## Equipe FFIVE

- Augusto de Souza Ávila — RM:570839 
- Davi Simoncelo — RM: 571738 
- João Pedro Sousa — RM: 573962 
- Matheus Evangelista Silva — RM: 568593 
- Murilo Lima de Carvalho — RM:570156

## O que é o projeto:

O ChargeGrid App busca ser  uma solução comercial imaginada para facilitar a realização de transações comerciais para varejistas donos de eletropostos que utilizem o carregador elétrico da HCA G2 da GoodWe. O aplicativo se foca em ser rápido, intuitivo e informativo para o varejista, permitindo que ele seja capaz de realizar recargas e cobrar por elas de forma dinâmica e fácil de entender. O aplicativo foi desenvolvido em Python utilizando a interface gráfica customTkinter para ser agradável visualmente ao usuário.

## Funcionalidades:

- Cadastro e persistência de Login
- Capacidade de diversas recargas em segundo plano
- Adicionar ou remover carregadores
- Regras de tarifação dinâmica (horários de pico, alta demanda dos carregadores e rotatividade)
- Capacidade de definir o dinheiro a ser pago baseado no tempo de recarga que o usuário desejar
- Capacidade de definir o tempo a ser gasto com base no valor em dinheiro que o usuário deseja pagar
- Gestão de dispositivos, permitindo alterar em cada dispotivo: a velocidade, tempo máximo que pode ser carregado por sessão e se há tarifações dinâmicas
- Simulação da leitura e escrita do protocolo Modbus
- Gestão de cupons, permitindo adicionar ou remover
- Criação um histórico salvo localmente em JSON permitindo ver as recargas passadas
- Históricos individuais para cada carregador
- Gráficos com o tempo de recarga, ou valor pago, pelas ultimas 6 sessões 

## Como executar:

```bash
git clone https://github.com/MatheusSilva-Inf/ChargeGridAPP_FFIVE
cd ChargeGridAPP_FFIVE
python -m venv .venv
.venv\Scripts\activate
# Linux abaixo
# source .venv/bin/activate
pip install -r requirements.txt
python ChargeGrid_FFIVE.py
```

## Limitações:

- Sem persistência de histórico entre sessões
- Interface apenas via terminal
- Foi testado com interpretador 3.10+ apenas

# Vídeo de demonstração: 
