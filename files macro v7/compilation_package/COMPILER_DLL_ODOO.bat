@echo off
REM =========================================================================
REM Script de compilation de la DLL Odoo pour QuickDevis - VERSION 2
REM =========================================================================

echo.
echo ╔═══════════════════════════════════════════════════════════════════════╗
echo ║          COMPILATION DLL ODOO POUR QUICKDEVIS - V2                    ║
echo ╚═══════════════════════════════════════════════════════════════════════╝
echo.

REM =========================================================================
REM ETAPE 1 : TROUVER QUICKDEVIS
REM =========================================================================

echo [1/6] Recherche de QuickDevis...
echo.

set QDV_PATH=""

REM Chercher dans les emplacements courants
if exist "C:\Program Files\QDV 7\Qdv.UserApi.dll" (
    set QDV_PATH="C:\Program Files\QDV 7"
    echo Trouve : C:\Program Files\QDV 7
)

if exist "C:\Program Files\QDV 7 ULT\Qdv.UserApi.dll" (
    set QDV_PATH="C:\Program Files\QDV 7 ULT"
    echo Trouve : C:\Program Files\QDV 7 ULT
)

if exist "C:\Program Files (x86)\QDV 7\Qdv.UserApi.dll" (
    set QDV_PATH="C:\Program Files (x86)\QDV 7"
    echo Trouve : C:\Program Files (x86)\QDV 7
)

if exist "C:\Program Files (x86)\QDV 7 ULT\Qdv.UserApi.dll" (
    set QDV_PATH="C:\Program Files (x86)\QDV 7 ULT"
    echo Trouve : C:\Program Files (x86)\QDV 7 ULT
)

if exist "C:\Program Files\Est360\QuickDevis 7\Qdv.UserApi.dll" (
    set QDV_PATH="C:\Program Files\Est360\QuickDevis 7"
    echo Trouve : C:\Program Files\Est360\QuickDevis 7
)

if exist "C:\Program Files (x86)\Est360\QuickDevis 7\Qdv.UserApi.dll" (
    set QDV_PATH="C:\Program Files (x86)\Est360\QuickDevis 7"
    echo Trouve : C:\Program Files (x86)\Est360\QuickDevis 7
)

REM Si pas trouvé, demander à l'utilisateur
if %QDV_PATH%=="" (
    echo.
    echo QuickDevis n'a pas ete trouve automatiquement.
    echo.
    echo Veuillez entrer le chemin d'installation de QuickDevis.
    echo Exemple : C:\Program Files\QDV 7 ULT
    echo.
    set /p QDV_PATH="Chemin QuickDevis : "
    
    REM Vérifier que le chemin existe
    if not exist "%QDV_PATH%\Qdv.UserApi.dll" (
        echo.
        echo [ERREUR] Fichier Qdv.UserApi.dll introuvable dans ce dossier !
        echo.
        echo Le script va compiler SANS les references QuickDevis.
        echo La macro fonctionnera quand meme, mais avec fonctionnalites limitees.
        echo.
        set QDV_PATH=""
        pause
    )
)

echo.

REM =========================================================================
REM ETAPE 2 : TROUVER LE COMPILATEUR
REM =========================================================================

echo [2/6] Recherche du compilateur VB.NET...
echo.

set VBC=""

REM Essayer .NET Framework 4.0/4.5/4.8
if exist "C:\Windows\Microsoft.NET\Framework\v4.0.30319\vbc.exe" (
    set VBC="C:\Windows\Microsoft.NET\Framework\v4.0.30319\vbc.exe"
    echo Trouve : .NET Framework 4.0 (compatible 4.8^)
)

if exist "C:\Windows\Microsoft.NET\Framework64\v4.0.30319\vbc.exe" (
    set VBC="C:\Windows\Microsoft.NET\Framework64\v4.0.30319\vbc.exe"
    echo Trouve : .NET Framework 4.0 x64 (compatible 4.8^)
)

if %VBC%=="" (
    echo [ERREUR] Compilateur VB.NET introuvable !
    echo.
    echo Installez .NET Framework 4.8 Developer Pack :
    echo https://dotnet.microsoft.com/download/dotnet-framework/net48
    echo.
    pause
    exit /b 1
)

echo Compilateur : %VBC%
echo.

REM =========================================================================
REM ETAPE 3 : PREPARER LES REFERENCES
REM =========================================================================

echo [3/6] Preparation des references...
echo.

REM Références système de base
set REFS=/r:System.dll
set REFS=%REFS% /r:System.Core.dll
set REFS=%REFS% /r:System.Data.dll
set REFS=%REFS% /r:System.Xml.dll
set REFS=%REFS% /r:System.Net.dll
set REFS=%REFS% /r:System.Windows.Forms.dll
set REFS=%REFS% /r:System.Drawing.dll

REM System.Web pour JavaScriptSerializer
if exist "C:\Windows\Microsoft.NET\Framework\v4.0.30319\System.Web.dll" (
    set REFS=%REFS% /r:"C:\Windows\Microsoft.NET\Framework\v4.0.30319\System.Web.dll"
    echo + System.Web.dll
)

if exist "C:\Windows\Microsoft.NET\Framework\v4.0.30319\System.Web.Extensions.dll" (
    set REFS=%REFS% /r:"C:\Windows\Microsoft.NET\Framework\v4.0.30319\System.Web.Extensions.dll"
    echo + System.Web.Extensions.dll
)

REM Références QuickDevis (si disponibles)
if not %QDV_PATH%=="" (
    if exist "%QDV_PATH%\Qdv.UserApi.dll" (
        set REFS=%REFS% /r:"%QDV_PATH%\Qdv.UserApi.dll"
        echo + Qdv.UserApi.dll
    )
    
    if exist "%QDV_PATH%\Qdv.CommonApi.dll" (
        set REFS=%REFS% /r:"%QDV_PATH%\Qdv.CommonApi.dll"
        echo + Qdv.CommonApi.dll
    )
)

echo.

REM =========================================================================
REM ETAPE 4 : COMPILATION
REM =========================================================================

echo [4/6] Compilation en cours...
echo.
echo Ceci peut prendre 10-30 secondes...
echo.

REM Compiler la DLL
%VBC% /target:library ^
      /out:MACROC61945A7645743AF8DCB0CF1E0B7905B.dll ^
      /optionexplicit+ ^
      /optioncompare:binary ^
      /optionstrict- ^
      /optioninfer+ ^
      /nowarn:40056,42016,41999,42017,42018,42019,42032,42036,42020,42021,42022 ^
      %REFS% ^
      MACROC61945A7645743AF8DCB0CF1E0B7905B.Startup.vb ^
      MACROC61945A7645743AF8DCB0CF1E0B7905B.Functions_Odoo.vb ^
      MACROC61945A7645743AF8DCB0CF1E0B7905B.ObjFromOdoo.vb ^
      MACROC61945A7645743AF8DCB0CF1E0B7905B.FrmChoice.FORM.vb ^
      MACROC61945A7645743AF8DCB0CF1E0B7905B.FrmChoice.FORM.Designer.vb ^
      MACROC61945A7645743AF8DCB0CF1E0B7905B.frmMessage.FORM.vb ^
      MACROC61945A7645743AF8DCB0CF1E0B7905B.frmMessage.FORM.Designer.vb ^
      MACROC61945A7645743AF8DCB0CF1E0B7905B.frmPromptDocuments.FORM.vb ^
      MACROC61945A7645743AF8DCB0CF1E0B7905B.frmPromptDocuments.FORM.Designer.vb ^
      MACROC61945A7645743AF8DCB0CF1E0B7905B.PromptSFOperation.FORM.vb ^
      MACROC61945A7645743AF8DCB0CF1E0B7905B.PromptSFOperation.FORM.Designer.vb

if errorlevel 1 (
    echo.
    echo ╔═══════════════════════════════════════════════════════════════════════╗
    echo ║                    ERREUR DE COMPILATION !                            ║
    echo ╚═══════════════════════════════════════════════════════════════════════╝
    echo.
    echo Des erreurs sont apparues lors de la compilation.
    echo.
    echo CAUSES POSSIBLES :
    echo   1. QuickDevis mal localise (chemin incorrect)
    echo   2. System.Web.Extensions manquant
    echo   3. Fichiers sources incomplets
    echo.
    echo SOLUTIONS :
    echo   A. Verifiez le chemin QuickDevis ci-dessus
    echo   B. Installez .NET Framework 4.8 Developer Pack
    echo   C. Relancez ce script
    echo.
    echo Si le probleme persiste, utilisez l'Option 2 :
    echo Compiler directement dans l'editeur QuickDevis (Alt+F11)
    echo.
    pause
    exit /b 1
)

echo.

REM =========================================================================
REM ETAPE 5 : VERIFICATION
REM =========================================================================

echo [5/6] Verification...
echo.

if not exist "MACROC61945A7645743AF8DCB0CF1E0B7905B.dll" (
    echo [ERREUR] Le fichier DLL n'a pas ete cree !
    pause
    exit /b 1
)

for %%I in (MACROC61945A7645743AF8DCB0CF1E0B7905B.dll) do set DLLSIZE=%%~zI
echo Taille de la DLL : %DLLSIZE% octets
echo.

REM =========================================================================
REM ETAPE 6 : CREATION DE LA MACRO
REM =========================================================================

echo [6/6] Creation de la macro complete...
echo.

REM Supprimer l'ancienne macro si elle existe
if exist "Communication_With_SalesForce.qdvmacro" (
    del "Communication_With_SalesForce.qdvmacro"
)

REM Créer l'archive ZIP et la renommer en .qdvmacro
echo Creation de l'archive...

powershell -NoProfile -ExecutionPolicy Bypass -Command "& {" ^
    "Compress-Archive -Path (" ^
        "'Communication_With_SalesForce.vbproj'," ^
        "'MACROC61945A7645743AF8DCB0CF1E0B7905B.dll'," ^
        "'MACROC61945A7645743AF8DCB0CF1E0B7905B.Startup.vb'," ^
        "'MACROC61945A7645743AF8DCB0CF1E0B7905B.Functions_Odoo.vb'," ^
        "'MACROC61945A7645743AF8DCB0CF1E0B7905B.ObjFromOdoo.vb'," ^
        "'MACROC61945A7645743AF8DCB0CF1E0B7905B.FrmChoice.FORM.vb'," ^
        "'MACROC61945A7645743AF8DCB0CF1E0B7905B.FrmChoice.FORM.Designer.vb'," ^
        "'MACROC61945A7645743AF8DCB0CF1E0B7905B.FrmChoice.resx;er'," ^
        "'MACROC61945A7645743AF8DCB0CF1E0B7905B.frmMessage.FORM.vb'," ^
        "'MACROC61945A7645743AF8DCB0CF1E0B7905B.frmMessage.FORM.Designer.vb'," ^
        "'MACROC61945A7645743AF8DCB0CF1E0B7905B.frmMessage.resx;er'," ^
        "'MACROC61945A7645743AF8DCB0CF1E0B7905B.frmPromptDocuments.FORM.vb'," ^
        "'MACROC61945A7645743AF8DCB0CF1E0B7905B.frmPromptDocuments.FORM.Designer.vb'," ^
        "'MACROC61945A7645743AF8DCB0CF1E0B7905B.frmPromptDocuments.resx;er'," ^
        "'MACROC61945A7645743AF8DCB0CF1E0B7905B.PromptSFOperation.FORM.vb'," ^
        "'MACROC61945A7645743AF8DCB0CF1E0B7905B.PromptSFOperation.FORM.Designer.vb'," ^
        "'MACROC61945A7645743AF8DCB0CF1E0B7905B.PromptSFOperation.resx;er'," ^
        "'MACROC61945A7645743AF8DCB0CF1E0B7905B.properties.xml'," ^
        "'My Project'," ^
        "'Resources'" ^
    ") -DestinationPath 'temp_macro.zip' -Force; " ^
    "if (Test-Path 'temp_macro.zip') { " ^
        "Move-Item -Path 'temp_macro.zip' -Destination 'Communication_With_SalesForce.qdvmacro' -Force; " ^
        "Write-Host 'Macro creee avec succes !'; " ^
    "} else { " ^
        "Write-Host 'ERREUR: Impossible de creer l archive'; " ^
        "exit 1; " ^
    "}" ^
"}"

if not exist "Communication_With_SalesForce.qdvmacro" (
    echo.
    echo [ERREUR] Impossible de creer le fichier .qdvmacro
    echo.
    echo Vous pouvez creer la macro manuellement :
    echo   1. Creer un fichier ZIP contenant tous les fichiers
    echo   2. Renommer l'extension .zip en .qdvmacro
    echo.
    pause
    exit /b 1
)

echo.
echo ╔═══════════════════════════════════════════════════════════════════════╗
echo ║                      ✅ COMPILATION REUSSIE !                         ║
echo ╚═══════════════════════════════════════════════════════════════════════╝
echo.
echo Fichiers crees :
echo   - MACROC61945A7645743AF8DCB0CF1E0B7905B.dll (%DLLSIZE% octets)
echo   - Communication_With_SalesForce.qdvmacro
echo.
echo ╔═══════════════════════════════════════════════════════════════════════╗
echo ║                      📦 PROCHAINES ETAPES                             ║
echo ╚═══════════════════════════════════════════════════════════════════════╝
echo.
echo 1. Copier : Communication_With_SalesForce.qdvmacro
echo.
echo 2. Vers : C:\ProgramData\Est360\QuickDevis 7\Macros\
echo    (ou votre dossier macros QuickDevis)
echo.
echo 3. Redemarrer QuickDevis
echo.
echo 4. Tester la macro avec une opportunite Odoo
echo.
echo ═══════════════════════════════════════════════════════════════════════
echo.
echo ✅ La macro pointe maintenant vers ODOO (pas Salesforce) !
echo.
pause
