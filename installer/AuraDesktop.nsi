!include "MUI2.nsh"
Name "AuraDesktop"
OutFile "${__FILEDIR__}\..\dist\AuraDesktop-Setup.exe"
InstallDir "$LOCALAPPDATA\Programs\AuraDesktop"
RequestExecutionLevel user
!define MUI_ABORTWARNING
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_LANGUAGE "English"
Section "AuraDesktop"
  SetOutPath "$INSTDIR"
  File /r "${__FILEDIR__}\..\dist\AuraDesktop\*.*"
  CreateDirectory "$SMPROGRAMS\AuraDesktop"
  CreateShortcut "$SMPROGRAMS\AuraDesktop\AuraDesktop.lnk" "$INSTDIR\AuraDesktop.exe"
  ; Register the saver executable, but do not silently overwrite the user's timeout.
  WriteRegStr HKCU "Control Panel\Desktop" "SCRNSAVE.EXE" "$INSTDIR\AuraDesktop.scr"
  WriteUninstaller "$INSTDIR\Uninstall.exe"
SectionEnd
Section "Uninstall"
  DeleteRegValue HKCU "Software\Microsoft\Windows\CurrentVersion\Run" "AuraDesktop"
  ReadRegStr $0 HKCU "Control Panel\Desktop" "SCRNSAVE.EXE"
  StrCmp $0 "$INSTDIR\AuraDesktop.scr" 0 +2
    DeleteRegValue HKCU "Control Panel\Desktop" "SCRNSAVE.EXE"
  Delete "$SMPROGRAMS\AuraDesktop\AuraDesktop.lnk"
  RMDir "$SMPROGRAMS\AuraDesktop"
  Delete "$INSTDIR\Uninstall.exe"
  RMDir /r "$INSTDIR"
SectionEnd
