import Link from "next/link";

export function Footer() {
  return (
    <footer className="border-t border-surface-800 bg-surface-900/50 mt-auto">
      <div className="max-w-6xl mx-auto px-4 py-6 flex flex-col sm:flex-row items-center justify-between gap-3 text-xs text-surface-500">
        <span>
          聚职住 <span className="font-mono">JobPulse</span> &mdash; 北美华人招聘·租房信息聚合监控
        </span>
        <div className="flex items-center gap-4">
          <Link href="/about" className="hover:text-surface-300 transition-colors">
            关于 / About
          </Link>
          <span>
            数据来源: c.dadi360 / 168worker / us168168
          </span>
        </div>
      </div>
    </footer>
  );
}
