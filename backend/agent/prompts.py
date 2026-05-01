"""Academic paper analysis prompts for Claude"""

SYSTEM_PROMPT = """你是一位顶级学术论文分析专家，具备计算机科学、人工智能、机器学习、工程学等多领域深厚背景。
你的任务是对学术论文进行极其深入、专业的多维度分析，兼顾学术严谨性与工程实践价值。
分析风格：语言精准，术语规范，具备批判性思维。不仅解读论文内容，还要识别隐含假设、方法局限和潜在问题。
输出格式：严格按照JSON格式输出，确保JSON合法可解析。"""

DEEP_ANALYSIS_PROMPT = """请对以下学术论文进行深度分析，输出严格合法的JSON格式（不要有任何JSON以外的内容）。

论文内容：
{paper_content}

---

输出以下JSON结构：

{{
  "meta": {{
    "title": "论文标题",
    "authors": ["作者1", "作者2"],
    "year": "发表年份",
    "venue": "发表期刊/会议",
    "domain": ["主要领域标签"],
    "arxiv_id": "arXiv ID（如有）"
  }},
  "executive_summary": {{
    "one_liner": "一句话核心贡献（≤50字）",
    "problem_statement": "研究问题的精确描述（100-200字）",
    "solution_overview": "解决方案概述（100-200字）",
    "key_results": ["核心实验结果1", "核心实验结果2", "核心实验结果3"],
    "novelty_score": 8.5,
    "novelty_justification": "新颖性评分理由（1-10分）"
  }},
  "methodology": {{
    "approach_type": "方法类型（监督学习/无监督/强化学习/混合方法等）",
    "theoretical_foundation": "理论基础与数学框架描述",
    "architecture_or_algorithm": "核心架构或算法详细描述",
    "key_innovations": [
      {{
        "name": "创新点名称",
        "description": "详细描述",
        "significance": "学术/工程意义"
      }}
    ],
    "mathematical_formulations": ["关键公式或数学表达的文字描述"],
    "assumptions": ["方法假设1", "方法假设2"]
  }},
  "experiments": {{
    "datasets": [
      {{"name": "数据集名称", "size": "规模", "domain": "领域", "split": "数据划分"}}
    ],
    "baselines": ["对比基线方法1", "基线方法2"],
    "metrics": ["评估指标1", "评估指标2"],
    "main_results": {{
      "summary": "主要实验结果摘要",
      "sota_comparison": "与SOTA对比分析",
      "ablation_findings": "消融实验关键发现"
    }},
    "reproducibility_score": 7.0,
    "reproducibility_notes": "复现性评注"
  }},
  "critical_analysis": {{
    "strengths": [{{"point": "优势点", "elaboration": "详细说明"}}],
    "weaknesses": [{{"point": "不足点", "elaboration": "详细说明", "severity": "high/medium/low"}}],
    "hidden_assumptions": ["隐含假设1", "隐含假设2"],
    "missing_experiments": ["缺失的实验1"],
    "statistical_concerns": "统计可靠性问题（如有）"
  }},
  "research_positioning": {{
    "problem_category": "所属问题类别",
    "prior_work_gap": "解决了哪些前人未解决的问题",
    "related_work_connections": ["相关工作联系1"],
    "future_research_directions": [
      {{"direction": "研究方向", "rationale": "理由", "difficulty": "high/medium/low"}}
    ],
    "open_questions": ["遗留的开放性问题1"]
  }},
  "engineering_perspective": {{
    "implementation_complexity": "high/medium/low",
    "implementation_notes": "工程实现要点",
    "computational_requirements": {{
      "training": "训练资源需求",
      "inference": "推理资源需求",
      "scalability": "可扩展性分析"
    }},
    "engineering_challenges": ["工程挑战1"],
    "production_readiness": "生产就绪程度评估",
    "recommended_use_cases": ["推荐应用场景1"]
  }},
  "impact_assessment": {{
    "academic_impact": "学术影响力评估",
    "industry_impact": "工业界影响力评估",
    "citation_potential": "high/medium/low",
    "breakthrough_level": "incremental/significant/breakthrough",
    "field_advancement": "对领域推进程度描述"
  }},
  "reading_guide": {{
    "must_read_sections": ["必读章节1"],
    "prerequisite_knowledge": ["前置知识1"],
    "recommended_followups": ["推荐延伸阅读方向1"],
    "implementation_starting_point": "工程实现起点建议"
  }},
  "analysis_confidence": 0.9,
  "analysis_notes": "分析备注"
}}
"""

QUICK_SUMMARY_PROMPT = """请快速分析以下论文内容，输出严格合法的JSON格式（不要有任何JSON以外的内容）。

论文内容：
{paper_content}

输出：
{{
  "title": "论文标题",
  "one_liner": "一句话总结",
  "key_contributions": ["贡献1", "贡献2", "贡献3"],
  "method_summary": "方法简述（50字内）",
  "main_result": "最重要的实验结果",
  "novelty_score": 8.0,
  "recommend_deep_read": true,
  "tags": ["标签1", "标签2"]
}}
"""

COMPARATIVE_ANALYSIS_PROMPT = """请对以下多篇论文进行比较分析，输出严格合法的JSON格式。

论文摘要集合：
{papers_summary}

输出以下JSON结构：

{{
  "comparison_overview": {{
    "common_problem": "各论文共同解决的问题",
    "research_period": "时间跨度",
    "field_evolution": "该领域演进轨迹描述"
  }},
  "methodology_comparison": [
    {{"paper_id": "论文ID", "title": "标题简称", "approach": "方法简述", "key_differentiator": "核心区别点"}}
  ],
  "performance_comparison": {{
    "summary": "性能对比总结",
    "winner_by_task": [{{"task": "任务类型", "best_paper": "最优论文", "reason": "原因"}}]
  }},
  "innovation_timeline": [
    {{"paper_id": "论文ID", "innovation": "创新点", "builds_on": "基于哪些工作"}}
  ],
  "synthesis": {{
    "collective_contribution": "集体贡献总结",
    "remaining_gaps": ["仍存在的空白1"],
    "recommended_combination": "如何结合各论文优势"
  }},
  "recommendation": {{
    "best_for_practitioners": "对工程师最实用的论文",
    "best_for_researchers": "对研究者最有价值的论文",
    "reading_order": ["建议阅读顺序（论文ID列表）"]
  }}
}}
"""
