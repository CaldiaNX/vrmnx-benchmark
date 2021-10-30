@echo off
echo VRMNXベンチマークで表示するシステム情報をファイル出力しています。この表示は数秒で消えます。
cd /d %~dp0
dxdiag /t
exit /b 0