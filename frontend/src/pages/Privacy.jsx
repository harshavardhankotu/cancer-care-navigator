import React, { useEffect, useState } from 'react'
import { api } from '../api.js'
import { DISCLAIMER } from '../components/Layout.jsx'

export default function Privacy() {
  const [region, setRegion] = useState('IN')
  const [regionNote, setRegionNote] = useState(null)
  const [regimes, setRegimes] = useState(null)

  useEffect(() => {
    api('/legal/region-notes').then(setRegimes).catch(() => {})
  }, [])
  useEffect(() => {
    api(`/legal/region-notes?country=${region}`).then(setRegionNote).catch(() => {})
  }, [region])

  return (
    <div className="max-w-3xl">
      <h1 className="text-xl font-bold mb-1">Privacy notice</h1>
      <p className="text-xs text-slate-500 mb-3">
        Plain-language notice in line with the Digital Personal Data Protection Act, 2023 (India),
        GDPR-grade principles worldwide.
        <span className="ml-2 bg-amber-100 border border-amber-300 rounded px-1.5 py-0.5 text-amber-800 font-semibold">
          TEMPLATE — lawyer review required before real patient use
        </span>
      </p>

      <div className="card mb-3 border-l-4 border-l-blue-500">
        <label className="label">Laws where YOU are (select your country)</label>
        <select className="input max-w-xs mb-2" value={region} onChange={(e) => setRegion(e.target.value)}>
          {(regimes ? Object.keys(regimes) : ['IN']).map((code) => (
            <option key={code} value={code}>{code === 'EU' ? 'European Union' : code}</option>
          ))}
          {!regimes && <option value="IN">IN</option>}
          {!regimes && <option value="US">US</option>}
        </select>
        {regionNote && (
          <>
            <p className="text-sm font-semibold text-blue-800">{regionNote.law}</p>
            <ul className="list-disc ml-5 text-xs text-slate-600 mt-1 space-y-0.5">
              {regionNote.points.map((p, i) => <li key={i}>{p}</li>)}
            </ul>
            <p className="text-[11px] text-slate-400 mt-1">Complaints: {regionNote.regulator}. This summary is general information, not legal advice.</p>
          </>
        )}
      </div>

      <div className="card mb-3">
        <h2 className="font-semibold mb-1">What we collect — and exactly why</h2>
        <table className="text-sm w-full">
          <tbody>
            {[
              ['Email + password', 'Creating your account; logging you in. Password is stored only as a salted hash.'],
              ['Consent record (timestamp)', 'Legal proof that you agreed to processing. You can withdraw it any time.'],
              ['Case details you type (name/age/sex, cancer type, stage, status)', 'Building the case file and running the decision-flag engine against guideline rules.'],
              ['Documents you upload', 'Extracting dates/type/findings to build your timeline. Stored on our server\'s disk, never sold or shared.'],
              ['Financial profile fields (all optional)', 'Rules-based matching against public scheme criteria (PM-JAY/CGHS). No insurance APIs are queried.'],
              ['Wait-time reports you submit', 'Aggregated averages shown to other families. Not linked to your name in the UI.'],
              ['Opinion-request records', 'Tracking which doctors received your package and their responses.'],
            ].map(([k, v]) => (
              <tr key={k}><td className="pr-4 py-1 align-top font-medium whitespace-nowrap">{k}</td><td className="py-1 text-slate-600">{v}</td></tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="card mb-3">
        <h2 className="font-semibold mb-1">What we never do</h2>
        <ul className="list-disc ml-5 text-sm space-y-0.5 text-slate-600">
          <li>Sell, rent or share your data with advertisers, insurers, hospitals or brokers</li>
          <li>Send your data to third-party AI/diagnosis services</li>
          <li>Query insurance company APIs with your information</li>
          <li>Make automated decisions about your treatment</li>
        </ul>
      </div>

      <div className="card mb-3">
        <h2 className="font-semibold mb-1">Your rights (and how to use them here)</h2>
        <ul className="list-disc ml-5 text-sm space-y-1 text-slate-600">
          <li><strong>Access (s.11):</strong> Dashboard → Account → “Download my data” gives you everything we hold in machine-readable form.</li>
          <li><strong>Correction/completion/updating (s.12):</strong> edit any field directly in the app.</li>
          <li><strong>Erasure (s.12):</strong> Dashboard → Account → “Delete my account” erases everything immediately, including uploaded files. Withdrawal of consent is as easy as giving it.</li>
          <li><strong>Grievance redressal (s.13):</strong> write to the Grievance Officer below before approaching the Data Protection Board of India.</li>
          <li><strong>Nomination (s.14):</strong> email us a nominee who may exercise these rights if you are unable to.</li>
        </ul>
      </div>

      <div className="card mb-3">
        <h2 className="font-semibold mb-1">Children's data</h2>
        <p className="text-sm text-slate-600">
          If you add a patient under 18, the DPDP Act requires verifiable consent of a parent or
          lawful guardian. By adding a minor's details you confirm you are their parent or lawful
          guardian. (Certain healthcare providers may be notified-exempt by the government; we
          still ask for this confirmation.)
        </p>
      </div>

      <div className="card mb-3">
        <h2 className="font-semibold mb-1">Security &amp; breaches</h2>
        <p className="text-sm text-slate-600">
          Passwords are PBKDF2-hashed; every record is scoped to your account and checked
          server-side. If a breach affects your data we will inform you and report to the Data
          Protection Board within 72 hours, describing the breach, risks and remedies.
          Note: on free-tier hosting, uploaded files are stored on ephemeral disks — treat the
          platform as a working copy, not your only archive.
        </p>
      </div>

      <div className="card mb-3">
        <h2 className="font-semibold mb-1">Grievance Officer</h2>
        <p className="text-sm text-slate-600">
          [Name] · [email] · [address]
          <span className="ml-2 bg-amber-100 border border-amber-300 rounded px-1.5 py-0.5 text-[10px] font-semibold text-amber-800 uppercase">fill before launch — required publication</span>
        </p>
      </div>

      <div className="bg-amber-100 border border-amber-300 rounded p-3 text-xs text-amber-900">
        ⚠️ {DISCLAIMER}
      </div>
    </div>
  )
}
