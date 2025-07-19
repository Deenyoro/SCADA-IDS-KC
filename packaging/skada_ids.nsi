; SKADA-IDS-KC NSIS Installer Script
; Creates a Windows installer that includes dependencies and the main application

!define APP_NAME "SKADA-IDS-KC"
!define APP_VERSION "1.0.0"
!define APP_PUBLISHER "SKADA-IDS-KC Team"
!define APP_URL "https://github.com/skada-ids-kc/skada-ids-kc"
!define APP_DESCRIPTION "Network Intrusion Detection System"

; Installer settings
Name "${APP_NAME}"
OutFile "SKADA-IDS-KC-Setup.exe"
InstallDir "$PROGRAMFILES64\${APP_NAME}"
InstallDirRegKey HKLM "Software\${APP_NAME}" "InstallDir"
RequestExecutionLevel admin

; Modern UI
!include "MUI2.nsh"

; Interface settings
!define MUI_ABORTWARNING
!define MUI_ICON "..\src\ui\icons\tray.ico"
!define MUI_UNICON "..\src\ui\icons\tray.ico"

; Pages
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "..\LICENSE"
!insertmacro MUI_PAGE_COMPONENTS
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

; Uninstaller pages
!insertmacro MUI_UNPAGE_WELCOME
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_UNPAGE_FINISH

; Languages
!insertmacro MUI_LANGUAGE "English"

; Version information
VIProductVersion "1.0.0.0"
VIAddVersionKey "ProductName" "${APP_NAME}"
VIAddVersionKey "ProductVersion" "${APP_VERSION}"
VIAddVersionKey "CompanyName" "${APP_PUBLISHER}"
VIAddVersionKey "FileDescription" "${APP_DESCRIPTION}"
VIAddVersionKey "FileVersion" "${APP_VERSION}"
VIAddVersionKey "LegalCopyright" "© 2025 ${APP_PUBLISHER}"

; Installer sections
Section "Core Application" SecCore
    SectionIn RO  ; Required section
    
    SetOutPath "$INSTDIR"
    
    ; Copy main executable
    File "..\dist\SKADA-IDS-KC.exe"
    
    ; Copy documentation
    File "..\README.md"
    File "..\LICENSE"
    
    ; Create uninstaller
    WriteUninstaller "$INSTDIR\Uninstall.exe"
    
    ; Registry entries
    WriteRegStr HKLM "Software\${APP_NAME}" "InstallDir" "$INSTDIR"
    WriteRegStr HKLM "Software\${APP_NAME}" "Version" "${APP_VERSION}"
    
    ; Add/Remove Programs entry
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "DisplayName" "${APP_NAME}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "DisplayVersion" "${APP_VERSION}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "Publisher" "${APP_PUBLISHER}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "URLInfoAbout" "${APP_URL}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "DisplayIcon" "$INSTDIR\SKADA-IDS-KC.exe"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "UninstallString" "$INSTDIR\Uninstall.exe"
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "NoModify" 1
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "NoRepair" 1
SectionEnd

Section "Desktop Shortcut" SecDesktop
    CreateShortcut "$DESKTOP\${APP_NAME}.lnk" "$INSTDIR\SKADA-IDS-KC.exe" "" "$INSTDIR\SKADA-IDS-KC.exe" 0
SectionEnd

Section "Start Menu Shortcuts" SecStartMenu
    CreateDirectory "$SMPROGRAMS\${APP_NAME}"
    CreateShortcut "$SMPROGRAMS\${APP_NAME}\${APP_NAME}.lnk" "$INSTDIR\SKADA-IDS-KC.exe" "" "$INSTDIR\SKADA-IDS-KC.exe" 0
    CreateShortcut "$SMPROGRAMS\${APP_NAME}\Uninstall.lnk" "$INSTDIR\Uninstall.exe" "" "$INSTDIR\Uninstall.exe" 0
SectionEnd

Section "Npcap Driver" SecNpcap
    ; Check if Npcap is already installed
    ReadRegStr $0 HKLM "SOFTWARE\Npcap" "InstallDir"
    StrCmp $0 "" install_npcap npcap_exists
    
    install_npcap:
        DetailPrint "Installing Npcap driver..."
        File "..\installers\npcap-1.79.exe"
        ExecWait '"$INSTDIR\npcap-1.79.exe" /S' $0
        Delete "$INSTDIR\npcap-1.79.exe"
        
        IntCmp $0 0 npcap_success npcap_error npcap_error
        npcap_success:
            DetailPrint "Npcap installed successfully"
            Goto npcap_done
        npcap_error:
            DetailPrint "Npcap installation failed (exit code: $0)"
            Goto npcap_done
    
    npcap_exists:
        DetailPrint "Npcap is already installed"
    
    npcap_done:
SectionEnd

Section "Visual C++ Redistributable" SecVCRedist
    ; Check if VC++ Redistributable is installed
    ReadRegDWORD $0 HKLM "SOFTWARE\Microsoft\VisualStudio\14.0\VC\Runtimes\x64" "Installed"
    IntCmp $0 1 vcredist_exists install_vcredist install_vcredist
    
    install_vcredist:
        DetailPrint "Installing Visual C++ Redistributable..."
        File "..\installers\vc_redist.x64.exe"
        ExecWait '"$INSTDIR\vc_redist.x64.exe" /quiet /norestart' $0
        Delete "$INSTDIR\vc_redist.x64.exe"
        
        IntCmp $0 0 vcredist_success vcredist_error vcredist_error
        vcredist_success:
            DetailPrint "Visual C++ Redistributable installed successfully"
            Goto vcredist_done
        vcredist_error:
            DetailPrint "Visual C++ Redistributable installation failed (exit code: $0)"
            Goto vcredist_done
    
    vcredist_exists:
        DetailPrint "Visual C++ Redistributable is already installed"
    
    vcredist_done:
SectionEnd

; Section descriptions
!insertmacro MUI_FUNCTION_DESCRIPTION_BEGIN
    !insertmacro MUI_DESCRIPTION_TEXT ${SecCore} "Core application files (required)"
    !insertmacro MUI_DESCRIPTION_TEXT ${SecDesktop} "Create desktop shortcut"
    !insertmacro MUI_DESCRIPTION_TEXT ${SecStartMenu} "Create Start Menu shortcuts"
    !insertmacro MUI_DESCRIPTION_TEXT ${SecNpcap} "Install Npcap packet capture driver (required for network monitoring)"
    !insertmacro MUI_DESCRIPTION_TEXT ${SecVCRedist} "Install Visual C++ Redistributable (required runtime)"
!insertmacro MUI_FUNCTION_DESCRIPTION_END

; Uninstaller section
Section "Uninstall"
    ; Remove files
    Delete "$INSTDIR\SKADA-IDS-KC.exe"
    Delete "$INSTDIR\README.md"
    Delete "$INSTDIR\LICENSE"
    Delete "$INSTDIR\Uninstall.exe"
    
    ; Remove shortcuts
    Delete "$DESKTOP\${APP_NAME}.lnk"
    Delete "$SMPROGRAMS\${APP_NAME}\${APP_NAME}.lnk"
    Delete "$SMPROGRAMS\${APP_NAME}\Uninstall.lnk"
    RMDir "$SMPROGRAMS\${APP_NAME}"
    
    ; Remove registry entries
    DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}"
    DeleteRegKey HKLM "Software\${APP_NAME}"
    
    ; Remove installation directory
    RMDir "$INSTDIR"
SectionEnd

; Functions
Function .onInit
    ; Check Windows version
    ${IfNot} ${AtLeastWin7}
        MessageBox MB_OK|MB_ICONSTOP "This application requires Windows 7 or later."
        Abort
    ${EndIf}
    
    ; Check for administrator privileges
    UserInfo::GetAccountType
    Pop $0
    ${If} $0 != "admin"
        MessageBox MB_OK|MB_ICONSTOP "Administrator privileges are required to install this application."
        Abort
    ${EndIf}
FunctionEnd
