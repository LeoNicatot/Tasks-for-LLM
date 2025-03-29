# Highlight-to-footnote

我现在需要实现一个markdown的python处理脚本，可以将高亮（即`==*==`）部分变成footnote，并且对footnote自动排序。例如，输入1-input.md，可以得到1-output.md。你可以复用之前实现过的md_footnote_sort.py脚本。

## Case 1

```
So, I need to build a Python script that processes markdown, converting highlighted text (==...==) into footnotes and sorting them. The input file has footnote markers like [^hey], [^*], etc., as well as highlighted sections. The expected output has changes like "in ==1921==" becoming "1921[^2]" and "==Psychological Types==" turning into "Psychological Types[^3]". Footnotes are auto-numbered when derived from highlights. The footnote definitions at the bottom also need to be reordered accordingly. I'll implement it with these rules in mind!
Let's break it down. In the input, footnotes are denoted by [^hey], [^*], [^4], and [^8]. The highlights ("==1921==" and "==Psychological Types==") need to be converted into footnotes. The highlight "==1921==" becomes [^2], and "==Psychological Types==" turns into [^3]. The footnotes' order gets adjusted, which shifts footnote 4 to 5 and footnote 8 to 6. But there’s a missing definition for [^8] in the input, which is puzzling because the output still gives it a definition ("sdf").
The input has footnotes like [^hey], [^*], [^4], and [^8], with some needing to be transformed. Highlights such as "==1921==" and "==Psychological Types==" should be converted into footnotes too. However, footnote [^8] didn’t have a definition, but it’s still numbered [^6]. It seems the algorithm should either skip undefined footnotes or generate defaults for them. Footnotes in text are renumbered, but the highlight changes result in additional footnotes only when they directly map to numbered footnotes. Code blocks should be ignored.
Okay, here's the plan: highlighted text ("==...==") should be replaced with footnotes, and the text remains, but a footnote marker is added directly after it. Definitions for new footnotes are created based on the highlighted text, with a colon added to the content. The footnotes are renumbered, ensuring the ones already in the text have their definitions included if they exist. We'll handle code blocks separately, skipping them during replacement. Regex will help detect inline code and replace footnote markers sequentially, taking special care to maintain the order for both existing and new footnotes.
```

```python
#!/usr/bin/env python3
import re
import sys

def process_markdown(text):
    # 提取并移除文末原有的脚注定义块（假设它们在末尾连续出现）
    original_defs = {}
    def_block_pattern = re.compile(r"(?m)(\n\s*\[\^[^\]]+\]:.*)+\s*$")
    def_block_match = def_block_pattern.search(text)
    if def_block_match:
        defs_text = def_block_match.group(0)
        text = text[:def_block_match.start()].rstrip()
        for line in defs_text.splitlines():
            m = re.match(r"\[\^([^\]]+)\]:\s*(.*)", line)
            if m:
                original_defs[m.group(1)] = m.group(2)

    # 保护fenced code block（例如 ```python ... ```）
    fenced_code_pattern = re.compile(r"(```[\s\S]+?```)")
    code_blocks = {}
    def replace_code_block(match):
        placeholder = f"__CODEBLOCK_{len(code_blocks)}__"
        code_blocks[placeholder] = match.group(1)
        return placeholder
    text = fenced_code_pattern.sub(replace_code_block, text)

    # 保护行内代码（以反引号包裹的部分）
    inline_code_pattern = re.compile(r"(`+)(.+?)(\1)")
    inline_codes = {}
    def replace_inline_code(match):
        placeholder = f"__INLINECODE_{len(inline_codes)}__"
        inline_codes[placeholder] = match.group(0)
        return placeholder
    text = inline_code_pattern.sub(replace_inline_code, text)

    # 使用正则一次处理两类目标：
    # 1. 已有的脚注标记 [^xxx]
    # 2. 高亮标记 ==...==
    # 注意：此处假设高亮内容中不包含连续“==”
    pattern = re.compile(r"(\[\^([^\]]+)\])|==(.+?)==")
    # footnote_map 保存源标记到新编号的映射，footnote_sources保存出现顺序及类型（"footnote"或"highlight"）
    footnote_map = {}
    footnote_sources = []  # 每项：(new_number, type, 原始内容)
    next_num = 1

    def replacer(match):
        nonlocal next_num
        if match.group(1):  # 匹配到已有的脚注 [^xxx]
            orig = match.group(2)
            key = f"FN:{orig}"
            if key not in footnote_map:
                footnote_map[key] = str(next_num)
                footnote_sources.append((next_num, "footnote", orig))
                next_num += 1
            return f"[^{footnote_map[key]}]"
        elif match.group(3):  # 匹配到高亮部分 ==text==
            highlight_text = match.group(3)
            key = f"HL:{highlight_text}"
            if key not in footnote_map:
                footnote_map[key] = str(next_num)
                footnote_sources.append((next_num, "highlight", highlight_text))
                next_num += 1
            # 替换：去掉高亮标记，保留文本，并追加脚注标记
            return f"{highlight_text}[^{footnote_map[key]}]"
        return match.group(0)

    new_text = pattern.sub(replacer, text)

    # 恢复行内代码
    for placeholder, code in inline_codes.items():
        new_text = new_text.replace(placeholder, code)
    # 恢复fenced code blocks
    for placeholder, code in code_blocks.items():
        new_text = new_text.replace(placeholder, code)

    # 构造新的脚注定义块：按新编号升序排列，
    # 对于已有的脚注，如果在原定义中有对应内容，则使用原内容；
    # 对于高亮生成的脚注，使用其原文本后追加冒号。
    defs_lines = []
    for num, typ, orig in sorted(footnote_sources, key=lambda x: x[0]):
        if typ == "footnote":
            if orig in original_defs:
                defs_lines.append(f"[^{num}]: {original_defs[orig]}")
        elif typ == "highlight":
            defs_lines.append(f"[^{num}]: {orig}:")
    if defs_lines:
        new_text += "\n\n" + "\n".join(defs_lines)
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

```

