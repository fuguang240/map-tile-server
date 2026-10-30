# 基于 Apache 的地图瓦片服务器搭建

以论文《基于 OSGEarth 的地图数据服务器构建方法》为思路指导，复刻一套轻量地图瓦片服务器：
**Python 自动抓取 XYZ 瓦片 → 数据处理 → 导入 CentOS Stream 10 + Apache 提供静态服务 →
HTML（Leaflet）本地可视化**，并对比本地文件与服务器双端访问。

## 架构

```
        Python 抓取脚本
  fetch_tiles.py  (XYZ 瓦片)
            |
            v
  tiles/{z}/{x}/{y}.png   (本地瓦片库)
            |
            v
  Apache (httpd)  Alias /tiles  ->  /var/www/tiles
            |
            v
  Leaflet 页面 (web/index.html) 加载 /tiles/{z}/{x}/{y}.png
```

## 快速开始

### 1. 抓取瓦片（本地）

```bash
# 以长沙市区为例，抓取 z10-z14 层级
python3 scripts/fetch_tiles.py --center 28.228,112.937 --min-zoom 10 --max-zoom 14
```

### 2. 部署到服务器（CentOS Stream 10 + Apache）

```bash
sudo bash scripts/deploy.sh
```

自动完成：安装 httpd → 拷贝瓦片到 `/var/www/tiles` → 启用站点配置 →
放行 80 端口 → 重启并验证。

### 3. 可视化

- 服务器端：浏览器访问 `http://<服务器IP>/map/`（`web/` 部署到 Apache 站点目录）
- 本地端：直接双击打开 `web/index.html`（file:// 协议加载本地瓦片）

## 双端对比

| 对比项 | 本地打开 (file://) | 服务器访问 (http://) |
|---|---|---|
| 瓦片加载 | 读本地磁盘，快 | 走 Apache 静态服务 + Cache-Control |
| 访问范围 | 仅本机 | 局域网/公网任意设备 |
| 用途 | 开发调试 | 对外提供服务 |

## 关键技术点

- **瓦片坐标换算**：`deg2num` 实现经纬度 → XYZ 行列号（Web Mercator 反算）。
- **数据校验**：下载后按文件大小过滤坏瓦片，保留 `tiles.json` 清单。
- **缓存策略**：Apache 对瓦片资源下发 `Cache-Control: max-age=86400`。
- **可视化**：Leaflet + 本地瓦片图层，无外网瓦片依赖。

## 目录结构

```
map-tile-server/
├── scripts/
│   ├── fetch_tiles.py      # 瓦片抓取与校验
│   └── deploy.sh           # CentOS Stream 10 + Apache 一键部署
├── apache/
│   └── tiles.conf          # Apache 瓦片站点配置
├── web/
│   └── index.html          # Leaflet 本地可视化
└── README.md
```

## 后续优化建议

1. 接入 `mod_rewrite` 做瓦片防盗链与访问控制；
2. 瓦片预生成 `tiles/{z}/{x}/{y}.png` 后启用 gzip/brotli 压缩；
3. 增加多区域批量抓取与增量更新脚本；
4. 结合 OSGEarth 思路扩展三维地形瓦片服务。

> 瓦片来源仅用于学习演示，正式对外服务请遵守目标瓦片服务的使用政策并自行准备数据。
