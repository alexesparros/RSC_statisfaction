@echo off
title MenuPro - Gestion des Menus
color 0A

echo.
echo  ========================================
echo       MenuPro - Demarrage en cours...
echo  ========================================
echo.

cd /d "%~dp0"

echo  [*] Lancement de l'application...
echo.
echo  L'application va s'ouvrir dans votre navigateur.
echo  Pour arreter, fermez cette fenetre.
echo.
echo  ========================================
echo.

streamlit run app_streamlit.py --server.headless true

pause


