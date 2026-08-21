import React from 'react'
import { Route, Routes } from 'react-router-dom'
import { AuthProvider, RequireAuth } from './auth.jsx'
import Layout from './components/Layout.jsx'
import Login from './pages/Login.jsx'
import Register from './pages/Register.jsx'
import Dashboard from './pages/Dashboard.jsx'
import CaseDetail from './pages/CaseDetail.jsx'
import Centers from './pages/Centers.jsx'
import Doctors from './pages/Doctors.jsx'
import CoverageCheck from './pages/CoverageCheck.jsx'
import PackageShareView from './pages/PackageShareView.jsx'
import Privacy from './pages/Privacy.jsx'
import Terms from './pages/Terms.jsx'
import Pricing from './pages/Pricing.jsx'

export default function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/package/:pkgId/:token" element={<PackageShareView />} />
        <Route element={<Layout />}>
          <Route path="/" element={<RequireAuth><Dashboard /></RequireAuth>} />
          <Route path="/cases/:id" element={<RequireAuth><CaseDetail /></RequireAuth>} />
          <Route path="/centers" element={<Centers />} />
          <Route path="/doctors" element={<RequireAuth><Doctors /></RequireAuth>} />
          <Route path="/coverage-check" element={<CoverageCheck />} />
          <Route path="/privacy" element={<Privacy />} />
          <Route path="/terms" element={<Terms />} />
          <Route path="/support" element={<Pricing />} />
        </Route>
      </Routes>
    </AuthProvider>
  )
}
