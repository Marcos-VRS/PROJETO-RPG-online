# Configuração para deploy

## Primeiros passos

- Prepare o local_settings.py
- Crie o seu servidor Ubuntu 20.04 LTS (onde preferir)

## Comando para gerar SECRET_KEY no terminal power shell( se for no wsl é python3 no começo )

```
python -c "import string as s;from secrets import SystemRandom as SR;print(''.join(SR().choices(s.ascii_letters + s.digits + s.punctuation, k=64)));"
```

## Criando sua chave SSH

```
ssh-keygen -C 'COMENTÁRIO'
```

## No servidor

### Conectando

```
ssh usuário@IP_SERVIDOR
```

### Comandos iniciais

```
sudo apt update -y
sudo apt upgrade -y
sudo apt autoremove -y
sudo apt install build-essential -y

sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt install python3.13 python3.13-venv

sudo apt install nginx -y
sudo apt install certbot python3-certbot-nginx -y
sudo apt install postgresql postgresql-contrib -y
sudo apt install libpq-dev -y
sudo apt install git -y
```

### Configurando o git

```
git config --global user.name 'Seu nome'
git config --global user.email 'seu_email@gmail.com'
git config --global init.defaultBranch main
```

Criando as pastas do projeto e repositório

```
mkdir ~/roll3d6repo ~/roll3d6app
```

## Configurando os repositórios

```
cd ~/roll3d6repo
git init --bare
cd ..
cd ~/roll3d6app
git init
git remote add roll3d6repo ~/roll3d6repo
git add .
git commit -m 'Initial'
git push roll3d6repo main -u # erro
```

## No seu computador local

```
git remote add roll3d6repo usuario@IP_SERVIDOR:~/roll3d6repo
git push roll3d6repo main
```

## No servidor

```
cd ~/roll3d6app
git pull roll3d6repo main
```

## Configurando o Postgresql

```
sudo -u postgres psql

postgres=# create role marcosvrsdevmail with login superuser createdb createrole password 'tunebrightspeed32178094666';
CREATE ROLE
postgres=# create database roll3d6_data_base with owner marcosvrsdevmail;
CREATE DATABASE
postgres=# grant all privileges on database roll3d6_data_base to marcosvrsdevmail;
GRANT
postgres=# \q

sudo systemctl restart postgresql
```

## Criando o local_settings.py no servidor

```
nano ~/roll3d6app/project/local_settings.py
```

Cole os dados.

## Configurando o Django no servidor

```
cd ~/roll3d6app
python3.13 -m venv venv
. venv/bin/activate
pip install --upgrade pip
pip install django
pip install pillow
pip install gunicorn
pip install psycopg

python manage.py runserver
python manage.py migrate
python manage.py collectstatic
python manage.py createsuperuser
```

## Permitir arquivos maiores no nginx

```
sudo nano /etc/nginx/nginx.conf
```

Adicione em http {}:

```
client_max_body_size 30M;
```

```
sudo systemctl restart nginx
```


## Reiniciando serviço 
. venv/bin/activate
python manage.py collectstatic
sudo systemctl restart nginx
sudo systemctl restart daphne
