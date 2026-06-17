import asyncio

from typing import List, Dict

# å¯¼å¥ AgentScope 2.x æ ¸å¿ç»ä»¶

from agentscope.agent import Agent

from agentscope.model import ChatModelBase

from agentscope.message import UserMsg

from prompts import get_role_prompt

from models import DiscussionModelCN, VoteModelCN



class ThreeKingdomsWerewolfGame:

    def __init__(self, player_configs: List[Dict[str, str]], model: ChatModelBase):

        """
        初始化游戏状态，创建 Agent 实例，并注入角色提示词
        Args:
            player_configs: 玩家配置列表，示例:
                [{"name": "诸葛亮", "role": "预言家"}, ...]
            model: AgentScope 2.x 模型实例（如 DashScopeChatModel / OllamaChatModel）
        """
        self.round_num = 0
        self.is_game_over = False
        self.model = model  # 保存模型实例，供创建 Agent 时使用
        
        # 核心状态维护列表
        self.all_players: List[Agent] = []      # 存放所有已创建的 Agent 实例
        self.alive_players: List[Agent] = []    # 存放当前存活的 Agent 实例
        self.werewolves: List[Agent] = []       # 专门存放狼人 Agent，方便黑夜拉群

        # 游戏运行时状态
        self.night_kill_target: str | None = None        # 狼人今晚击杀目标
        self.night_poison_target: str | None = None      # 女巫今晚毒杀目标
        self.seer_check_results: Dict[str, str] = {}     # 预言家查验记录 {name: "狼人"|"好人"}
        self.witch_antidote_used: bool = False           # 女巫解药是否已用
        self.witch_poison_used: bool = False             # 女巫毒药是否已用
        
        # 模拟法官/主持人，是一个特殊的裁判 Agent，负责发号施令和宣读结果
        self.moderator = Agent(
            name="法官",
            system_prompt="你是三国狼人杀的绝对中立裁判。你负责主持流程、宣读死讯和公告，不偏袒任何阵营。",
            model=model,
        )
        
        # 初始化玩家和阵营
        # 传入玩家配置列表，创建 Agent 实例，并注入角色提示词
        self._setup_game(player_configs)

    def _setup_game(self, configs: List[Dict[str, str]]):
        """内部方法：根据配置初始化 Agent，分配身份并注入 Prompt"""
        print("[系统初始化] 正在注入武将灵魂与狼人杀规则...")

        # 遍历 configs，调用 get_role_prompt 组装系统提示词
        for config in configs:
            name = config["name"]
            role = config["role"]

            # 1. 动态生成这个Agent专属的双重身份的提示词
            sys_prompt = get_role_prompt(role, name)
            
            # 2. 实例化 AgentScope 2.x 的标准智能体 Agent，注入系统提示词和模型实例
            agent = Agent(
                name=name,
                system_prompt=sys_prompt,
                model=self.model,
            )
            
            # 3. 动态给 Agent 实例挂载自定义属性，方便控制层后续判断
            agent.role = role  # 直接挂载角色属性，方便后续逻辑判断
            agent.is_alive = True  # 直接挂载存活状态属性，方便后续逻辑判断

            # 4. 分类存储 Agent 实例，狼人单独一类，方便黑夜拉群；所有玩家都放入总列表和存活列表
            self.all_players.append(agent)
            self.alive_players.append(agent)
            
            if role == "狼人":
                self.werewolves.append(agent)

            print(f"-> 成功创建玩家：【{name}】，赋予武将人格，阵营职位：[{role}]")

        print(f"[初始化成功] 当前存活玩家总数: {len(self.alive_players)}，狼人总数: {len(self.werewolves)}")

    async def start_game(self):
        """游戏主循环引擎"""
        print("\n=== 三国狼人杀 游戏正式开始 ===")
        
        while not self.is_game_over:
            self.round_num += 1
            print(f"\n================ 第 {self.round_num} 天 ================")
            
            # 1. 黑夜降临
            await self.night_phase()
            
            # 2. 检查黑夜过后是否有人死亡，并判断胜负
            self.check_victory_conditions()
            if self.is_game_over:
                break
                
            # 3. 白天讨论与放逐投票
            await self.day_phase()
            
            # 4. 检查投票过后是否有人出局，并再次判断胜负
            self.check_victory_conditions()

    async def night_phase(self):
        """黑夜阶段控制流"""
        print("\n【天黑请闭眼...】")
        
        # Step 2.1: 狼人睁眼，秘密商量并投票
        print("\n-> 1. 狼人正在秘密潜入频道商议...")
        await self._werewolf_night_action()
        
        # Step 2.2: 预言家睁眼验人
        print("\n-> 2. 预言家正在夜观星象查验身份...")
        await self._seer_night_action()
        
        # Step 2.3: 女巫睁眼用药
        print("\n-> 3. 女巫正在密室调配生死毒药...")
        await self._witch_night_action()

    async def day_phase(self):
        """白天阶段控制流"""
        print("\n【天亮请睁眼！】")

        # ============================================================
        # 结算昨夜死亡：狼人击杀 + 女巫毒杀
        # ============================================================
        deaths = []
        if self.night_kill_target:
            deaths.append((self.night_kill_target, "被狼人杀害"))
        if self.night_poison_target:
            deaths.append((self.night_poison_target, "中毒身亡"))

        # 更新存活状态
        for name, cause in deaths:
            agent = next((a for a in self.alive_players if a.name == name), None)
            if agent:
                agent.is_alive = False
                self.alive_players.remove(agent)
                if agent in self.werewolves:
                    self.werewolves.remove(agent)

        # 法官公布死讯
        if deaths:
            death_str = "、".join(f"【{n}】({c})" for n, c in deaths)
            print(f"  法官宣布: 昨夜{death_str}")
            # 向所有存活玩家广播死讯
            for player in self.alive_players:
                await player.observe(UserMsg(
                    "法官",
                    f"天亮了！昨夜{death_str}。"
                    f"当前存活玩家：{'、'.join(a.name for a in self.alive_players)}"
                ))
        else:
            print("  法官宣布: 昨夜是平安夜，无人死亡。")
            for player in self.alive_players:
                await player.observe(UserMsg(
                    "法官",
                    "天亮了！昨夜是平安夜，无人死亡。"
                ))

        # 重置黑夜状态
        self.night_kill_target = None
        self.night_poison_target = None

        # Step 3.1: 幸存者自由辩论
        print("\n-> 4. 幸存武将开始公开辩论...")
        await self._public_discussion()

        # Step 3.2: 全员同时公投驱逐
        print("\n-> 5. 诸位武将开始投票放逐可疑人员...")
        await self._public_vote()

    # ================= 核心原子行动接口 =================

    async def _werewolf_night_action(self):
        """
        [AgentScope 2.x] 狼人黑夜密谋与投票核心逻辑
        
        流程：
        1. 告知每只狼队友身份和可击杀目标
        2. 各狼发表刺杀建议
        3. 互传建议（模拟秘密频道）
        4. 看到队友意见后最终投票
        5. 统计票数决定击杀目标
        
        Returns:
            str | None: 最终决定击杀的玩家姓名，无人可杀时返回 None
        """
        print(f"  [黑夜流转] 正在调用：狼人密谋。当前有 {len(self.werewolves)} 只狼可行动。")

        if not self.werewolves:
            print("  [狼人] 没有存活的狼人，跳过黑夜行动。")
            self.night_kill_target = None
            return None

        # === 准备数据 ===
        alive_names = [a.name for a in self.alive_players]
        wolf_names = [w.name for w in self.werewolves]

        # 策略规则：
        # - 只要场上还有非狼人存活，狼人可以杀任何人（包括队友），
        #   通过"卖队友""自刀"等策略混淆好人视听
        # - 只有当全场只剩狼人阵营时（狼人已获胜），才禁止行动
        non_wolf_alive = [n for n in alive_names if n not in wolf_names]

        if not non_wolf_alive:
            print("  [狼人] 场上仅剩狼人阵营，狼人已获胜，跳过黑夜行动。")
            self.night_kill_target = None
            return None

        # 所有存活玩家均可作为目标（包括狼人队友）
        targets = alive_names

        targets_str = "、".join(targets)
        wolf_str = "、".join(wolf_names)

        # ============================================================
        # Phase 1: 向每只狼通报局面（使用 observe 喂入上下文）
        # ============================================================
        print(f"  [黑夜行动] 正在拉取狼人加密频道...")
        for wolf in self.werewolves:
            await wolf.observe(UserMsg(
                "系统",
                f"【黑夜密谋频道·第{self.round_num}夜】\n"
                f"你的狼人队友：{wolf_str}\n"
                f"当前所有存活玩家：{targets_str}\n"
                f"战术提示：你可以击杀任何存活玩家，包括狼人队友——\n"
                f"\"卖队友\"或\"自刀\"可以混淆好人视线、骗取解药、建立信任。\n"
                f"但注意：如果只剩狼人阵营存活，则无需行动。\n"
                f"请与队友商议，达成一致后决定今晚的刺杀目标。"
            ))

        # ============================================================
        # Phase 2: 第一轮讨论 —— 各狼发表建议（并发）
        # ============================================================
        print(f"  [狼人-讨论] 各狼正在发表刺杀建议...")
        discuss_tasks = [
            wolf.reply(UserMsg(
                "系统",
                f"请发表你的刺杀建议：今晚杀谁？理由是什么？"
                f"（可击杀名单：{targets_str}）"
            ))
            for wolf in self.werewolves
        ]
        round1_replies = await asyncio.gather(*discuss_tasks)

        # 打印第一轮发言
        for i, reply in enumerate(round1_replies):
            name = self.werewolves[i].name
            text = reply.get_text_content()
            print(f"    [{name}] 发言:\n{text[:500]}")

        # ============================================================
        # Phase 3: 互传消息 —— 每只狼看到其他队友的发言
        # ============================================================
        for i, wolf in enumerate(self.werewolves):
            for j, reply in enumerate(round1_replies):
                if i != j:
                    speaker = self.werewolves[j].name
                    text = reply.get_text_content()
                    await wolf.observe(UserMsg(speaker, f"[秘密频道] {text}"))

        # ============================================================
        # Phase 4: 最终投票 —— 看到队友意见后表态（并发）
        # ============================================================
        print(f"  [狼人-投票] 狼人看到队友意见，正在最终投票...")
        vote_tasks = [
            wolf.reply(UserMsg(
                "系统",
                f"你已看到队友的发言。现在是最终决定时刻——"
                f"请明确说出你今晚要击杀的【一个】玩家姓名。"
                f"只需说出名字即可。"
            ))
            for wolf in self.werewolves
        ]
        round2_replies = await asyncio.gather(*vote_tasks)

        # ============================================================
        # Phase 5: 统计票数，决定猎物
        # ============================================================
        vote_count: Dict[str, int] = {}
        vote_details = []
        for i, reply in enumerate(round2_replies):
            name = self.werewolves[i].name
            text = reply.get_text_content()
            # 在回复文本中匹配目标姓名（取最后出现的，最靠近决策）
            voted = None
            last_pos = -1
            for target in targets:
                pos = text.rfind(target)
                if pos > last_pos:
                    last_pos = pos
                    voted = target
            if voted:
                vote_count[voted] = vote_count.get(voted, 0) + 1
                vote_details.append(f"{name} -> {voted}")
                print(f"    [{name}] 投票: {voted}")
            else:
                vote_details.append(f"{name} -> (未识别)")
                print(f"    [{name}] 投票未识别:\n{text[:500]}")

        # 确定最高票目标
        if vote_count:
            victim = max(vote_count, key=vote_count.get)
            print(f"\n  [狼人决议] 今晚击杀目标：【{victim}】"
                  f"（投票详情: {'; '.join(vote_details)}）")
            self.night_kill_target = victim
            return victim
        else:
            print(f"\n  [狼人决议] 未能达成一致，今晚平安夜。")
            self.night_kill_target = None
            return None

    async def _seer_night_action(self):
        """
        [AgentScope 2.x] 预言家黑夜验人逻辑
        
        流程：
        1. 找到存活预言家
        2. 提供可选查验名单（已查过的标出上次结果，避免重复验人）
        3. 预言家选择一名玩家查验
        4. 告知查验结果（"狼人" 或 "好人"）
        5. 记录结果供白天使用
        """
        print("  [黑夜流转] 正在调用：预言家验人。")

        # 找到存活的预言家
        seer = next((a for a in self.alive_players if a.role == "预言家"), None)
        if not seer:
            print("  [预言家] 预言家已死亡，跳过验人。")
            return

        # 可选查验名单：所有存活玩家（排除自己）
        alive_names = [a.name for a in self.alive_players if a.name != seer.name]
        if not alive_names:
            print("  [预言家] 没有可查验的目标，跳过。")
            return

        # 构建已查验/未查验名单（分开显示，引导不重复查验）
        unchecked = []
        checked = []
        for name in alive_names:
            if name in self.seer_check_results:
                prev = self.seer_check_results[name]
                checked.append(f"{name}（{prev}）")
            else:
                unchecked.append(name)
        unchecked_str = "、".join(unchecked) if unchecked else "（无）"
        checked_str = "、".join(checked) if checked else "（无）"

        # ============================================================
        # Phase 1: 告知预言家夜晚信息
        # ============================================================
        await seer.observe(UserMsg(
            "系统",
            f"【预言家夜观星象·第{self.round_num}夜】\n"
            f"你可以查验一名存活玩家的真实阵营身份。\n"
            f"未查验目标：{unchecked_str}\n"
            f"已查验目标：{checked_str}\n"
            f"重要：已查验过的玩家身份已知，重复查验纯属浪费机会！"
            f"请选择一名【未查验过】的玩家。"
        ))

        # ============================================================
        # Phase 2: 预言家选择目标
        # ============================================================
        reply = await seer.reply(UserMsg(
            "系统",
            f"请说出你要查验的【一个】玩家姓名。"
        ))
        text = reply.get_text_content()
        print(f"  [预言家] {seer.name} 查验回复:\n{text[:500]}")

        # 匹配目标姓名（取文本中最后出现的，最靠近决策句）
        target_name = None
        last_pos = -1
        for name in alive_names:
            pos = text.rfind(name)
            if pos > last_pos:
                last_pos = pos
                target_name = name

        if not target_name:
            print(f"  [预言家] 未能识别查验目标，默认查验第一位: {alive_names[0]}")
            target_name = alive_names[0]

        # ============================================================
        # Phase 3: 查询真实身份并告知结果
        # ============================================================
        target_agent = next(a for a in self.all_players if a.name == target_name)
        is_wolf = target_agent.role == "狼人"
        result = "狼人" if is_wolf else "好人"

        # 记录查验结果
        self.seer_check_results[target_name] = result

        await seer.observe(UserMsg(
            "系统",
            f"星象已显——【{target_name}】的真实阵营是：【{result}】！"
            f"请牢记此信息，在白天辩论中谨慎使用。"
        ))

        print(f"  [预言家] {seer.name} 查验了【{target_name}】，结果为【{result}】")

    async def _witch_night_action(self):
        """
        [AgentScope 2.x] 女巫夜间用药逻辑

        流程：
        1. 找到存活女巫
        2. 告知今夜死讯（狼人击杀目标）
        3. 展示药水状态（解药/毒药各一次）
        4. 女巫决定：救人或毒人或都不做
        5. 执行决策

        规则：
        - 解药和毒药各只能用一次
        - 同一晚不能同时使用解药和毒药
        """
        print("  [黑夜流转] 正在调用：女巫用药。")

        # 找到存活的女巫
        witch = next((a for a in self.alive_players if a.role == "女巫"), None)
        if not witch:
            print("  [女巫] 女巫已死亡，跳过用药。")
            self.night_poison_target = None
            return

        # 检查是否还有可用药水
        has_antidote = not self.witch_antidote_used
        has_poison = not self.witch_poison_used

        if not has_antidote and not has_poison:
            print("  [女巫] 解药与毒药均已用完，跳过。")
            self.night_poison_target = None
            return

        # ============================================================
        # Phase 1: 告知女巫今夜局势
        # ============================================================
        killed = self.night_kill_target
        dead_msg = f"今夜【{killed}】被狼人杀害！" if killed else "今夜无人死亡（平安夜）。"

        # 药水状态
        potion_parts = []
        if has_antidote:
            potion_parts.append("解药（可救活被杀者）可用")
        else:
            potion_parts.append("解药 已用")
        if has_poison:
            alive_names = [a.name for a in self.alive_players if a.name != witch.name]
            poison_targets = "、".join(alive_names) if alive_names else "无"
            potion_parts.append(f"毒药（可毒杀一人）可用 可选目标：{poison_targets}")
        else:
            potion_parts.append("毒药 已用")

        await witch.observe(UserMsg(
            "系统",
            f"【女巫密室·第{self.round_num}夜】\n"
            f"{dead_msg}\n"
            f"你的药水状态：\n"
            f"  * {potion_parts[0]}\n"
            f"  * {potion_parts[1]}\n"
            f"规则提醒：同一晚不能同时使用解药和毒药。"
        ))

        # ============================================================
        # Phase 2: 女巫决策
        # ============================================================
        # 构建决策选项
        decisions = []
        if has_antidote and killed:
            decisions.append(f"【救】使用解药救活{killed}")
        if has_poison:
            decisions.append("【毒】使用毒药毒杀一名玩家（请指明姓名）")
        decisions.append("【不】不使用任何药水")

        prompt = (
            f"请做出你的决定（只能选一项）：\n"
            + "\n".join(f"  {d}" for d in decisions)
            + f"\n请明确说出你的选择。"
        )

        reply = await witch.reply(UserMsg("系统", prompt))
        text = reply.get_text_content()
        print(f"  [女巫] {witch.name} 决策:\n{text[:500]}")

        # ============================================================
        # Phase 3: 解析并执行决策
        # ============================================================
        chose_antidote = "救" in text and has_antidote and killed
        chose_poison = "毒" in text and has_poison

        # 同一晚不能双开
        if chose_antidote and chose_poison:
            # 看哪个意图更明确
            if text.find("救") < text.find("毒"):
                chose_poison = False
            else:
                chose_antidote = False

        if chose_antidote:
            # 使用解药救活被杀者
            self.witch_antidote_used = True
            self.night_kill_target = None  # 取消狼人击杀
            self.night_poison_target = None
            await witch.observe(UserMsg(
                "系统",
                f"你使用了【解药】，【{killed}】被救活了！"
                f"解药已耗尽，今后不能再救人。"
            ))
            print(f"  [女巫] {witch.name} 使用解药救活了【{killed}】")

        elif chose_poison:
            # 使用毒药毒杀一名玩家
            alive_names = [a.name for a in self.alive_players if a.name != witch.name]
            # 匹配目标姓名（取最后出现的）
            target_name = None
            last_pos = -1
            for name in alive_names:
                pos = text.rfind(name)
                if pos > last_pos:
                    last_pos = pos
                    target_name = name

            if target_name:
                self.witch_poison_used = True
                self.night_poison_target = target_name
                await witch.observe(UserMsg(
                    "系统",
                    f"你使用了【毒药】，【{target_name}】将在天亮前毒发身亡！"
                    f"毒药已耗尽，今后不能再毒人。"
                ))
                print(f"  [女巫] {witch.name} 使用毒药毒杀了【{target_name}】")
            else:
                print(f"  [女巫] 选择用毒但未识别目标，默认不操作。")
                self.night_poison_target = None
                await witch.observe(UserMsg(
                    "系统",
                    "未能识别你的毒杀目标，今晚不做任何操作。"
                ))
        else:
            print(f"  [女巫] {witch.name} 选择不使用药水。")
            self.night_poison_target = None
            await witch.observe(UserMsg(
                "系统",
                "你选择不使用任何药水。静待天明。"
            ))

    async def _public_discussion(self):
        """
        [AgentScope 2.x] 白天全员公开辩论

        流程：
        1. 第一轮：各玩家发表开场陈述（并发）
        2. 互传发言（模拟公聊频道，每人看到其他人的发言）
        3. 第二轮：回应与反驳（并发）
        4. 互传第二轮发言
        """
        alive_count = len(self.alive_players)
        print(f"  [白天流转] 正在调用：公开辩论。当前存活人数: {alive_count}")

        if alive_count <= 1:
            print("  [辩论] 存活人数不足，跳过辩论。")
            return

        alive_names_str = "、".join(a.name for a in self.alive_players)

        # ============================================================
        # Round 1: 开场陈述
        # ============================================================
        print(f"  [辩论·第一轮] 各武将正在发表开场陈述...")
        round1_tasks = [
            player.reply(UserMsg(
                "法官",
                f"公开辩论开始。当前在场武将：{alive_names_str}。"
                f"请发表你的开场陈述：你认为谁可能是狼人？为什么？"
            ))
            for player in self.alive_players
        ]
        round1_replies = await asyncio.gather(*round1_tasks)

        for i, reply in enumerate(round1_replies):
            name = self.alive_players[i].name
            text = reply.get_text_content()
            print(f"    [{name}] 陈述:\n{text[:500]}")

        # ============================================================
        # 互传第一轮发言（每人看到其他所有人的发言）
        # ============================================================
        for i, player in enumerate(self.alive_players):
            for j, reply in enumerate(round1_replies):
                if i != j:
                    speaker = self.alive_players[j].name
                    text = reply.get_text_content()
                    await player.observe(UserMsg(speaker, f"[公开陈述] {text}"))

        # ============================================================
        # Round 2: 回应与反驳
        # ============================================================
        print(f"  [辩论·第二轮] 武将们正在回应与反驳...")
        round2_tasks = [
            player.reply(UserMsg(
                "法官",
                f"你已听到所有人的陈述。请做出回应："
                f"你怀疑谁？相信谁？是否有新的推理？"
            ))
            for player in self.alive_players
        ]
        round2_replies = await asyncio.gather(*round2_tasks)

        for i, reply in enumerate(round2_replies):
            name = self.alive_players[i].name
            text = reply.get_text_content()
            print(f"    [{name}] 反驳:\n{text[:500]}")

        # ============================================================
        # 互传第二轮发言
        # ============================================================
        for i, player in enumerate(self.alive_players):
            for j, reply in enumerate(round2_replies):
                if i != j:
                    speaker = self.alive_players[j].name
                    text = reply.get_text_content()
                    await player.observe(UserMsg(speaker, f"[公开回应] {text}"))

        # ============================================================
        # 辩论总结：法官提示即将投票
        # ============================================================
        print(f"  [辩论] 公开辩论结束，即将进入放逐投票阶段。")
        for player in self.alive_players:
            await player.observe(UserMsg(
                "法官",
                f"辩论结束。接下来请投票放逐你认为最可疑的玩家。"
                f"在场武将：{alive_names_str}"
            ))

    async def _public_vote(self):
        """
        [AgentScope 2.x] 白天公开放逐投票

        流程：
        1. 所有存活玩家并发投票选出要放逐的人
        2. 统计票数
        3. 票数最高者被放逐（平票则无人放逐）
        4. 更新存活状态并公告结果
        """
        print("  [白天流转] 正在调用：全员放逐投票。")

        alive_count = len(self.alive_players)
        if alive_count <= 1:
            print("  [投票] 存活人数不足，跳过投票。")
            return

        alive_names = [a.name for a in self.alive_players]
        alive_names_str = "、".join(alive_names)

        # ============================================================
        # Phase 1: 全员并发投票
        # ============================================================
        print(f"  [投票] 各武将正在投票...")
        vote_tasks = [
            player.reply(UserMsg(
                "法官",
                f"现在是放逐投票时间。请说出你要放逐的【一个】玩家姓名。"
                f"在场武将：{alive_names_str}"
            ))
            for player in self.alive_players
        ]
        vote_replies = await asyncio.gather(*vote_tasks)

        # ============================================================
        # Phase 2: 统计票数
        # ============================================================
        vote_count: Dict[str, int] = {}
        vote_details = []
        for i, reply in enumerate(vote_replies):
            voter = self.alive_players[i].name
            text = reply.get_text_content()
            # 匹配目标姓名（取最后出现的，最靠近决策）
            voted = None
            last_pos = -1
            for name in alive_names:
                if name != voter:
                    pos = text.rfind(name)
                    if pos > last_pos:
                        last_pos = pos
                        voted = name
            if voted:
                vote_count[voted] = vote_count.get(voted, 0) + 1
                vote_details.append(f"{voter} -> {voted}")
                print(f"    [{voter}] 投票放逐: {voted}")
            else:
                vote_details.append(f"{voter} -> (弃权/未识别)")
                print(f"    [{voter}] 投票未识别:\n{text[:500]}")

        # ============================================================
        # Phase 3: 确定放逐结果
        # ============================================================
        if not vote_count:
            print(f"\n  [投票结果] 无人获得有效票数，今日平安。")
            for player in self.alive_players:
                await player.observe(UserMsg(
                    "法官",
                    "投票结束，无人获得有效票数，今日无人被放逐。"
                ))
            return

        # 找最高票
        max_votes = max(vote_count.values())
        top_candidates = [name for name, cnt in vote_count.items() if cnt == max_votes]

        if len(top_candidates) > 1:
            # 平票，无人被放逐
            print(f"\n  [投票结果] 平票！{' 与 '.join(top_candidates)} 各获 {max_votes} 票，"
                  f"今日无人被放逐。")
            for player in self.alive_players:
                await player.observe(UserMsg(
                    "法官",
                    f"投票结束——{' 与 '.join(top_candidates)} 平票（各{max_votes}票），"
                    f"今日无人被放逐。（投票详情: {'; '.join(vote_details)}）"
                ))
            return

        # 一人最高票 -> 放逐
        exiled_name = top_candidates[0]
        exiled_agent = next(a for a in self.alive_players if a.name == exiled_name)
        exiled_role = exiled_agent.role

        # 执行放逐
        exiled_agent.is_alive = False
        self.alive_players.remove(exiled_agent)
        if exiled_agent in self.werewolves:
            self.werewolves.remove(exiled_agent)

        print(f"\n  [投票结果] 【{exiled_name}】以 {max_votes} 票被放逐！"
              f"（投票详情: {'; '.join(vote_details)}）")

        # 向所有存活玩家公告结果
        for player in self.alive_players:
            await player.observe(UserMsg(
                "法官",
                f"投票结束——【{exiled_name}】以 {max_votes} 票被放逐！"
                f"（投票详情: {'; '.join(vote_details)}）"
            ))
        # 被放逐者也收到通知
        await exiled_agent.observe(UserMsg(
            "法官",
            f"你已被放逐！你的身份是【{exiled_role}】。"
            f"（投票详情: {'; '.join(vote_details)}）"
        ))

    def check_victory_conditions(self):
        """胜负裁决器"""
        # 统计阵营存活人数
        alive_wolves = sum(1 for a in self.alive_players if a.role == "狼人")
        alive_good = len(self.alive_players) - alive_wolves

        if alive_wolves == 0:
            print("\n  【好人阵营胜利】所有狼人已被消灭！")
            self.is_game_over = True
        elif alive_wolves >= alive_good:
            print("\n  【狼人阵营胜利】狼人数量已大于等于好人，狼人屠城！")
            self.is_game_over = True
