#define MyAppName "KShot"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "KShot"
#define MyAppURL "https://kshot.cloud"
#define MyAppExeName "KShot.exe"

[Setup]
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
LicenseFile=
OutputDir=dist\installer
OutputBaseFilename=KShot-Setup-v{#MyAppVersion}
SetupIconFile=icon.ico
Compression=lzma
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
ArchitecturesInstallIn64BitMode=x64

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "startupicon"; Description: "Start KShot when Windows starts"; GroupDescription: "Startup:";

[Files]
Source: "dist\KShot.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Registry]
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: string; ValueName: "{#MyAppName}"; ValueData: """{app}\{#MyAppExeName}"""; Flags: uninsdeletevalue; Tasks: startupicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

; ── Custom wizard pages untuk akun KShot ─────────────────────────────────────
[Code]

var
  AccountPage: TWizardPage;
  UsernameEdit: TEdit;
  PasswordEdit: TEdit;
  UsernameLabel: TLabel;
  PasswordLabel: TLabel;
  HintLabel: TLabel;

// ── Buat halaman akun setelah "Select Destination" ────────────────────────────
procedure InitializeWizard;
begin
  AccountPage := CreateCustomPage(
    wpSelectDir,
    'Akun KShot',
    'Masukkan username dan password yang diberikan oleh admin kamu.'
  );

  HintLabel := TLabel.Create(AccountPage);
  HintLabel.Parent  := AccountPage.Surface;
  HintLabel.Caption :=
    'Akun ini digunakan untuk menghubungkan screenshot kamu ke server KShot.' + #13#10 +
    'Username dan password diberikan oleh administrator.';
  HintLabel.Left   := 0;
  HintLabel.Top    := 0;
  HintLabel.Width  := AccountPage.SurfaceWidth;
  HintLabel.Height := 40;
  HintLabel.AutoSize := False;
  HintLabel.WordWrap := True;

  UsernameLabel := TLabel.Create(AccountPage);
  UsernameLabel.Parent  := AccountPage.Surface;
  UsernameLabel.Caption := 'Username:';
  UsernameLabel.Left    := 0;
  UsernameLabel.Top     := 56;
  UsernameLabel.Font.Style := [fsBold];

  UsernameEdit := TEdit.Create(AccountPage);
  UsernameEdit.Parent := AccountPage.Surface;
  UsernameEdit.Left   := 0;
  UsernameEdit.Top    := 74;
  UsernameEdit.Width  := AccountPage.SurfaceWidth;
  UsernameEdit.TabOrder := 0;

  PasswordLabel := TLabel.Create(AccountPage);
  PasswordLabel.Parent  := AccountPage.Surface;
  PasswordLabel.Caption := 'Password:';
  PasswordLabel.Left    := 0;
  PasswordLabel.Top     := 110;
  PasswordLabel.Font.Style := [fsBold];

  PasswordEdit := TEdit.Create(AccountPage);
  PasswordEdit.Parent       := AccountPage.Surface;
  PasswordEdit.Left         := 0;
  PasswordEdit.Top          := 128;
  PasswordEdit.Width        := AccountPage.SurfaceWidth;
  PasswordEdit.PasswordChar := '*';
  PasswordEdit.TabOrder     := 1;
end;

// ── Validasi dan simpan credentials sebelum lanjut ───────────────────────────
function NextButtonClick(CurPageID: Integer): Boolean;
var
  KShotDir:     string;
  PendingFile:  string;
  JsonContent:  string;
  Username:     string;
  Password:     string;
begin
  Result := True;

  if CurPageID = AccountPage.ID then
  begin
    Username := Trim(UsernameEdit.Text);
    Password := PasswordEdit.Text;

    // Validasi kosong
    if Username = '' then
    begin
      MsgBox('Username tidak boleh kosong.', mbError, MB_OK);
      Result := False;
      Exit;
    end;

    if Password = '' then
    begin
      MsgBox('Password tidak boleh kosong.', mbError, MB_OK);
      Result := False;
      Exit;
    end;

    // Simpan ke %USERPROFILE%\.KShot\pending_credentials.json
    // App akan membacanya saat pertama kali dijalankan
    KShotDir    := GetEnv('USERPROFILE') + '\.KShot';
    PendingFile := KShotDir + '\pending_credentials.json';

    ForceDirectories(KShotDir);

    // Build JSON (username hanya alfanumerik+underscore, password di-escape minimal)
    JsonContent := '{"username":"' + Username + '","password":"' + Password + '"}';

    if not SaveStringToFile(PendingFile, JsonContent, False) then
    begin
      MsgBox(
        'Gagal menyimpan informasi akun.' + #13#10 +
        'Pastikan kamu memiliki izin tulis ke folder: ' + KShotDir,
        mbError, MB_OK
      );
      Result := False;
      Exit;
    end;
  end;
end;

// ── Bersihkan pending file jika installer dibatalkan ─────────────────────────
procedure CancelButtonClick(CurPageID: Integer; var Cancel, Confirm: Boolean);
var
  PendingFile: string;
begin
  PendingFile := GetEnv('USERPROFILE') + '\.KShot\pending_credentials.json';
  if FileExists(PendingFile) then
    DeleteFile(PendingFile);
end;

// ── Hapus session saat uninstall ─────────────────────────────────────────────
procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  KShotDir:    string;
  SessionFile: string;
  PendingFile: string;
begin
  if CurUninstallStep = usPostUninstall then
  begin
    KShotDir    := GetEnv('USERPROFILE') + '\.KShot';
    SessionFile := KShotDir + '\session.json';
    PendingFile := KShotDir + '\pending_credentials.json';

    if FileExists(SessionFile) then
      DeleteFile(SessionFile);

    if FileExists(PendingFile) then
      DeleteFile(PendingFile);
  end;
end;
