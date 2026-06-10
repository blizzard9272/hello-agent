"""
文件导出工具 —— 将智能体协作生成的内容保存为实际文件。

生成的目录结构：
  result/YYYYMMDD_HHMM/
    ├── conversation.md          # 完整对话记录
    ├── code/                     # 提取的代码文件（仅 Engineer 产出）
    │   └── bitcoin_app.py
    └── agents/                   # 各智能体的独立输出
        ├── 01_ProductManager.md
        ├── 02_Engineer.md
        ├── 03_CodeReviewer.md
        └── 04_UserProxy.md
"""

import os
import re
from datetime import datetime


# 只有这些智能体的代码块才会被提取为独立文件
CODE_PRODUCERS = {"Engineer"}

# 需要跳过的消息来源（系统内部消息）
SKIP_SOURCES = {"unknown", "user"}


class FileExporter:
    """负责将智能体对话导出为文件"""

    def __init__(self, base_dir: str = "result"):
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        self.session_dir = os.path.join(base_dir, self.timestamp)
        self.code_dir = os.path.join(self.session_dir, "code")
        self.agents_dir = os.path.join(self.session_dir, "agents")

        for d in [self.session_dir, self.code_dir, self.agents_dir]:
            os.makedirs(d, exist_ok=True)

        self.conversation_lines: list[str] = []
        self.agent_outputs: dict[str, list[str]] = {}  # agent_name → [content, ...]
        self.code_files: dict[str, int] = {}            # filename → version

    # ------------------------------------------------------------------
    # 写入一条消息
    # ------------------------------------------------------------------
    def write_message(self, message) -> bool:
        """处理单条智能体消息。返回 True 表示成功写入，False 表示已跳过。"""
        source = str(getattr(message, "source", ""))
        content = getattr(message, "content", "")

        # 跳过系统内部消息 & 无源消息
        if not source or source in SKIP_SOURCES:
            return False
        if not content or not isinstance(content, str):
            return False

        # 1) 完整对话记录
        self.conversation_lines.append(f"## [{source}]\n\n{content}\n")

        # 2) 该智能体的独立输出
        if source not in self.agent_outputs:
            self.agent_outputs[source] = []
        self.agent_outputs[source].append(content)

        # 3) 仅对 Engineer 提取代码块
        if source in CODE_PRODUCERS:
            self._extract_and_save_code(source, content)

        return True

    # ------------------------------------------------------------------
    # 提取代码块并写入文件
    # ------------------------------------------------------------------
    def _extract_and_save_code(self, source: str, text: str):
        """从文本中提取 ```语言 ... ``` 代码块，按 # file: 标注命名，保存到 code/ 目录"""
        pattern = re.compile(r"```(\w+)\s*\n(.*?)```", re.DOTALL)
        for lang, code in pattern.findall(text):
            lang = lang.strip().lower()
            ext_map = {
                "python": "py", "py": "py",
                "javascript": "js", "js": "js",
                "html": "html", "css": "css",
                "json": "json", "yaml": "yml", "yml": "yml",
                "markdown": "md", "md": "md",
                "bash": "sh", "sh": "sh", "shell": "sh",
            }
            ext = ext_map.get(lang, lang)

            # 尝试从代码第一行提取文件名标注：# file: xxx.ext
            filename = None
            first_line = code.strip().split("\n")[0].strip()
            file_match = re.match(r"#\s*file\s*:\s*(.+\.\w+)", first_line)
            if file_match:
                filename = file_match.group(1).strip()
                # 去掉 # file: 这行，保留纯代码
                code = code.strip().split("\n", 1)[1].strip() if "\n" in code else code

            # 如果没标注，尝试从代码块前的文本中提取反引号包裹的文件名
            if not filename:
                # 在当前 text 中找代码块前面最近的 `xxx.py` 样式
                code_start = text.find(f"```{lang}")
                if code_start > 0:
                    before = text[:code_start]
                    name_match = re.findall(r"`([^`]+\.\w{1,6})`", before)
                    if name_match:
                        filename = name_match[-1]  # 取最后一个

            # 回退：用 Engineer.xxx
            if not filename:
                filename = f"{source}.{ext}"

            # 去重：同名文件加版本号
            base = filename
            count = self.code_files.get(base, 0) + 1
            self.code_files[base] = count

            if count == 1:
                final_name = filename
            else:
                name_part, dot_ext = os.path.splitext(filename)
                final_name = f"{name_part}_{count}{dot_ext}"

            filepath = os.path.join(self.code_dir, final_name)
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(code.strip() + "\n")

    # ------------------------------------------------------------------
    # 保存所有内容到磁盘（按固定顺序输出 agent 文件）
    # ------------------------------------------------------------------
    def save_all(self) -> str:
        """将所有缓存内容写入文件，返回会话目录路径"""

        # 完整对话记录
        conv_path = os.path.join(self.session_dir, "conversation.md")
        with open(conv_path, "w", encoding="utf-8") as f:
            f.write(f"# 智能体协作记录\n\n> 生成时间：{self.timestamp}\n\n")
            f.write("\n---\n\n".join(self.conversation_lines))

        # 各智能体独立输出（按固定顺序）
        ordered = ["user", "ProductManager", "Engineer", "CodeReviewer", "UserProxy"]
        idx = 1
        for name in ordered:
            if name in self.agent_outputs:
                safe_name = name.replace(" ", "_")
                agent_path = os.path.join(self.agents_dir, f"{idx:02d}_{safe_name}.md")
                idx += 1
                contents = self.agent_outputs[name]
                with open(agent_path, "w", encoding="utf-8") as f:
                    f.write(f"# {name} 的输出\n\n")
                    for i, c in enumerate(contents, 1):
                        f.write(f"## 第 {i} 轮\n\n{c}\n\n---\n\n")

        # 其他未排序的 agent（防止遗漏）
        for name, contents in self.agent_outputs.items():
            if name in ordered:
                continue
            safe_name = name.replace(" ", "_")
            agent_path = os.path.join(self.agents_dir, f"{idx:02d}_{safe_name}.md")
            idx += 1
            with open(agent_path, "w", encoding="utf-8") as f:
                f.write(f"# {name} 的输出\n\n")
                for i, c in enumerate(contents, 1):
                    f.write(f"## 第 {i} 轮\n\n{c}\n\n---\n\n")

        return self.session_dir
