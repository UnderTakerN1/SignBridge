import { BrowserRouter, Routes, Route } from 'react-router-dom'
import LandingScreen from './pages/LandingScreen'
import PatientModeSelect from './pages/PatientModeSelect'
import PatientScreen from './pages/PatientScreen'
import StaffScreen from './pages/StaffScreen'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<LandingScreen />} />
        <Route path="/patient" element={<PatientModeSelect />} />
        <Route path="/patient/:mode" element={<PatientScreen />} />
        <Route path="/staff" element={<StaffScreen />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App