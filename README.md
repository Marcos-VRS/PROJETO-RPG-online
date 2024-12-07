# **PROJETO-RPG-online**  

[![Django Version](https://img.shields.io/badge/Django-5.1.2-green)](https://www.djangoproject.com/) [![Python Version](https://img.shields.io/badge/Python-3.11-blue)](https://www.python.org/)  

Uma plataforma completa para jogos de RPG online, desenvolvida em **Python** com o framework **Django**.  
O projeto oferece:  
- **Chamadas de áudio e vídeo** para conectar jogadores durante as sessões.  
- Uma página de **interação entre jogadores** com chat embutido.  
- Um **tabuleiro dinâmico virtual**, permitindo a personalização e gerenciamento de partidas.  

---

## **Tabela de Conteúdo**

1. [Recursos](#recursos)  
2. [Tecnologias Utilizadas](#tecnologias-utilizadas)  
3. [Instalação](#instalação)  
4. [Uso](#uso)  
5. [Contribuição](#contribuição)  
6. [Licença](#licença)  

---

## **Recursos**  

### **Comunicação ao Vivo**  
- Suporte a **chamadas de áudio e vídeo** para facilitar a interação em tempo real.  

### **Interação Entre Jogadores**  
- Página dedicada à **troca de mensagens** com chat integrado para melhorar a comunicação entre participantes.  

### **Tabuleiro Virtual**  
- **Tabuleiro dinâmico** personalizável para gerenciar os jogos de maneira visual e interativa.  

---

## **Tecnologias Utilizadas**  

- **Frontend:** HTML, CSS, JavaScript.  
- **Backend:** Django 5.1.2, Python 3.11.  
- **Banco de Dados:** SQLite (configuração padrão, personalizável).  
- **Bibliotecas e Dependências:**  
  - [Django JSON Widget](https://github.com/jazzband/django-json-widget) para gerenciamento de dados JSON.  
  - [Pillow](https://pillow.readthedocs.io/) para manipulação de imagens.  

---

## **Instalação**  

### **Pré-requisitos**  
- Python 3.11 ou superior.  
- Pip instalado.  

### **Passos para Instalação**  
1. Clone o repositório:  
   ```bash
   git clone https://github.com/Marcos-VRS/PROJETO-RPG-online.git
   cd PROJETO-RPG-online
2. Crie e ative um ambiente virtual:
   ```bash
   python -m venv venv  
   source venv/bin/activate  # Linux/Mac  
   venv\Scripts\activate     # Windows
3. Instale as dependências:
   ```bash
   pip install -r requirements.txt

4. Execute as migrações:
   ```bash
   python manage.py migrate


5. Inicie o servidor:
   ```bash
   python manage.py runserver  

---

## **Uso**
1. Acesse a plataforma na URL: http://127.0.0.1:8000/.
2. Crie uma conta para começar a jogar ou faça login se já tiver um perfil.
3. Navegue até o chat ou o tabuleiro virtual para iniciar uma sessão de RPG online.

---

## **Contribuição**
Contribuições são bem-vindas! Para contribuir:
1. Faça um fork do repositório.
2. Crie uma branch com sua funcionalidade ou correção:
   git checkout -b minha-contribuicao  
3. Envie um Pull Request para revisão.

---

## **Licença**
Este projeto está licenciado sob a licença MIT. Veja o arquivo LICENSE para mais detalhes.


---

## **Contato**
•Desenvolvedor: Marcos-VRS
•Email: marcosvrsdevmail@gmail.com
•LinkedIn: https://www.linkedin.com/in/marcos-vin%C3%ADcius-ramos-da-silva-557b18a5/



