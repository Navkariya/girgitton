; Inno Setup script — Girgitton App Windows installer
; Compile: iscc /DAppVersion=3.2.4 installer\girgitton.iss
;
; Natija: installer\Output\Girgitton_Windows_Setup.exe
; Foydalanuvchi: bossa wizard ochiladi → C:\Girgitton\ ga o'rnatadi → Desktop yarlik
; Uninstall: Add/Remove Programs yoki C:\Girgitton\unins000.exe orqali

#ifndef AppVersion
  #define AppVersion "3.2.4"
#endif

#define AppName "Girgitton App"
#define AppPublisher "Girgitton"
#define AppExeName "Girgitton.exe"
#define AppId "{{A0E5C8F2-4F1B-4E5A-B2D0-1C8E3F0A9B7C}"

[Setup]
AppId={#AppId}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
AppPublisherURL=https://github.com/Navkariya/girgitton
AppSupportURL=https://github.com/Navkariya/girgitton/issues
AppUpdatesURL=https://github.com/Navkariya/girgitton/releases
DefaultDirName={sd}\Girgitton
DefaultGroupName={#AppName}
OutputBaseFilename=Girgitton_Windows_Setup
OutputDir=Output
SetupIconFile=..\scripts\assets\icon.ico
UninstallDisplayName={#AppName}
UninstallDisplayIcon={app}\{#AppExeName}
DisableProgramGroupPage=auto
DisableDirPage=no
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
WizardStyle=modern
Compression=lzma2
SolidCompression=yes
LicenseFile=
ChangesEnvironment=no
CloseApplications=yes
RestartApplications=no

; Yangi versiya o'rnatilganda eski versiyani avtomatik chiqaradi (AppId orqali)

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Desktopga yarlik joylash"; GroupDescription: "Qo'shimcha:"; Flags: checkedonce
Name: "startmenuicon"; Description: "Start menyusiga yarlik joylash"; GroupDescription: "Qo'shimcha:"; Flags: checkedonce

[Files]
; PyInstaller --onedir natijasi: dist\Girgitton\Girgitton.exe + _internal/
Source: "..\dist\Girgitton\*"; DestDir: "{app}"; Flags: recursesubdirs ignoreversion createallsubdirs

[Icons]
; Desktop'da "Girgitton App" yarlik (.exe ko'rinmaydi, faqat ism va ikonka)
Name: "{commondesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}"; IconFilename: "{app}\{#AppExeName}"; Tasks: desktopicon
; Start menu (Programs)
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExeName}"; IconFilename: "{app}\{#AppExeName}"; Tasks: startmenuicon
; Uninstall yarligi (group ichida)
Name: "{group}\{#AppName} ni o'chirish"; Filename: "{uninstallexe}"; Tasks: startmenuicon

[Run]
; O'rnatilgandan keyin App ni ishga tushirish (ixtiyoriy)
Filename: "{app}\{#AppExeName}"; Description: "Hozir {#AppName} ni ishga tushirish"; Flags: postinstall nowait skipifsilent unchecked

[UninstallDelete]
; Foydalanuvchi data papkasini ham o'chiramiz (sessions, credentials, progress, log)
Type: filesandordirs; Name: "{app}\data"
; Eski lokatsiyani ham (migratsiya bo'lgan bo'lsa)
Type: filesandordirs; Name: "{userappdata}\..\.girgitton"

[Registry]
; Installation directory'ni saqlaymiz (App `app_paths.py` ENV o'rniga registry'dan o'qishi uchun)
Root: HKCU; Subkey: "Software\Girgitton"; ValueType: string; ValueName: "InstallDir"; ValueData: "{app}"; Flags: uninsdeletevalue
Root: HKCU; Subkey: "Software\Girgitton"; Flags: uninsdeletekeyifempty

[Code]
// Yangi versiya o'rnatilganda eski versiyani aniqlash va uninstall qilish
function GetUninstallString(): String;
var
  sUnInstPath: String;
  sUnInstallString: String;
begin
  sUnInstPath := ExpandConstant('Software\Microsoft\Windows\CurrentVersion\Uninstall\{#emit SetupSetting("AppId")}_is1');
  sUnInstallString := '';
  if not RegQueryStringValue(HKLM, sUnInstPath, 'UninstallString', sUnInstallString) then
    RegQueryStringValue(HKCU, sUnInstPath, 'UninstallString', sUnInstallString);
  Result := sUnInstallString;
end;

function IsUpgrade(): Boolean;
begin
  Result := (GetUninstallString() <> '');
end;

function UnInstallOldVersion(): Integer;
var
  sUnInstallString: String;
  iResultCode: Integer;
begin
  Result := 0;
  sUnInstallString := GetUninstallString();
  if sUnInstallString <> '' then begin
    sUnInstallString := RemoveQuotes(sUnInstallString);
    if Exec(sUnInstallString, '/SILENT /NORESTART /SUPPRESSMSGBOXES', '', SW_HIDE, ewWaitUntilTerminated, iResultCode) then
      Result := 3
    else
      Result := 2;
  end else
    Result := 1;
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if (CurStep = ssInstall) then
  begin
    if IsUpgrade() then
      UnInstallOldVersion();
  end;
end;
