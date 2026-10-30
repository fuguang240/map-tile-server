#!/usr/bin/env bash
# CentOS Stream 10 + Apache 部署地图瓦片服务器
# 使用：sudo bash scripts/deploy.sh
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
TILES_SRC="${PROJECT_DIR}/tiles"
TILES_DEST="/var/www/tiles"
WEB_SRC="${PROJECT_DIR}/web"
WEB_DEST="/var/www/html/map"

echo "[1/5] 安装 Apache..."
dnf install -y httpd

echo "[2/5] 拷贝瓦片与站点配置..."
mkdir -p "${TILES_DEST}" "${WEB_DEST}"
if [ -d "${TILES_SRC}" ]; then
    cp -r "${TILES_SRC}"/* "${TILES_DEST}"/
else
    echo "!! 未找到 tiles/ 目录，请先运行 python3 scripts/fetch_tiles.py"
    exit 1
fi
cp "${WEB_SRC}"/index.html "${WEB_DEST}"/
cp "${PROJECT_DIR}/apache/tiles.conf" /etc/httpd/conf.d/tiles.conf

echo "[3/5] 放行 80 端口..."
firewall-cmd --permanent --add-service=http || true
firewall-cmd --reload || true

echo "[4/5] 启动并设置开机自启..."
systemctl enable --now httpd
systemctl restart httpd

echo "[5/5] 验证..."
echo "--- 瓦片可访问性 ---"
curl -s -o /dev/null -w "%{http_code} %{size_download}B" \
    "http://127.0.0.1/tiles/10/907/425.png" || echo "瓦片未命中（按实际层级调整路径）"
echo
echo "--- 可视化页面 ---"
curl -s -o /dev/null -w "%{http_code}" "http://127.0.0.1/map/"
echo
echo "部署完成：http://<服务器IP>/map/"
