import json, os
d = {"lines": []}
l = d["lines"]

l.append("# Alphabet (GOOGL) 深度研究分析报告")
l.append("")
l.append("> 角色：段永平（步步高/OPPO/vivo 投资人视角）")
l.append("> 分析日期：2026年6月")
l.append("")
l.append("---")
l.append("")
l.append("## 一、商业模式拆解：核心是“注意力拍卖”")
l.append("")
l.append("### 1.1 收入结构（2025年年报口径）")
l.append("")
l.append("| 业务板块 | 2025年收入 | 占比 | 利润率特征 | 本质 |")
l.append("|---------|-----------|------|-----------|------|")
l.append("| Google Search & Other | ~,750亿 | ~57% | 超高利润率(70%+运营利润率) | 全球最大注意力拍卖平台 |")
l.append("| YouTube Ads | ~60亿 | ~12% | 高利润率(60%+) | 视频版搜索广告 |")
l.append("| Google Cloud | ~30亿 | ~14% | 2025年首次盈利(运营利润~0亿) | 第二增长曲线 |")
l.append("| **总计** | **~,100亿** | **100%** | FCF margin ~25-28% | --- |")
l.append("")
l.append("---")
l.append("")

with open("content.json", "w", encoding="utf-8") as f:
    json.dump(d, f, ensure_ascii=False)
print("Script generated content.json with", len(l), "lines")