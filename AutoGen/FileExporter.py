"""
文件导出工具 —— 将智能体协作生成的内容保存为实际文件。

生成的目录结构：
  result/YYYYMMDD_HHMM/
    ├── conversation.md          # 完整对话记录
    ├── code/                     # 提取的代码文件
    │   ├── app.py
    │   └── ...
    └── agents/                   # 各智能体的输出（Markdown）
        ├── 01_ProductManager.md
        ├── 02_Engineer.md
        ├── 03_CodeReviewer.md
        └── 04_UserProxy.md
"""

import os
import re
from datetime import datetime
from autogen_agentchat.messages import TextMessage


class FileExporter:
    """负责将智能体对话导出为文件"""

    def __init__(self, base_dir: str = "result"):
        # 创建时间戳子目录
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        self.session_dir = os.path.join(base_dir, self.timestamp)
        self.code_dir = os.path.join(self.session_dir, "code")
        self.agents_dir = os.path.join(self.session_dir, "agents")

        for d in [self.session_dir, self.code_dir, self.agents_dir]:
            os.makedirs(d, exist_ok=True)

        self.conversation_lines: list[str] = []
        self.agent_outputs: dict[str, list[str]] = {}  # agent_name → lines
        self.agent_counter: dict[str, int] = {}         # agent_name → 序号
        self.code_files: dict[str, int] = {}            # 文件名 → 版本号

    # ------------------------------------------------------------------
    # 写入一条消息
    # ------------------------------------------------------------------
    def write_message(self, message: TextMessage):
        """处理单条智能体消息"""
        source = getattr(message, "source", "unknown")
        content = getattr(message, "content", str(message))

        # 1) 记录到完整对话
        self.conversation_lines.append(f"## [{source}]\n\n{content}\n")

        # 2) 记录到该智能体的独立输出
        if source not in self.agent_outputs:
            self.agent_outputs[source] = []
        self.agent_outputs[source].append(content)

        # 3) 提取代码块 → 保存为 .py / .md 等文件
        self._extract_and_save_code(source, content)

    # ------------------------------------------------------------------
    # 提取代码块并写入文件
    # ------------------------------------------------------------------
    def _extract_and_save_code(self, source: str, text: str):
        """从文本中提取 ```语言 ... ``` 代码块，保存到 code/ 目录"""
        pattern = re.compile(r"```(\w+)?\s*\n(.*?)```", re.DOTALL)
        for lang, code in pattern.findall(text):
            lang = (lang or "txt").strip()
            ext_map = {
                "python": "py", "py": "py",
                "javascript": "js", "js": "js",
                "html": "html", "css": "css",
                "json": "json", "yaml": "yml", "yml": "yml",
                "markdown": "md", "md": "md",
                "bash": "sh", "sh": "sh", "shell": "sh",
            }
            ext = ext_map.get(lang, lang)

            base_name = f"{source}_{ext}"
            count = self.code_files.get(base_name, 0) + 1
            self.code_files[base_name] = count

            if count == 1:
                filename = f"{source}.{ext}"
            else:
                filename = f"{source}_{count}.{ext}"

            filepath = os.path.join(self.code_dir, filename)
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(code.strip() + "\n")

    # ------------------------------------------------------------------
    # 保存所有内容到磁盘
    # ------------------------------------------------------------------
    def save_all(self):
        """将所有缓存内容写入文件"""

        # 完整对话记录
        conv_path = os.path.join(self.session_dir, "conversation.md")
        with open(conv_path, "w", encoding="utf-8") as f:
            f.write(f"# 智能体协作记录\n\n> 生成时间：{self.timestamp}\n\n")
            f.write("\n---\n\n".join(self.conversation_lines))

        # 各智能体独立输出
        for idx, (agent, contents) in enumerate(self.agent_outputs.items(), 1):
            safe_name = agent.replace(" ", "_").replace("/", "_")
            agent_path = os.path.join(
                self.agents_dir, f"{idx:02d}_{safe_name}.md"
            )
            with open(agent_path, "w", encoding="utf-8") as f:
                f.write(f"# {agent} 的输出\n\n")
                for i, c in enumerate(contents, 1):
                    f.write(f"## 第 {i} 轮\n\n{c}\n\n---\n\n")

        return self.session_dir
