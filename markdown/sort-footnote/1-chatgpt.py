#!/usr/bin/env python3
import re
import sys

def process_markdown(text):
    # 用于保存原始脚注标签到新编号的映射，和已分配的新编号
    footnote_map = {}
    next_num = 1

    # 先处理正文部分，把所有脚注引用替换为顺序编号
    # 使用回调函数来分配编号
    def replace_ref(match):
        nonlocal next_num
        orig = match.group(1)
        if orig not in footnote_map:
            footnote_map[orig] = str(next_num)
            next_num += 1
        return f"[^{footnote_map[orig]}]"

    # 替换正文中的脚注引用 [^xxx]
    new_text = re.sub(r"\[\^([^\]]+)\]", replace_ref, text)

    # 找出所有脚注定义行（注意：此处假设定义位于单独的行上）
    # 脚注定义格式: [^label]: content
    footnote_defs = re.findall(r"(?m)^\[\^([^\]]+)\]:\s*(.*)$", text)
    # 构造新的定义列表，按新编号排序，仅包含文本中有引用的脚注
    new_defs = []
    for orig, content in footnote_defs:
        if orig in footnote_map:
            new_label = footnote_map[orig]
            new_defs.append((int(new_label), new_label, content))
    # 按数字排序
    new_defs.sort(key=lambda x: x[0])

    # 构造新的脚注定义字符串，每行一个
    defs_text = "\n".join(f"[^{new_label}]: {content}" for _, new_label, content in new_defs)

    # 假设脚注定义需要放到文末，可以先去掉原有的定义，再追加新的定义
    # 这里简单地将最后连续的脚注定义块删除（如果存在）
    new_text = re.sub(r"(?m)(\n\s*\[\^[^\]]+\]:.*)+\s*$", "", new_text).rstrip()

    # 拼接正文和新的脚注定义（之间空一行）
    if defs_text:
        new_text += "\n\n" + defs_text

    return new_text

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python md_footnote_sort.py input.md output.md")
        sys.exit(1)
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    with open(input_file, "r", encoding="utf-8") as f:
        text = f.read()
    processed = process_markdown(text)
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(processed)
