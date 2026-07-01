#!/usr/bin/env python3
content = open("/dev/stdin").read()
with open("/Users/yimgao/dev/dadi360/scraper/qorvo_risk_assessment.md", "w") as f:
    f.write(content)
print("Written", len(content), "bytes")
