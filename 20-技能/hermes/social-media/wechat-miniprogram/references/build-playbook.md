# 小程序 1.0 落地手册（原生小程序 + 云开发）

从 PRD 变成用户手上能玩的东西。默认技术栈：原生小程序（WXML/WXSS/JS）+ 微信云开发，不引三方框架。

## 交付顺序

1. 先写代码，不等审批（AppID 可以占位）。
2. 本地把算法测试跑通（§4），再上开发者工具——开发者工具装上之前你就能给用户看证据。
3. 用户装开发者工具 + 给 AppID → 导入项目 → 上传部署云函数 → 编译真机试玩。
4. 支付、后台管理、提审材料放 1.1，别塞进 1.0。

## 1. 目录与项目配置

```
<项目>/
  project.config.json      # appid / cloudfunctionRoot: cloudfunctions/ / miniprogramRoot: miniprogram/
  miniprogram/             # app.js|app.json|app.wxss, utils/, pages/
  cloudfunctions/api/      # 单入口云函数（index.js + package.json）
  tests/                   # 本地算法测试
  README.md                # 给用户的「跑起来 6 步」
```

- `appid` 先填 `touristappid` 占位，拿到用户真实 AppID 再换；换之前确认用的就是他要上线的那个小程序。
- `miniprogramRoot` 与 `cloudfunctionRoot` 必须分开写，否则云函数目录会被当成页面目录打包。
- README 面向用户写，含「怎么用两个微信号试」——这是用户最容易卡住的地方。

## 2. 云函数：单入口 action 路由

- 一个 `api` 云函数 + `event.action` 分发，胜过十几个云函数：部署只点一次，鉴权与校验集中在一处。
- 骨架：`cloud.init({ env: cloud.DYNAMIC_CURRENT_ENV })`；`const { OPENID } = cloud.getWXContext()` 取身份；统一返回 `{ok:true,data}` / `{ok:false,msg}`；`default: return bad('未知操作')`；外层 try/catch 把 `errMsg` 回给前端。
- **建表放在 `action:'init'`** 里逐个 `db.createCollection(name)` try/catch（已存在会抛，忽略即可），前端在「关于/隐私」页放一个「初始化云数据库」按钮——比让用户去控制台手建集合省事得多。
- 集合名统一加项目前缀（`zl_sessions` / `zl_members` / `zl_records` / `zl_matches`），避免和用户既有数据撞名。
- 可调参数放一张 `<prefix>_config/default` 文档（距离阈值、权重），改参数不用重新部署。

## 3. 安全与幂等（照抄这几条）

- 身份只从 `getWXContext()` 取；客户端传的 `openid` / `ready` / `unlocked` 一律忽略。
- 写操作两步校验：先「你是不是这个会话的成员」，再「这条数据是不是你的」（`if (r.openid !== OPENID) return bad('只能删除自己的记录')`）。
- 重算类操作（匹配/结算）先 `where({session_id}).remove()` 清旧结果再写——重复触发不会翻倍。
- 邀请码用不可预测随机字符集（剔掉易混的 `0/O/1/I`），入库前查重；不要用递增 ID。
- 限额一律服务端卡：每人每会话条数、每日新建会话数、字符串长度上限、坐标与时间区间合法性（`end > start`）。

## 4. 让算法脱离云、在本地就能测

把纯函数从 handler 里抽出来（`distanceM` / `scoreOf` / `matchPairs`），文件末尾加一行导出：

```js
module.exports._test = { distanceM, scoreOf, matchPairs };
```

测试文件里把 SDK 换成空壳，然后 `node tests/test-match.js` —— 不连云、不装依赖：

```js
const Module = require('module');
const orig = Module._load;
Module._load = function (req) {
  if (req === 'wx-server-sdk') return {
    DYNAMIC_CURRENT_ENV: 'test', init() {},
    getWXContext: () => ({ OPENID: 'test' }),
    database: () => ({ command: { in: () => ({}), gte: () => ({}) }, collection: () => ({}) }),
  };
  return orig.apply(this, arguments);
};
```

- 阈值边界（比如 ±1 米判不判定）、指数区间、排序、规模耗时，都能在开发者工具装上之前先跑给用户看。
- 测「接受/拒绝」这类语义时，用真实语义的用例名（如「49 米判交集 / 51 米不判 / 同地点无时间重叠不判」），用户一眼知道你在验什么。
- **断言要对着先跑出来的真实值写**：凭直觉写的分数区间会假失败；先跑一次拿到实际值矩阵，再定断言，并把矩阵留成一张「标定表」打印出来——用户可以直接拿它校准体感，比描述公式有效。
- 规模用例记得跑：上限量级（如每人 30 条 → 900 对）耗时应该是毫秒级，这一条同时证明了「不需要 PostGIS」。

## 5. 受控接口的降级写法

`wx.getLocation` / `wx.chooseLocation` / `onLocationChange` 要在小程序后台申报用途才稳，别让主流程依赖它们：

- 选点用 `map` 组件 + 准星覆盖层：`bindregionchange` 里判断 `e.type === 'end'`，再 `MapContext.getCenterLocation()` 取地图中心点经纬度。全程不碰受控接口。
- 「用微信地图选点」按钮（`wx.chooseLocation`）作为**可选增强**：`app.json` 声明 `requiredPrivateInfos`，`fail` 回调里提示降级方案；主流程没有它也能走完。
- 逆地理（地名）不要引第三方 key：让用户手填地点名，后续再接腾讯位置服务。

## 6. 双人闭环的页面清单（可直接复用）

`index`（创建 / 输邀请码进入 / 我的会话列表）、`create`、`join`（接 `?code=`）、`session`（双方状态 + 我的记录 + 准备 + 揭晓入口）、`record`（选点 + 起止时间）、`reveal`（CSS 动画）、`result`（指标 + 列表）、`poster`（Canvas 2D 出图）、`about`（隐私说明 + 初始化/删除数据入口）。

- **揭晓页别串行等结果**：`onLoad` 就发计算请求，动画按固定节奏播（如 1.5s 一拍），动画结束时若结果未回就短暂轮询（`tries < 20`）。用户只会觉得「算得快」。
- 分享路径带邀请码：`onShareAppMessage` 的 `path` 写成 `/pages/join/join?code=XXX`；`app.js` 里从 `options.query.code` 与 `options.scene` 双路解析，分享卡片和扫码两种进入方式都通。
- 海报：`createSelectorQuery().fields({node:true,size:true})` 拿 canvas 节点，按 `pixelRatio` 放大画布后 `ctx.scale(dpr,dpr)` 再画，保存走 `wx.canvasToTempFilePath({canvas})` → `wx.saveImageToPhotosAlbum`。海报只放地名与指标，不放原始经纬度。
- 深色底 + 单一品牌色的排版在截图/海报上比地图截图更像「产品」，用户更容易接受（本用户偏好克制、高级的视觉）。

## 7. 两个人怎么测

同一个人测不了双人流程。做法：A 用真机预览创建会话拿到邀请码；B 换一个微信号，在开发者工具「添加编译模式」里把启动页面设为 `pages/join/join`、启动参数填 `code=XXXXXX`，或扫分享卡片在真机进入。把这套写进 README。

## 8. 工具层

- 微信开发者工具是独立 App，要单独装、扫码登录，并给运营者微信号开开发者权限（成员管理里加）。
- 安装最快路径：请用户点开官方下载页装（页面 JS 渲染，`curl`/正文提取拿不到 `.dmg`，官方跳转接口的 302 不带 `Location`）。
- 云开发环境要在他的 AppID 下开通（首次有免费体验环境）；代码里 `wx.cloud.init({ env: wx.cloud.DYNAMIC_CURRENT_ENV })` 会自动用它。
- 读小程序后台状态（认证/备案/类目/主体）需扫码登录 `mp.weixin.qq.com`，**登录态跨调用会掉**，「登录 + 读完状态」必须在一次浏览器操作里完成。
- 浏览器侧若报 Chrome 占用 profile 锁（用户日常开着 Chrome），让用户完全退出 Chrome（含后台进程）或调整 `browser.use_real_profile` 配置后重试——这是配置/状态问题，不是浏览器能力问题。

## 9. 什么时候才需要上线材料

备案、服务类目、微信认证、虚拟支付开通、隐私保护指引——挡的是「发布 + 收钱」，挡不住开发版/体验版内部试玩。开发期唯一要提前守的是：不用受控接口（§5）、用户自定义文本过 `security.msgSecCheck`、到期数据真的能删。
