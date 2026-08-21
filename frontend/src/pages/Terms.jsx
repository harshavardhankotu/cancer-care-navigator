import React from 'react'
import { DISCLAIMER } from '../components/Layout.jsx'

export default function Terms() {
  return (
    <div className="max-w-3xl">
      <h1 className="text-xl font-bold mb-1">Terms of use</h1>
      <p className="text-xs text-slate-500 mb-4">
        <span className="bg-amber-100 border border-amber-300 rounded px-1.5 py-0.5 text-amber-800 font-semibold">
          TEMPLATE — have a lawyer review before real patient use
        </span>
      </p>

      <div className="card mb-3">
        <h2 className="font-semibold mb-1">1. This is not medical advice</h2>
        <p className="text-sm text-slate-600">{DISCLAIMER} No doctor-patient relationship is created
        between you and this platform. Never start, stop or change treatment because of anything
        shown here — raise it with your treating oncologist instead.</p>
      </div>

      <div className="card mb-3">
        <h2 className="font-semibold mb-1">2. How we compare hospitals (and why we don't rank doctors)</h2>
        <ul className="list-disc ml-5 text-sm space-y-1 text-slate-600">
          <li>Centre comparisons use ONLY objective, publicly citable facts (ownership type,
          accreditation status, government scheme empanelment, capability lists) with a source link
          and as-of date on every fact. We publish the exact scoring weights in the app.</li>
          <li>We do not aggregate user reviews anywhere. Reviews are easy to buy, fake or game —
          relying on them would put families at risk.</li>
          <li><strong>Individual doctors are never scored or ranked.</strong> Doctor ratings invite
          gaming and defamation risk. The directory shows verifiable credential fields only, once a
          human curator has checked them against public registers (e.g., the National Medical
          Commission's Indian Medical Register).</li>
          <li>A fact being listed does not mean endorsement; an absence of a note means "not yet
          verified", not "bad".</li>
        </ul>
      </div>

      <div className="card mb-3">
        <h2 className="font-semibold mb-1">3. Community content rules</h2>
        <ul className="list-disc ml-5 text-sm space-y-1 text-slate-600">
          <li>Wait-time reports and similar submissions are user-generated opinions, shown as
          indicative only. We may edit or remove any submission.</li>
          <li>Do not post false, misleading or defamatory statements about any hospital, doctor or
          person. State only what you personally experienced.</li>
          <li>Genuine grievances about a hospital belong with official channels: the hospital's
          grievance desk, the consumer commission (e-Daakhil), the Clinical Establishments
          authority of your state, or the PM-JAY/NHA anti-fraud channels.</li>
          <li>You are responsible for what you submit and will indemnify the platform against
          claims arising from content you post.</li>
        </ul>
      </div>

      <div className="card mb-3">
        <h2 className="font-semibold mb-1">4. Accounts &amp; acceptable use</h2>
        <p className="text-sm text-slate-600">
          One account per family; you are responsible for keeping credentials safe. Only upload
          records you have the right to hold. Do not attempt to access other families' data — all
          access is logged server-side. Automated scraping of the directory is not permitted.
        </p>
      </div>

      <div className="card mb-3">
        <h2 className="font-semibold mb-1">5. Availability &amp; liability</h2>
        <p className="text-sm text-slate-600">
          The service runs on free-tier infrastructure and is provided “as is”, without warranty of
          uninterrupted availability (cold starts happen) or fitness for a particular purpose.
          To the maximum extent permitted by law, the platform's operators are not liable for
          decisions made based on information displayed here. Flagged risks are prompts for
          questions, not diagnoses or treatment plans.
        </p>
      </div>

      <div className="card mb-3">
        <h2 className="font-semibold mb-1">6. Governing law</h2>
        <p className="text-sm text-slate-600">
          These terms are governed by the laws of India; subject-matter jurisdiction lies with the
          courts at [city]. Data handling follows the Digital Personal Data Protection Act, 2023 —
          see the Privacy notice for details.
          <span className="ml-2 bg-amber-100 border border-amber-300 rounded px-1.5 py-0.5 text-[10px] font-semibold text-amber-800 uppercase">fill jurisdiction before launch</span>
        </p>
      </div>

      <div className="bg-amber-100 border border-amber-300 rounded p-3 text-xs text-amber-900">
        ⚠️ {DISCLAIMER}
      </div>
    </div>
  )
}
