import json
import pandas as pd
from typing import List, Dict, Any

def compare_candidates(candidates_data: List[Dict[str, Any]], output_format: str = "markdown") -> str:
    """
    对比多个候选人，标出差异与风险点
    
    Args:
        candidates_data: 候选人数据列表
        output_format: 输出格式 ('markdown', 'csv', 'json')
    
    Returns:
        对比结果字符串
    """
    if output_format == "markdown":
        # 创建Markdown格式的对比表格
        headers = ["维度"]
        for candidate in candidates_data:
            headers.append(candidate.get("姓名", "未知"))
        
        # 构建表格行
        rows = []
        
        # 基本信息对比
        rows.append(["姓名"] + [c.get("姓名", "") for c in candidates_data])
        rows.append(["工作年限"] + [str(c.get("工作年限", "")) for c in candidates_data])
        rows.append(["当前公司"] + [c.get("当前公司", "") for c in candidates_data])
        rows.append(["当前职位"] + [c.get("当前职位", "") for c in candidates_data])
        rows.append(["期望薪资"] + [c.get("期望薪资", "") for c in candidates_data])
        
        # 技能对比
        all_skills = set()
        for c in candidates_data:
            skills = c.get("技能栈", {}).get("技术技能", [])
            if isinstance(skills, list):
                all_skills.update(skills)
            elif isinstance(skills, str):
                all_skills.add(skills)
        
        for skill in sorted(list(all_skills)):
            skill_row = [f"技能: {skill}"]
            for c in candidates_data:
                c_skills = c.get("技能栈", {}).get("技术技能", [])
                if isinstance(c_skills, list) and skill in c_skills:
                    skill_row.append("✅")
                elif isinstance(c_skills, str) and skill in c_skills:
                    skill_row.append("✅")
                else:
                    skill_row.append("❌")
            rows.append(skill_row)
        
        # 匹配度对比
        rows.append(["匹配度评分"] + [str(c.get("匹配度评分", "")) for c in candidates_data])
        
        # 风险点对比
        all_risks = set()
        for c in candidates_data:
            risks = c.get("风险评估", [])
            if isinstance(risks, list):
                all_risks.update(risks)
            elif isinstance(risks, str):
                all_risks.add(risks)
        
        for risk in sorted(list(all_risks)):
            risk_row = [f"风险: {risk}"]
            for c in candidates_data:
                c_risks = c.get("风险评估", [])
                if isinstance(c_risks, list) and risk in c_risks:
                    risk_row.append("🔴")
                elif isinstance(c_risks, str) and risk in c_risks:
                    risk_row.append("🔴")
                else:
                    risk_row.append("")
            rows.append(risk_row)
        
        # 生成Markdown表格
        md_result = "## 候选人对比\n\n"
        md_result += "| " + " | ".join(headers) + " |\n"
        md_result += "| " + " | ".join(["---"] * len(headers)) + " |\n"
        
        for row in rows:
            md_result += "| " + " | ".join(row) + " |\n"
        
        # 添加总结部分
        md_result += "\n## 对比总结\n\n"
        for i, candidate in enumerate(candidates_data):
            name = candidate.get("姓名", f"候选人{i+1}")
            strengths = candidate.get("优势项", [])
            if isinstance(strengths, list):
                strengths_str = ", ".join(strengths[:3])  # 显示前3个优势
            else:
                strengths_str = str(strengths)
            
            risks = candidate.get("风险评估", [])
            if isinstance(risks, list):
                risks_str = ", ".join(risks[:2])  # 显示前2个风险
            else:
                risks_str = str(risks)
                
            md_result += f"### {name}\n"
            md_result += f"- **优势**: {strengths_str}\n"
            md_result += f"- **风险**: {risks_str}\n"
            md_result += f"- **综合建议**: {candidate.get('建议', '')}\n\n"
        
        return md_result
    
    elif output_format == "csv":
        # 转换为DataFrame并返回CSV
        df_rows = []
        all_keys = set()
        for c in candidates_data:
            all_keys.update(c.keys())
        
        for key in sorted(list(all_keys)):
            row = [key]
            for c in candidates_data:
                value = c.get(key, "")
                if isinstance(value, (list, dict)):
                    value = str(value)
                row.append(str(value))
            df_rows.append(row)
        
        # 创建DataFrame
        headers = ["维度"]
        for candidate in candidates_data:
            headers.append(candidate.get("姓名", "未知"))
        
        df = pd.DataFrame(df_rows, columns=headers)
        return df.to_csv(index=False)
    
    elif output_format == "json":
        return json.dumps(candidates_data, ensure_ascii=False, indent=2)
    
    else:
        raise ValueError(f"Unsupported output format: {output_format}")

if __name__ == "__main__":
    # 示例用法
    candidates = [
        {
            "姓名": "张三",
            "工作年限": 5,
            "当前公司": "ABC科技",
            "当前职位": "高级工程师",
            "期望薪资": "35k",
            "技能栈": {"技术技能": ["Python", "Go", "Kubernetes"]},
            "匹配度评分": 82,
            "优势项": ["技术能力强", "团队协作好", "项目经验丰富"],
            "风险评估": ["薪资期望较高"],
            "建议": "推荐面试"
        },
        {
            "姓名": "李四",
            "工作年限": 7,
            "当前公司": "XYZ互联网",
            "当前职位": "技术专家",
            "期望薪资": "45k",
            "技能栈": {"技术技能": ["Java", "Go", "微服务"]},
            "匹配度评分": 87,
            "优势项": ["经验丰富", "架构能力强", "领导力好"],
            "风险评估": ["薪资期望高", "可能跳槽频繁"],
            "建议": "强烈推荐"
        }
    ]
    
    result = compare_candidates(candidates, "markdown")
    print(result)