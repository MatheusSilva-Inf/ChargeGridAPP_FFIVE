# ChargeGrid APP 

## Equipe FFIVE

- Augusto de Souza Ávila — RM:570839 
- Davi Simoncelo — RM: 571738 
- João Pedro Sousa — RM: 573962 
- Matheus Evangelista Silva — RM: 568593 
- Murilo Lima de Carvalho — RM:570156

## O que é o projeto:

O ChargeGrid App busca ser  uma solução comercial imaginada para facilitar a realização de transações comerciais para varejistas donos de eletropostos que utilizem o carregador elétrico da HCA G2 da GoodWe. O aplicativo se foca em ser rápido, intuitivo e informativo para o varejista, permitindo que ele seja capaz de realizar recargas e cobrar por elas de forma dinâmica e fácil de entender. Além de proporcionar as informações do histórico de maneira organizada e ágil.

## Objetivo do ChargeGrid

O chargeGrid deseja facilitar a vida dos donos dos eletropostos com a ajuda de meios de verificar e ajustar de sua própria maneira como cobrar, e gerir seu eletroposto, a alta usabilidade do usuário é nosso maior foco. Além disso com esse aplicativo é possível também ajudar na sustentabilidade ambiental, pois com mais usos do aplicativo e consequentemente mais eletropostos há uma tendência ao uso de carros elétricos, reduzindo emissões de CO2 e  menor uso de combustíveis fósseis, além de com a tarifação dinâmica e a rotatividade ajudando a reduzir o consumo em horários de alto movimento, assim evitando sobrecargas. E por fim no futuro com essa base de aplicativo pode ser facilmente aplicada arquiteturas que integrem com painéis solares e sistemas de armazenamento por baterias.

## Estrutura do projeto: 
O aplicativo foi criado em Python, utilizando a biblioteca customtkinter para UI, assim garantindo uma interface moderna e agradável. O projeto para simular um banco de dados cria um arquivo JSON responsável por organizar todos os dados do projeto, desde configurações do usuário à cadastro e históricos de recarga. O aplicativo foi projetado utilizando arquitetura orientada à objetos, contendo 3 classes principais, a DataManager, responsável pela persistência de dados durante e entre sessões; o FakeModbusSimulator, responsável por emular a comunicação baseada no protocolo MODBUS, permitindo que o aplicativo se aproxime de como será ao ser aplicado de forma real e por fim a classe do aplicativo mesmo, onde estão todas as funções e é a responsável pela execução do aplicativo e pela utilização das threads assíncronas para permitir que o aplicativo execute suas simulações de recarga em segundo plano enquanto no loop principal apareça a interface gráfica sempre.

## bibliotecas usadas: 
customtkinter | tkinter | json | os | time | threading | datetime | random | math

## Funcionalidades:

- Interface gráfica moderna
- Cadastro e login
- Persistência de Login
- Gerenciamento de múltiplos carregadores
- simulações de recargas em segundo plano
- Regras de tarifação dinâmica (horários de pico, alta demanda dos carregadores e rotatividade)
- Capacidade de definir o dinheiro a ser pago baseado no tempo de recarga que o usuário desejar
- Capacidade de definir o tempo a ser gasto com base no valor em dinheiro que o usuário deseja pagar
- Gestão de dispositivos, permitindo alterar em cada dispotivo: a velocidade, tempo máximo que pode ser carregado por sessão e se há tarifações dinâmicas
- Simulação da leitura e escrita do protocolo Modbus
- Gestão de cupons, permitindo adicionar ou remover
- Criação um histórico salvo localmente em JSON permitindo ver as recargas passadas
- Históricos individuais para cada carregador
- Gráficos com o tempo de recarga, ou valor pago, pelas ultimas 6 sessões 

## Instruções e avisos de uso:
1 - Ao iniciar o aplicativo pela primeira vez será criado um JSON de histórico, faça o cadastro e ficará salvo podendo acessar o aplicativo.
2 - Na tela principal você terá 3 opções, a primeira de recarga é a principal ferramenta do projeto, a segunda é histórico, que só apresentará resultados após uma recarga e a terceira são as configurações, que permitem adicionar cupons.
3 - na tela de recarga, clicar em adicionar carregador para criar novos independentes, e cada um deles pode ser separadamente configurado ao clicar em configurar.
4 - Ao iniciar recarga você pode definir se quer definir em minutos que ficará carregando ou em dinheiro a ser pago, o valor de tempo ou dinheiro que não foi conhecido é mostrado logo na tela seguinte, sendo adquirido por equações matemáticas.
5 - Na tela do histórico é possível ver a lista das últimas recargas, sendo mostradas em uma lista em formato de pilha (a última primeiro), e nos gráficos os números correspondem à recarga mais antiga sendo o 0 e incrementando conforme mais recargas são feitas.
6 - A tela de cupom permite adicionar um cupom de desconto, o valor é em número inteiro correspondente à porcentagem, e pode ser removido, letras maíusculas importam
7 - Se fechar o aplicativo e ainda possuir o JSON registrado o aplicativo ainda manterá as informações, para tentar novamente executar sem nenhuma informação é necessário um novo usuário ou apagar o JSON.

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

# Vídeo de demonstração: https://youtu.be/sOoYKYRHelY
