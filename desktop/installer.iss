; Inno Setup script do roll3d6 RPG.
;
; Compila com:  "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" desktop\installer.iss
; (ou usa .\desktop\build.ps1 que faz collectstatic + pyinstaller + iscc.)
;
; Saída: dist\roll3d6-setup.exe (um único instalador, ~150 MB).
;
; Instalação:
;   - Per-user, sem precisar de admin (PrivilegesRequired=lowest).
;   - Destino: %LOCALAPPDATA%\Programs\roll3d6
;   - Atalhos: área de trabalho + menu iniciar.
;   - Dados do usuário: continuam em %APPDATA%\roll3d6 (NÃO tocados pelo
;     instalador — gerenciados pelo launcher na primeira execução).
;   - Desinstalador: registrado em "Apps & features".

#define MyAppName "roll3d6 RPG"
#define MyAppVersion "0.1.0"
#define MyAppPublisher "roll3d6"
#define MyAppURL "https://roll3d6rpg.com"
#define MyAppExeName "roll3d6.exe"

[Setup]
AppId={{B9F4A8E2-2A1F-4D6B-9C3E-roll3d6rpgapp}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}

; Per-user: zero admin. Destino abaixo de %LOCALAPPDATA%.
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog

DefaultDirName={localappdata}\Programs\roll3d6
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
DisableDirPage=yes

; Saída do compilador
OutputDir=..\dist
OutputBaseFilename=roll3d6-setup

Compression=lzma2/ultra64
SolidCompression=yes
LZMAUseSeparateProcess=yes

WizardStyle=modern
SetupIconFile=icon.ico

; Aceita arquitetura x64 (bundle é windows-amd64).
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

UninstallDisplayIcon={app}\{#MyAppExeName}
UninstallDisplayName={#MyAppName}

; Sem internacionalização agora — pt-BR via Português brasileiro abaixo.

[Languages]
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: checkedonce

[Files]
; Bundle inteiro vai pra {app}. recursesubdirs preserva _internal/, bin/, etc.
Source: "..\dist\roll3d6\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#MyAppName}}"; Flags: nowait postinstall skipifsilent

; -------- WebView2 Runtime (Win10/11) --------
; Pywebview usa WebView2. Win11 já vem com ele. Em Win10 algumas instalações
; podem não ter. O bloco [Code] abaixo detecta e baixa silenciosamente do
; Microsoft Edge canal estável se faltar. Comentado por ora — testar primeiro
; sem ele; ativar se algum usuário Win10 reclamar.

;[Code]
;function IsWebView2Installed: Boolean;
;var
;  Version: string;
;begin
;  Result := RegQueryStringValue(HKLM, 'Software\Wow6432Node\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}', 'pv', Version) and (Version <> '');
;  if not Result then
;    Result := RegQueryStringValue(HKCU, 'Software\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}', 'pv', Version) and (Version <> '');
;end;
