# /home/airhust/zyt/SaveBite/deploy.sh
#!/bin/bash
cd /home/airhust/zyt/SaveBite
# git pull origin main
sudo systemctl restart savebite
echo "✅ SaveBite 已更新并重启！"