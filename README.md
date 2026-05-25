# 库房物资管理系统 — 后端

基于 **FastAPI + SQLAlchemy + SQLite/MySQL** 的模块化后端。

---

## 目录结构

```
wms-backend/
├── main.py                  # 应用入口，启动点
├── requirements.txt         # Python 依赖
├── .env.example             # 环境变量模板（复制为 .env 使用）
├── data/                    # SQLite 数据库文件（自动创建）
├── static/                  # 前端静态文件（放入 index.html）
└── app/
    ├── core/
    │   ├── config.py        # 读取 .env 配置
    │   ├── database.py      # 数据库连接 & 会话
    │   ├── security.py      # 密码哈希 & JWT
    │   ├── deps.py          # 依赖注入（获取当前用户）
    │   └── init_db.py       # 首次启动初始化数据
    ├── models/
    │   └── models.py        # 数据库表模型（ORM）
    ├── schemas/
    │   └── schemas.py       # 请求/响应数据格式（Pydantic）
    └── routers/
        ├── auth.py          # 登录认证
        ├── users.py         # 用户管理（管理员）
        ├── fields.py        # 字段管理（管理员）
        ├── inventory.py     # 库存物资 CRUD + 出入库
        ├── archive.py       # 出入库档案查询
        ├── analysis.py      # 数据分析统计
        └── config.py        # 系统配置 & 操作日志
```

---

## 快速启动

### 1. 安装依赖

```bash
cd wms-backend
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 用文本编辑器打开 .env，按需修改配置
```

> **生产环境必须修改** `SECRET_KEY` 为随机长字符串！

### 3. 启动服务

```bash
# 开发模式（自动重载）
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# 生产模式
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

### 4. 访问

| 地址 | 说明 |
|------|------|
| `http://localhost:8000/docs` | Swagger 交互式 API 文档 |
| `http://localhost:8000/redoc` | ReDoc 文档 |
| `http://localhost:8000/api/health` | 健康检查 |
| `http://localhost:8000/` | 前端页面（需放 static/index.html） |

默认管理员账号：`admin` / `123456`（首次启动自动创建）

---

## 前端集成

将前端 HTML 文件改名为 `index.html`，放入 `static/` 目录，访问
`http://localhost:8000/` 即可。

前端需要将所有 `DB.get/set` 替换为 API 调用，例如：

```javascript
// 登录
const res = await fetch('/api/auth/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ username: 'admin', password: '123456' })
});
const { access_token } = await res.json();

// 后续请求带 Token
const items = await fetch('/api/inventory', {
  headers: { 'Authorization': `Bearer ${access_token}` }
}).then(r => r.json());
```

---

## API 接口一览

### 认证
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/auth/login | 登录，返回 JWT Token |
| GET  | /api/auth/me    | 获取当前用户信息 |
| POST | /api/auth/logout | 退出（记录日志） |

### 库存
| 方法 | 路径 | 说明 |
|------|------|------|
| GET  | /api/inventory | 查询列表（支持搜索/筛选/分页） |
| POST | /api/inventory | 新增物资并入库 |
| GET  | /api/inventory/{id} | 物资详情 |
| PUT  | /api/inventory/{id} | 修改物资信息 |
| DELETE | /api/inventory/{id} | 删除物资（管理员） |
| POST | /api/inventory/{id}/stock-in | 追加入库 |
| POST | /api/inventory/{id}/stock-out | 出库 |
| GET  | /api/inventory/{id}/records | 该物资流水 |

### 管理
| 方法 | 路径 | 说明 |
|------|------|------|
| GET/POST/PUT/DELETE | /api/users | 用户管理 |
| GET/POST/PUT/DELETE | /api/fields | 字段管理 |
| GET/PUT | /api/config | 系统配置 |
| GET/DELETE | /api/logs | 操作日志 |
| GET | /api/analysis/summary | 汇总统计 |
| GET | /api/analysis/stock-top | 库存排行 |
| GET | /api/analysis/category | 类别分布 |
| GET | /api/analysis/trend | 出入库趋势 |
| GET | /api/archive | 全量流水档案 |

---

## 切换数据库

编辑 `.env` 文件中的 `DATABASE_URL`：

```bash
# MySQL（需安装 pip install pymysql）
DATABASE_URL=mysql+pymysql://root:password@localhost:3306/wms

# PostgreSQL（需安装 pip install psycopg2-binary）
DATABASE_URL=postgresql://user:password@localhost:5432/wms
```

---

## 打包为桌面 App

结合前端 HTML，用 **PyInstaller + 内嵌 Uvicorn** 可打包为 .exe：

```bash
pip install pyinstaller
pyinstaller --onefile --add-data "static:static" --add-data "data:data" main.py
```

或使用 **Electron** 包裹前端，后端作为独立进程运行。
