"use client";

import { Info, Shield, FileText, ExternalLink } from "lucide-react";

export default function AboutPage() {
  return (
    <div className="space-y-8 animate-in fade-in duration-500 max-w-2xl">
      <div>
        <h1 className="text-2xl font-bold flex items-center gap-3">
          <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-brand-400 to-brand-600 flex items-center justify-center">
            <Info size={16} className="text-white" />
          </div>
          关于 / About
        </h1>
      </div>

      {/* Project Info */}
      <section className="rounded-2xl border border-surface-800 bg-surface-900/50 p-6 space-y-3">
        <h2 className="text-sm font-semibold text-surface-300 flex items-center gap-2">
          <Info size={14} className="text-brand-400" />
          聚职住 JobPulse
        </h2>
        <p className="text-sm text-surface-400 leading-relaxed">
          北美华人招聘·租房信息聚合监控平台。自动抓取多个华人社区的招聘和租房信息，
          集中展示和搜索，方便求职者和租房者一站式浏览。
        </p>
        <div className="text-sm text-surface-500 space-y-1">
          <p>数据来源 Data Sources:</p>
          <ul className="list-disc list-inside space-y-0.5 text-surface-400 ml-2">
            <li><a href="https://c.dadi360.com" target="_blank" rel="noopener noreferrer" className="text-brand-400 hover:underline">c.dadi360.com</a> — 纽约华人论坛</li>
            <li><a href="https://www.168worker.com" target="_blank" rel="noopener noreferrer" className="text-brand-400 hover:underline">168worker.com</a> — 华人找工网</li>
            <li><a href="https://www.us168168.com" target="_blank" rel="noopener noreferrer" className="text-brand-400 hover:underline">us168168.com</a> — 华人168</li>
          </ul>
        </div>
        <p className="text-xs text-surface-600">
          本项目为个人学习研究用途，非商业项目。
        </p>
      </section>

      {/* Disclaimer */}
      <section className="rounded-2xl border border-amber-500/20 bg-amber-500/5 p-6 space-y-3">
        <h2 className="text-sm font-semibold text-amber-400 flex items-center gap-2">
          <Shield size={14} />
          免责声明 Disclaimer
        </h2>
        <div className="text-sm text-surface-400 leading-relaxed space-y-2">
          <p>
            本平台仅作为信息聚合展示工具，所有数据均来自公开的第三方网站。
            信息的真实性、准确性和完整性由原始发布方负责。
          </p>
          <p>
            本平台不对任何用户因使用本服务而遭受的任何直接或间接损失承担责任。
            用户在使用信息时应自行核实。
          </p>
          <p>
            如果您是原始数据的所有者，认为某些内容侵犯了您的权益，
            请通过下方联系方式与我们联系，我们将在核实后尽快处理。
          </p>
        </div>
      </section>

      {/* Copyright */}
      <section className="rounded-2xl border border-surface-800 bg-surface-900/50 p-6 space-y-3">
        <h2 className="text-sm font-semibold text-surface-300 flex items-center gap-2">
          <FileText size={14} className="text-brand-400" />
          侵权联系 Copyright &amp; Takedown
        </h2>
        <div className="text-sm text-surface-400 leading-relaxed space-y-1">
          <p>如涉及版权或内容侵权，请通过以下方式联系我们：</p>
          <p className="mt-2 font-mono text-surface-300 bg-surface-800 px-3 py-1.5 rounded-lg inline-block text-xs">
            yimgao99@gmail.com
          </p>
          <p className="mt-2 text-xs text-surface-500">
            我们承诺在收到通知后 48 小时内响应并处理。
          </p>
        </div>
      </section>

      {/* GitHub */}
      <section className="rounded-2xl border border-surface-800 bg-surface-900/50 p-6 space-y-3">
        <h2 className="text-sm font-semibold text-surface-300 flex items-center gap-2">
          <ExternalLink size={14} className="text-brand-400" />
          开源 Open Source
        </h2>
        <p className="text-sm text-surface-400">
          本项目开源在 GitHub：
        </p>
        <a
          href="https://github.com/yimgao/Dadi360-Rental-Job-Monitor"
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-1.5 text-sm text-brand-400 hover:text-brand-300 transition-colors font-mono"
        >
          yimgao/Dadi360-Rental-Job-Monitor <ExternalLink size={12} />
        </a>
        <p className="text-xs text-surface-600 mt-2">
          MIT License &copy; {new Date().getFullYear()}
        </p>
      </section>
    </div>
  );
}
