#!/bin/bash

# COMANDOS GIT ÚTEIS PARA O SISTEMA

# 1. SALVAR ALTERAÇÕES (Fazer backup antes de modificar)
git_backup() {
    echo "📦 Criando backup antes das alterações..."
    git add .
    git commit -m "💾 Backup antes de modificações - $(date +%Y-%m-%d_%H:%M:%S)"
    echo "✅ Backup criado!"
}

# 2. VER DIFERENÇAS
git_diff() {
    echo "📊 Diferenças nos arquivos:"
    git diff
}

# 3. VER HISTÓRICO
git_history() {
    echo "📜 Histórico de commits:"
    git log --oneline --graph --all --decorate
}

# 4. VOLTAR PARA VERSÃO ANTERIOR
git_rollback() {
    echo "⚠️  ATENÇÃO: Isto irá descartar TODAS as alterações não commitadas!"
    read -p "Deseja continuar? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        git reset --hard HEAD
        echo "✅ Voltado para último commit"
    else
        echo "❌ Operação cancelada"
    fi
}

# 5. VOLTAR PARA VERSÃO ESTÁVEL (v1.0.0)
git_restore_stable() {
    echo "🔄 Restaurando versão estável v1.0.0..."
    read -p "Isto irá descartar TODAS as alterações. Continuar? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        git checkout v1.0.0
        echo "✅ Versão v1.0.0 restaurada!"
        echo "⚠️  Para voltar ao desenvolvimento: git checkout main"
    else
        echo "❌ Operação cancelada"
    fi
}

# 6. VER VERSÕES DISPONÍVEIS
git_versions() {
    echo "🏷️  Versões disponíveis:"
    git tag -l
}

# 7. CRIAR NOVA VERSÃO
git_new_version() {
    echo "Versão atual:"
    git describe --tags --abbrev=0 2>/dev/null || echo "Nenhuma tag encontrada"
    echo ""
    read -p "Nome da nova versão (ex: v1.1.0): " version
    read -p "Descrição: " description
    
    git add .
    git commit -m "🚀 Release $version - $description"
    git tag -a "$version" -m "$description"
    echo "✅ Versão $version criada!"
}

# MENU
echo "========================================="
echo "🔧 GIT - COMANDOS ÚTEIS"
echo "========================================="
echo ""
echo "Escolha uma opção:"
echo "1) Fazer backup das alterações"
echo "2) Ver diferenças (o que mudou)"
echo "3) Ver histórico de versões"
echo "4) Voltar para última versão salva"
echo "5) Restaurar versão estável (v1.0.0)"
echo "6) Ver todas as versões disponíveis"
echo "7) Criar nova versão"
echo ""
read -p "Opção: " option

case $option in
    1) git_backup ;;
    2) git_diff ;;
    3) git_history ;;
    4) git_rollback ;;
    5) git_restore_stable ;;
    6) git_versions ;;
    7) git_new_version ;;
    *) echo "Opção inválida" ;;
esac
