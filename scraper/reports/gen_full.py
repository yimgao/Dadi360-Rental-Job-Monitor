# -*- coding: utf-8 -*-
import json

# Content lines
data = {"lines": []}
l = data["lines"]
l.append("# Alphabet (GOOGL) 深度研究分析报告")

with open("content.json","w",encoding="utf-8") as f:
    json.dump(data,f,ensure_ascii=False)
print("done")