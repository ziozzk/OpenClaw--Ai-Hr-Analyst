import re
from typing import Dict, List, Tuple

def parse_interview_notes(notes: str) -> Dict[str, List[str]]:
    """
    解析面试笔记，分离事实/观点/推论
    
    Args:
        notes: 面试笔记文本
    
    Returns:
        包含事实、观点、推论的字典
    """
    # 定义关键词模式
    fact_keywords = [
        r'他说', r'她提到', r'候选人表示', r'回答是', r'结果显示', r'数据显示',
        r'拥有.*年经验', r'毕业于', r'学历', r'工作经历', r'项目经验', r'掌握.*技术',
        r'时间:', r'地点:', r'数量:', r'金额:', r'规模:', r'时长:'
    ]
    
    opinion_keywords = [
        r'我觉得', r'我认为', r'看起来', r'似乎', r'感觉', r'印象',
        r'优秀', r'良好', r'一般', r'较差', r'出色', r'不错', r'有待提高',
        r'强', r'弱', r'好', r'差', r'积极', r'消极', r'自信', r'紧张'
    ]
    
    inference_keywords = [
        r'可能', r'应该', r'推测', r'估计', r'假设', r'意味着', r'表明',
        r'由此看来', r'因此', r'所以', r'如果.*那么', r'这说明', r'这暗示',
        r'潜在', r'未来', r'趋势', r'发展', r'成长性', r'适应性'
    ]
    
    # 初始化结果
    facts = []
    opinions = []
    inferences = []
    
    # 按句子分割笔记
    sentences = re.split(r'[.!?。！？\n]+', notes)
    
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
            
        # 检查是否包含事实关键词
        is_fact = any(re.search(keyword, sentence) for keyword in fact_keywords)
        # 检查是否包含观点关键词
        is_opinion = any(re.search(keyword, sentence) for keyword in opinion_keywords)
        # 检查是否包含推论关键词
        is_inference = any(re.search(keyword, sentence) for keyword in inference_keywords)
        
        # 根据检测结果分类
        if is_fact and not is_opinion and not is_inference:
            facts.append(sentence)
        elif is_opinion and not is_fact and not is_inference:
            opinions.append(sentence)
        elif is_inference and not is_fact and not is_opinion:
            inferences.append(sentence)
        # 如果同时包含多种类型，可以根据优先级分配
        elif is_fact and is_opinion:
            # 如果既有事实又有观点，归类为事实
            facts.append(sentence)
        elif is_fact and is_inference:
            # 如果既有事实又有推论，归类为事实
            facts.append(sentence)
        elif is_opinion and is_inference:
            # 如果既有观点又有推论，归类为观点
            opinions.append(sentence)
        else:
            # 如果都不匹配，根据上下文判断
            if any(word in sentence for word in ['技术', '经验', '项目', '学历', '公司', '职位', '时间']):
                facts.append(sentence)
            elif any(word in sentence for word in ['觉得', '认为', '印象', '感觉', '表现']):
                opinions.append(sentence)
            else:
                # 默认归为事实
                facts.append(sentence)
    
    # 返回结果
    return {
        "facts": facts,
        "opinions": opinions,
        "inferences": inferences
    }

def extract_focus_points_and_issues(parsed_notes: Dict[str, List[str]]) -> Dict[str, List[str]]:
    """
    从解析后的面试笔记中提取聚焦点和待解决问题
    
    Args:
        parsed_notes: 解析后的面试笔记字典
    
    Returns:
        包含聚焦点和待解决问题的字典
    """
    focus_points = []
    pending_issues = []
    
    # 从所有类型的笔记中提取聚焦点和待解决问题
    all_sentences = []
    all_sentences.extend(parsed_notes["facts"])
    all_sentences.extend(parsed_notes["opinions"])
    all_sentences.extend(parsed_notes["inferences"])
    
    # 聚焦点关键词
    focus_keywords = [
        r'重点考察', r'关注.*方面', r'聚焦.*领域', r'核心能力', r'关键技术',
        r'专业技能', r'沟通能力', r'团队合作', r'问题解决', r'学习能力',
        r'技术深度', r'项目经验', r'架构思维', r'领导力', r'创新思维'
    ]
    
    # 待解决问题关键词
    issue_keywords = [
        r'需要确认', r'有待验证', r'不清楚', r'不了解', r'疑问',
        r'待核实', r'需进一步了解', r'还需要', r'不足', r'欠缺',
        r'有问题', r'存在风险', r'需要注意', r'有疑虑', r'不确定'
    ]
    
    # 提取聚焦点
    for sentence in all_sentences:
        for keyword in focus_keywords:
            if re.search(keyword, sentence):
                focus_points.append(sentence)
                break
    
    # 提取待解决问题
    for sentence in all_sentences:
        for keyword in issue_keywords:
            if re.search(keyword, sentence):
                pending_issues.append(sentence)
                break
    
    # 如果没有明确标识，根据内容类型推测
    if not focus_points:
        # 从观点和推论中提取可能的聚焦点
        focus_points.extend(parsed_notes["opinions"][-2:])  # 取最后几个观点作为聚焦点
        focus_points.extend(parsed_notes["inferences"][:2])  # 取前几个推论作为聚焦点
    
    if not pending_issues:
        # 从推论和观点中查找可能的问题
        for sentence in parsed_notes["inferences"]:
            if any(word in sentence for word in ['如果', '可能', '待验证', '不确定']):
                pending_issues.append(sentence)
        for sentence in parsed_notes["opinions"]:
            if any(word in sentence for word in ['有待提高', '需注意', '不够', '不足']):
                pending_issues.append(sentence)
    
    return {
        "focus_points": list(set(focus_points)),  # 去重
        "pending_issues": list(set(pending_issues))  # 去重
    }

def generate_candidate_summary(parsed_notes: Dict[str, List[str]], candidate_name: str = "候选人") -> str:
    """
    生成候选人评估摘要
    
    Args:
        parsed_notes: 解析后的面试笔记字典
        candidate_name: 候选人姓名
    
    Returns:
        候选人评估摘要字符串
    """
    summary = f"# {candidate_name} 面试评估摘要\n\n"
    
    # 事实部分
    if parsed_notes["facts"]:
        summary += "## 事实记录\n\n"
        for i, fact in enumerate(parsed_notes["facts"], 1):
            summary += f"{i}. {fact}\n"
        summary += "\n"
    
    # 观点部分
    if parsed_notes["opinions"]:
        summary += "## 面试官观点\n\n"
        for i, opinion in enumerate(parsed_notes["opinions"], 1):
            summary += f"{i}. {opinion}\n"
        summary += "\n"
    
    # 推论部分
    if parsed_notes["inferences"]:
        summary += "## 面试官推论\n\n"
        for i, inference in enumerate(parsed_notes["inferences"], 1):
            summary += f"{i}. {inference}\n"
        summary += "\n"
    
    return summary

def process_interview_notes(notes: str, candidate_name: str = "候选人") -> str:
    """
    完整处理面试笔记的函数
    
    Args:
        notes: 原始面试笔记
        candidate_name: 候选人姓名
    
    Returns:
        完整的面试分析报告
    """
    # 解析笔记
    parsed_notes = parse_interview_notes(notes)
    
    # 提取聚焦点和待解决问题
    focus_and_issues = extract_focus_points_and_issues(parsed_notes)
    
    # 生成摘要
    summary = generate_candidate_summary(parsed_notes, candidate_name)
    
    # 组合完整报告
    report = summary
    
    report += "## 本轮面试聚焦点\n\n"
    if focus_and_issues["focus_points"]:
        for i, point in enumerate(focus_and_issues["focus_points"], 1):
            report += f"{i}. {point}\n"
    else:
        report += "无明确聚焦点\n"
    report += "\n"
    
    report += "## 待解决问题\n\n"
    if focus_and_issues["pending_issues"]:
        for i, issue in enumerate(focus_and_issues["pending_issues"], 1):
            report += f"{i}. {issue}\n"
    else:
        report += "无待解决问题\n"
    
    return report

if __name__ == "__main__":
    # 示例用法
    sample_notes = """
    候选人张三有5年Java开发经验，毕业于清华大学计算机系。
    我觉得他的技术基础很扎实，特别是在分布式系统方面。
    他参与过大型电商系统的重构项目，担任核心开发角色。
    他提到在项目中使用了微服务架构，解决了性能瓶颈问题。
    但是感觉他在软技能方面可能有所欠缺，沟通表达略显生硬。
    如果他能加强沟通能力，可能会更适合团队合作。
    候选人的项目经验丰富，但可能需要进一步验证其系统设计能力。
    """
    
    result = process_interview_notes(sample_notes, "张三")
    print(result)