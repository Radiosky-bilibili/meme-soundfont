#!/usr/bin/env python3
"""SF2 结构自检：检查常见的加载失败原因。

用法: python3 sf2check.py file.sf2
"""
import struct
import sys

INFO_IDS = {b'ifil', b'isng', b'INAM', b'ICRD', b'ISFT', b'ICMT',
            b'IENG', b'IPRD', b'ICOP', b'ISBJ', b'IGNR', b'ICMS'}
PDTA_ORDER = [b'phdr', b'pbag', b'pgen', b'pmod',
              b'inst', b'ibag', b'igen', b'imod', b'shdr']
REC_LEN = {b'phdr': 38, b'pbag': 4, b'pgen': 4, b'pmod': 10,
           b'inst': 22, b'ibag': 4, b'igen': 4, b'imod': 10, b'shdr': 46}

errors, warns = [], []


def walk(buf, start, end, depth=0, path=''):
    """遍历 chunk，返回 [(id, body, offset)]"""
    out, p = [], start
    while p + 8 <= end:
        cid = buf[p:p + 4]
        n = struct.unpack('<I', buf[p + 4:p + 8])[0]
        if p + 8 + n > end:
            errors.append('%s: chunk %r 长度 %d 超出边界' % (path or 'root', cid, n))
            break
        body = buf[p + 8:p + 8 + n]
        out.append((cid, body, p))
        if cid == b'LIST':
            out += walk(buf, p + 12, p + 8 + n, depth + 1, path + '/' + repr(body[:4]))
        p += 8 + n + (n % 2)
    return out


def main(path):
    d = open(path, 'rb').read()
    print('文件 %s，%d 字节' % (path, len(d)))

    if d[:4] != b'RIFF' or d[8:12] != b'sfbk':
        errors.append('不是 SF2 文件（RIFF/sfbk 标识不符）')
        return report()

    riff_size = struct.unpack('<I', d[4:8])[0]
    if riff_size != len(d) - 8:
        errors.append('RIFF 长度字段 %d，实际应为 %d' % (riff_size, len(d) - 8))

    chunks = walk(d, 12, len(d))

    # ---- INFO
    for cid, body, off in chunks:
        if cid == b'LIST' and body[:4] == b'INFO':
            p = 4
            while p + 8 <= len(body):
                sid = body[p:p + 4]
                n = struct.unpack('<I', body[p + 4:p + 8])[0]
                val = body[p + 8:p + 8 + n]
                if sid not in INFO_IDS:
                    errors.append('INFO 子块 ID 应为大写，发现 %r' % sid)
                if n % 2:
                    errors.append('INFO 子块 %r 长度 %d 是奇数（应为偶数）' % (sid, n))
                if not val.endswith(b'\0'):
                    warns.append('INFO 子块 %r 没有以 \\0 结尾' % sid)
                p += 8 + n + (n % 2)

    # ---- pdta
    for cid, body, off in chunks:
        if cid == b'LIST' and body[:4] == b'pdta':
            order, p = [], 4
            while p + 8 <= len(body):
                sid = body[p:p + 4]
                n = struct.unpack('<I', body[p + 4:p + 8])[0]
                order.append((sid, n))
                p += 8 + n + (n % 2)
            names = [o[0] for o in order]
            print('pdta 顺序:', [n.decode('latin1') for n in names])
            if names != PDTA_ORDER:
                errors.append('pdta 表顺序不是 %s' % [n.decode() for n in PDTA_ORDER])
            for sid, n in order:
                if sid in REC_LEN and n % REC_LEN[sid]:
                    errors.append('%r 长度 %d 不是 %d 的整数倍' % (sid, n, REC_LEN[sid]))
                if sid in (b'pmod', b'imod', b'igen', b'igen') and n == 0:
                    errors.append('%r 为空（多数播放器需要至少一条终止记录）' % sid)

    # ---- 数量关系
    tabs = {}
    for cid, body, off in chunks:
        if cid in REC_LEN:
            tabs[cid] = body
    if b'phdr' in tabs and b'pbag' in tabs:
        npres = len(tabs[b'phdr']) // 38 - 1
        bagi = [struct.unpack('<H', tabs[b'phdr'][i * 38 + 24:i * 38 + 26])[0]
                for i in range(len(tabs[b'phdr']) // 38)]
        zones = sum(bagi[i + 1] - bagi[i] for i in range(len(bagi) - 1))
        nbag = len(tabs[b'pbag']) // 4
        print('预设 %d，zone 合计 %d，pbag 记录 %d（期望 %d）' % (npres, zones, nbag, zones + 1))
        if nbag != zones + 1:
            errors.append('pbag 记录数应为 Σzone + 1 = %d，实际 %d' % (zones + 1, nbag))
    if b'shdr' in tabs:
        print('采样头 %d 个' % (len(tabs[b'shdr']) // 46 - 1))

    return report()


def report():
    print()
    if errors:
        print('❌ 发现 %d 个问题：' % len(errors))
        for e in errors:
            print('   -', e)
    else:
        print('✅ 结构检查通过')
    if warns:
        print('⚠️  %d 条提醒：' % len(warns))
        for w in warns:
            print('   -', w)
    return 1 if errors else 0


if __name__ == '__main__':
    if len(sys.argv) != 2:
        sys.exit('用法: python3 sf2check.py file.sf2')
    sys.exit(main(sys.argv[1]))
