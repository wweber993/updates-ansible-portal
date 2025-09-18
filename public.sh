#!/bin/bash
# Script para enviar todo o conteúdo da pasta atual para o GitHub

# Configura identidade (ajuste para o seu email do GitHub)
git config user.name "William Weber"
git config user.email "wweber993@gmail.com"

# Inicializa git (se ainda não estiver inicializado)
git init

# Adiciona remoto (sobrescreve se já existir)
git remote remove origin 2>/dev/null
git remote add origin https://wweber993@github.com/wweber993/updates-ansible-portal.git

# Adiciona todos os arquivos
git add .

# Cria commit
git commit -m "Publicação inicial - sistema de updates para PMEs" || echo "Nada para commitar"

# Força envio para o branch main (sobrescreve o remoto)
git branch -M main
git push -u origin main --force
