#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""取回某封邮件的全部附件（复用 ~/.nova-tools/mail.py 的账号配置，不打印任何密钥）。

用法:
    python3 fetch_attach.py <account> <folder> <uid> <outdir>

为什么不用 mail.py show：它只打印正文与头部，**不列也不存附件**。
历史邮件（几个月前的）常靠 mail_facts.jsonl 定位 uid，见 SKILL.md。
"""
import importlib.util
import os
import sys
from email import message_from_bytes

MAIL_PY = os.path.expanduser("~/.nova-tools/mail.py")


def load_novamail():
    spec = importlib.util.spec_from_file_location("novamail", MAIL_PY)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main():
    if len(sys.argv) != 5:
        sys.exit(__doc__)
    account, folder, uid, outdir = sys.argv[1:5]
    mail = load_novamail()
    cfg = mail.load_cfg()
    _, acct = mail.acct(cfg, account)
    imap = mail.imap_connect(acct)
    imap.select(folder)
    typ, data = imap.uid("fetch", uid, "(RFC822)")
    if typ != "OK" or not data or data[0] is None:
        sys.exit("取回失败：检查 account/folder/uid")
    msg = message_from_bytes(data[0][1])
    os.makedirs(outdir, exist_ok=True)
    saved = 0
    for part in msg.walk():
        filename = part.get_filename()
        if not filename:
            continue
        safe = mail.dec(filename).replace("/", "_")
        path = os.path.join(outdir, safe)
        payload = part.get_payload(decode=True) or b""
        with open(path, "wb") as fh:
            fh.write(payload)
        saved += 1
        print("SAVED\t%s\t%d bytes" % (path, len(payload)))
    print("attachments:", saved)
    imap.logout()


if __name__ == "__main__":
    main()
