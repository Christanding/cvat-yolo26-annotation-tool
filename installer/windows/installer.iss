#ifndef AppVersion
  #define AppVersion "0.0.0"
#endif
#ifndef StagingDir
  #error StagingDir is required
#endif
#ifndef OutputDir
  #define OutputDir ".\Output"
#endif

#define AppName "YOLO26 图片标注软件"

[Setup]
AppId={{03C492A9-A25F-4E0F-B3ED-CF3C37908AE0}
AppName={#AppName}
AppVersion={#AppVersion}
DefaultDirName={localappdata}\Programs\YOLO26图片标注软件
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
OutputDir={#OutputDir}
OutputBaseFilename=标注软件-Setup
Compression=zip/7
SolidCompression=no
PrivilegesRequired=lowest
SetupArchitecture=x64
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
WizardStyle=modern dynamic
SetupLogging=yes
UninstallDisplayName={#AppName}
VersionInfoDescription={#AppName} 离线安装程序
VersionInfoProductName={#AppName}
VersionInfoVersion={#AppVersion}

[Languages]
Name: "chinesesimplified"; MessagesFile: "compiler:Default.isl,{#SourcePath}\ChineseSimplified.isl"

[Files]
Source: "{#StagingDir}\runtime\docker-compose.yml"; DestDir: "{app}\runtime"; Flags: ignoreversion
Source: "{#StagingDir}\runtime\docker-compose.local.yml"; DestDir: "{app}\runtime"; Flags: ignoreversion
Source: "{#StagingDir}\runtime\images.tar"; DestDir: "{app}\runtime"; Flags: ignoreversion deleteafterinstall
Source: "{#StagingDir}\runtime\image-list.txt"; DestDir: "{app}\runtime"; Flags: ignoreversion
Source: "{#StagingDir}\runtime\LICENSE"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#StagingDir}\runtime\THIRD_PARTY.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#SourcePath}\scripts\*.ps1"; DestDir: "{app}\scripts"; Flags: ignoreversion

[Icons]
Name: "{autodesktop}\启动标注软件"; Filename: "{sys}\WindowsPowerShell\v1.0\powershell.exe"; Parameters: "-NoProfile -ExecutionPolicy Bypass -File ""{app}\scripts\Start-App.ps1"" -InstallDir ""{app}"""; WorkingDir: "{app}"
Name: "{group}\启动标注软件"; Filename: "{sys}\WindowsPowerShell\v1.0\powershell.exe"; Parameters: "-NoProfile -ExecutionPolicy Bypass -File ""{app}\scripts\Start-App.ps1"" -InstallDir ""{app}"""; WorkingDir: "{app}"
Name: "{group}\停止标注软件"; Filename: "{sys}\WindowsPowerShell\v1.0\powershell.exe"; Parameters: "-NoProfile -ExecutionPolicy Bypass -File ""{app}\scripts\Stop-App.ps1"" -InstallDir ""{app}"""; WorkingDir: "{app}"
Name: "{group}\卸载标注软件"; Filename: "{uninstallexe}"

[UninstallRun]
Filename: "{sys}\WindowsPowerShell\v1.0\powershell.exe"; Parameters: "-NoProfile -ExecutionPolicy Bypass -File ""{app}\scripts\Stop-App.ps1"" -InstallDir ""{app}"" -RemoveContainers"; Flags: runhidden waituntilterminated skipifdoesntexist

[UninstallDelete]
Type: files; Name: "{app}\.env"

[Code]
var
  WorkspacePage: TInputDirWizardPage;
  AccountPage: TInputQueryWizardPage;

procedure InitializeWizard;
var
  PreviousWorkspace: String;
begin
  WorkspacePage := CreateInputDirPage(
    wpSelectDir,
    '选择工作根目录',
    '原始图片、视频和持久化数据放在哪里？',
    '请选择一个长期保留的目录。软件只会在其中创建 .cvat-local，不会修改原始图片和视频。',
    False,
    ''
  );
  WorkspacePage.Add('');
  PreviousWorkspace := GetPreviousData('WorkspaceRoot', '');
  if PreviousWorkspace <> '' then
    WorkspacePage.Values[0] := PreviousWorkspace
  else
    WorkspacePage.Values[0] := ExpandConstant('{userdocs}\标注工作区');

  AccountPage := CreateInputQueryPage(
    WorkspacePage.ID,
    '设置本地账户',
    '首次打开软件时使用此账户登录',
    '账户仅保存在本机。浏览器会长期保持登录状态。'
  );
  AccountPage.Add('账户名：', False);
  AccountPage.Add('密码（至少 8 个字符）：', True);
  AccountPage.Add('确认密码：', True);
  AccountPage.Values[0] := 'annotator';
end;

function IsValidUsername(const Value: String): Boolean;
var
  I: Integer;
begin
  Result := (Length(Value) > 0) and (Length(Value) <= 150);
  for I := 1 to Length(Value) do
    if Pos(Value[I], 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789@.+-_') = 0 then
      Result := False;
end;

function NextButtonClick(CurPageID: Integer): Boolean;
begin
  Result := True;
  if CurPageID = WorkspacePage.ID then begin
    if Trim(WorkspacePage.Values[0]) = '' then begin
      MsgBox('请选择工作根目录。', mbError, MB_OK);
      Result := False;
    end;
  end else if CurPageID = AccountPage.ID then begin
    if not IsValidUsername(Trim(AccountPage.Values[0])) then begin
      MsgBox('账户名只能包含字母、数字和 @ . + - _，且不能为空。', mbError, MB_OK);
      Result := False;
    end else if Length(AccountPage.Values[1]) < 8 then begin
      MsgBox('密码至少需要 8 个字符。', mbError, MB_OK);
      Result := False;
    end else if AccountPage.Values[1] <> AccountPage.Values[2] then begin
      MsgBox('两次输入的密码不一致。', mbError, MB_OK);
      Result := False;
    end;
  end;
end;

procedure RegisterPreviousData(PreviousDataKey: Integer);
begin
  SetPreviousData(PreviousDataKey, 'WorkspaceRoot', WorkspacePage.Values[0]);
end;

function PrepareToInstall(var NeedsRestart: Boolean): String;
begin
  SetEnvironmentVariable('CVAT_LOCAL_USERNAME', Trim(AccountPage.Values[0]));
  SetEnvironmentVariable('CVAT_LOCAL_PASSWORD', AccountPage.Values[1]);
  Result := '';
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  ResultCode: Integer;
  Parameters: String;
begin
  if CurStep = ssPostInstall then begin
    WizardForm.StatusLabel.Caption := '正在导入离线镜像并启动服务，首次安装可能需要数分钟...';
    Parameters := '-NoProfile -ExecutionPolicy Bypass -File "' +
      ExpandConstant('{app}\scripts\Install-App.ps1') + '" -InstallDir "' +
      ExpandConstant('{app}') + '" -WorkspaceRoot "' + WorkspacePage.Values[0] +
      '" -AppVersion "{#AppVersion}"';
    if (not Exec(
      ExpandConstant('{sys}\WindowsPowerShell\v1.0\powershell.exe'),
      Parameters,
      ExpandConstant('{app}'),
      SW_HIDE,
      ewWaitUntilTerminated,
      ResultCode
    )) or (ResultCode <> 0) then
      RaiseException('安装未完成。请确认 Docker Desktop 已启动、使用 WSL 2 且已接受许可条款。');
    SetEnvironmentVariable('CVAT_LOCAL_USERNAME', '');
    SetEnvironmentVariable('CVAT_LOCAL_PASSWORD', '');
  end;
end;
