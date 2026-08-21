import React from 'react'
import { DISCLAIMER } from '../components/Layout.jsx'

export default function Pricing() {
  return (
    <div className="max-w-3xl">
      <h1 className="text-xl font-bold mb-1">Free forever — supported by people who can give</h1>
      <p className="text-sm text-slate-600 mb-4">
        A family facing cancer should never be blocked by a paywall at 2 a.m. Everything that
        affects safety or access is free for everyone, forever. People who are willing to pay can
        become supporters — they fund the free version for everyone else.
      </p>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mb-4">
        <div className="card border-l-4 border-l-green-500">
          <h2 className="font-semibold mb-2">✅ Free — everyone, always</h2>
          <ul className="list-disc ml-5 text-sm space-y-1 text-slate-600">
            <li>Case file, records &amp; timeline (manual + free PDF extraction)</li>
            <li>Guideline-sourced decision flags with citations</li>
            <li>Immutable second-opinion packages + PDF + share links</li>
            <li>Global centres comparison &amp; hidden-subsidy discovery</li>
            <li>Live worldwide trial search with importance context</li>
            <li>Coverage matching &amp; My Plan</li>
            <li>Data export &amp; one-click erasure (your rights)</li>
          </ul>
        </div>
        <div className="card border-l-4 border-l-blue-500">
          <h2 className="font-semibold mb-2">💙 Supporter — funds the mission</h2>
          <ul className="list-disc ml-5 text-sm space-y-1 text-slate-600">
            <li>My Plan shows deeper lists (top 12 vs top 6)</li>
            <li>Planned: multi-language plan output</li>
            <li>Planned: family co-account sharing</li>
            <li>Planned: priority human review of curated data</li>
          </ul>
          <p className="text-xs text-slate-500 mt-3">
            Suggested contribution: ₹200 / $5 per month. Payment collection is not wired up yet
            (deliberately zero-dependency) — see README for the Stripe/Razorpay swap point.
          </p>
        </div>
      </div>

      <div className="card mb-4 text-sm text-slate-600">
        <h2 className="font-semibold mb-1">Our promise</h2>
        <ul className="list-disc ml-5 space-y-1">
          <li>No ads. No selling data. Ever.</li>
          <li>No hospital or insurer can pay to change your ranking or your plan.</li>
          <li>If you have nothing, you still get everything essential above.</li>
        </ul>
      </div>

      <div className="bg-amber-100 border border-amber-300 rounded p-3 text-xs text-amber-900">
        ⚠️ {DISCLAIMER}
      </div>
    </div>
  )
}
