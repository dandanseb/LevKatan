# Tests Selenium - LevKatan (לב קטן)

## Aperçu
Ce dépôt contient 5 tests Selenium complets pour tester l'application web LevKatan, une plateforme de prêt d'articles pour bébés.

## Fichiers créés

### Tests principaux
- `selenium_tests.py` - Les 5 tests Selenium avec commentaires détaillés
- `run_selenium_tests.sh` - Script d'exécution rapide et facile
- `requirements-selenium.txt` - Dépendances Python nécessaires

### Configuration et documentation
- `GUIDE_TESTS_SELENIUM.md` - Guide détaillé pour l'exécution et la maintenance
- `pytest.ini` - Configuration pytest optimisée
- `README_SELENIUM.md` - Ce fichier

## Les 5 tests Selenium (Spécifications Exactes)

| Test | Nom Hébreu | Nom Fonction | Description |
|------|------------|--------------|-------------|
| 1 | ניווט למסך הבית | `test_01_login_routing` | Login & Routage - Vérifier redirection Client vs Admin |
| 2 | צפייה במוצרים של הקטלוג | `test_02_product_details` | Détails Produit - Vérifier affichage détails (Description, Image, Info) |
| 3 | אישור בקשות השאלה | `test_03_approve_requests` | Validation (Admin) - Vérifier approbation demandes emprunt |
| 4 | רשימת הפריטים המושאלים | `test_04_borrowed_items_list` | Affichage (Admin) - Vérifier tableau emprunts en cours |
| 5 | הסרת פריטים | `test_05_delete_product` | Suppression (Admin) - Vérifier suppression articles |

## Démarrage rapide

### 1. Installation
```bash
pip install -r requirements-selenium.txt
```

### 2. Lancement de l'application
```bash
python app.py
```

### 3. Exécution des tests
```bash
# Tous les tests
./run_selenium_tests.sh

# Test spécifique (ex: test de connexion)
./run_selenium_tests.sh 1

# Avec pytest directement
pytest selenium_tests.py -v
```

## Prérequis
- Python 3.7+
- Google Chrome installé
- Application LevKatan en cours d'exécution sur `localhost:5230`

## Fonctionnalités testées
- ✅ Authentification (connexion/inscription)
- ✅ Navigation dans l'interface utilisateur
- ✅ Catalogue de produits
- ✅ Processus d'emprunt
- ✅ Changement de thème (sombre/clair)
- ✅ Gestion des erreurs et timeouts
- ✅ Compatibilité responsive

## Rapport de test
Après exécution, un rapport HTML est généré automatiquement :
- `selenium_report.html` - Rapport détaillé avec captures d'écran

## Support
Consultez `GUIDE_TESTS_SELENIUM.md` pour :
- Instructions détaillées d'installation
- Configuration avancée
- Dépannage des problèmes courants
- Intégration CI/CD

## Vidéo explicative
📹 Une vidéo détaillée montrant l'exécution complète des tests sera bientôt disponible.

---
**לב קטן** - Plateforme de partage d'articles pour bébés
