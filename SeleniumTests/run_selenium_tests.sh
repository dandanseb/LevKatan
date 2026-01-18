#!/bin/bash

# Script d'exécution des tests Selenium pour LevKatan (לב קטן)
# Tests adaptés aux spécifications exactes demandées
# Utilisation: ./run_selenium_tests.sh [test_number]

set -e

echo "🚀 Démarrage des tests Selenium pour LevKatan (לב קטן)"
echo "======================================================"
echo "Tests configurés selon les spécifications :"
echo "1. ניווט למסך הבית - Login & Routage"
echo "2. צפייה במוצרים של הקטלוג - Détails Produit"
echo "3. אישור בקשות השאלה - Validation (Admin)"
echo "4. רשימת הפריטים המושאלים - Affichage (Admin)"
echo "5. הסרת פריטים - Suppression (Admin)"
echo ""

# Vérifier si Python est installé
if ! command -v python &> /dev/null; then
    echo "❌ Python n'est pas installé. Veuillez installer Python 3.7+"
    exit 1
fi

# Vérifier si pip est installé
if ! command -v pip &> /dev/null; then
    echo "❌ pip n'est pas installé. Veuillez installer pip"
    exit 1
fi

# Installer les dépendances si requirements-selenium.txt existe
if [ -f "requirements-selenium.txt" ]; then
    echo "📦 Installation des dépendances..."
    pip install -r requirements-selenium.txt
else
    echo "⚠️  Fichier requirements-selenium.txt non trouvé"
fi

# Vérifier si Chrome est installé
if ! command -v google-chrome &> /dev/null && ! command -v google-chrome-stable &> /dev/null; then
    echo "⚠️  Google Chrome n'est pas installé. Les tests peuvent échouer."
    echo "   Installez Chrome depuis: https://www.google.com/chrome/"
fi

# Vérifier si l'application est en cours d'exécution
echo "🔍 Vérification de l'application LevKatan..."
if curl -s http://localhost:5230 > /dev/null; then
    echo "✅ Application accessible sur http://localhost:5230"
else
    echo "⚠️  Application non accessible sur http://localhost:5230"
    echo "   Lancez l'application avec: python app.py"
    echo ""
    read -p "Voulez-vous continuer malgré tout ? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo ""
echo "🧪 Exécution des tests..."
echo "========================"

# Fonction pour exécuter un test spécifique
run_specific_test() {
    local test_number=$1
    local test_name=""

    case $test_number in
        1) test_name="test_01_login_routing" ;;
        2) test_name="test_02_product_details" ;;
        3) test_name="test_03_approve_requests" ;;
        4) test_name="test_04_borrowed_items_list" ;;
        5) test_name="test_05_delete_product" ;;
        *) echo "❌ Numéro de test invalide: $test_number (1-5)"; exit 1 ;;
    esac

    echo "Exécution du test $test_number: $test_name"
    pytest selenium_tests.py::TestLevKatanSelenium::$test_name -v --tb=short
}

# Exécuter tous les tests ou un test spécifique
if [ $# -eq 0 ]; then
    echo "Exécution de tous les tests..."
    pytest selenium_tests.py -v --tb=short
elif [ "$1" = "all" ]; then
    echo "Exécution de tous les tests..."
    pytest selenium_tests.py -v --tb=short
elif [[ $1 =~ ^[1-5]$ ]]; then
    run_specific_test $1
else
    echo "❌ Argument invalide: $1"
    echo ""
    echo "Utilisation:"
    echo "  $0              # Exécuter tous les tests"
    echo "  $0 all          # Exécuter tous les tests"
    echo "  $0 <numéro>     # Exécuter un test spécifique (1-5)"
    echo ""
    echo "Exemples:"
    echo "  $0 1            # ניווט למסך הבית - Login & Routage"
    echo "  $0 2            # צפייה במוצרים של הקטלוג - Détails Produit"
    echo "  $0 3            # אישור בקשות השאלה - Validation (Admin)"
    exit 1
fi

echo ""
echo "✅ Tests terminés !"
echo "📊 Rapport généré: selenium_report.html"
