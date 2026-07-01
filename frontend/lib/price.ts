/** Extract price info from listing title/fields */
export function extractPrice(title: string, salary?: string): { amount: number | null; label: string } {
  const t = title || "";

  // $1500 /月, $1500, $ 1500
  const dollar = t.match(/\$\s*(\d[\d,]*)/);
  if (dollar) return { amount: parseInt(dollar[1].replace(/,/g, "")), label: `$${dollar[1]}` };

  // 1500元, 1500/月
  const yuan = t.match(/(\d[\d,]*)\s*元/);
  if (yuan) return { amount: parseInt(yuan[1].replace(/,/g, "")), label: `${yuan[1]}元` };

  // 电议, 面议
  if (/电议|面议/i.test(t)) return { amount: null, label: "面议" };

  // 时薪 $23-27 → take the lower
  const range = t.match(/\$\s*(\d+)\s*[-~]\s*\$?\s*(\d+)/);
  if (range) return { amount: parseInt(range[1]), label: `$${range[1]}-${range[2]}` };

  return { amount: null, label: "" };
}
