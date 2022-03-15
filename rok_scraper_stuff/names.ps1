$name = Get-Clipboard
set-location "E:\Rok\2020_KvK3\temp_screenshots"
$last_screenshot = gci . | sort LastWriteTime | select -last 1
Rename-Item -Path $last_screenshot.Name -NewName "$name.png"