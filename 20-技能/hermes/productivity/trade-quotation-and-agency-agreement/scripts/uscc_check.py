#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""统一社会信用代码（USCC）校验位与结构拆解。

用法：python3 uscc_check.py 91440300MAKHQG59X0 [更多代码 ...]
输出 JSON：校验位是否通过、行政区划码、主体标识码前缀、登记时点提示。

用途：签合同/付款前第一步——号码格式不合的直接停，不进入后续核验。
校验位通过不等于对方可靠（真号码也可以属于空壳公司），只是排除伪造号码的常见形态。
"""
import json
import sys

CHARS = "0123456789ABCDEFGHJKLMNPQRTUWXY"  # 无 I O S V Z
WEIGHTS = [1, 3, 9, 27, 19, 26, 16, 17, 20, 29, 25, 13, 8, 24, 10, 30, 28]
AREAS = {
    "110000": "北京市", "120000": "天津市", "310000": "上海市", "500000": "重庆市",
    "440300": "深圳市", "440100": "广州市", "370100": "济南市", "320100": "南京市",
    "330100": "杭州市", "510100": "成都市", "420100": "武汉市", "610100": "西安市",
}


def check(code: str) -> dict:
    code = code.strip().upper().replace(" ", "").replace("\u3000", "")
    out = {"code": code}
    if len(code) != 18:
        out["verdict"] = f"格式不合：长度 {len(code)}，应为 18 位 — 停，不要继续核验"
        return out
    bad = sorted({c for c in code if c not in CHARS})
    if bad:
        out["verdict"] = f"格式不合：含非法字符 {bad}（合法字符集不含 I O S V Z）— 停"
        return out
    vals = [CHARS.index(c) for c in code[:17]]
    expect = CHARS[(31 - sum(v * w for v, w in zip(vals, WEIGHTS)) % 31) % 31]
    out.update({
        "area": code[2:8],
        "area_name": AREAS.get(code[2:8], "（未收录，自行核对行政区划码）"),
        "org_code": code[8:17],
        "check_expected": expect,
        "check_actual": code[17],
        "checksum_ok": expect == code[17],
        "registered_after_2015_10": code[8] == "M",
    })
    out["verdict"] = ("校验位通过：号码格式合法（不等于对方可靠 — 继续查工商四项、对公账户户名、凭证）"
                      if out["checksum_ok"] else
                      f"校验位不通过：应为 {expect}，实为 {code[17]} — 号码可能有误或被篡改，停")
    return out


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    for arg in sys.argv[1:]:
        print(json.dumps(check(arg), ensure_ascii=False, indent=1))
